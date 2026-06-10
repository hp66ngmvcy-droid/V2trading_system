from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from tar_system.backtest.engine import BacktestResult
from tar_system.assets.registry import get_asset_profile, list_asset_profiles
from tar_system.assets.profiles import ASSET_PROFILES
from tar_system.brokers.registry import list_missing_symbols, load_broker_profile
from tar_system.cli import build_parser, show_broker_cmd
from tar_system.execution.paper_broker import PaperBroker
from tar_system.execution.paper_broker import Fill
from tar_system.portfolio.tracker import PortfolioTracker
from tar_system.risk.engine import RiskEngine
from tar_system.risk.position_sizer import size_position
from tar_system.strategies.resolver import resolve_strategy
from tar_system.strategies.base import Signal


def test_asset_profiles_load_required_symbols() -> None:
    symbols = {profile.symbol for profile in list_asset_profiles()}
    assert {"BTCUSD", "ETHUSD", "XRPUSD", "XAUUSD", "XAGUSD", "USOUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD"}.issubset(symbols)
    btc = get_asset_profile("BTCUSD")
    assert btc.asset_class == "crypto"
    assert btc.risk_limit < 0.02


def test_asset_profiles_have_required_fields() -> None:
    for profile in list_asset_profiles():
        payload = profile.to_dict()
        for field in ("asset_class", "volatility_level", "session_model", "available"):
            assert field in payload
    assert get_asset_profile("USOUSD").session_model == "LONDON_NY"
    assert get_asset_profile("BTCUSD").session_model == "ALL_HOURS"
    assert get_asset_profile("XAGUSD").available is False


def test_broker_profile_loads_paper_only_symbol_settings() -> None:
    broker = load_broker_profile("current_broker_demo")
    assert broker.paper_mode_only is True
    assert broker.max_leverage == 500
    assert broker.symbol_profile("XAUUSD").contract_size == 100
    assert broker.symbol_profile("XAGUSD").contract_size == 5000
    assert list_missing_symbols(broker, ASSET_PROFILES) == []


def test_broker_profile_fallback_warns_without_crashing(caplog) -> None:
    broker = load_broker_profile("current_broker_demo")
    with caplog.at_level("WARNING"):
        fallback = broker.symbol_profile("UNKNOWN")
    assert fallback.contract_size == 1
    assert fallback.spread_model == "medium"
    assert "not in broker config" in caplog.text


def test_strategy_variant_resolves_by_strategy_symbol_timeframe() -> None:
    resolved = resolve_strategy("gold_v2", "BTCUSD", "M5", "current_broker_demo")
    assert resolved.variant.variant_name == "gold_v2_btcusd_m5"
    assert resolved.variant.parameters["atr_multiplier"] == 2.2
    assert resolved.asset_profile.symbol == "BTCUSD"
    assert resolved.broker_profile.symbol_profile("BTCUSD").min_lot_size == 0.01


def test_paper_broker_margin_calculation_never_uses_full_leverage() -> None:
    broker_profile = load_broker_profile("current_broker_demo")
    asset = get_asset_profile("BTCUSD")
    signal = Signal(
        timestamp=pd.Timestamp("2026-01-01"),
        symbol="BTCUSD",
        timeframe="M5",
        strategy="gold_v2",
        version="0.1.0",
        side="BUY",
        confidence=0.8,
        entry=50000,
        stop_loss=49000,
        take_profit=52000,
        reason_code="SIGNAL_BUY",
    )
    estimate = PaperBroker().estimate_margin(signal, broker_profile, asset, account_equity=10_000)
    assert estimate.notional_exposure < 10_000 * broker_profile.max_leverage
    assert estimate.margin_utilisation < 0.5
    assert estimate.spread_cost >= 0
    assert estimate.slippage_cost >= 0


def test_fixed_risk_pct_xauusd_position_size_is_point_two_lots() -> None:
    broker = load_broker_profile("current_broker_demo")
    asset = get_asset_profile("XAUUSD")
    size = size_position("FIXED_RISK_PCT", "XAUUSD", 2000.0, 10000.0, broker, asset, stop_distance=5.0, risk_pct=0.01)
    assert size.recommended_lot == 0.2
    assert size.risk_amount == 100


def test_atr_sizing_uses_symbol_specific_stop_multiplier() -> None:
    broker = load_broker_profile("current_broker_demo")
    xau = size_position("ATR_BASED", "XAUUSD", 2000.0, 10000.0, broker, get_asset_profile("XAUUSD"), atr=2.5, risk_pct=0.01)
    btc = size_position("ATR_BASED", "BTCUSD", 50000.0, 10000.0, broker, get_asset_profile("BTCUSD"), atr=100.0, risk_pct=0.01)
    assert xau.recommended_lot == 0.2
    assert btc.recommended_lot == 0.33


def test_half_kelly_is_half_full_kelly() -> None:
    broker = load_broker_profile("current_broker_demo")
    size = size_position("HALF_KELLY", "XAUUSD", 10.0, 10000.0, broker, get_asset_profile("XAUUSD"), win_rate=0.6, avg_win=2.0, avg_loss=1.0)
    assert size.recommended_lot == 20.0


def test_position_size_caps_floor_and_leverage_limit() -> None:
    broker = load_broker_profile("current_broker_demo")
    asset = get_asset_profile("XAUUSD")
    capped = size_position("FIXED_RISK_PCT", "XAUUSD", 2000.0, 10000.0, broker, asset, stop_distance=0.01, risk_pct=0.5)
    floored = size_position("FIXED_RISK_PCT", "XAUUSD", 2000.0, 10000.0, broker, asset, stop_distance=10000.0, risk_pct=0.0001)
    assert capped.capped is True
    assert capped.effective_leverage <= broker.max_leverage * 0.1
    assert floored.recommended_lot == broker.symbol_profile("XAUUSD").min_lot_size


def test_asset_class_exposure_cap_blocks_oversizing() -> None:
    broker = load_broker_profile("current_broker_demo")
    size = size_position("FIXED_LOT", "XAUUSD", 2000.0, 10000.0, broker, get_asset_profile("XAUUSD"), current_asset_class_exposure=3000.0)
    assert size.recommended_lot == 0
    assert size.reason == "ASSET_CLASS_EXPOSURE_LIMIT"


def test_swap_cost_points_type_known_inputs() -> None:
    broker_profile = load_broker_profile("current_broker_demo")
    symbol_profile = broker_profile.symbol_profile("XAUUSD")
    swap_cost, days = PaperBroker().calculate_swap_cost(symbol_profile, "BUY", lots=2.0, notional=10000.0, timeframe="D1", bars_held=3)
    assert days == 3
    assert swap_cost == -93.44 * 2 * 3


def test_swap_cost_percentage_type_known_inputs() -> None:
    broker_profile = load_broker_profile("current_broker_demo")
    symbol_profile = broker_profile.symbol_profile("BTCUSD")
    swap_cost, days = PaperBroker().calculate_swap_cost(symbol_profile, "BUY", lots=1.0, notional=36500.0, timeframe="D1", bars_held=1)
    assert days == 1
    assert round(swap_cost, 6) == -30.0


def test_spread_applied_on_entry_and_exit() -> None:
    broker_profile = load_broker_profile("current_broker_demo")
    signal_buy = Signal(pd.Timestamp("2026-01-01"), "EURUSD", "M15", "gold_v2", "0.1", "BUY", 0.8, 1.1000, 1.0, 1.2, "BUY")
    signal_sell = Signal(pd.Timestamp("2026-01-01"), "EURUSD", "M15", "gold_v2", "0.1", "SELL", 0.8, 1.1000, 1.2, 1.0, "SELL")
    buy_fill = PaperBroker(random_seed=1).execute(signal_buy, broker_profile=broker_profile)
    sell_fill = PaperBroker(random_seed=1).execute(signal_sell, broker_profile=broker_profile)
    assert buy_fill.price > signal_buy.entry
    assert sell_fill.price < signal_sell.entry
    assert buy_fill.spread_cost > 0
    assert sell_fill.spread_cost > 0


def test_slippage_within_model_range() -> None:
    broker_profile = load_broker_profile("current_broker_demo")
    signal = Signal(pd.Timestamp("2026-01-01"), "EURUSD", "M15", "gold_v2", "0.1", "BUY", 0.8, 1.1000, 1.0, 1.2, "BUY")
    fill = PaperBroker(random_seed=2).execute(signal, broker_profile=broker_profile)
    assert 0 <= float(fill.metadata["slippage"]) <= 0.2 * 0.0001


def test_oil_overnight_holding_flags_high_swap_drag(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    broker_profile = load_broker_profile("current_broker_demo")
    asset = get_asset_profile("USOUSD")
    signal = Signal(
        timestamp=pd.Timestamp("2026-01-01"),
        symbol="USOUSD",
        timeframe="M15",
        strategy="gold_v2",
        version="0.1.0",
        side="SELL",
        confidence=0.8,
        entry=70.0,
        stop_loss=72.0,
        take_profit=66.0,
        reason_code="SIGNAL_SELL",
    )
    estimate = PaperBroker().estimate_margin(signal, broker_profile, asset, account_equity=10_000, holding_bars=2, held_overnight=True)
    assert "HIGH_SWAP_DRAG" in estimate.reason_codes
    assert estimate.swap == -134.5588


def test_swap_drag_gate_fires_above_threshold() -> None:
    signal = Signal(pd.Timestamp("2026-01-01"), "USOUSD", "M15", "gold_v2", "0.1", "SELL", 0.8, 70.0, 72.0, 66.0, "SELL")
    decision = RiskEngine().evaluate(signal, expected_swap_drag=0.31)
    assert not decision.approved
    assert decision.reason_code == "HIGH_SWAP_DRAG"


def _loss_fill(timestamp: str, pnl: float) -> tuple[Fill, Fill]:
    entry = Fill(pd.Timestamp(timestamp), "XAUUSD", "BUY", 1.0, 100.0, 0.0, {})
    exit_price = 100.0 + pnl
    exit_fill = Fill(pd.Timestamp(timestamp) + pd.Timedelta(minutes=15), "XAUUSD", "SELL", 1.0, exit_price, 0.0, {})
    return entry, exit_fill


def test_consecutive_loss_gate_blocks_at_limit_and_resets_on_win() -> None:
    portfolio = PortfolioTracker(10000)
    for day, pnl in enumerate([-1.0, -1.0, 1.0, -1.0], start=1):
        entry, exit_fill = _loss_fill(f"2026-01-0{day}", pnl)
        portfolio.on_fill(entry)
        portfolio.on_fill(exit_fill)
    assert portfolio.consecutive_losses() == 1
    entry, exit_fill = _loss_fill("2026-01-05", -1.0)
    portfolio.on_fill(entry)
    portfolio.on_fill(exit_fill)
    entry, exit_fill = _loss_fill("2026-01-06", -1.0)
    portfolio.on_fill(entry)
    portfolio.on_fill(exit_fill)
    decision = RiskEngine().evaluate(
        Signal(pd.Timestamp("2026-01-07"), "XAUUSD", "M15", "gold_v2", "0.1", "BUY", 0.8, 100, 99, 102, "BUY"),
        consecutive_losses=portfolio.consecutive_losses(),
    )
    assert portfolio.consecutive_losses() == 3
    assert not decision.approved
    assert decision.reason_code == "CONSECUTIVE_LOSS_LIMIT"


def test_daily_loss_limit_blocks_correctly() -> None:
    decision = RiskEngine().evaluate(
        Signal(pd.Timestamp("2026-01-01"), "XAUUSD", "M15", "gold_v2", "0.1", "BUY", 0.8, 100, 99, 102, "BUY"),
        daily_loss_pct=0.021,
    )
    assert not decision.approved
    assert decision.reason_code == "DAILY_LOSS_LIMIT"


def test_equity_curve_exports_cumulative_cost(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    portfolio = PortfolioTracker(10000)
    entry = Fill(pd.Timestamp("2026-01-01"), "XAUUSD", "BUY", 1.0, 100.0, 0.0, {}, total_cost=1.0)
    exit_fill = Fill(pd.Timestamp("2026-01-02"), "XAUUSD", "SELL", 1.0, 110.0, 0.0, {}, total_cost=2.0)
    portfolio.on_fill(entry)
    portfolio.on_fill(exit_fill)
    path = portfolio.export_equity_curve("XAUUSD", "M15", "gold_v2")
    assert "cumulative_cost" in path.read_text(encoding="utf-8")


def test_cost_analysis_four_tiers_and_sensitive_flag(monkeypatch) -> None:
    import tar_system.validation.cost_analysis as cost_analysis

    monkeypatch.setattr(cost_analysis, "load_feature_data", lambda symbol, timeframe: pd.DataFrame({"timestamp": [pd.Timestamp("2026-01-01")]}))
    monkeypatch.setattr(cost_analysis, "resolve_strategy", lambda *args: SimpleNamespace(strategy=object(), broker_profile=object(), asset_profile=object()))

    def fake_backtest(*args: object, **kwargs: object) -> BacktestResult:
        multiplier = float(kwargs["cost_multiplier"])
        return BacktestResult(
            metrics={
                "total_trades": 40.0,
                "win_rate": 0.6,
                "profit_factor": 1.8,
                "max_drawdown": 0.1,
                "expectancy": 10.0,
                "gross_profit": 100.0,
                "swap_cost": multiplier * 10,
                "total_cost": multiplier * 50,
            },
            trades=40,
            final_equity=10000,
        )

    monkeypatch.setattr(cost_analysis, "run_backtest", fake_backtest)
    monkeypatch.setattr(cost_analysis, "score_strategy", lambda metrics: SimpleNamespace(score=100 - metrics["total_cost"]))
    result = cost_analysis.run_cost_analysis("gold_v2", "XAUUSD", "M15", "current_broker_demo")
    assert set(result.tiers) == {"gross", "realistic", "stressed", "extreme"}
    assert result.gross_score == 100
    assert result.realistic_score == 50
    assert result.cost_sensitive is True
    assert result.swap_drag == 0.1


def test_resolve_strategy_cli_command_exists() -> None:
    commands = build_parser()._subparsers._group_actions[0].choices.keys()  # type: ignore[attr-defined]
    assert "resolve-strategy" in commands
    assert "show-broker" in commands
    assert "cost-analysis" in commands


def test_show_broker_prints_all_symbols(capsys) -> None:
    show_broker_cmd(SimpleNamespace(broker="current_broker_demo"))
    output = capsys.readouterr().out
    for symbol in ("AUDUSD", "USDCAD", "USDJPY", "GBPUSD", "USOUSD", "XAGUSD"):
        assert symbol in output
    assert '"paper_only": true' in output


def _script_eval(command: str, cwd: Path | None = None) -> str:
    script = Path("/Users/whs1/Dev/V2trading_system/scripts/import_all_assets.sh")
    completed = subprocess.run(
        ["bash", "-lc", f"source {script}; {command}"],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def test_batch_script_parses_known_files() -> None:
    assert _script_eval("parse_asset_file XAUUSD_M15.csv") == "XAUUSD M15"
    assert _script_eval("parse_asset_file USOUSD_H1.csv") == "USOUSD H1"
    assert _script_eval("parse_asset_file GBPUSD_M30.csv") == "GBPUSD M30"


def test_batch_script_skips_unrecognised_file() -> None:
    output = _script_eval("import_status_for_file GBPUSD_M15_.csv")
    assert output == "SKIPPED_UNRECOGNISED"


def test_batch_script_skips_already_imported_unless_force(tmp_path) -> None:
    path = tmp_path / "data/validated"
    path.mkdir(parents=True)
    (path / "XAUUSD_M15.parquet").write_text("stub", encoding="utf-8")
    assert _script_eval("import_status_for_file XAUUSD_M15.csv", tmp_path) == "ALREADY_IMPORTED"
    assert _script_eval("FORCE=1 import_status_for_file XAUUSD_M15.csv", tmp_path) == "IMPORT"


def test_asset_seed_overrides_fx_relaxes_atr_breakout() -> None:
    from tar_system.strategies.asset_variants import asset_seed_overrides
    overrides = asset_seed_overrides("atr_breakout_v3", "EURUSD")
    assert overrides.get("atr_multiplier") == 1.5


def test_asset_seed_overrides_gold_unchanged() -> None:
    from tar_system.strategies.asset_variants import asset_seed_overrides
    overrides = asset_seed_overrides("atr_breakout_v3", "XAUUSD")
    assert overrides == {}


def test_asset_seed_overrides_btc_widens_rsi_only() -> None:
    from tar_system.strategies.asset_variants import asset_seed_overrides
    overrides = asset_seed_overrides("rsi_only_v3", "BTCUSD")
    assert overrides.get("rsi_buy_level") == 35.0
    assert overrides.get("rsi_sell_level") == 65.0


def test_asset_seed_overrides_fx_liquidity_sweep_loosened() -> None:
    from tar_system.strategies.asset_variants import asset_seed_overrides
    overrides = asset_seed_overrides("liquidity_sweep_v1", "GBPUSD")
    assert overrides.get("wick_ratio") == 0.35
    assert overrides.get("min_confidence") == 0.5


def test_asset_seed_overrides_unknown_strategy_returns_empty() -> None:
    from tar_system.strategies.asset_variants import asset_seed_overrides
    assert asset_seed_overrides("unknown_strategy_xyz", "EURUSD") == {}

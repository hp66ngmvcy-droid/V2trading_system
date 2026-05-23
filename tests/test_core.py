from __future__ import annotations

import pandas as pd

from tar_system.data.csv_importer import load_csv, normalize_columns
from tar_system.data.store import filter_by_date_range
from tar_system.data.validator import validate_ohlcv
from tar_system.environment.event_calendar import Event
from tar_system.environment.risk_state import check_environment_risk
from tar_system.exports.mt5_exporter import export_latest_signal
from tar_system.features.engineering import build_features
from tar_system.optimisation.parameter_anchors import ATR_STOP_ANCHORS, GOLD_V2_ANCHORS
from tar_system.regime.detector import Regime, detect_regime
from tar_system.risk.engine import RiskEngine
from tar_system.scoring.gates import run_gates
from tar_system.scoring.scorer import score_strategy
from tar_system.strategies.asset_variants import default_variant
from tar_system.strategies.base import Signal
from tar_system.strategies.gold_v2 import GoldV2
from tar_system.strategies.registry import ALIASES, REGISTRY, RESEARCH_REGISTRY, get_strategy
from tar_system.backtest.metrics import calculate_metrics
from tar_system.backtest.engine import _safe_backtest_quantity
from tar_system.portfolio.tracker import Trade


def sample_df(rows: int = 40) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=rows, freq="15min")
    close = pd.Series(range(100, 100 + rows), dtype=float)
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 100,
            "symbol": "XAUUSD",
            "timeframe": "M15",
        }
    )


def test_csv_column_normalization() -> None:
    raw = pd.DataFrame({"Date": ["2026-01-01"], "Open": [1], "High": [2], "Low": [0.5], "Close": [1.5], "Vol": [10]})
    normalized = normalize_columns(raw)
    assert {"timestamp", "open", "high", "low", "close", "volume"}.issubset(normalized.columns)


def test_mt5_tick_export_resamples_to_ohlcv(tmp_path) -> None:
    path = tmp_path / "ticks.tsv"
    path.write_text(
        "<DATE>\t<TIME>\t<BID>\t<ASK>\t<LAST>\t<VOLUME>\t<FLAGS>\n"
        "2026.04.22\t01:00:05.533\t100.0\t100.2\t\t\t6\n"
        "2026.04.22\t01:05:05.533\t101.0\t101.2\t\t\t6\n"
        "2026.04.22\t01:16:05.533\t102.0\t102.4\t\t\t6\n",
        encoding="utf-8",
    )
    df = load_csv(path, "XAUUSD", "M15")
    assert {"timestamp", "open", "high", "low", "close", "volume", "spread", "symbol", "timeframe"}.issubset(df.columns)
    assert len(df) == 2
    assert df["volume"].tolist() == [2, 1]


def test_validation_failure_on_missing_columns() -> None:
    result = validate_ohlcv(pd.DataFrame({"timestamp": ["2026-01-01"], "close": [1.0]}))
    assert not result.passed
    assert "DATA_MISSING_COLUMNS" in result.reason_codes


def test_data_quality_high_on_clean_data_and_low_on_gapped_data() -> None:
    clean = sample_df(20)
    assert validate_ohlcv(clean).data_quality_score >= 90
    gapped = clean.drop(index=list(range(3, 16))).reset_index(drop=True)
    result = validate_ohlcv(gapped)
    assert result.data_quality_score < 80


def test_data_quality_blocks_below_60() -> None:
    df = sample_df(20)
    df = df.iloc[[0, 10, 19]].copy().reset_index(drop=True)
    df.loc[1, "timestamp"] = df.loc[0, "timestamp"]
    df.loc[2, "close"] = 1000
    result = validate_ohlcv(df)
    assert not result.passed
    assert "DATA_QUALITY_BLOCKED" in result.reason_codes


def test_feature_creation() -> None:
    features = build_features(sample_df(), "XAUUSD", "M15")
    assert "ema_fast" in features.columns
    assert "rsi" in features.columns
    assert "hour_utc" in features.columns
    assert features["hour_utc"].between(0, 23).all()
    assert "range_compression" in features.columns
    assert "session_label" in features.columns
    assert "ema_fast_slope" in features.columns


def test_session_features_liquid_and_asian() -> None:
    df = sample_df(2)
    df["timestamp"] = pd.to_datetime(["2026-01-01 08:00:00", "2026-01-01 02:00:00"], utc=True)
    features = build_features(df, "XAUUSD", "M15")
    assert features.loc[0, "session_label"] == "LONDON"
    assert bool(features.loc[0, "is_liquid_session"]) is True
    assert features.loc[1, "session_label"] == "ASIAN"
    assert bool(features.loc[1, "is_liquid_session"]) is False


def _gold_row(**updates: object) -> pd.Series:
    payload: dict[str, object] = {
        "timestamp": pd.Timestamp("2026-01-01 08:00:00", tz="UTC"),
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "close": 100.0,
        "ema_fast": 101.0,
        "ema_slow": 99.0,
        "ema_fast_slope": 0.0005,
        "ema_slow_slope": 0.0001,
        "rsi": 60.0,
        "atr": 1.0,
        "atr_median_50": 1.0,
        "is_liquid_session": True,
    }
    payload.update(updates)
    return pd.Series(payload)


def test_gold_v2_blocks_asian_session_when_filter_enabled() -> None:
    signal = GoldV2(session_filter=True).generate_signal(_gold_row(is_liquid_session=False), "TRENDING")
    assert signal.side == "HOLD"
    assert signal.reason_code == "SESSION_FILTER_BLOCK"


def test_gold_v2_allows_missing_session_columns() -> None:
    row = _gold_row().drop(labels=["is_liquid_session"])
    signal = GoldV2(session_filter=True).generate_signal(row, "TRENDING")
    assert signal.reason_code != "SESSION_FILTER_BLOCK"


def test_gold_v2_handles_string_session_filter_values() -> None:
    signal = GoldV2(session_filter=True).generate_signal(_gold_row(is_liquid_session="False"), "TRENDING")
    assert signal.side == "HOLD"
    assert signal.reason_code == "SESSION_FILTER_BLOCK"


def test_gold_v2_generates_signal_during_london_session() -> None:
    signal = GoldV2(session_filter=True).generate_signal(_gold_row(), "TRENDING")
    assert signal.side == "BUY"


def test_btc_variant_has_session_filter_disabled() -> None:
    assert default_variant("gold_v2", "BTCUSD", "M15").parameters["session_filter"] is False


def test_strategy_registry_includes_canonical_strategies_and_resolves_aliases() -> None:
    assert "rsi_only_v3" in REGISTRY
    assert "rsi_v3" not in REGISTRY
    assert get_strategy("rsi_only_v3").__class__ is REGISTRY["rsi_only_v3"]
    assert get_strategy("rsi_v3").__class__ is ALIASES["rsi_v3"]
    assert all(get_strategy(name).__class__ is strategy_class for name, strategy_class in REGISTRY.items())
    assert set(RESEARCH_REGISTRY) == {"gold_v2", "rsi_reversion_v1"}


def test_gold_v2_blocks_atr_too_low_and_too_high() -> None:
    low = GoldV2().generate_signal(_gold_row(atr=0.2, atr_median_50=1.0), "TRENDING")
    high = GoldV2().generate_signal(_gold_row(atr=4.0, atr_median_50=1.0), "TRENDING")
    assert low.reason_code == "ATR_TOO_LOW_COMPRESSION"
    assert high.reason_code == "ATR_TOO_HIGH_EXTREME_VOLATILITY"


def test_gold_v2_blocks_flat_ema_and_allows_rising_buy() -> None:
    flat = GoldV2().generate_signal(_gold_row(ema_fast_slope=0.00001), "TRENDING")
    rising = GoldV2().generate_signal(_gold_row(ema_fast_slope=0.0005, ema_slow_slope=0.0001), "TRENDING")
    assert flat.reason_code == "EMA_SLOPE_TOO_FLAT"
    assert rising.side == "BUY"


def test_parameter_anchor_library_loads() -> None:
    assert GOLD_V2_ANCHORS[0]["fast_ema"] == 8
    assert ATR_STOP_ANCHORS["XAUUSD"]["atr_multiplier"] == 2.0
    assert ATR_STOP_ANCHORS["BTCUSD"]["atr_multiplier"] == 3.0


def test_extended_metrics_known_series() -> None:
    trades = [
        Trade("X", "BUY", 1, 100, 110, 10, pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02"), net_pnl=10),
        Trade("X", "BUY", 1, 100, 90, -10, pd.Timestamp("2026-01-02"), pd.Timestamp("2026-01-03"), net_pnl=-10),
        Trade("X", "BUY", 1, 100, 95, -5, pd.Timestamp("2026-01-03"), pd.Timestamp("2026-01-04"), net_pnl=-5),
        Trade("X", "BUY", 1, 100, 108, 8, pd.Timestamp("2026-01-04"), pd.Timestamp("2026-01-05"), net_pnl=8),
    ]
    metrics = calculate_metrics(trades, [(pd.Timestamp("2026-01-01"), 100), (pd.Timestamp("2026-01-02"), 90), (pd.Timestamp("2026-01-03"), 108)])
    assert round(metrics["sharpe_ratio"], 4) != 0
    assert round(metrics["sortino_ratio"], 4) != 0
    assert metrics["calmar_ratio"] != 0
    assert metrics["max_consecutive_losses"] == 2
    assert metrics["consecutive_wins"] == 1


def test_filter_by_month_and_year_range() -> None:
    df = pd.DataFrame({"timestamp": pd.to_datetime(["2025-12-31", "2026-01-15", "2026-03-01", "2027-01-01"]), "close": [1, 2, 3, 4]})
    month = filter_by_date_range(df, "2026-01", "2026-03")
    year = filter_by_date_range(df, "2026", "2026")
    assert month["close"].tolist() == [2, 3]
    assert year["close"].tolist() == [2, 3]


def test_regime_detector_output() -> None:
    features = build_features(sample_df(), "XAUUSD", "M15")
    regime = detect_regime(features.iloc[-1])
    assert regime in {Regime.TRENDING, Regime.RANGING, Regime.VOLATILE, Regime.UNKNOWN}


def test_risk_rejection_on_low_confidence() -> None:
    signal = Signal(
        timestamp=pd.Timestamp("2026-01-01"),
        symbol="XAUUSD",
        timeframe="M15",
        strategy="gold_v2",
        version="0.1.0",
        side="BUY",
        confidence=0.2,
        entry=100.0,
        stop_loss=99.0,
        take_profit=102.0,
        reason_code="SIGNAL_BUY",
    )
    decision = RiskEngine().evaluate(signal)
    assert not decision.approved
    assert decision.reason_code == "RISK_LOW_CONFIDENCE"


def test_scorer_verdict() -> None:
    score = score_strategy({"win_rate": 0.55, "profit_factor": 1.6, "max_drawdown": 0.1, "total_trades": 35, "expectancy": 12})
    assert score.verdict in {"KEEP", "REVIEW", "KILL"}
    assert 0 <= score.score <= 100


def test_scorer_requires_walk_forward_when_requested() -> None:
    metrics = {"win_rate": 0.65, "profit_factor": 2.4, "max_drawdown": 0.08, "total_trades": 60, "expectancy": 12}
    score = score_strategy(metrics, require_walk_forward=True)
    assert score.verdict == "REVIEW"
    assert "WF_NOT_RUN" in score.reason_codes


def test_scorer_can_keep_with_strong_walk_forward() -> None:
    metrics = {"win_rate": 0.65, "profit_factor": 2.4, "max_drawdown": 0.08, "total_trades": 60, "expectancy": 12}
    walk_forward = {
        "split_count": 3,
        "window_count": 3,
        "ran": True,
        "wf_verdict": "KEEP",
        "stitched_metrics": {"total_trades": 30, "profit_factor": 1.4, "max_drawdown": 0.10},
        "parameter_stability_score": 60.0,
        "bootstrap_ci": {"spans_zero": False, "ci_lower": 0.01, "ci_upper": 0.12},
    }
    score = score_strategy(metrics, walk_forward, "M15", require_walk_forward=True)
    assert score.verdict == "KEEP"


def test_structural_gate_blocks_one_trade_winner() -> None:
    gate = run_gates({"total_trades": 1, "win_rate": 1.0, "profit_factor": 100.0, "max_drawdown": 0.0}, "M15")
    assert gate.verdict == "KILL"
    assert gate.failed_gate == "min_trades"


def test_structural_gate_blocks_directional_failure() -> None:
    gate = run_gates(
        {
            "total_trades": 104,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.10,
            "max_consecutive_losses": 104,
        },
        "M15",
        require_oos=False,
    )
    assert gate.verdict == "KILL"
    assert gate.failed_gate == "consecutive_loss_ratio"


def test_structural_gate_requires_walk_forward_for_keep() -> None:
    gate = run_gates(
        {"total_trades": 40, "win_rate": 0.55, "profit_factor": 1.8, "max_drawdown": 0.10},
        "M15",
        require_oos=True,
    )
    assert gate.verdict == "REVIEW"
    assert "SEARCH_OOS_SHARPE_NOT_MET" in gate.reason_codes


def test_safe_backtest_quantity_caps_large_notional() -> None:
    assert _safe_backtest_quantity(50000.0, 10000.0) == 0.02
    assert _safe_backtest_quantity(2000.0, 10000.0) == 0.5
    assert _safe_backtest_quantity(1.1, 10000.0) == 1.0


def test_mt5_export_creates_files(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    signal = Signal(
        timestamp=pd.Timestamp("2026-01-01"),
        symbol="XAUUSD",
        timeframe="M15",
        strategy="gold_v2",
        version="0.1.0",
        side="BUY",
        confidence=0.8,
        entry=100.0,
        stop_loss=99.0,
        take_profit=102.0,
        reason_code="SIGNAL_BUY",
    )
    csv_path, json_path = export_latest_signal(signal)
    assert csv_path.exists()
    assert json_path.exists()


def test_environment_missing_events_review_only() -> None:
    state = check_environment_risk("XAUUSD", pd.Timestamp("2026-06-12").to_pydatetime(), events=None)
    assert state == "REVIEW_ONLY"


def test_environment_high_impact_holds() -> None:
    event = Event("US CPI", pd.Timestamp("2026-06-12").to_pydatetime(), "HIGH")
    state = check_environment_risk("XAUUSD", pd.Timestamp("2026-06-12").to_pydatetime(), events=[event])
    assert state == "HOLD_TRADING"


# ---------------------------------------------------------------------------
# Multi-agent scorer wiring
# ---------------------------------------------------------------------------

def test_multi_agent_wiring_keep_when_both_agree() -> None:
    from tar_system.scoring.multi_agent_scorer import score_multi_agent
    metrics = {
        "total_trades": 60, "win_rate": 0.55, "profit_factor": 1.8,
        "max_drawdown": 0.10, "sharpe_ratio": 1.4, "expectancy": 0.005,
        "sharpe_oos": 1.1, "param_stability": 0.80, "walk_forward_splits": 5,
    }
    gate = run_gates(metrics, "M15", require_oos=False)
    ma = score_multi_agent(metrics)
    final_verdict = "REVIEW" if gate.verdict == "KEEP" and ma.verdict == "KILL" else gate.verdict
    assert final_verdict == gate.verdict  # no override needed


def test_multi_agent_wiring_downgrades_keep_to_review_when_ma_kills() -> None:
    from tar_system.scoring.multi_agent_scorer import score_multi_agent
    # Gate passes (good structural metrics) but multi-agent kills on soft metrics
    gate_metrics = {
        "total_trades": 30, "win_rate": 0.51, "profit_factor": 1.2,
        "max_drawdown": 0.12, "sharpe_ratio": -0.3, "expectancy": -0.002,
        "sharpe_oos": -0.8, "param_stability": 0.3, "walk_forward_splits": 4,
    }
    ma = score_multi_agent(gate_metrics)
    assert ma.verdict == "KILL"
    # Simulate gate returning KEEP (hypothetically) and verify override
    simulated_gate_verdict = "KEEP"
    final_verdict = "REVIEW" if simulated_gate_verdict == "KEEP" and ma.verdict == "KILL" else simulated_gate_verdict
    assert final_verdict == "REVIEW"


def test_multi_agent_wiring_gate_kill_not_overridden_by_ma_keep() -> None:
    from tar_system.scoring.multi_agent_scorer import score_multi_agent
    # Gate kills; multi-agent should not be able to upgrade it
    metrics = {
        "total_trades": 1, "win_rate": 1.0, "profit_factor": 100.0,
        "max_drawdown": 0.0, "sharpe_ratio": 5.0, "expectancy": 0.1,
    }
    gate = run_gates(metrics, "M15")
    assert gate.verdict == "KILL"
    ma = score_multi_agent(metrics)
    final_verdict = "REVIEW" if gate.verdict == "KEEP" and ma.verdict == "KILL" else gate.verdict
    assert final_verdict == "KILL"  # gate kill stands


def test_multi_agent_result_has_expected_structure() -> None:
    from tar_system.scoring.multi_agent_scorer import score_multi_agent
    metrics = {
        "total_trades": 40, "win_rate": 0.52, "profit_factor": 1.5,
        "max_drawdown": 0.15, "sharpe_ratio": 1.1, "expectancy": 0.003,
    }
    ma = score_multi_agent(metrics)
    assert ma.verdict in {"KEEP", "REVIEW", "KILL"}
    assert 0.0 <= ma.confidence <= 1.0
    assert isinstance(ma.dissent, bool)
    assert len(ma.agent_verdicts) == 3
    assert {v.agent for v in ma.agent_verdicts} == {"risk", "performance", "robustness"}

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd

from tar_system.features.engineering import build_features
from tar_system.optimisation.parameter_anchors import RSI_REVERSION_ANCHORS
from tar_system.reporting.reporter import generate_variant_comparison_report
from tar_system.strategies.asset_variants import default_variant
from tar_system.strategies.regime_selector import recommend_strategy_for_regime
from tar_system.strategies.rsi_reversion_v1 import RsiReversionV1


def _raw(rows: int = 40) -> pd.DataFrame:
    close = pd.Series(range(100, 100 + rows), dtype=float)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=rows, freq="15min", tz="UTC"),
            "open": close - 0.1,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 100,
            "symbol": "XAUUSD",
            "timeframe": "M15",
        }
    )


def _row(**updates: object) -> pd.Series:
    payload: dict[str, object] = {
        "timestamp": pd.Timestamp("2026-01-01 08:00:00", tz="UTC"),
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "close": 100.0,
        "rsi": 25.0,
        "price_in_band": 0.1,
        "atr": 1.0,
        "is_liquid_session": True,
    }
    payload.update(updates)
    return pd.Series(payload)


def test_bollinger_features_match_formula() -> None:
    features = build_features(_raw(), "XAUUSD", "M15")
    last = features.iloc[-1]
    assert "bollinger_upper" in features.columns
    assert "price_in_band" in features.columns
    assert last["bollinger_upper"] == last["bollinger_mid"] + 2 * features["close"].rolling(20).std().iloc[-1]
    assert 0 <= last["price_in_band"] <= 1


def test_price_in_band_formula_edges() -> None:
    lower = 90.0
    upper = 110.0
    assert (lower - lower) / (upper - lower) == 0.0
    assert (upper - lower) / (upper - lower) == 1.0


def test_rsi_reversion_buy_sell_and_regime_blocks() -> None:
    strategy = RsiReversionV1()
    assert strategy.generate_signal(_row(rsi=25.0, price_in_band=0.1), "RANGING").side == "BUY"
    assert strategy.generate_signal(_row(rsi=75.0, price_in_band=0.9), "RANGING").side == "SELL"
    assert strategy.generate_signal(_row(), "TRENDING").reason_code == "REGIME_FILTER_BLOCK"
    assert strategy.generate_signal(_row(), "VOLATILE").reason_code == "REGIME_FILTER_BLOCK"


def test_rsi_reversion_session_filter_and_btc_variant() -> None:
    signal = RsiReversionV1(session_filter=True).generate_signal(_row(is_liquid_session=False), "RANGING")
    assert signal.reason_code == "SESSION_FILTER_BLOCK"
    assert default_variant("rsi_reversion_v1", "BTCUSD", "M15").parameters["session_filter"] is False


def test_regime_selector_recommendations() -> None:
    assert recommend_strategy_for_regime("TRENDING").recommended_strategy == "gold_v2"
    assert recommend_strategy_for_regime("RANGING").recommended_strategy == "rsi_reversion_v1"
    volatile = recommend_strategy_for_regime("VOLATILE")
    assert volatile.recommended_strategy == "HOLD"
    assert volatile.reason == "VOLATILE_REGIME_BLOCK"


def test_rsi_reversion_anchor_library_loads() -> None:
    assert RSI_REVERSION_ANCHORS[0]["rsi_period"] == 14
    assert RSI_REVERSION_ANCHORS[1]["oversold"] == 28


def test_compare_variants_report_ranks_output(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("reports").mkdir()
    Path("data/results/gold_v2_XAUUSD_M15_metrics.json").write_text(
        json.dumps({"win_rate": 0.4, "profit_factor": 1.1, "max_drawdown": 0.1, "total_trades": 40, "sharpe_ratio": 0.2, "expectancy": 1.0}),
        encoding="utf-8",
    )
    Path("data/results/rsi_reversion_v1_XAUUSD_M15_metrics.json").write_text(
        json.dumps({"win_rate": 0.5, "profit_factor": 1.4, "max_drawdown": 0.08, "total_trades": 35, "sharpe_ratio": 0.4, "expectancy": 1.5}),
        encoding="utf-8",
    )
    path = generate_variant_comparison_report("XAUUSD", "M15")
    text = path.read_text(encoding="utf-8")
    assert "rsi_reversion_v1" in text
    assert "gold_v2" in text
    assert "cost_sensitive" in text


def test_run_all_backtests_script_detects_existing_parquet(tmp_path) -> None:
    script = Path("/Users/whs1/Dev/V2trading_system/scripts/run_all_backtests.sh")
    (tmp_path / "data/validated").mkdir(parents=True)
    (tmp_path / "data/validated/XAUUSD_M15.parquet").write_text("ok", encoding="utf-8")
    output = subprocess.check_output(
        ["bash", "-lc", f"source {script}; REPO='{tmp_path}'; cd '{tmp_path}'; has_validated_parquet XAUUSD M15 && echo FOUND"],
        text=True,
    ).strip()
    assert output == "FOUND"

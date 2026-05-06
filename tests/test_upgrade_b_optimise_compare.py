from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tar_system.analysis.asset_comparison import compare_assets
from tar_system.cli import build_parser
from tar_system.data.store import save_feature_data
from tar_system.features.engineering import build_features
from tar_system.memory.strategy_memory import record_strategy_memory
from tar_system.optimisation.optimiser import optimise_asset
from tar_system.optimisation.parameter_space import one_parameter_mutations


def _features(symbol: str = "BTCUSD", timeframe: str = "M5", rows: int = 80) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=rows, freq="5min")
    close = pd.Series(range(100, 100 + rows), dtype=float)
    raw = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": close - 0.1,
            "high": close + 0.3,
            "low": close - 0.3,
            "close": close,
            "volume": 100,
            "symbol": symbol,
            "timeframe": timeframe,
            "data_hash": "test-hash",
        }
    )
    return build_features(raw, symbol, timeframe)


def test_one_parameter_mutation_changes_one_parameter() -> None:
    variants = one_parameter_mutations({"fast_ema": 10, "slow_ema": 30}, max_variants=2)
    assert len(variants) == 2
    assert variants[0].changed_parameter == "fast_ema"
    assert variants[0].parameters["slow_ema"] == 30


def test_optimise_asset_runs_and_writes_memory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("configs/brokers").mkdir(parents=True)
    source = Path("/Users/whs1/Dev/V2trading_system/configs/brokers/current_broker_demo.yaml")
    Path("configs/brokers/current_broker_demo.yaml").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    save_feature_data(_features(), "BTCUSD", "M5")

    result = optimise_asset("gold_v2", "BTCUSD", "M5", "current_broker_demo", max_variants=2, max_rows=80)

    assert result.ranked_variants
    assert result.parameter_source == "anchors"
    assert result.narrowed_from_walk_forward is False
    assert Path("data/results/gold_v2_BTCUSD_M5_optimisation.json").exists()
    assert Path("data/tar_system.duckdb").exists()


def test_optimise_asset_uses_walk_forward_ranges_when_available(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("configs/brokers").mkdir(parents=True)
    source = Path("/Users/whs1/Dev/V2trading_system/configs/brokers/current_broker_demo.yaml")
    Path("configs/brokers/current_broker_demo.yaml").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    save_feature_data(_features(), "BTCUSD", "M5")
    Path("data/results").mkdir(parents=True, exist_ok=True)
    Path("data/results/gold_v2_BTCUSD_M5_walk_forward.json").write_text(
        json.dumps({"stable_parameter_ranges": {"fast_ema": [8, 13]}}),
        encoding="utf-8",
    )
    result = optimise_asset("gold_v2", "BTCUSD", "M5", "current_broker_demo", max_variants=1, max_rows=80)
    assert result.narrowed_from_walk_forward is True
    assert result.search_ranges == {"fast_ema": (8.0, 13.0)}


def test_compare_assets_uses_available_metrics_and_missing_data(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("data/results/gold_v2_BTCUSD_M15_metrics.json").write_text(
        json.dumps({"total_trades": 20, "win_rate": 0.5, "profit_factor": 1.2, "max_drawdown": 0.1, "expectancy": 2.0}),
        encoding="utf-8",
    )
    rows = compare_assets("gold_v2", "M15", "current_broker_demo", symbols=["BTCUSD", "XAUUSD"])
    assert rows[0].symbol == "BTCUSD"
    assert any(row.status == "missing_data" for row in rows)
    assert Path("data/results/gold_v2_M15_asset_comparison.json").exists()


def test_expanded_memory_write_accepts_new_schema(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    record_strategy_memory(
        base_strategy="gold_v2",
        variant_name="gold_v2_btcusd_m5",
        version="0.1.0",
        symbol="BTCUSD",
        timeframe="M5",
        broker="current_broker_demo",
        asset_profile={"asset_class": "crypto"},
        broker_profile={"max_leverage": 500},
        parameters={"fast_ema": 10},
        backtest_metrics={"win_rate": 0.5},
        walk_forward_metrics={"win_rate": 0.4},
        forward_test_metrics={},
        score=50,
        verdict="REVISE",
        reason_codes=["TEST"],
    )
    assert Path("data/tar_system.duckdb").exists()


def test_upgrade_b_cli_commands_exist() -> None:
    commands = build_parser()._subparsers._group_actions[0].choices.keys()  # type: ignore[attr-defined]
    assert "optimise-asset" in commands
    assert "compare-assets" in commands

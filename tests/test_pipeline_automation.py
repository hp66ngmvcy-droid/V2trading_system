from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pytest

from tar_system.cli import import_csv, run_full_pipeline_cmd
from tar_system.backtest.engine import BacktestResult
from tar_system.data.csv_importer import load_csv
from tar_system.data.tick_converter import convert_ticks_file, detect_tick_format


def _write_ticks(path: Path) -> str:
    text = (
        "<DATE>\t<TIME>\t<BID>\t<ASK>\t<LAST>\t<VOLUME>\t<FLAGS>\n"
        "2026.04.22\t01:00:05.533\t100.0\t100.2\t\t1\t6\n"
        "2026.04.22\t01:01:05.533\t101.0\t101.2\t\t2\t6\n"
        "2026.04.22\t01:06:05.533\t102.0\t102.4\t\t3\t6\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text


def _write_ohlcv(path: Path, rows: int = 80) -> None:
    timestamps = pd.date_range("2026-01-01", periods=rows, freq="5min")
    close = pd.Series(range(100, 100 + rows), dtype=float)
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": close - 0.1,
            "high": close + 0.3,
            "low": close - 0.3,
            "close": close,
            "volume": 100,
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def test_import_csv_detects_tick_data(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = Path("data/raw/BTCUSD_M5.csv")
    original = _write_ticks(source)

    import_csv(argparse.Namespace(file=str(source), symbol="BTCUSD", timeframe="M5"))

    assert detect_tick_format(source)
    assert source.read_text(encoding="utf-8") == original
    assert Path("data/raw/BTCUSD_M5_clean.csv").exists()
    assert Path("data/validated/BTCUSD_M5.parquet").exists()


def test_tick_data_converts_to_ohlcv(tmp_path) -> None:
    source = tmp_path / "BTCUSD_M5.csv"
    _write_ticks(source)
    result = convert_ticks_file(source, "BTCUSD", "M5")
    df = pd.read_csv(result.output_path)
    assert {"timestamp", "open", "high", "low", "close", "volume", "spread", "symbol", "timeframe"}.issubset(df.columns)
    assert result.output_path.name == "BTCUSD_M5_clean.csv"


def test_import_csv_works_with_clean_ohlcv(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = Path("data/raw/XAUUSD_M15.csv")
    _write_ohlcv(source, rows=40)
    import_csv(argparse.Namespace(file=str(source), symbol="XAUUSD", timeframe="M15"))
    df = load_csv(source, "XAUUSD", "M15")
    assert len(df) == 40
    assert Path("data/validated/XAUUSD_M15.parquet").exists()


def test_run_full_pipeline_creates_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = Path("data/raw/BTCUSD_M5.csv")
    _write_ohlcv(source, rows=80)

    run_full_pipeline_cmd(
        argparse.Namespace(
            strategy="gold_v2",
            symbol="BTCUSD",
            timeframe="M5",
            file=str(source),
            skip_walk_forward=True,
            force=True,
            broker="current_broker_demo",
            resume=False,
            max_walk_forward_splits=100,
        )
    )

    assert Path("data/validated/BTCUSD_M5.parquet").exists()
    assert Path("data/features/BTCUSD_M5.parquet").exists()
    assert Path("data/results/gold_v2_BTCUSD_M5_metrics.json").exists()
    assert Path("reports/BTCUSD_M5_gold_v2_report.md").exists()
    assert Path("data/tar_system.duckdb").exists()
    assert Path("logs/audit/audit.jsonl").exists()
    audit = Path("logs/audit/audit.jsonl").read_text(encoding="utf-8")
    assert "FORWARD_TEST_COMPLETED" in audit


def test_run_full_pipeline_stops_safely_on_invalid_data(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = Path("data/raw/BTCUSD_M5.csv")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("timestamp,close\n2026-01-01,100\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        run_full_pipeline_cmd(
            argparse.Namespace(
                strategy="gold_v2",
                symbol="BTCUSD",
                timeframe="M5",
                file=str(source),
                skip_walk_forward=True,
                force=True,
                broker="current_broker_demo",
                resume=False,
                max_walk_forward_splits=100,
            )
        )

    audit = Path("logs/audit/audit.jsonl").read_text(encoding="utf-8")
    assert "IMPORT_CSV_FAILED" in audit
    assert not Path("data/features/BTCUSD_M5.parquet").exists()


def test_run_full_pipeline_blocks_partial_backtest_memory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = Path("data/raw/BTCUSD_M5.csv")
    _write_ohlcv(source, rows=80)

    def stopped_backtest(*args: object, **kwargs: object) -> BacktestResult:
        return BacktestResult(metrics={}, trades=0, final_equity=10000, stopped=True, partial=True, reason_code="STOP_REQUESTED")

    monkeypatch.setattr("tar_system.backtest.engine.run_backtest", stopped_backtest)
    with pytest.raises(SystemExit):
        run_full_pipeline_cmd(
            argparse.Namespace(
                strategy="gold_v2",
                symbol="BTCUSD",
                timeframe="M5",
                file=str(source),
                skip_walk_forward=True,
                force=True,
                broker="current_broker_demo",
                resume=False,
                max_walk_forward_splits=100,
            )
        )

    assert "RUN_BACKTEST_FAILED" in Path("logs/audit/audit.jsonl").read_text(encoding="utf-8")
    assert not Path("data/tar_system.duckdb").exists()


def test_walk_forward_pipeline_uses_split_cap(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = Path("data/raw/BTCUSD_M5.csv")
    _write_ohlcv(source, rows=400)

    run_full_pipeline_cmd(
        argparse.Namespace(
            strategy="gold_v2",
            symbol="BTCUSD",
            timeframe="M5",
            file=str(source),
            skip_walk_forward=False,
            force=True,
            broker="current_broker_demo",
            resume=False,
            max_walk_forward_splits=3,
        )
    )

    payload = Path("data/results/gold_v2_BTCUSD_M5_walk_forward.json").read_text(encoding="utf-8")
    assert '"split_count": 3' in payload


def test_original_raw_file_is_never_overwritten(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = Path("data/raw/BTCUSD_M5.csv")
    original = _write_ticks(source)
    import_csv(argparse.Namespace(file=str(source), symbol="BTCUSD", timeframe="M5"))
    assert source.read_text(encoding="utf-8") == original

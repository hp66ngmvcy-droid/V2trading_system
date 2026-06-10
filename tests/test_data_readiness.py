from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tar_system.research.data_readiness import check_data_readiness


def test_check_data_readiness_marks_ready_csv(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    pd.DataFrame({"timestamp": pd.date_range("2020-01-01", periods=1200, freq="1D")}).to_csv(raw / "EURUSD_D1.csv", index=False)

    result = check_data_readiness(["EURUSD"], ["D1"], raw_dir=raw, output_dir=tmp_path / "reports", min_months=24, min_rows=1000)

    assert result.ready_count == 1
    assert result.rows[0].ready is True
    assert Path(result.report_path).exists()
    assert json.loads(Path(result.report_json_path).read_text(encoding="utf-8"))["ready_count"] == 1


def test_check_data_readiness_reports_missing_and_short_history(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    pd.DataFrame({"timestamp": pd.date_range("2026-01-01", periods=10, freq="1h")}).to_csv(raw / "GBPUSD_H1.csv", index=False)

    result = check_data_readiness(["GBPUSD", "AUDUSD"], ["H1"], raw_dir=raw, output_dir=tmp_path / "reports", min_months=12, min_rows=100)

    assert result.ready_count == 0
    assert result.missing_count == 1
    reasons = {row.symbol: row.reason for row in result.rows}
    assert "insufficient_rows" in reasons["GBPUSD"]
    assert reasons["AUDUSD"] == "missing_raw_csv"


def test_check_data_readiness_reads_mt5_date_time_columns(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "EURUSD_H1.csv").write_text(
        "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\n"
        "2020.01.01\t00:00:00\t1\t1\t1\t1\n"
        "2024.01.01\t00:00:00\t1\t1\t1\t1\n",
        encoding="utf-8",
    )

    result = check_data_readiness(["EURUSD"], ["H1"], raw_dir=raw, output_dir=tmp_path / "reports", min_months=12, min_rows=2)

    assert result.ready_count == 1
    assert result.rows[0].start.startswith("2020-01-01")

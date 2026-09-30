from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd


SPEC = importlib.util.spec_from_file_location(
    "xauusd_provenance_report",
    Path(__file__).resolve().parents[1] / "scripts/xauusd_provenance_report.py",
)
provenance = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = provenance
SPEC.loader.exec_module(provenance)


def _write_fixture(root: Path) -> None:
    (root / "data/raw/source_exports").mkdir(parents=True)
    (root / "data/validated").mkdir(parents=True)
    raw = pd.DataFrame(
        {
            "date": ["2026.09.04", "2026.09.05", "2026.09.07"],
            "time": ["23:45:00", "00:00:00", "00:15:00"],
            "open": [2400.0, 2401.0, 2402.0],
            "high": [2402.0, 2404.0, 2403.0],
            "low": [2399.0, 2400.0, 2401.0],
            "close": [2401.0, 2403.0, 2402.5],
            "volume": [10, 0, 12],
        }
    )
    raw.to_csv(root / "data/raw/XAUUSD_M15.csv", index=False)
    raw.to_csv(root / "data/raw/source_exports/XAUUSD_M15_export.csv", index=False)
    validated = raw.copy()
    validated["timestamp"] = pd.to_datetime(validated["date"] + " " + validated["time"])
    validated.to_parquet(root / "data/validated/XAUUSD_M15.parquet")


def test_build_report_flags_saturday_and_hashes(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    report = provenance.build_report(tmp_path)

    assert report["source_trust_verdict"] == "UNRESOLVED"
    assert report["canonical_candidate"]["status"] == "SOURCE_REVIEW_REQUIRED"
    assert report["canonical_candidate"]["sha256"]
    assert report["aggregate"]["paths_with_saturday_bars"]["data/validated/XAUUSD_M15.parquet"] == 1
    assert report["file_count"] == 3


def test_count_weekday_gaps_uses_weekday_proxy() -> None:
    timestamps = pd.to_datetime(
        [
            "2026-09-07T00:00:00Z",
            "2026-09-07T00:30:00Z",
            "2026-09-07T00:45:00Z",
        ],
        utc=True,
    )

    assert provenance.count_weekday_gaps(pd.Series(timestamps), "M15") == 1


def test_mt5_tab_export_timestamps_are_parsed(tmp_path: Path) -> None:
    path = tmp_path / "XAUUSD_M15_export.csv"
    path.write_text(
        "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n"
        "2026.09.04\t23:45:00\t2400\t2401\t2399\t2400.5\t10\t0\t18\n",
        encoding="utf-8",
    )

    frame, error = provenance.read_frame(path)
    timestamps, source = provenance.normalise_timestamps(frame)

    assert error is None
    assert source == "date+time"
    assert timestamps.iloc[0].isoformat() == "2026-09-04T23:45:00+00:00"


def test_write_summary_is_human_readable(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    report = provenance.build_report(tmp_path)
    summary = tmp_path / "summary.md"

    provenance.write_summary(report, summary)

    text = summary.read_text(encoding="utf-8")
    assert "XAUUSD Provenance Summary" in text
    assert "UNRESOLVED" in text
    assert "read-only" in text

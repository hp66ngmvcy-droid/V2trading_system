from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd


SPEC = importlib.util.spec_from_file_location(
    "xauusd_source_comparison",
    Path(__file__).resolve().parents[1] / "scripts/xauusd_source_comparison.py",
)
comparison = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = comparison
SPEC.loader.exec_module(comparison)


def test_compare_frames_counts_mismatches_and_missing_rows() -> None:
    canonical = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-09-01T00:00:00Z", "2026-09-01T00:15:00Z", "2026-09-01T00:30:00Z"]),
            "open": [1.0, 2.0, 3.0],
            "high": [1.1, 2.1, 3.1],
            "low": [0.9, 1.9, 2.9],
            "close": [1.05, 2.05, 3.05],
        }
    )
    candidate = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-09-01T00:00:00Z", "2026-09-01T00:15:00Z", "2026-09-01T00:45:00Z"]),
            "open": [1.0, 2.5, 4.0],
            "high": [1.1, 2.1, 4.1],
            "low": [0.9, 1.9, 3.9],
            "close": [1.05, 2.05, 4.05],
        }
    )

    got = comparison.compare_frames(canonical, candidate)

    assert got["overlap_rows"] == 2
    assert got["missing_in_candidate"] == 1
    assert got["missing_in_canonical"] == 1
    assert got["mismatch_rows"] == 1
    assert got["field_mismatch_counts"]["open"] == 1


def test_build_report_compares_local_csv_candidate(tmp_path: Path) -> None:
    (tmp_path / "data/validated").mkdir(parents=True)
    (tmp_path / "data/raw").mkdir(parents=True)
    canonical = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-09-04T23:45:00Z", "2026-09-05T00:00:00Z"]),
            "open": [2400.0, 2401.0],
            "high": [2401.0, 2402.0],
            "low": [2399.0, 2400.0],
            "close": [2400.5, 2401.5],
        }
    )
    canonical.to_parquet(tmp_path / "data/validated/XAUUSD_M15.parquet")
    (tmp_path / "data/raw/XAUUSD_M15_export.csv").write_text(
        "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\n"
        "2026.09.04\t23:45:00\t2400.0\t2401.0\t2399.0\t2400.5\n",
        encoding="utf-8",
    )

    report = comparison.build_report(tmp_path)

    assert report["canonical"]["saturday_bars"] == 1
    assert report["comparisons"][0]["overlap_rows"] == 1
    assert report["comparisons"][0]["mismatch_rows"] == 0
    assert report["summary"]["zero_saturday_candidates_with_exact_overlap"] == 1


def test_write_summary_lists_candidates(tmp_path: Path) -> None:
    report = {
        "generated_on": "2026-09-29",
        "canonical": {
            "path": "data/validated/XAUUSD_M15.parquet",
            "row_count": 2,
            "saturday_bars": 1,
            "first_saturday_timestamp": "2026-09-05T00:00:00+00:00",
        },
        "tolerance": 0.01,
        "comparisons": [
            {
                "path": "data/raw/XAUUSD_M15_export.csv",
                "row_count": 1,
                "saturday_bars": 0,
                "overlap_rows": 1,
                "mismatch_rows": 0,
                "missing_in_canonical": 0,
                "missing_in_candidate": 1,
            }
        ],
    }
    path = tmp_path / "summary.md"

    comparison.write_summary(report, path)

    text = path.read_text(encoding="utf-8")
    assert "XAUUSD Source Comparison Summary" in text
    assert "XAUUSD_M15_export.csv" in text

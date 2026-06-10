from __future__ import annotations

import json
from pathlib import Path

from tar_system.research.raw_data_inventory import apply_raw_data_cleanup, audit_raw_data, plan_raw_data_cleanup


def test_audit_raw_data_accepts_standard_names(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "EURUSD_H1.csv").write_text("timestamp,close\n2026-01-01,1.1\n", encoding="utf-8")

    result = audit_raw_data(raw, tmp_path / "reports")

    assert result.total_csv == 1
    assert result.ok_count == 1
    assert result.issue_count == 0
    assert Path(result.report_path).exists()
    assert json.loads(Path(result.report_json_path).read_text(encoding="utf-8"))["ok_count"] == 1


def test_audit_raw_data_flags_nonstandard_names(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "XAUUSD_M15_New 26.csv").write_text("timestamp,close\n2026-01-01,2000\n", encoding="utf-8")
    (raw / "gbpusd_h1.csv").write_text("", encoding="utf-8")

    result = audit_raw_data(raw, tmp_path / "reports")

    assert result.issue_count == 2
    issues = {issue for row in result.rows for issue in row.issues}
    assert "nonstandard_filename" in issues
    assert "expected_SYMBOL_TIMEFRAME" in issues
    assert "use_uppercase_symbol_timeframe" in issues
    assert "empty_file" in issues
    assert any("data/raw/source_exports" in row.suggested_action for row in result.rows)


def test_audit_raw_data_ignores_source_exports_subfolder(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    source_exports = raw / "source_exports"
    source_exports.mkdir(parents=True)
    (raw / "EURUSD_H1.csv").write_text("timestamp,close\n2026-01-01,1.1\n", encoding="utf-8")
    (source_exports / "EURUSD_H1_download 1.csv").write_text("timestamp,close\n2026-01-01,1.1\n", encoding="utf-8")

    result = audit_raw_data(raw, tmp_path / "reports")

    assert result.total_csv == 1
    assert result.issue_count == 0
    assert result.rows[0].filename == "EURUSD_H1.csv"


def test_plan_raw_data_cleanup_is_dry_run(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    odd_file = raw / "XAUUSD_M15_New 26.csv"
    odd_file.write_text("timestamp,close\n2026-01-01,2000\n", encoding="utf-8")
    (raw / "EURUSD_H1.csv").write_text("timestamp,close\n2026-01-01,1.1\n", encoding="utf-8")

    result = plan_raw_data_cleanup(raw, tmp_path / "reports")

    assert result.dry_run is True
    assert result.move_count == 1
    assert result.moves[0].source.endswith("XAUUSD_M15_New 26.csv")
    assert result.moves[0].destination.endswith("source_exports/XAUUSD_M15_New 26.csv")
    assert odd_file.exists()
    assert Path(result.report_path).exists()


def test_apply_raw_data_cleanup_requires_confirmation(tmp_path: Path) -> None:
    try:
        apply_raw_data_cleanup(tmp_path / "data" / "raw", tmp_path / "reports")
    except ValueError as exc:
        assert "confirm=True" in str(exc)
    else:
        raise AssertionError("cleanup apply should require confirmation")


def test_apply_raw_data_cleanup_moves_noncanonical_files(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    odd_file = raw / "XAUUSD_M15_New 26.csv"
    odd_file.write_text("timestamp,close\n2026-01-01,2000\n", encoding="utf-8")
    canonical = raw / "XAUUSD_M15.csv"
    canonical.write_text("timestamp,close\n2026-01-01,2000\n", encoding="utf-8")

    result = apply_raw_data_cleanup(raw, tmp_path / "reports", confirm=True)

    assert result.moved_count == 1
    assert result.skipped_count == 0
    assert not odd_file.exists()
    assert (raw / "source_exports" / "XAUUSD_M15_New 26.csv").exists()
    assert canonical.exists()
    assert Path(result.report_path).exists()


def test_apply_raw_data_cleanup_refuses_overwrite(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    source_exports = raw / "source_exports"
    source_exports.mkdir(parents=True)
    odd_file = raw / "XAUUSD_M15_New 26.csv"
    odd_file.write_text("timestamp,close\n2026-01-01,2000\n", encoding="utf-8")
    (source_exports / "XAUUSD_M15_New 26.csv").write_text("existing\n", encoding="utf-8")

    result = apply_raw_data_cleanup(raw, tmp_path / "reports", confirm=True)

    assert result.moved_count == 0
    assert result.skipped_count == 1
    assert odd_file.exists()

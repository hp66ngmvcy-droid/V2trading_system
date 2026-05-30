"""Inventory and naming checks for local raw market CSV files."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


_EXPECTED_NAME = re.compile(r"^[A-Z0-9]+_[A-Z0-9]+\.csv$")
_SUPPORTED_TIMEFRAMES = {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"}


@dataclass
class RawDataInventoryRow:
    path: str
    filename: str
    symbol: str = ""
    timeframe: str = ""
    size_bytes: int = 0
    status: str = "OK"
    issues: list[str] = field(default_factory=list)
    suggested_action: str = "Use as canonical raw input."


@dataclass
class RawDataInventoryResult:
    generated_at: str
    raw_dir: str
    report_path: str
    report_json_path: str
    total_csv: int
    ok_count: int
    issue_count: int
    rows: list[RawDataInventoryRow]


@dataclass
class RawDataCleanupMove:
    source: str
    destination: str
    reason: str


@dataclass
class RawDataCleanupPlan:
    generated_at: str
    raw_dir: str
    source_exports_dir: str
    report_path: str
    report_json_path: str
    move_count: int
    dry_run: bool
    moves: list[RawDataCleanupMove]


@dataclass
class RawDataCleanupApplyResult:
    generated_at: str
    raw_dir: str
    source_exports_dir: str
    report_path: str
    report_json_path: str
    moved_count: int
    skipped_count: int
    moved: list[RawDataCleanupMove]
    skipped: list[RawDataCleanupMove]


def audit_raw_data(
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "reports/raw_data_inventory",
) -> RawDataInventoryResult:
    source = Path(raw_dir)
    rows = [_inspect_csv(path) for path in sorted(source.glob("*.csv"))] if source.exists() else []
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output / f"{stamp}_raw_data_inventory.md"
    report_json_path = output / f"{stamp}_raw_data_inventory.json"
    result = RawDataInventoryResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        raw_dir=str(source),
        report_path=str(report_path),
        report_json_path=str(report_json_path),
        total_csv=len(rows),
        ok_count=sum(1 for row in rows if row.status == "OK"),
        issue_count=sum(1 for row in rows if row.status != "OK"),
        rows=rows,
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    report_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def apply_raw_data_cleanup(
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "reports/raw_data_inventory",
    confirm: bool = False,
) -> RawDataCleanupApplyResult:
    if not confirm:
        raise ValueError("confirm=True is required to move raw data files")
    plan = plan_raw_data_cleanup(raw_dir=raw_dir, output_dir=output_dir)
    source_exports = Path(plan.source_exports_dir)
    source_exports.mkdir(parents=True, exist_ok=True)
    moved: list[RawDataCleanupMove] = []
    skipped: list[RawDataCleanupMove] = []
    for move in plan.moves:
        source = Path(move.source)
        destination = Path(move.destination)
        if not source.exists() or destination.exists():
            skipped.append(move)
            continue
        shutil.move(str(source), str(destination))
        moved.append(move)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output / f"{stamp}_raw_data_cleanup_apply.md"
    report_json_path = output / f"{stamp}_raw_data_cleanup_apply.json"
    result = RawDataCleanupApplyResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        raw_dir=str(Path(raw_dir)),
        source_exports_dir=str(source_exports),
        report_path=str(report_path),
        report_json_path=str(report_json_path),
        moved_count=len(moved),
        skipped_count=len(skipped),
        moved=moved,
        skipped=skipped,
    )
    report_path.write_text(_apply_markdown(result), encoding="utf-8")
    report_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def plan_raw_data_cleanup(
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "reports/raw_data_inventory",
) -> RawDataCleanupPlan:
    source = Path(raw_dir)
    source_exports = source / "source_exports"
    rows = [_inspect_csv(path) for path in sorted(source.glob("*.csv"))] if source.exists() else []
    moves = [
        RawDataCleanupMove(
            source=row.path,
            destination=str(source_exports / row.filename),
            reason=", ".join(row.issues),
        )
        for row in rows
        if row.status == "ISSUE" and "empty_file" not in row.issues
    ]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output / f"{stamp}_raw_data_cleanup_plan.md"
    report_json_path = output / f"{stamp}_raw_data_cleanup_plan.json"
    result = RawDataCleanupPlan(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        raw_dir=str(source),
        source_exports_dir=str(source_exports),
        report_path=str(report_path),
        report_json_path=str(report_json_path),
        move_count=len(moves),
        dry_run=True,
        moves=moves,
    )
    report_path.write_text(_cleanup_markdown(result), encoding="utf-8")
    report_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _inspect_csv(path: Path) -> RawDataInventoryRow:
    issues: list[str] = []
    filename = path.name
    symbol = ""
    timeframe = ""
    if not _EXPECTED_NAME.match(filename):
        issues.append("nonstandard_filename")
    stem = path.stem
    parts = stem.split("_")
    if len(parts) != 2:
        issues.append("expected_SYMBOL_TIMEFRAME")
    else:
        symbol, timeframe = parts[0].upper(), parts[1].upper()
        if symbol != parts[0] or timeframe != parts[1]:
            issues.append("use_uppercase_symbol_timeframe")
        if timeframe not in _SUPPORTED_TIMEFRAMES:
            issues.append("unsupported_or_unusual_timeframe")
    size = path.stat().st_size
    if size == 0:
        issues.append("empty_file")
    suggested_action = _suggested_action(filename, issues)
    return RawDataInventoryRow(
        path=str(path),
        filename=filename,
        symbol=symbol,
        timeframe=timeframe,
        size_bytes=size,
        status="ISSUE" if issues else "OK",
        issues=issues,
        suggested_action=suggested_action,
    )


def _suggested_action(filename: str, issues: list[str]) -> str:
    if not issues:
        return "Use as canonical raw input."
    if "empty_file" in issues:
        return "Replace with a valid CSV or remove after review."
    if "expected_SYMBOL_TIMEFRAME" in issues or "nonstandard_filename" in issues:
        return f"Keep as reference or move to data/raw/source_exports/{filename}; create a canonical SYMBOL_TIMEFRAME.csv before testing."
    if "use_uppercase_symbol_timeframe" in issues:
        return "Rename to uppercase SYMBOL_TIMEFRAME.csv before testing."
    if "unsupported_or_unusual_timeframe" in issues:
        return "Confirm timeframe is supported before testing."
    return "Review before using as strategy input."


def _markdown(result: RawDataInventoryResult) -> str:
    lines = [
        "# Raw Data Inventory",
        "",
        f"- Generated: {result.generated_at}",
        f"- Raw dir: `{result.raw_dir}`",
        f"- CSV files: {result.total_csv}",
        f"- OK: {result.ok_count}",
        f"- Issues: {result.issue_count}",
        "",
        "## Rules",
        "",
        "- Put market CSV files in `data/raw/`.",
        "- Use `SYMBOL_TIMEFRAME.csv`, for example `EURUSD_H1.csv` or `XAUUSD_M15.csv`.",
        "- Keep filenames uppercase and avoid spaces or extra suffixes.",
        "- Put broker exports, merged drafts, or one-off source files in `data/raw/source_exports/` after review.",
        "- Use `data/validated/` and `data/features/` only for system-generated outputs.",
        "",
        "## Files",
        "",
        "| Status | File | Symbol | TF | Size | Issues | Suggested Action |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in result.rows:
        issues = ", ".join(row.issues) if row.issues else "none"
        lines.append(f"| {row.status} | `{row.filename}` | {row.symbol} | {row.timeframe} | {row.size_bytes} | {issues} | {row.suggested_action} |")
    lines.append("")
    return "\n".join(lines)


def _cleanup_markdown(result: RawDataCleanupPlan) -> str:
    lines = [
        "# Raw Data Cleanup Plan",
        "",
        f"- Generated: {result.generated_at}",
        f"- Raw dir: `{result.raw_dir}`",
        f"- Source exports dir: `{result.source_exports_dir}`",
        f"- Dry run: {result.dry_run}",
        f"- Proposed moves: {result.move_count}",
        "",
        "## Guardrails",
        "",
        "- This plan does not move, rename, or delete files.",
        "- Review each move before changing local data.",
        "- Keep canonical strategy inputs directly under `data/raw/`.",
        "",
        "## Proposed Moves",
        "",
        "| Source | Destination | Reason |",
        "| --- | --- | --- |",
    ]
    if not result.moves:
        lines.append("| none | none | no noncanonical top-level CSVs found |")
    for move in result.moves:
        lines.append(f"| `{move.source}` | `{move.destination}` | {move.reason} |")
    lines.append("")
    return "\n".join(lines)


def _apply_markdown(result: RawDataCleanupApplyResult) -> str:
    lines = [
        "# Raw Data Cleanup Apply Report",
        "",
        f"- Generated: {result.generated_at}",
        f"- Raw dir: `{result.raw_dir}`",
        f"- Source exports dir: `{result.source_exports_dir}`",
        f"- Moved: {result.moved_count}",
        f"- Skipped: {result.skipped_count}",
        "",
        "## Moved",
        "",
        "| Source | Destination | Reason |",
        "| --- | --- | --- |",
    ]
    if not result.moved:
        lines.append("| none | none | no files moved |")
    for move in result.moved:
        lines.append(f"| `{move.source}` | `{move.destination}` | {move.reason} |")
    lines.extend(["", "## Skipped", "", "| Source | Destination | Reason |", "| --- | --- | --- |"])
    if not result.skipped:
        lines.append("| none | none | no files skipped |")
    for move in result.skipped:
        lines.append(f"| `{move.source}` | `{move.destination}` | source missing or destination already exists |")
    lines.append("")
    return "\n".join(lines)

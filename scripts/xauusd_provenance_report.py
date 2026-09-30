"""Read-only XAUUSD source provenance report.

This script inspects local XAUUSD raw, validated and feature files without
modifying market data. It is an evidence report, not a data repair.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "D1": 1440}


@dataclass(frozen=True)
class FileTarget:
    path: Path
    category: str
    timeframe: str


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def discover_targets(root: Path) -> list[FileTarget]:
    targets: list[FileTarget] = []
    for base, category, patterns in [
        (root / "data/raw", "raw_csv", ["XAUUSD_*.csv"]),
        (root / "data/raw/source_exports", "source_export_csv", ["XAUUSD_*.csv"]),
        (root / "data/validated", "validated_parquet", ["XAUUSD_*.parquet"]),
        (root / "data/features", "feature_parquet", ["XAUUSD_*.parquet"]),
    ]:
        if not base.exists():
            continue
        for pattern in patterns:
            for path in sorted(base.glob(pattern)):
                targets.append(FileTarget(path=path, category=category, timeframe=_timeframe_from_name(path)))
    return targets


def find_import_metadata(root: Path) -> list[dict[str, Any]]:
    names = ["*receipt*", "*metadata*", "*manifest*", "*import*"]
    matches: list[Path] = []
    for base in [root / "data", root / "logs"]:
        if not base.exists():
            continue
        for pattern in names:
            matches.extend(path for path in base.rglob(pattern) if path.is_file())
    return [
        {
            "path": str(path.relative_to(root)),
            "byte_size": path.stat().st_size,
            "sha256": digest(path),
        }
        for path in sorted(set(matches))
    ]


def read_frame(path: Path) -> tuple[pd.DataFrame, str | None]:
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path, sep=None, engine="python"), None
        if path.suffix.lower() == ".parquet":
            return pd.read_parquet(path), None
        return pd.DataFrame(), f"unsupported suffix {path.suffix}"
    except Exception as exc:  # pragma: no cover - exact parser errors vary by engine
        return pd.DataFrame(), f"{type(exc).__name__}: {exc}"


def normalise_timestamps(frame: pd.DataFrame) -> tuple[pd.Series, str]:
    if frame.empty:
        return pd.Series([], dtype="datetime64[ns, UTC]"), "empty"
    cols = {_normalise_column(col): col for col in frame.columns}
    if "timestamp" in cols:
        raw = frame[cols["timestamp"]]
        source = "timestamp"
    elif "datetime" in cols:
        raw = frame[cols["datetime"]]
        source = "datetime"
    elif "date" in cols and "time" in cols:
        raw = frame[cols["date"]].astype(str) + " " + frame[cols["time"]].astype(str)
        source = "date+time"
    else:
        return pd.Series([pd.NaT] * len(frame), dtype="datetime64[ns, UTC]"), "missing"
    return pd.to_datetime(raw, errors="coerce", utc=True), source


def _normalise_column(column: object) -> str:
    return str(column).strip().lower().strip("<>")


def summarise_file(root: Path, target: FileTarget) -> dict[str, Any]:
    frame, error = read_frame(target.path)
    timestamps, timestamp_source = normalise_timestamps(frame)
    summary: dict[str, Any] = {
        "path": str(target.path.relative_to(root)),
        "category": target.category,
        "timeframe": target.timeframe,
        "byte_size": target.path.stat().st_size,
        "sha256": digest(target.path),
        "read_error": error,
        "row_count": int(len(frame)),
        "columns": [str(col) for col in frame.columns],
        "timestamp_source": timestamp_source,
        "timezone_assumption": "UTC; naive local broker/export convention not independently verified",
    }
    valid_ts = timestamps.dropna()
    summary["invalid_timestamp_count"] = int(timestamps.isna().sum())
    summary["first_timestamp"] = valid_ts.min().isoformat() if len(valid_ts) else None
    summary["last_timestamp"] = valid_ts.max().isoformat() if len(valid_ts) else None
    summary["duplicate_timestamp_count"] = int(valid_ts.duplicated(keep=False).sum())
    monthly = monthly_diagnostics(frame, timestamps, target.timeframe)
    summary["monthly"] = monthly
    summary["total_saturday_bars"] = int(sum(item["saturday_bars"] for item in monthly))
    summary["total_weekday_missing_slots"] = int(sum(item["weekday_missing_slots"] for item in monthly))
    return summary


def monthly_diagnostics(frame: pd.DataFrame, timestamps: pd.Series, timeframe: str) -> list[dict[str, Any]]:
    valid = frame.copy()
    valid["_timestamp_utc"] = timestamps
    valid = valid.dropna(subset=["_timestamp_utc"]).sort_values("_timestamp_utc")
    if valid.empty:
        return []
    result: list[dict[str, Any]] = []
    for month, group in valid.groupby(valid["_timestamp_utc"].dt.strftime("%Y-%m")):
        ts = group["_timestamp_utc"]
        saturday = group[ts.dt.dayofweek == 5]
        ranges = _numeric(group, "high") - _numeric(group, "low")
        saturday_ranges = _numeric(saturday, "high") - _numeric(saturday, "low")
        volume = _volume(group)
        saturday_volume = _volume(saturday)
        result.append(
            {
                "month": str(month),
                "rows": int(len(group)),
                "first_timestamp": ts.min().isoformat(),
                "last_timestamp": ts.max().isoformat(),
                "duplicate_timestamp_count": int(ts.duplicated(keep=False).sum()),
                "saturday_bars": int(len(saturday)),
                "saturday_range": _series_stats(saturday_ranges),
                "saturday_volume": _series_stats(saturday_volume),
                "range": _series_stats(ranges),
                "volume": _series_stats(volume),
                "weekday_missing_slots": int(count_weekday_gaps(ts, timeframe)),
            }
        )
    return result


def count_weekday_gaps(timestamps: pd.Series, timeframe: str) -> int:
    minutes = TIMEFRAME_MINUTES.get(timeframe.upper())
    if not minutes or minutes >= 1440:
        return 0
    unique = pd.DatetimeIndex(pd.Series(timestamps).dropna().drop_duplicates().sort_values())
    if len(unique) < 2:
        return 0
    expected = pd.date_range(unique.min(), unique.max(), freq=f"{minutes}min", tz="UTC")
    expected = expected[expected.dayofweek < 5]
    actual = unique[unique.dayofweek < 5]
    return len(expected.difference(actual))


def build_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    targets = discover_targets(root)
    files = [summarise_file(root, target) for target in targets]
    validated = next((item for item in files if item["path"] == "data/validated/XAUUSD_M15.parquet"), None)
    return {
        "report": "xauusd_source_provenance",
        "generated_on": date.today().isoformat(),
        "scope": "read_only_local_files",
        "promotion_eligible": False,
        "source_trust_verdict": "UNRESOLVED",
        "limitations": [
            "No provider API payloads were authenticated.",
            "Naive timestamps are interpreted as UTC for diagnostics only.",
            "Weekday gap counts use a continuous Monday-Friday M15 proxy, not a verified broker session calendar.",
            "Saturday bars are flagged for XAUUSD review; no rows are deleted or repaired.",
            "Hashes identify local files only and do not prove external provenance.",
        ],
        "canonical_candidate": {
            "path": validated["path"] if validated else None,
            "sha256": validated["sha256"] if validated else None,
            "row_count": validated["row_count"] if validated else 0,
            "status": "SOURCE_REVIEW_REQUIRED" if validated else "MISSING",
        },
        "file_count": len(files),
        "files": files,
        "import_receipt_metadata": find_import_metadata(root),
        "aggregate": aggregate(files),
    }


def aggregate(files: list[dict[str, Any]]) -> dict[str, Any]:
    by_category = Counter(str(item["category"]) for item in files)
    saturday_by_path = {item["path"]: item["total_saturday_bars"] for item in files if item["total_saturday_bars"]}
    gaps_by_path = {item["path"]: item["total_weekday_missing_slots"] for item in files if item["total_weekday_missing_slots"]}
    return {
        "files_by_category": dict(by_category),
        "paths_with_saturday_bars": saturday_by_path,
        "paths_with_weekday_gaps": gaps_by_path,
    }


def write_summary(report: dict[str, Any], path: Path) -> None:
    candidate = report["canonical_candidate"]
    aggregate_block = report["aggregate"]
    lines = [
        "# XAUUSD Provenance Summary",
        "",
        f"Generated: {report['generated_on']}",
        f"Verdict: {report['source_trust_verdict']}",
        f"Canonical candidate: {candidate['path'] or 'missing'}",
        f"Canonical rows: {candidate['row_count']}",
        f"Canonical sha256: {candidate['sha256'] or 'missing'}",
        "",
        "## Flags",
        "",
        f"- Files inspected: {report['file_count']}",
        f"- Files with Saturday bars: {len(aggregate_block['paths_with_saturday_bars'])}",
        f"- Files with weekday gaps: {len(aggregate_block['paths_with_weekday_gaps'])}",
        f"- Import metadata files found: {len(report['import_receipt_metadata'])}",
        "",
        "This report is read-only and does not clear XAUUSD for performance use.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _timeframe_from_name(path: Path) -> str:
    parts = path.stem.upper().split("_")
    for part in reversed(parts):
        if part in TIMEFRAME_MINUTES:
            return part
    return "UNKNOWN"


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series([], dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").dropna()


def _volume(frame: pd.DataFrame) -> pd.Series:
    for column in ("volume", "<TICKVOL>", "tick_volume", "tickvol"):
        if column in frame:
            return pd.to_numeric(frame[column], errors="coerce").dropna()
    return pd.Series([], dtype=float)


def _series_stats(series: pd.Series) -> dict[str, float | int | None]:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return {"count": 0, "min": None, "median": None, "max": None, "mean": None}
    return {
        "count": int(len(clean)),
        "min": float(clean.min()),
        "median": float(clean.median()),
        "max": float(clean.max()),
        "mean": float(clean.mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    output = args.output or args.root / "data/research" / f"xauusd_provenance_report_{date.today().isoformat()}.json"
    summary = args.summary or output.with_suffix(".md")
    if output.exists() and not args.overwrite:
        parser.error(f"Output exists: {output}")
    if summary.exists() and not args.overwrite:
        parser.error(f"Summary exists: {summary}")
    report = build_report(args.root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    write_summary(report, summary)
    print(json.dumps({"output": str(output), "summary": str(summary), "aggregate": report["aggregate"]}, indent=2))


if __name__ == "__main__":
    main()

"""Read-only XAUUSD M15 source comparison report.

Compares the current canonical validated parquet against local MT5-style
zero-Saturday CSV candidates. This script writes report artifacts only; it does
not modify raw, validated or feature market data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

OHLC = ("open", "high", "low", "close")
TOLERANCE = 0.01


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_market_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(path)
    elif path.suffix.lower() == ".csv":
        frame = pd.read_csv(path, sep=None, engine="python")
    else:
        raise ValueError(f"Unsupported market file: {path}")
    cols = {_normalise_column(col): col for col in frame.columns}
    if "timestamp" in cols:
        timestamp_raw = frame[cols["timestamp"]]
    elif "date" in cols and "time" in cols:
        timestamp_raw = frame[cols["date"]].astype(str) + " " + frame[cols["time"]].astype(str)
    else:
        raise ValueError(f"No timestamp/date+time columns found in {path}")
    out = pd.DataFrame({"timestamp": pd.to_datetime(timestamp_raw, errors="coerce", utc=True)})
    for field in OHLC:
        if field not in cols:
            raise ValueError(f"Missing {field} column in {path}")
        out[field] = pd.to_numeric(frame[cols[field]], errors="coerce")
    out = out.dropna(subset=["timestamp", *OHLC]).drop_duplicates(subset=["timestamp"], keep="last")
    return out.sort_values("timestamp").reset_index(drop=True)


def discover_candidates(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for base in [root / "data/raw", root / "data/raw/source_exports"]:
        if not base.exists():
            continue
        candidates.extend(sorted(base.glob("XAUUSD_M15*.csv")))
    return candidates


def first_saturday_timestamp(frame: pd.DataFrame) -> str | None:
    saturday = frame[frame["timestamp"].dt.dayofweek == 5]
    if saturday.empty:
        return None
    return saturday["timestamp"].min().isoformat()


def compare_frames(canonical: pd.DataFrame, candidate: pd.DataFrame, tolerance: float = TOLERANCE) -> dict[str, Any]:
    left = canonical.set_index("timestamp")
    right = candidate.set_index("timestamp")
    overlap = left.index.intersection(right.index).sort_values()
    left_only = left.index.difference(right.index)
    right_only = right.index.difference(left.index)
    result: dict[str, Any] = {
        "overlap_start": overlap.min().isoformat() if len(overlap) else None,
        "overlap_end": overlap.max().isoformat() if len(overlap) else None,
        "overlap_rows": int(len(overlap)),
        "missing_in_candidate": int(len(left_only)),
        "missing_in_canonical": int(len(right_only)),
        "ohlc_tolerance": tolerance,
        "field_mismatch_counts": {},
        "mismatch_rows": 0,
        "first_mismatch_examples": [],
    }
    if len(overlap) == 0:
        return result
    left_o = left.loc[overlap, list(OHLC)]
    right_o = right.loc[overlap, list(OHLC)]
    mismatch_mask = pd.DataFrame(False, index=overlap, columns=list(OHLC))
    for field in OHLC:
        diff = (left_o[field] - right_o[field]).abs()
        field_mask = diff > tolerance
        mismatch_mask[field] = field_mask
        result["field_mismatch_counts"][field] = int(field_mask.sum())
    row_mask = mismatch_mask.any(axis=1)
    result["mismatch_rows"] = int(row_mask.sum())
    for ts in overlap[row_mask][:10]:
        example = {"timestamp": ts.isoformat()}
        for field in OHLC:
            if bool(mismatch_mask.loc[ts, field]):
                example[field] = {
                    "canonical": float(left_o.loc[ts, field]),
                    "candidate": float(right_o.loc[ts, field]),
                    "abs_diff": float(abs(left_o.loc[ts, field] - right_o.loc[ts, field])),
                }
        result["first_mismatch_examples"].append(example)
    return result


def build_report(root: Path, canonical_path: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    canonical_path = canonical_path or root / "data/validated/XAUUSD_M15.parquet"
    if not canonical_path.is_absolute():
        canonical_path = root / canonical_path
    canonical_path = canonical_path.resolve()
    canonical = read_market_file(canonical_path)
    comparisons = []
    for path in discover_candidates(root):
        candidate = read_market_file(path)
        saturday_count = int((candidate["timestamp"].dt.dayofweek == 5).sum())
        if saturday_count:
            include_reason = "HAS_SATURDAY_BARS"
        else:
            include_reason = "ZERO_SATURDAY_CANDIDATE"
        comparison = compare_frames(canonical, candidate)
        comparisons.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": digest(path),
                "row_count": int(len(candidate)),
                "first_timestamp": candidate["timestamp"].min().isoformat() if len(candidate) else None,
                "last_timestamp": candidate["timestamp"].max().isoformat() if len(candidate) else None,
                "saturday_bars": saturday_count,
                "candidate_status": include_reason,
                **comparison,
            }
        )
    return {
        "report": "xauusd_source_comparison",
        "generated_on": date.today().isoformat(),
        "scope": "read_only_local_files",
        "promotion_eligible": False,
        "canonical": {
            "path": str(canonical_path.relative_to(root)),
            "sha256": digest(canonical_path),
            "row_count": int(len(canonical)),
            "first_timestamp": canonical["timestamp"].min().isoformat() if len(canonical) else None,
            "last_timestamp": canonical["timestamp"].max().isoformat() if len(canonical) else None,
            "saturday_bars": int((canonical["timestamp"].dt.dayofweek == 5).sum()),
            "first_saturday_timestamp": first_saturday_timestamp(canonical),
        },
        "tolerance": TOLERANCE,
        "comparisons": comparisons,
        "summary": summarise(comparisons),
        "limitations": [
            "This compares local files only and does not authenticate provider payloads.",
            "Naive timestamps are interpreted as UTC for comparison.",
            "OHLC tolerance is ±0.01 points.",
            "No market data is modified or rebuilt.",
        ],
    }


def summarise(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    zero_sat = [item for item in comparisons if item["saturday_bars"] == 0]
    perfect_overlap = [
        item
        for item in zero_sat
        if item["overlap_rows"] > 0 and item["mismatch_rows"] == 0
    ]
    return {
        "candidate_count": len(comparisons),
        "zero_saturday_candidates": len(zero_sat),
        "zero_saturday_candidates_with_exact_overlap": len(perfect_overlap),
        "best_overlap_rows": max((int(item["overlap_rows"]) for item in zero_sat), default=0),
        "best_exact_overlap_rows": max((int(item["overlap_rows"]) for item in perfect_overlap), default=0),
    }


def write_summary(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# XAUUSD Source Comparison Summary",
        "",
        f"Generated: {report['generated_on']}",
        f"Canonical: {report['canonical']['path']}",
        f"Canonical rows: {report['canonical']['row_count']}",
        f"Canonical Saturday bars: {report['canonical']['saturday_bars']}",
        f"First canonical Saturday: {report['canonical']['first_saturday_timestamp']}",
        f"OHLC tolerance: ±{report['tolerance']} pts",
        "",
        "## Candidate Summary",
        "",
        "| Candidate | Rows | Saturday | Overlap | Mismatch rows | Missing in canonical | Missing in candidate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in report["comparisons"]:
        lines.append(
            "| {path} | {row_count} | {saturday_bars} | {overlap_rows} | {mismatch_rows} | {missing_in_canonical} | {missing_in_candidate} |".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "This report is read-only and does not clear XAUUSD for performance use.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _normalise_column(column: object) -> str:
    return str(column).strip().lower().strip("<>")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--canonical", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    output = args.output or args.root / "data/research" / f"xauusd_source_comparison_{date.today().isoformat()}.json"
    summary = args.summary or output.with_suffix(".md")
    if output.exists() and not args.overwrite:
        parser.error(f"Output exists: {output}")
    if summary.exists() and not args.overwrite:
        parser.error(f"Summary exists: {summary}")
    report = build_report(args.root, args.canonical)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    write_summary(report, summary)
    print(json.dumps({"output": str(output), "summary": str(summary), "summary_stats": report["summary"]}, indent=2))


if __name__ == "__main__":
    main()

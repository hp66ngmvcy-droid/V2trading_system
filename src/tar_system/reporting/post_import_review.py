"""Isolated synthetic import-to-report prototype; no scheduler or strategy scoring."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import math
from pathlib import Path
import tempfile
from typing import Any

EVALUATOR_VERSION = "synthetic-observation-v1"


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise ValueError("Timestamps must include an explicit UTC offset")
    return result.astimezone(timezone.utc)


def number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("Prices must be finite numbers")
    return float(value)


def unique(items: list[dict], key: str) -> dict[str, dict]:
    result = {}
    for item in items:
        identity = item[key]
        if not isinstance(identity, str) or not identity or identity in result:
            raise ValueError(f"Missing or duplicate {key}")
        result[identity] = item
    return result


def evaluate(packet: dict) -> dict:
    """Evaluate threshold observations, never fills, returns or strategy eligibility.

    Bars use [open_time, close_time) intervals with OHLC available at close_time.
    Full regular-bar coverage is required for this synthetic-only first slice.
    """
    if packet.get("schema_version") != 1 or packet.get("evidence_class") != "SYNTHETIC":
        raise ValueError("Prototype accepts schema 1 SYNTHETIC evidence only")
    if not isinstance(packet.get("prompt_version"), str) or not packet["prompt_version"]:
        raise ValueError("prompt_version is required")
    required = packet["required_dataset_ids"]
    if not required or len(set(required)) != len(required):
        raise ValueError("Required datasets must be non-empty and unique")
    datasets = unique(packet["datasets"], "dataset_id")
    forecasts = unique(packet["forecasts"], "forecast_id")
    if not forecasts:
        raise ValueError("At least one synthetic forecast is required")
    as_of = timestamp(packet["import_completed_at"])
    issues = []
    prepared = {}
    for identity in required:
        data = datasets.get(identity)
        if data is None or data.get("validation_status") != "PASSED" or data.get("feature_status") != "READY":
            issues.append({"dataset_id": identity, "reason": "INPUT_NOT_READY"})
            continue
        if digest(data["bars"]) != data["data_hash"] or digest(data["features"]) != data["feature_hash"]:
            issues.append({"dataset_id": identity, "reason": "HASH_MISMATCH"})
            continue
        if data.get("feature_source_hash") != data["data_hash"] or not data.get("feature_version"):
            issues.append({"dataset_id": identity, "reason": "FEATURE_LINEAGE_MISMATCH"})
            continue
        step = data["bar_minutes"]
        if isinstance(step, bool) or not isinstance(step, int) or step <= 0:
            raise ValueError("bar_minutes must be a positive integer")
        bars = []
        previous = None
        for bar in data["bars"]:
            start, end = timestamp(bar["open_time"]), timestamp(bar["close_time"])
            lo, hi, op, cl = (number(bar[k]) for k in ("low", "high", "open", "close"))
            if end - start != timedelta(minutes=step) or lo > min(op, cl) or hi < max(op, cl) or lo > hi:
                raise ValueError("Invalid OHLC or bar interval")
            if previous is not None and start < previous:
                raise ValueError("Duplicate, overlapping or out-of-order bars")
            if end > as_of:
                issues.append({"dataset_id": identity, "reason": "INCOMPLETE_BAR"})
            previous = end
            bars.append((start, end, lo, hi))
        prepared[identity] = bars
    outcomes = []
    for identity, forecast in forecasts.items():
        dataset_id = forecast["dataset_id"]
        if dataset_id not in required:
            raise ValueError("Forecast references an undeclared dataset")
        start, end = timestamp(forecast["evaluation_start"]), timestamp(forecast["evaluation_end"])
        frozen = timestamp(forecast["frozen_at"])
        if not timestamp(forecast["input_available_at"]) <= frozen < start < end:
            raise ValueError("Forecast chronology violates the frozen evaluation window")
        lower, upper = number(forecast["lower_level"]), number(forecast["upper_level"])
        if lower >= upper or forecast["expected_side"] not in ("UPPER", "LOWER"):
            raise ValueError("Invalid observation levels or expected_side")
        bars = [b for b in prepared.get(dataset_id, []) if b[0] >= start and b[1] <= end]
        complete = (end <= as_of and bool(bars) and bars[0][0] == start
                    and bars[-1][1] == end and all(a[1] == b[0] for a, b in zip(bars, bars[1:])))
        if not complete:
            issues.append({"forecast_id": identity, "reason": "WINDOW_INCOMPLETE"})
            continue
        outcome = "NO_THRESHOLD_REACHED"
        event_time = None
        for _, bar_end, low, high in bars:
            up, down = high >= upper, low <= lower
            if up or down:
                outcome = "AMBIGUOUS_SAME_BAR" if up and down else "UPPER_FIRST" if up else "LOWER_FIRST"
                event_time = bar_end.isoformat()
                break
        expected = forecast["expected_side"] + "_FIRST"
        interpretation = "UNRESOLVED" if outcome in ("AMBIGUOUS_SAME_BAR", "NO_THRESHOLD_REACHED") else "SUPPORTED" if outcome == expected else "CONTRADICTED"
        outcomes.append({"forecast_id": identity, "dataset_id": dataset_id,
                         "forecast_hash": digest(forecast), "outcome": outcome,
                         "interpretation": interpretation, "event_bar_close": event_time})
    # A partial batch cannot publish performance-like conclusions.
    if issues:
        outcomes = []
    return {"schema_version": 1, "evaluator_version": EVALUATOR_VERSION,
            "evidence_class": "SYNTHETIC", "prompt_version": packet["prompt_version"],
            "input_hash": digest(packet), "run_status": "WAITING_FOR_DATA" if issues else "COMPLETE",
            "findings": issues, "outcomes": outcomes,
            "outcome_counts": dict(Counter(row["outcome"] for row in outcomes)),
            "eligible_prospective_days": 0, "checkpoint_due": False,
            "model_review_status": "NOT_REQUESTED",
            "next_action": "REPAIR_SYNTHETIC_INPUT" if issues else "REVIEW_SYNTHETIC_REPORT"}


def run_review(packet: dict, output_dir: Path) -> tuple[Path, bool]:
    """Atomically publish an immutable report pair; advisory lock recovers on exit."""
    report = evaluate(packet)
    key = digest({"packet": packet, "evaluator": EVALUATOR_VERSION})
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / key
    with (output_dir / ".review.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lines = ["# Synthetic post-import review", "", f"Status: {report['run_status']}",
                 "", "Synthetic observation labels only. No trading performance or promotion evidence.",
                 "", f"Input hash: {report['input_hash']}", "", "## Findings", ""]
        lines.extend("- " + canonical(item) for item in report["findings"])
        lines.extend(["", "## Observation outcomes", ""])
        lines.extend("- " + canonical(row) for row in report["outcomes"])
        lines.extend(["", f"Next action: {report['next_action']}", ""])
        markdown = "\n".join(lines)
        if destination.exists():
            if (json.loads((destination / "report.json").read_text()) != report
                    or (destination / "report.md").read_text() != markdown):
                raise ValueError("Existing report incomplete or changed; preserve it for investigation")
            return destination, True
        with tempfile.TemporaryDirectory(prefix=".review-", dir=output_dir) as temporary:
            staged = Path(temporary) / "result"
            staged.mkdir()
            (staged / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
            (staged / "report.md").write_text(markdown)
            staged.rename(destination)
    return destination, False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        packet = json.loads(args.input.read_text())
        destination, reused = run_review(packet, args.output_dir)
        report = json.loads((destination / "report.json").read_text())
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"Review failed: {error}\n")
    print(json.dumps({"status": report["run_status"], "reused": reused, "report_dir": str(destination)}))
    return 0 if report["run_status"] == "COMPLETE" else 3


if __name__ == "__main__":
    raise SystemExit(main())

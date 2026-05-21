"""Append-only learning log for REVIEW and KILL candidate decisions."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.scoring.gates import GateResult

FAILURE_LOG = Path("runtime") / "failure_log.jsonl"

KEEP_PARTS_HEURISTICS = {
    "min_trades": "Signal frequency is too low; widen trigger logic or test a lower timeframe.",
    "max_drawdown": "Risk profile failed; review stop distance, ATR sizing, and circuit-breaker settings.",
    "consecutive_loss_ratio": "Directional failure detected; add trend/regime filter before further parameter search.",
    "soft_gates": "Core idea may be salvageable; review failed soft gates before mutating nearby parameters.",
}


def log_failure(candidate: Any, gate_result: GateResult) -> None:
    """Write a structured failure/review record without mutating the queue."""

    if gate_result.verdict == "KEEP":
        return
    FAILURE_LOG.parent.mkdir(parents=True, exist_ok=True)
    metrics = getattr(candidate, "metrics", None) or {}
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_id": getattr(candidate, "candidate_id", None),
        "strategy": getattr(candidate, "strategy", None),
        "asset": getattr(candidate, "symbol", None),
        "timeframe": getattr(candidate, "timeframe", None),
        "params": getattr(candidate, "parameters", None),
        "verdict": gate_result.verdict,
        "failed_gate": gate_result.failed_gate,
        "reason": gate_result.reason,
        "reason_codes": gate_result.reason_codes,
        "metrics": metrics,
        "what_to_keep": KEEP_PARTS_HEURISTICS.get(gate_result.failed_gate or "", "Review manually."),
        "mutation_parent": getattr(candidate, "parent_id", None),
    }
    with FAILURE_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(record), sort_keys=True) + "\n")


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)

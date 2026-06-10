"""Review log and markdown summary generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.settings import LOG_DIR, REPORT_DIR


def append_review_result(
    strategy: str,
    version: str,
    symbol: str,
    timeframe: str,
    metrics: dict[str, float],
    score: float,
    verdict: str,
    reason: str,
    next_action: str,
) -> Path:
    path = Path(LOG_DIR) / "review_log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "version": version,
        "symbol": symbol,
        "timeframe": timeframe,
        "metrics": metrics,
        "score": score,
        "verdict": verdict,
        "reason": reason,
        "next_action": next_action,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=str) + "\n")
    return path


def load_review_results(path: str | Path | None = None) -> list[dict[str, Any]]:
    source = Path(path) if path else Path(LOG_DIR) / "review_log.jsonl"
    if not source.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"strategy": "unknown", "symbol": "", "timeframe": "", "verdict": "REVIEW", "score": 0, "next_action": "REPAIR_REVIEW_LOG"})
    return rows


def write_review_summary(results: list[dict[str, Any]] | None = None) -> Path:
    rows = results if results is not None else load_review_results()
    output = Path(REPORT_DIR) / "review_summary.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Review Summary", ""]
    if not rows:
        lines.append("No review results yet.")
    for row in rows[-25:]:
        lines.append(
            f"- {row.get('strategy', 'unknown')} {row.get('symbol', '')} {row.get('timeframe', '')}: "
            f"{row.get('verdict', 'REVIEW')} score={row.get('score', 0)} next={row.get('next_action', 'REVIEW')}"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output

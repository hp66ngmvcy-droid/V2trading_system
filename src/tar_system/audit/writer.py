"""JSONL audit logging."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from tar_system.settings import LOG_DIR


def append_audit_event(
    event_type: str,
    strategy: str,
    symbol: str,
    timeframe: str,
    decision: str,
    reason_code: str,
    metadata: dict[str, object] | None = None,
) -> Path:
    output = Path(LOG_DIR) / "audit" / "audit.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "strategy": strategy,
        "symbol": symbol,
        "timeframe": timeframe,
        "decision": decision,
        "reason_code": reason_code,
        "metadata": metadata or {},
    }
    with output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, default=str) + "\n")
    return output

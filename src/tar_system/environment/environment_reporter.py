"""Environment report writer."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from tar_system.environment.risk_state import EnvironmentDecision
from tar_system.settings import REPORT_DIR


def write_environment_report(symbol: str, timeframe: str, target_date: datetime, decision: EnvironmentDecision) -> tuple[Path, Path]:
    output_dir = Path(REPORT_DIR) / "environment"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{symbol}_{timeframe}_{target_date.date().isoformat()}"
    payload = {
        "symbol": symbol,
        "timeframe": timeframe,
        "date": target_date.isoformat(),
        "state": decision.state,
        "reason_codes": decision.reason_codes,
        "matched_events": [asdict(event) for event in decision.matched_events],
        "message": decision.message,
    }
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    lines = [f"# Environment Report {symbol} {timeframe}", "", f"- Date: {target_date.isoformat()}", f"- State: {decision.state}"]
    lines.append(f"- Reasons: {', '.join(decision.reason_codes) if decision.reason_codes else 'None'}")
    lines.append("")
    lines.append("## Matched Events")
    if not decision.matched_events:
        lines.append("- None")
    for event in decision.matched_events:
        lines.append(f"- {event.title or event.name} ({event.event_type}) {event.impact} at {event.date.isoformat()}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path, json_path

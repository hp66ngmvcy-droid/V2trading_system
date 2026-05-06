"""Daily local research summary page."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from tar_system.dashboard.components.layout import page_header
from tar_system.dashboard.runtime_control import read_mt5_promotion_log, read_schedule
from tar_system.environment.event_calendar import load_events
from tar_system.environment.risk_state import evaluate_environment


def build_daily_summary(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now()
    today = now.date().isoformat()
    metrics = _today_metrics(today)
    loaded_events = load_events() or []
    events = [event for event in loaded_events if now <= event.date <= now + timedelta(hours=48)]
    return {
        "date": today,
        "strategies_tested_today": len(metrics),
        "best_score_today": max([item.get("score", 0.0) for item in metrics], default=0.0),
        "worst_performer": min(metrics, key=lambda item: item.get("score", 0.0), default={}),
        "current_environment_state": evaluate_environment("XAUUSD", now, loaded_events).state,
        "events_next_48h": [event.__dict__ for event in events],
        "audit_events_today_last_20": _audit_events_today(today)[-20:],
        "pending_scheduled_jobs": [job for job in read_schedule().get("jobs", []) if job.get("status") in {"scheduled", "run_now"}],
        "mt5_promotion_log_entries": read_mt5_promotion_log(),
        "multi_asset_comparison": _load_json(Path("data/results/gold_v2_M15_asset_comparison.json")),
    }


def render(st: object) -> None:
    page_header(st, "Daily Summary", "Today’s paper research, event risk, audit trail and pending jobs.")
    summary = build_daily_summary()
    st.write(summary)


def _today_metrics(today: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in Path("data/results").glob("*_*_*_metrics.json"):
        if datetime.fromtimestamp(path.stat().st_mtime).date().isoformat() != today:
            continue
        metrics = _load_json(path)
        rows.append({"path": str(path), "score": float(metrics.get("score", 0.0)), "metrics": metrics})
    return rows


def _audit_events_today(today: str) -> list[dict[str, Any]]:
    path = Path("logs/audit/audit.jsonl")
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(payload.get("timestamp", "")).startswith(today):
            rows.append(payload)
    return rows


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

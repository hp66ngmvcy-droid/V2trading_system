"""Environment risk state logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from tar_system import reason_codes as rc
from tar_system.environment.asset_impact_map import event_impacts_asset, event_impacts_symbol
from tar_system.environment.event_calendar import Event


@dataclass
class EnvironmentDecision:
    state: str
    reason_codes: list[str] = field(default_factory=list)
    matched_events: list[Event] = field(default_factory=list)
    message: str = ""


HIGH_IMPACT_WINDOWS = {
    "CENTRAL_BANK_RATE_DECISION": (4, 4),
    "EMERGENCY_CENTRAL_BANK_ACTION": (4, 4),
    "NFP": (2, 3),
    "CPI": (2, 3),
}


def event_hold_window(event: Event) -> tuple[int, int]:
    if event.pre_window_hours is not None and event.post_window_hours is not None:
        return event.pre_window_hours, event.post_window_hours
    return HIGH_IMPACT_WINDOWS.get(event.event_type.upper(), (2, 2))


def evaluate_environment(symbol: str, target_date: datetime, events: list[Event] | None = None) -> EnvironmentDecision:
    if events is None:
        return EnvironmentDecision(rc.ENV_REVIEW_ONLY, ["MISSING_EVENT_DATA"], [], "Missing local event data")
    target_for_compare = _comparable_datetime(target_date)
    state = rc.ENV_SAFE_TO_TEST
    reasons: list[str] = []
    matched: list[Event] = []
    for event in events:
        impacts = event_impacts_asset(event.event_type, event.country, symbol, event.affected_assets) or event_impacts_symbol(event.name, symbol)
        if not impacts:
            continue
        matched.append(event)
        if event.shock:
            return EnvironmentDecision(rc.ENV_BLOCK_TRADING, ["UNSCHEDULED_SHOCK"], matched, "Shock event requires human review")
        pre_hours, post_hours = event_hold_window(event)
        event_for_compare = _comparable_datetime(event.date)
        in_hold_window = event_for_compare - timedelta(hours=pre_hours) <= target_for_compare <= event_for_compare + timedelta(hours=post_hours)
        date_only_review = target_for_compare.time().hour == 0 and target_for_compare.time().minute == 0 and target_for_compare.date() == event_for_compare.date()
        if event.impact.upper() == "HIGH" and (in_hold_window or date_only_review):
            state = rc.ENV_HOLD_TRADING
            reasons.append(f"HIGH_IMPACT_{event.event_type}")
        elif event.impact.upper() == "MEDIUM" and state not in {rc.ENV_HOLD_TRADING, rc.ENV_BLOCK_TRADING}:
            state = rc.ENV_REDUCE_RISK
            reasons.append(f"MEDIUM_IMPACT_{event.event_type}")
        elif event.impact.upper() == "LOW" and state == rc.ENV_SAFE_TO_TEST:
            state = rc.ENV_CAUTION
            reasons.append(f"LOW_IMPACT_{event.event_type}")
    return EnvironmentDecision(state, reasons, matched, "Environment checked")


def check_environment_risk(symbol: str, target_date: datetime, events: list[Event] | None = None) -> str:
    return evaluate_environment(symbol, target_date, events).state


def _comparable_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)

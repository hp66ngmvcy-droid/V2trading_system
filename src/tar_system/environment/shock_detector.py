"""Manual shock detection helpers."""

from __future__ import annotations

from tar_system.environment.event_calendar import Event

SHOCK_TYPES = {"GEOPOLITICAL_SHOCK", "EXCHANGE_OUTAGE", "CRYPTO_EXPLOIT", "BANK_FAILURE", "EMERGENCY_CENTRAL_BANK_ACTION"}


def is_shock_event(event: Event) -> bool:
    return event.shock or event.event_type.upper() in SHOCK_TYPES

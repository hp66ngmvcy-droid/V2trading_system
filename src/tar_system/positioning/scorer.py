"""Positioning context scoring helpers."""

from __future__ import annotations

from tar_system.positioning.store import latest_positioning_score


def get_positioning_context(symbol: str) -> dict[str, object]:
    """Return latest blended positioning context.

    This is context only. It must not place trades or force an automatic signal.
    """
    return latest_positioning_score(symbol)


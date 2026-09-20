"""Load daily key levels from morning brief JSON files."""

from __future__ import annotations

import json
from pathlib import Path


def load_macro(date: str, briefs_dir: Path) -> dict:
    """Return the top-level ``macro`` block for *date*, or ``{}`` if absent."""
    path = briefs_dir / f"{date}_levels.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    result = data.get("macro")
    return result if isinstance(result, dict) else {}


def load_opening_type(date: str, symbol: str, briefs_dir: Path) -> str | None:
    """Return the opening type for *symbol* on *date*, or None if not set.

    Resolution order:
    1. ``XAUUSD.opening_type`` / ``BTCUSD.opening_type`` (per-asset, most specific)
    2. ``macro.opening_type`` (session-level fallback)
    3. ``None``
    """
    path = briefs_dir / f"{date}_levels.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    asset = data.get(symbol)
    if isinstance(asset, dict) and asset.get("opening_type"):
        return str(asset["opening_type"])
    macro = data.get("macro")
    if isinstance(macro, dict) and macro.get("opening_type"):
        return str(macro["opening_type"])
    return None


def load_daily_levels(date: str, symbol: str, briefs_dir: Path) -> dict | None:
    """Return the symbol sub-dict for *date* or None if file/symbol missing.

    Args:
        date: ISO date string, e.g. ``"2026-09-07"``.
        symbol: e.g. ``"XAUUSD"``.
        briefs_dir: Path to the directory containing ``YYYY-MM-DD_levels.json`` files.

    Returns:
        The symbol dict (must contain ``key_levels``) or ``None``.
        Returns ``None`` on missing file, missing symbol key, or null symbol value.
        Never raises on a missing file.
    """
    path = briefs_dir / f"{date}_levels.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    entry = data.get(symbol)
    if not entry or not isinstance(entry, dict):
        return None
    # Require canonical key_levels block; skip non-standard brief formats
    if "key_levels" not in entry:
        return None
    # Propagate top-level issued_at so callers can apply a look-ahead gate
    if "issued_at" in data:
        entry = {**entry, "issued_at": data["issued_at"]}
    return entry

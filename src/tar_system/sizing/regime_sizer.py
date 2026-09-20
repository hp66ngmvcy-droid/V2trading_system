"""Regime-weighted position sizing overlay.

Reads `regime` and `opening_type` from the daily brief macro section
(both optional fields, default None if absent — backwards compatible).

Usage in a strategy or runner::

    from tar_system.sizing.regime_sizer import regime_size_multiplier

    multiplier = regime_size_multiplier(regime, opening_type)
    final_lot = base_lot * multiplier
"""

from __future__ import annotations

_FLOOR = 0.5
_CEILING = 1.5

# (regime_upper, opening_type_upper) -> multiplier
# Specific pairs take priority over regime-only rows.
_PAIR_TABLE: dict[tuple[str, str], float] = {
    ("RESERVE", "OPENING DRIVE"): 1.5,
    ("RATES GOLD", "TEST DRIVE"): 1.2,
    ("DOLLAR", "TEST DRIVE"): 1.1,
    ("FEAR", "OPENING DRIVE"): 0.6,
    ("MIXED", "OPEN AUCTION"): 0.5,
    ("MIXED", "RANGE REJECTION"): 0.7,
}

# Regime-only rows (opening_type is None or unrecognised).
_REGIME_TABLE: dict[str, float] = {
    "FEAR": 0.6,
}


def regime_size_multiplier(
    regime: str | None,
    opening_type: str | None = None,
) -> float:
    """Return a position size multiplier based on regime and optional opening type.

    Multiply the base position size by this value before submitting to the
    broker. The result is clamped to [0.5, 1.5].

    Rules (in priority order):
    1. Unknown / None regime → 1.0 (neutral).
    2. FEAR regime → always 0.6, regardless of opening_type.
    3. Known regime + known opening_type → lookup _PAIR_TABLE, else 1.0.
    4. Known regime + no opening_type → lookup _REGIME_TABLE, else 1.0.
    """
    if not regime:
        return 1.0

    r = regime.strip().upper()

    # FEAR always wins.
    if r == "FEAR":
        return 0.6

    if opening_type:
        ot = opening_type.strip().upper()
        pair_key = (r, ot)
        if pair_key in _PAIR_TABLE:
            raw = _PAIR_TABLE[pair_key]
            return max(_FLOOR, min(_CEILING, raw))

    # Regime-only fallback.
    raw = _REGIME_TABLE.get(r, 1.0)
    return max(_FLOOR, min(_CEILING, raw))

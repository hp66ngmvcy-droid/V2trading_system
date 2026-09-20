"""Unit tests for regime_size_multiplier."""

import pytest
from tar_system.sizing.regime_sizer import regime_size_multiplier


# --- Core table ---

def test_reserve_opening_drive():
    assert regime_size_multiplier("RESERVE", "Opening Drive") == 1.5


def test_rates_gold_test_drive():
    assert regime_size_multiplier("RATES GOLD", "Test Drive") == 1.2


def test_dollar_test_drive():
    assert regime_size_multiplier("DOLLAR", "Test Drive") == 1.1


def test_mixed_open_auction():
    assert regime_size_multiplier("MIXED", "Open Auction") == 0.5


def test_mixed_range_rejection():
    assert regime_size_multiplier("MIXED", "Range Rejection") == 0.7


# --- FEAR always wins ---

def test_fear_opening_drive():
    assert regime_size_multiplier("FEAR", "Opening Drive") == 0.6


def test_fear_test_drive():
    assert regime_size_multiplier("FEAR", "Test Drive") == 0.6


def test_fear_none_opening_type():
    assert regime_size_multiplier("FEAR") == 0.6


def test_fear_unknown_opening_type():
    assert regime_size_multiplier("FEAR", "something_random") == 0.6


# --- Neutral fallbacks ---

def test_unknown_regime_returns_neutral():
    assert regime_size_multiplier("SOMETHING_ELSE") == 1.0


def test_none_regime_returns_neutral():
    assert regime_size_multiplier(None) == 1.0


def test_empty_string_regime_returns_neutral():
    assert regime_size_multiplier("") == 1.0


def test_none_opening_type_uses_regime_only_rule():
    # FEAR has a regime-only rule; MIXED does not → neutral
    assert regime_size_multiplier("FEAR", None) == 0.6
    assert regime_size_multiplier("MIXED", None) == 1.0


def test_unrecognised_opening_type_falls_back_to_regime_only():
    # RESERVE has no regime-only row → neutral
    assert regime_size_multiplier("RESERVE", "UNKNOWN_SESSION") == 1.0


# --- Clamp ---

def test_multiplier_ceiling_never_exceeded():
    # RESERVE + Opening Drive = 1.5; verify clamp does not reduce it
    result = regime_size_multiplier("RESERVE", "Opening Drive")
    assert result <= 1.5


def test_multiplier_floor_never_breached():
    # MIXED + Open Auction = 0.5; verify clamp does not reduce further
    result = regime_size_multiplier("MIXED", "Open Auction")
    assert result >= 0.5


def test_all_multipliers_within_bounds():
    """Exhaustive check: every entry in both lookup tables stays in [0.5, 1.5]."""
    cases = [
        ("RESERVE", "Opening Drive"),
        ("RATES GOLD", "Test Drive"),
        ("DOLLAR", "Test Drive"),
        ("FEAR", "Opening Drive"),
        ("MIXED", "Open Auction"),
        ("MIXED", "Range Rejection"),
        ("FEAR", None),
        ("MIXED", None),
        (None, None),
        ("UNKNOWN", "Opening Drive"),
    ]
    for regime, ot in cases:
        result = regime_size_multiplier(regime, ot)
        assert 0.5 <= result <= 1.5, f"Out of bounds for ({regime}, {ot}): {result}"


# --- Case insensitivity ---

def test_case_insensitive_regime():
    assert regime_size_multiplier("reserve", "Opening Drive") == 1.5


def test_case_insensitive_opening_type():
    assert regime_size_multiplier("RESERVE", "opening drive") == 1.5

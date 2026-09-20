"""Unit tests for daily_brief_loader.load_daily_levels."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from tar_system.data.daily_brief_loader import load_daily_levels, load_opening_type


VALID_BRIEF = {
    "date": "2026-09-07",
    "XAUUSD": {
        "current_price": 4426,
        "daily_bias": "SELL",
        "sell_confidence": 0.67,
        "buy_confidence": 0.63,
        "key_levels": {
            "bearish_invalidation": 4470,
            "sell_zone_high": 4455,
            "sell_zone_low": 4435,
            "no_trade_high": 4435,
            "no_trade_low": 4415,
            "buy_zone_high": 4420,
            "buy_zone_low": 4410,
            "asia_liquidity_low": 4395,
        },
        "top_scenario_targets": [4410, 4390],
    },
}


@pytest.fixture()
def briefs_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write_brief(briefs_dir: Path, date: str, content: dict) -> Path:
    p = briefs_dir / f"{date}_levels.json"
    p.write_text(json.dumps(content))
    return p


# ---- missing file → None ----

def test_missing_file_returns_none(briefs_dir: Path) -> None:
    result = load_daily_levels("2026-09-99", "XAUUSD", briefs_dir)
    assert result is None


def test_missing_file_does_not_raise(briefs_dir: Path) -> None:
    """No FileNotFoundError on absent brief."""
    result = load_daily_levels("1900-01-01", "XAUUSD", briefs_dir)
    assert result is None


# ---- valid file → dict ----

def test_valid_file_returns_dict(briefs_dir: Path) -> None:
    _write_brief(briefs_dir, "2026-09-07", VALID_BRIEF)
    result = load_daily_levels("2026-09-07", "XAUUSD", briefs_dir)
    assert isinstance(result, dict)
    assert "key_levels" in result
    assert result["sell_confidence"] == 0.67


def test_correct_symbol_returned(briefs_dir: Path) -> None:
    _write_brief(briefs_dir, "2026-09-07", VALID_BRIEF)
    result = load_daily_levels("2026-09-07", "XAUUSD", briefs_dir)
    assert result is not None
    assert result["daily_bias"] == "SELL"


# ---- missing symbol → None ----

def test_missing_symbol_returns_none(briefs_dir: Path) -> None:
    _write_brief(briefs_dir, "2026-09-07", VALID_BRIEF)
    result = load_daily_levels("2026-09-07", "BTCUSD", briefs_dir)
    assert result is None


# ---- null symbol value → None ----

def test_null_symbol_returns_none(briefs_dir: Path) -> None:
    brief = {**VALID_BRIEF, "XAUUSD": None}
    _write_brief(briefs_dir, "2026-09-07", brief)
    result = load_daily_levels("2026-09-07", "XAUUSD", briefs_dir)
    assert result is None


# ---- no key_levels block → None ----

def test_no_key_levels_returns_none(briefs_dir: Path) -> None:
    """Non-canonical brief format (no key_levels) is rejected."""
    brief = {"date": "2026-09-10", "XAUUSD": {"current": 4414, "judgement_buy_pct": 63}}
    _write_brief(briefs_dir, "2026-09-10", brief)
    result = load_daily_levels("2026-09-10", "XAUUSD", briefs_dir)
    assert result is None


# ---- load_opening_type ----

def test_opening_type_from_asset_level(briefs_dir: Path) -> None:
    brief = {**VALID_BRIEF, "XAUUSD": {**VALID_BRIEF["XAUUSD"], "opening_type": "OPENING DRIVE"}}
    _write_brief(briefs_dir, "2026-09-07", brief)
    assert load_opening_type("2026-09-07", "XAUUSD", briefs_dir) == "OPENING DRIVE"


def test_opening_type_falls_back_to_macro(briefs_dir: Path) -> None:
    brief = {**VALID_BRIEF, "macro": {"opening_type": "TEST DRIVE"}}
    _write_brief(briefs_dir, "2026-09-07", brief)
    assert load_opening_type("2026-09-07", "XAUUSD", briefs_dir) == "TEST DRIVE"


def test_asset_opening_type_overrides_macro(briefs_dir: Path) -> None:
    brief = {
        **VALID_BRIEF,
        "XAUUSD": {**VALID_BRIEF["XAUUSD"], "opening_type": "RANGE REJECTION"},
        "macro": {"opening_type": "OPEN AUCTION"},
    }
    _write_brief(briefs_dir, "2026-09-07", brief)
    assert load_opening_type("2026-09-07", "XAUUSD", briefs_dir) == "RANGE REJECTION"


def test_opening_type_null_returns_none(briefs_dir: Path) -> None:
    brief = {**VALID_BRIEF, "macro": {"opening_type": None}}
    _write_brief(briefs_dir, "2026-09-07", brief)
    assert load_opening_type("2026-09-07", "XAUUSD", briefs_dir) is None


def test_opening_type_missing_file_returns_none(briefs_dir: Path) -> None:
    assert load_opening_type("1900-01-01", "XAUUSD", briefs_dir) is None

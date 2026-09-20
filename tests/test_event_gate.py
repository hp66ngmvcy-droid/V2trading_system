"""Unit tests for the event-gate filter in key_level_sweep_v1.

Three cases:
1. event_gate.active = true  → strategy returns HOLD with reason EVENT_GATE
2. event_gate.active = false → strategy proceeds normally (may produce BUY/SELL/HOLD)
3. No event_gate key present  → strategy proceeds normally (backwards compatible)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tar_system import reason_codes as rc
from tar_system.strategies.key_level_sweep_v1 import KeyLevelSweepV1, _brief_cache

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_BASE_LEVELS = {
    "XAUUSD": {
        "current_price": 2350,
        "daily_bias": "SELL",
        "sell_confidence": 0.70,
        "buy_confidence": 0.60,
        "key_levels": {
            "bearish_invalidation": 2400,
            "sell_zone_high": 2380,
            "sell_zone_low": 2370,
            "no_trade_high": 2365,
            "no_trade_low": 2345,
            "buy_zone_high": 2345,
            "buy_zone_low": 2335,
            "asia_liquidity_low": 2320,
        },
        "top_scenario_targets": [2340, 2320],
    }
}

_BASE_BAR = {
    "timestamp": pd.Timestamp("2099-01-01 14:00:00"),
    "symbol": "XAUUSD",
    "timeframe": "M15",
    "open": 2368.0,
    "high": 2375.0,
    "low": 2342.0,
    "close": 2343.0,
    "atr": 15.0,
}


def _write_brief(tmp_path: Path, date: str, macro_extra: dict) -> Path:
    data = {"macro": {"note": "test", **macro_extra}, **_BASE_LEVELS}
    brief = tmp_path / f"{date}_levels.json"
    brief.write_text(json.dumps(data))
    return tmp_path


def _make_strategy(briefs_dir: Path) -> KeyLevelSweepV1:
    _brief_cache.clear()
    return KeyLevelSweepV1(symbol="XAUUSD", briefs_dir=briefs_dir, min_confidence=0.55)


def _bar(date: str) -> pd.Series:
    return pd.Series({**_BASE_BAR, "timestamp": pd.Timestamp(f"{date} 14:00:00")})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_event_gate_active_returns_hold(tmp_path):
    """active=true must return HOLD with reason EVENT_GATE."""
    date = "2099-01-01"
    briefs_dir = _write_brief(tmp_path, date, {"event_gate": {"active": True, "event": "FOMC", "window_uk": "19:00-20:30"}})
    strategy = _make_strategy(briefs_dir)
    sig = strategy.generate_signal(_bar(date), regime="UNKNOWN")
    assert sig.side == "HOLD"
    assert sig.reason_code == rc.EVENT_GATE


def test_event_gate_inactive_proceeds(tmp_path):
    """active=false must NOT return EVENT_GATE — strategy runs normally."""
    date = "2099-01-02"
    briefs_dir = _write_brief(tmp_path, date, {"event_gate": {"active": False, "event": "CPI"}})
    strategy = _make_strategy(briefs_dir)
    sig = strategy.generate_signal(_bar(date), regime="UNKNOWN")
    assert sig.reason_code != rc.EVENT_GATE


def test_event_gate_absent_proceeds(tmp_path):
    """No event_gate key → backwards compatible, strategy runs normally."""
    date = "2099-01-03"
    briefs_dir = _write_brief(tmp_path, date, {})  # no event_gate at all
    strategy = _make_strategy(briefs_dir)
    sig = strategy.generate_signal(_bar(date), regime="UNKNOWN")
    assert sig.reason_code != rc.EVENT_GATE

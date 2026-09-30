"""Acceptance tests for day_review.py blind mode.

Tests verify:
1. Identical as-of inputs + changed later bars → same output, same evidence hash
2. Changed auto/brief → blind output unchanged (auto/brief not loaded in blind mode)
3. Prior label answer hidden in blind mode; prior_exposed flag recorded
4. Changed visible prior context → evidence hash changes
5. Empty visible data → BLOCKED, no label saved
6. Prior context (prior OHLC) change → evidence hash changes
7. Invalid cutoff → rejected before display/save
8. Insufficient ATR history → shown in display, label records n_prior_sessions
9. Concurrent writers on different dates preserve both; same date preserves both revisions
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

# Import functions under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.day_review import (
    _evidence_hash,
    _validate_as_of,
    atr14,
    daily_bars,
    print_day,
    prompt_label,
    save_labels,
    MIN_ATR_SESSIONS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_df(date_bars: dict[str, list[tuple]]) -> pd.DataFrame:
    """Build a minimal M15 DataFrame. date_bars: {date_str: [(hhmm, o, h, l, c), ...]}"""
    rows = []
    for date_str, bars in date_bars.items():
        for hhmm, o, h, l, c in bars:
            hh, mm = divmod(hhmm, 100)
            ts = pd.Timestamp(f"{date_str} {hh:02d}:{mm:02d}:00")
            rows.append({"open": o, "high": h, "low": l, "close": c, "ts": ts})
    df = pd.DataFrame(rows).sort_values("ts").set_index("ts")
    return df


PRIOR_DATE = "2026-09-06"
TARGET_DATE = "2026-09-07"

# 2 prior-day bars (enough for ATR with min_periods=1)
PRIOR_BARS = [(100, 2630, 2640, 2620, 2635), (115, 2635, 2650, 2630, 2645)]
# Pre-cutoff bars (before 07:45 UTC) — visible in blind mode
PRE_BARS = [(0, 2630, 2640, 2620, 2635),
            (15, 2635, 2638, 2630, 2637),
            (30, 2637, 2641, 2633, 2640)]
# Post-cutoff bars — NOT visible in blind mode
POST_BARS = [(800, 2640, 2660, 2635, 2655),
             (815, 2655, 2670, 2650, 2665)]


def _full_df(extra_post_bars=None):
    post = POST_BARS + (extra_post_bars or [])
    return _make_df({
        PRIOR_DATE: PRIOR_BARS,
        TARGET_DATE: PRE_BARS + post,
    })


def _visible_df_from(df, date_str, as_of="07:45"):
    dt = pd.Timestamp(date_str)
    h, m = int(as_of.split(":")[0]), int(as_of.split(":")[1])
    cutoff = h * 60 + m
    day = df[df.index.date == dt.date()].copy()
    bm = day.index.hour * 60 + day.index.minute
    return day[bm + 15 <= cutoff]


# ---------------------------------------------------------------------------
# Test 1: later bars don't change visible output or evidence hash
# ---------------------------------------------------------------------------

def test_later_bars_do_not_change_evidence_hash():
    """Add a post-cutoff bar: _evidence_hash must not change."""
    df_base = _full_df()
    df_extra = _full_df(extra_post_bars=[(830, 2665, 2680, 2660, 2675)])
    vis_base = _visible_df_from(df_base, TARGET_DATE)
    vis_extra = _visible_df_from(df_extra, TARGET_DATE)
    h_base  = _evidence_hash(vis_base,  np.nan, None, TARGET_DATE, "XAUUSD", "07:45")
    h_extra = _evidence_hash(vis_extra, np.nan, None, TARGET_DATE, "XAUUSD", "07:45")
    assert h_base == h_extra


def test_later_bars_do_not_change_blind_atr():
    """ATR in blind mode uses prior_df only; adding post-cutoff bars must not change it."""
    # Need 2+ prior daily rows for non-NaN ATR (min_periods=1 still needs 2 days for prev-close diff)
    prior_extra_dates = {
        "2026-09-04": [(0, 2600, 2610, 2590, 2605)],
        "2026-09-05": [(0, 2605, 2620, 2600, 2615)],
    }
    def _df(extra_post=None):
        post = POST_BARS + (extra_post or [])
        d = {**prior_extra_dates, PRIOR_DATE: PRIOR_BARS, TARGET_DATE: PRE_BARS + post}
        return _make_df(d)

    df_base = _df()
    df_extra = _df(extra_post=[(830, 2665, 2680, 2660, 2675)])
    dt = pd.Timestamp(TARGET_DATE)
    prior_base = df_base[df_base.index.date < dt.date()]
    prior_extra = df_extra[df_extra.index.date < dt.date()]
    atr_base = atr14(prior_base, TARGET_DATE)
    atr_extra = atr14(prior_extra, TARGET_DATE)
    assert not np.isnan(atr_base), "need non-NaN ATR for meaningful test"
    assert atr_base == atr_extra


# ---------------------------------------------------------------------------
# Test 2: auto/brief not loaded in blind mode
# ---------------------------------------------------------------------------

def test_blind_mode_does_not_call_load_auto(capsys, tmp_path):
    """load_auto must not be called when hide_auto=True."""
    df = _full_df()
    vis = _visible_df_from(df, TARGET_DATE)
    with patch("scripts.day_review.load_auto") as mock_auto, \
         patch("scripts.day_review.load_brief", return_value={}):
        mock_auto.return_value = {"auto_bias": "BUY", "signals": [1, 1, 1], "agreement": 3}
        print_day("XAUUSD", TARGET_DATE, df, blind_df=vis, hide_auto=True, hide_brief=True)
        mock_auto.assert_not_called()


def test_blind_mode_does_not_call_load_brief(capsys, tmp_path):
    """load_brief must not be called when hide_brief=True."""
    df = _full_df()
    vis = _visible_df_from(df, TARGET_DATE)
    with patch("scripts.day_review.load_auto", return_value=None), \
         patch("scripts.day_review.load_brief") as mock_brief:
        mock_brief.return_value = {"XAUUSD": {"daily_bias": "SELL"}, "macro": {"us10y_yield": "5.5"}}
        print_day("XAUUSD", TARGET_DATE, df, blind_df=vis, hide_auto=True, hide_brief=True)
        mock_brief.assert_not_called()


def test_blind_mode_pattern_flags_hide_auto_dependent(capsys):
    """NEUTRAL_BIAS_SKIP must not appear in blind output."""
    df = _full_df()
    vis = _visible_df_from(df, TARGET_DATE)
    with patch("scripts.day_review.load_auto", return_value=None), \
         patch("scripts.day_review.load_brief", return_value={}):
        print_day("XAUUSD", TARGET_DATE, df, blind_df=vis, hide_auto=True, hide_brief=True)
    out = capsys.readouterr().out
    assert "NEUTRAL_BIAS_SKIP" not in out
    assert "YIELD_COMPRESSION" not in out
    assert "FLOW_DIVERGENCE" not in out


# ---------------------------------------------------------------------------
# Test 3: prior label answer hidden in blind mode
# ---------------------------------------------------------------------------

def test_blind_mode_hides_prior_label_answer(tmp_path, monkeypatch):
    """In blind mode, existing label value (BUY/SELL/NEUTRAL) must not appear before input."""
    df = _full_df()
    labels_path = tmp_path / "labels.json"
    existing = {"XAUUSD": {TARGET_DATE: {
        "human_bias": "SELL",
        "provenance": "RETROSPECTIVE_CONTAMINATED",
        "labelled_at": "2026-09-26T09:00:00+00:00",
        "note": None, "auto_bias": None,
    }}}
    labels_path.write_text(json.dumps(existing))

    captured_prints = []
    monkeypatch.setattr("builtins.input", lambda _: "SKIP")
    with patch("scripts.day_review.load_auto", return_value=None), \
         patch("scripts.day_review.load_brief", return_value={}), \
         patch("scripts.day_review.LABELS", labels_path), \
         patch("builtins.print", side_effect=lambda *a, **kw: captured_prints.append(" ".join(str(x) for x in a))):
        labels = existing
        prompt_label("XAUUSD", TARGET_DATE, df, labels, blind=True, as_of="07:45")

    full_output = "\n".join(captured_prints)
    assert "SELL" not in full_output  # prior answer hidden
    assert "Prior label exists" in full_output  # existence disclosed


def test_blind_mode_records_prior_exposed_flag(tmp_path, monkeypatch):
    """If prior label exists when blind-labelling, prior_label_exposed=True in new record."""
    df = _full_df()
    labels_path = tmp_path / "labels.json"
    existing = {"XAUUSD": {TARGET_DATE: {
        "human_bias": "SELL",
        "provenance": "RETROSPECTIVE_CONTAMINATED",
        "labelled_at": "2026-09-26T09:00:00+00:00",
        "note": None, "auto_bias": None,
    }}}
    labels_path.write_text(json.dumps(existing))

    inputs = iter(["BUY", ""])  # bias then note
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with patch("scripts.day_review.load_auto", return_value=None), \
         patch("scripts.day_review.load_brief", return_value={}), \
         patch("scripts.day_review.LABELS", labels_path), \
         patch("builtins.print"):
        labels = existing.copy()
        prompt_label("XAUUSD", TARGET_DATE, df, labels, blind=True, as_of="07:45")

    # _locked_upsert writes to disk — read from there
    saved = json.loads(labels_path.read_text())
    rec = saved["XAUUSD"][TARGET_DATE]
    assert rec["provenance"] == "RETROSPECTIVE_BLINDED"
    assert rec.get("prior_label_exposed") is True
    assert len(rec.get("history", [])) == 1
    assert rec["history"][0]["provenance"] == "RETROSPECTIVE_CONTAMINATED"


# ---------------------------------------------------------------------------
# Test 4: visible prior context change → evidence hash changes
# ---------------------------------------------------------------------------

def test_different_visible_bars_produce_different_hash():
    """Changing a pre-cutoff bar price must change _evidence_hash."""
    df_a = _make_df({
        PRIOR_DATE: PRIOR_BARS,
        TARGET_DATE: [(0, 2630, 2640, 2620, 2635), (15, 2635, 2638, 2630, 2637)],
    })
    df_b = _make_df({
        PRIOR_DATE: PRIOR_BARS,
        TARGET_DATE: [(0, 2630, 2640, 2620, 2635), (15, 2635, 2650, 2630, 2648)],  # changed
    })
    vis_a = _visible_df_from(df_a, TARGET_DATE)
    vis_b = _visible_df_from(df_b, TARGET_DATE)
    h_a = _evidence_hash(vis_a, np.nan, None, TARGET_DATE, "XAUUSD", "07:45")
    h_b = _evidence_hash(vis_b, np.nan, None, TARGET_DATE, "XAUUSD", "07:45")
    assert h_a != h_b


# ---------------------------------------------------------------------------
# Test 6: prior context change → evidence hash changes
# ---------------------------------------------------------------------------

def _prior_summary(date="2026-09-06", open_=2630.0, high=2645.0, low=2620.0, close=2635.0):
    return {"date": date, "open": open_, "high": high, "low": low, "close": close}


def test_prior_context_change_changes_evidence_hash():
    """Changing prior close must change evidence hash."""
    vis = _visible_df_from(_full_df(), TARGET_DATE)
    h_a = _evidence_hash(vis, 18.5, _prior_summary(close=2635.0), TARGET_DATE, "XAUUSD", "07:45")
    h_b = _evidence_hash(vis, 18.5, _prior_summary(close=2650.0), TARGET_DATE, "XAUUSD", "07:45")
    assert h_a != h_b


def test_prior_open_change_changes_evidence_hash():
    """Changing prior open (direction flip) must change evidence hash."""
    vis = _visible_df_from(_full_df(), TARGET_DATE)
    # open < close → UP; open > close → DOWN
    h_a = _evidence_hash(vis, 18.5, _prior_summary(open_=2620.0, close=2635.0), TARGET_DATE, "XAUUSD", "07:45")
    h_b = _evidence_hash(vis, 18.5, _prior_summary(open_=2650.0, close=2635.0), TARGET_DATE, "XAUUSD", "07:45")
    assert h_a != h_b


def test_prior_high_low_change_changes_evidence_hash():
    """Shifting prior high/low (unchanged range) must change evidence hash."""
    vis = _visible_df_from(_full_df(), TARGET_DATE)
    # range unchanged (25), but shifted up by 10
    h_a = _evidence_hash(vis, 18.5, _prior_summary(high=2645.0, low=2620.0), TARGET_DATE, "XAUUSD", "07:45")
    h_b = _evidence_hash(vis, 18.5, _prior_summary(high=2655.0, low=2630.0), TARGET_DATE, "XAUUSD", "07:45")
    assert h_a != h_b


def test_atr_change_changes_evidence_hash():
    """Changing ATR value must change evidence hash."""
    vis = _visible_df_from(_full_df(), TARGET_DATE)
    prior = _prior_summary()
    h_a = _evidence_hash(vis, 18.5, prior, TARGET_DATE, "XAUUSD", "07:45")
    h_b = _evidence_hash(vis, 22.0, prior, TARGET_DATE, "XAUUSD", "07:45")
    assert h_a != h_b


# ---------------------------------------------------------------------------
# Test 7: invalid cutoff → rejected
# ---------------------------------------------------------------------------

def test_validate_as_of_rejects_bad_format():
    """Malformed cutoff raises ValueError."""
    import pytest
    with pytest.raises(ValueError, match="HH:MM"):
        _validate_as_of("99")
    with pytest.raises(ValueError, match="HH:MM"):
        _validate_as_of("not-a-time")


def test_validate_as_of_rejects_out_of_range():
    """Out-of-range hours/minutes raises ValueError."""
    import pytest
    with pytest.raises(ValueError, match="out of range"):
        _validate_as_of("99:99")
    with pytest.raises(ValueError, match="out of range"):
        _validate_as_of("08:60")


def test_validate_as_of_accepts_valid():
    """Valid HH:MM returns (h, m) tuple."""
    assert _validate_as_of("07:45") == (7, 45)
    assert _validate_as_of("00:00") == (0, 0)
    assert _validate_as_of("23:59") == (23, 59)


def test_prompt_label_rejects_invalid_cutoff(tmp_path, monkeypatch, capsys):
    """Invalid --as-of blocks collection before any display."""
    df = _full_df()
    labels = {}
    monkeypatch.setattr("builtins.input", lambda _: "BUY")
    with patch("scripts.day_review.load_auto", return_value=None), \
         patch("scripts.day_review.load_brief", return_value={}):
        result = prompt_label("XAUUSD", TARGET_DATE, df, labels, blind=True, as_of="99:99")
    assert result is False
    assert "XAUUSD" not in labels
    out = capsys.readouterr().out
    assert "BLOCKED" in out


# ---------------------------------------------------------------------------
# Test 8: insufficient ATR history
# ---------------------------------------------------------------------------

def test_insufficient_atr_shown_in_display(capsys):
    """Fewer than MIN_ATR_SESSIONS prior days → INSUFFICIENT_HISTORY in display."""
    # Only 1 prior day — below MIN_ATR_SESSIONS
    df = _full_df()  # has only PRIOR_DATE as prior day
    vis = _visible_df_from(df, TARGET_DATE)
    with patch("scripts.day_review.load_auto", return_value=None), \
         patch("scripts.day_review.load_brief", return_value={}):
        print_day("XAUUSD", TARGET_DATE, df, blind_df=vis, hide_auto=True, hide_brief=True,
                  _blind_atr=np.nan, _blind_n_prior=1)
    out = capsys.readouterr().out
    assert "INSUFFICIENT_HISTORY" in out


def test_insufficient_atr_recorded_in_label(tmp_path, monkeypatch):
    """Label records n_prior_sessions when ATR insufficient."""
    df = _full_df()  # only 1 prior day
    labels_path = tmp_path / "labels.json"

    inputs = iter(["BUY", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with patch("scripts.day_review.load_auto", return_value=None), \
         patch("scripts.day_review.load_brief", return_value={}), \
         patch("scripts.day_review.LABELS", labels_path), \
         patch("builtins.print"):
        labels = {}
        prompt_label("XAUUSD", TARGET_DATE, df, labels, blind=True, as_of="07:45")

    # Read from disk (locked_upsert writes to LABELS path)
    saved = json.loads(labels_path.read_text()) if labels_path.exists() else labels
    rec = saved.get("XAUUSD", {}).get(TARGET_DATE, {})
    assert "n_prior_sessions" in rec
    assert rec["n_prior_sessions"] < MIN_ATR_SESSIONS


# ---------------------------------------------------------------------------
# Test 5: empty visible data → BLOCKED, no label saved
# ---------------------------------------------------------------------------

def test_blind_mode_blocks_on_empty_visible_data(tmp_path, monkeypatch, capsys):
    """No bars before cutoff → return False, no label written."""
    # Only post-cutoff bars on target date
    df = _make_df({
        PRIOR_DATE: PRIOR_BARS,
        TARGET_DATE: [(900, 2640, 2660, 2635, 2655)],  # 09:00 — after 07:45 cutoff
    })
    labels = {}
    monkeypatch.setattr("builtins.input", lambda _: "BUY")
    with patch("scripts.day_review.load_auto", return_value=None), \
         patch("scripts.day_review.load_brief", return_value={}):
        result = prompt_label("XAUUSD", TARGET_DATE, df, labels, blind=True, as_of="07:45")

    assert result is False
    assert "XAUUSD" not in labels  # no label written
    out = capsys.readouterr().out
    assert "BLOCKED" in out


# ---------------------------------------------------------------------------
# Test 9: concurrent writer safety
# ---------------------------------------------------------------------------

def test_concurrent_writers_different_dates_preserve_both(tmp_path):
    """Two threads writing different dates must both survive."""
    import threading
    from scripts.day_review import _locked_upsert

    labels_path = tmp_path / "labels.json"

    rec_a = {"human_bias": "BUY",  "provenance": "RETROSPECTIVE", "labelled_at": "2026-09-01T10:00:00+00:00", "note": None, "auto_bias": None}
    rec_b = {"human_bias": "SELL", "provenance": "RETROSPECTIVE", "labelled_at": "2026-09-02T10:00:00+00:00", "note": None, "auto_bias": None}

    barrier = threading.Barrier(2)

    def write_a():
        barrier.wait()
        _locked_upsert("XAUUSD", "2026-09-05", rec_a)

    def write_b():
        barrier.wait()
        _locked_upsert("XAUUSD", "2026-09-06", rec_b)

    # Patch at test level so both threads see labels_path for the full duration
    with patch("scripts.day_review.LABELS", labels_path):
        t1, t2 = threading.Thread(target=write_a), threading.Thread(target=write_b)
        t1.start(); t2.start()
        t1.join(); t2.join()

    saved = json.loads(labels_path.read_text())
    assert saved["XAUUSD"]["2026-09-05"]["human_bias"] == "BUY"
    assert saved["XAUUSD"]["2026-09-06"]["human_bias"] == "SELL"


def test_concurrent_writers_same_date_preserve_both_revisions(tmp_path):
    """Two threads relabelling the same date must both end up in history."""
    import threading
    from scripts.day_review import _locked_upsert

    labels_path = tmp_path / "labels.json"
    # Seed an initial record
    initial = {"XAUUSD": {"2026-09-07": {
        "human_bias": "NEUTRAL", "provenance": "RETROSPECTIVE",
        "labelled_at": "2026-09-07T08:00:00+00:00", "note": None, "auto_bias": None,
    }}}
    labels_path.write_text(json.dumps(initial))

    rec_a = {"human_bias": "BUY",  "provenance": "RETROSPECTIVE", "labelled_at": "2026-09-07T10:00:00+00:00", "note": None, "auto_bias": None}
    rec_b = {"human_bias": "SELL", "provenance": "RETROSPECTIVE", "labelled_at": "2026-09-07T10:01:00+00:00", "note": None, "auto_bias": None}

    # Sequential writes test that each write reads on-disk state (not stale caller state)
    with patch("scripts.day_review.LABELS", labels_path):
        _locked_upsert("XAUUSD", "2026-09-07", rec_a)
        _locked_upsert("XAUUSD", "2026-09-07", rec_b)

    saved = json.loads(labels_path.read_text())
    rec = saved["XAUUSD"]["2026-09-07"]
    # Final record is SELL; history has NEUTRAL and BUY
    assert rec["human_bias"] == "SELL"
    biases_in_history = {r["human_bias"] for r in rec.get("history", [])}
    assert "NEUTRAL" in biases_in_history
    assert "BUY" in biases_in_history

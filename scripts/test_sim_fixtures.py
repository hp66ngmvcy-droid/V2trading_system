#!/usr/bin/env python3
"""Archived fixtures for paper_game_sim.simulate_setup_legacy.

Run: venv/bin/python scripts/test_sim_fixtures.py
These preserve the old contract, not acceptance for boundary_touch_v2.
Current replay tests live in tests/test_zone_touch_v2.py.
All bars use valid OHLC: open and close within [low, high].
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.paper_game_sim import simulate_setup_legacy as simulate_setup


def bars(*rows):
    """Build a minimal M15 DataFrame from (open, high, low, close) tuples."""
    records = [
        {"timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(minutes=15 * i),
         "open": r[0], "high": r[1], "low": r[2], "close": r[3]}
        for i, r in enumerate(rows)
    ]
    df = pd.DataFrame(records)
    df.index = range(len(df))
    return df


BASE_BUY = {
    "symbol": "BTCUSD", "date": "2026-01-01", "side": "BUY",
    "entry_zone_low": 100.0, "entry_zone_high": 102.0,
    "stop": 98.0, "t1": 106.0, "t2": 108.0,
    "rr_t1": 1.0, "confidence": 0.8, "issued_at": "08:00",
}

BASE_SELL = {
    "symbol": "BTCUSD", "date": "2026-01-01", "side": "SELL",
    "entry_zone_low": 100.0, "entry_zone_high": 102.0,
    "stop": 104.0, "t1": 96.0, "t2": 94.0,
    "rr_t1": 1.0, "confidence": 0.8, "issued_at": "08:00",
}


def check(label, result, expect_outcome, expect_zone_hit, expect_r=None):
    ok = True
    if result["outcome"] != expect_outcome:
        print(f"  FAIL outcome: got {result['outcome']!r}, want {expect_outcome!r}")
        ok = False
    if result["zone_hit"] != expect_zone_hit:
        print(f"  FAIL zone_hit: got {result['zone_hit']}, want {expect_zone_hit}")
        ok = False
    if expect_r is not None and abs(result["r_multiple"] - expect_r) > 0.01:
        print(f"  FAIL r_multiple: got {result['r_multiple']}, want {expect_r}")
        ok = False
    print(f"{'PASS' if ok else 'FAIL'} {label}")
    return ok


def main():
    passed = 0
    total = 0

    # -----------------------------------------------------------------------
    # BUY fixtures
    # -----------------------------------------------------------------------

    # F1: BUY fill-outside-range — bar touches zone (lo=100 <= ezh=102) but hi=101 < ezh=102
    # Valid OHLC: open=100, hi=101, lo=100, close=101
    r = simulate_setup(BASE_BUY, bars((100, 101, 100, 101)))
    total += 1
    if check("F1 BUY fill-outside-range → INVALID_FILL", r, "INVALID_FILL", True):
        passed += 1

    # F2: BUY simultaneous stop+T1 → SL wins, r=-1.0
    # Entry bar: lo=100 <= ezh=102, hi=103 >= ezh=102 → valid fill at 102
    # Next bar: hi=107 >= t1=106 AND lo=95 <= stop=98 → SL
    r = simulate_setup(BASE_BUY, bars((101, 103, 100, 103), (100, 107, 95, 101)))
    total += 1
    if check("F2 BUY simultaneous stop+T1 → SL wins", r, "SL", True, -1.0):
        passed += 1

    # F3: BUY clean TP_T1, T2 not reached
    # Entry bar: lo=101 <= ezh=102, hi=103 >= ezh=102 → valid fill at 102
    # entry=102, stop=98, t1=106 → risk=4, reward=4 → 1.0R
    r = simulate_setup(BASE_BUY, bars((101, 103, 101, 103), (103, 107, 103, 106)))
    total += 1
    ok = True
    if r["outcome"] != "TP_T1":
        print(f"  FAIL outcome: {r['outcome']!r}")
        ok = False
    if r.get("t2_reached") is not False:
        print(f"  FAIL t2_reached: {r.get('t2_reached')!r}")
        ok = False
    if abs(r["r_multiple"] - 1.0) > 0.01:
        print(f"  FAIL r_multiple: {r['r_multiple']}")
        ok = False
    print(f"{'PASS' if ok else 'FAIL'} F3 BUY TP_T1, T2 not reached")
    if ok:
        passed += 1

    # F4: BUY TP_T1 then T2 reached (no intervening stop)
    # Entry bar valid; T1 bar; T2 bar: open=105 so open >= lo (valid OHLC)
    r = simulate_setup(BASE_BUY, bars(
        (101, 103, 101, 103),   # entry
        (103, 107, 103, 106),   # T1 hit
        (105, 109, 105, 108),   # T2 hit — valid OHLC: open=105=lo
    ))
    total += 1
    ok = True
    if r["outcome"] != "TP_T1":
        print(f"  FAIL outcome: {r['outcome']!r}")
        ok = False
    if r.get("t2_reached") is not True:
        print(f"  FAIL t2_reached: {r.get('t2_reached')!r}")
        ok = False
    print(f"{'PASS' if ok else 'FAIL'} F4 BUY TP_T1 then T2 reached")
    if ok:
        passed += 1

    # F5: BUY T2 NOT reached when stop hit after T1
    r = simulate_setup(BASE_BUY, bars(
        (101, 103, 101, 103),
        (103, 107, 103, 106),   # T1 hit
        (100, 103, 95, 100),    # stop hit (lo=95 <= 98) — valid OHLC
    ))
    total += 1
    ok = True
    if r["outcome"] != "TP_T1":
        print(f"  FAIL outcome: {r['outcome']!r}")
        ok = False
    if r.get("t2_reached") is not False:
        print(f"  FAIL t2_reached: {r.get('t2_reached')!r}")
        ok = False
    print(f"{'PASS' if ok else 'FAIL'} F5 BUY T2 blocked by intervening stop")
    if ok:
        passed += 1

    # F6: BUY OPEN_EOD
    r = simulate_setup(BASE_BUY, bars(
        (101, 103, 101, 103),   # valid entry at 102
        (102, 104, 101, 103),   # neither stop(98) nor T1(106)
        (102, 104, 101, 103),
    ))
    total += 1
    if check("F6 BUY OPEN_EOD", r, "OPEN_EOD", True):
        passed += 1

    # -----------------------------------------------------------------------
    # SELL fixtures
    # -----------------------------------------------------------------------

    # FS1: SELL fill-outside-range — bar hi >= ezl=100 but lo=105 > ezl=100
    # Bar entirely above ezl → never traded at fill price → INVALID_FILL
    # Valid OHLC: open=106, hi=107, lo=105, close=106
    r = simulate_setup(BASE_SELL, bars((106, 107, 105, 106)))
    total += 1
    if check("FS1 SELL fill-outside-range → INVALID_FILL", r, "INVALID_FILL", True):
        passed += 1

    # FS2: SELL valid entry → TP_T1
    # Bar: lo=99 <= ezl=100 (fill valid), hi=103 >= ezl=100 (zone_entered)
    # Fill at ezl=100. stop=104, t1=96. risk=4, reward=4 → 1.0R
    # Next bar: lo=94 <= t1=96, hi=101 < stop=104 → TP_T1
    r = simulate_setup(BASE_SELL, bars(
        (101, 103, 99, 101),    # entry — lo=99 <= ezl=100
        (99,  101, 94, 97),     # T1 hit — lo=94 <= t1=96, hi=101 < stop=104
    ))
    total += 1
    if check("FS2 SELL valid entry → TP_T1", r, "TP_T1", True, 1.0):
        passed += 1

    # FS3: SELL simultaneous stop+T1 → SL wins, r=-1.0
    # Entry bar: valid fill (lo=99 <= ezl=100)
    # Next bar: hi=105 >= stop=104 AND lo=94 <= t1=96 → simultaneous → SL
    r = simulate_setup(BASE_SELL, bars(
        (101, 103, 99, 101),    # entry
        (100, 105, 94, 100),    # hi >= stop AND lo <= t1 → SL
    ))
    total += 1
    if check("FS3 SELL simultaneous stop+T1 → SL wins", r, "SL", True, -1.0):
        passed += 1

    print(f"\n{passed}/{total} fixtures passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

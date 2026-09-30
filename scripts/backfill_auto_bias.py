"""
backfill_auto_bias.py — Causal session-cutoff bias classifier for BTC + XAU M15.

Emits auto_bias per (date, cutoff) using only M15 bars closed before the
specified UTC cutoff time. Lookahead-free by construction.

Voting rule: BUY  when n_agree_buy  >= 2 AND n_oppose_sell == 0.
             SELL when n_agree_sell >= 2 AND n_oppose_buy  == 0.
             [1,1,-1] or [-1,-1,1] → NEUTRAL (opposing vote blocks consensus).
             INVALID_DATA when < 6 M15 bars visible before cutoff on target date.
             WARM_UP_INCOMPLETE when < 14 prior complete days for ATR.
             A complete day requires >= 88 M15 bars.

Signals:
  S1 — range position: close of last visible bar vs prior complete day range.
       >= 0.70 → +1 (BUY), <= 0.30 → -1 (SELL).
  S2 — session direction: Asia open (00:00 UTC) vs London close (08:00–cutoff).
       Only emits when cutoff >= 12:45 (London bars available); else 0.
       Threshold: abs(move) > 0.3 × prior ATR.
  S3 — prior close-to-close: close[t-1] vs close[t-2] (complete days).
       Threshold: > +0.3% → +1; < -0.3% → -1.

Usage:
    venv/bin/python scripts/backfill_auto_bias.py                  # Asia 07:45
    venv/bin/python scripts/backfill_auto_bias.py --cutoff 12:45   # pre-US
    venv/bin/python scripts/backfill_auto_bias.py --test           # invariance test
    venv/bin/python scripts/backfill_auto_bias.py --compare        # vs human briefs
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE   = Path(__file__).parent.parent
DATA_V = BASE / "data/validated"
BRIEFS = BASE / "data/daily_briefs"
OUT    = BASE / "data/research/auto_bias_results.json"

SYMBOLS = {
    "BTCUSD": DATA_V / "BTCUSD_M15.parquet",
    "XAUUSD": DATA_V / "XAUUSD_M15.parquet",
}

MIN_BARS_COMPLETE = 88   # minimum M15 bars for a day to count as complete
MIN_BARS_SESSION  = 6    # minimum M15 bars before cutoff to compute signals
ATR_PERIOD        = 14   # prior complete days for ATR warm-up


def load_m15(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df = df[["timestamp", "open", "high", "low", "close"]].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["date_str"] = df["timestamp"].dt.date.astype(str)
    df["bar_mins"] = df["timestamp"].dt.hour * 60 + df["timestamp"].dt.minute
    return df


def _complete_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Build daily OHLC from complete days only (>= MIN_BARS_COMPLETE bars)."""
    agg = df.groupby("date_str").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        bar_count=("open", "count"),
    )
    complete = agg[agg["bar_count"] >= MIN_BARS_COMPLETE].copy()
    return complete.sort_index()


def _atr_series(complete: pd.DataFrame) -> pd.Series:
    """ATR(14) computed from complete days. Index = date_str, value = ATR as-of that day.
    No shift; caller must look up atr_s[prev_str] to get ATR known before today."""
    prev_close = complete["close"].shift(1)
    tr = pd.concat([
        complete["high"] - complete["low"],
        (complete["high"] - prev_close).abs(),
        (complete["low"]  - prev_close).abs(),
    ], axis=1).max(axis=1)
    # rolling(14) on complete days, min_periods=14 enforces warm-up
    return tr.rolling(ATR_PERIOD, min_periods=ATR_PERIOD).mean()


def _vote(signals: list) -> str:
    """2-agree-0-oppose voting over {-1, 0, +1} signals."""
    n_buy  = sum(s == 1  for s in signals)
    n_sell = sum(s == -1 for s in signals)
    if n_buy >= 2 and n_sell == 0:
        return "BUY"
    if n_sell >= 2 and n_buy == 0:
        return "SELL"
    return "NEUTRAL"


def classify_day(df: pd.DataFrame, cutoff_hhmm: str = "07:45") -> list:
    """
    Classify each date in df with causal cutoff.

    target_dates: dates with >= MIN_BARS_SESSION closed bars before cutoff.
    complete.index: dates with >= MIN_BARS_COMPLETE bars (used for prior-day lookups only).
    """
    cutoff_h, cutoff_m = int(cutoff_hhmm.split(":")[0]), int(cutoff_hhmm.split(":")[1])
    cutoff_mins = cutoff_h * 60 + cutoff_m

    complete = _complete_daily(df)
    atr_s = _atr_series(complete)
    complete_dates = list(complete.index)  # for prior-day lookups

    # Build target_dates: any date with >= MIN_BARS_SESSION bars closed by cutoff.
    # Bar at bar_mins closes at bar_mins + 15; closed iff bar_mins + 15 <= cutoff_mins.
    bars_before_cutoff = df[df["bar_mins"] + 15 <= cutoff_mins]
    per_day_counts = bars_before_cutoff.groupby("date_str").size()
    target_dates = sorted(per_day_counts[per_day_counts >= MIN_BARS_SESSION].index.tolist())

    rows = []

    for today_str in target_dates:
        # prev_str and prev2_str must both be complete days (not just session days)
        prev_complete = [d for d in complete_dates if d < today_str]
        if len(prev_complete) < 2:
            # need at least t-1 and t-2 for signal 3
            continue

        prev_str  = prev_complete[-1]
        prev2_str = prev_complete[-2]

        # visible bars: today's M15 bars whose bar close is at or before cutoff
        # A bar opening at T closes at T+15; include it iff T+15 <= cutoff_mins.
        today_bars = df[(df["date_str"] == today_str) & (df["bar_mins"] + 15 <= cutoff_mins)]

        # ATR from prior complete days only — look up prev_str (no shift needed)
        if prev_str not in atr_s.index or pd.isna(atr_s[prev_str]):
            rows.append({
                "date": today_str, "auto_bias": "WARM_UP_INCOMPLETE",
                "signals": [0, 0, 0], "cutoff": cutoff_hhmm,
                "reason": f"ATR warm-up requires {ATR_PERIOD} complete days",
            })
            continue

        today_atr = float(atr_s[prev_str])

        # --- Signal 1: range position of last visible bar vs prior day range ---
        p_high  = float(complete.loc[prev_str, "high"])
        p_low   = float(complete.loc[prev_str, "low"])
        p_range = p_high - p_low
        s1 = 0
        if p_range > 0:
            last_close = float(today_bars.iloc[-1]["close"])
            pos = (last_close - p_low) / p_range
            if pos >= 0.70:
                s1 = 1
            elif pos <= 0.30:
                s1 = -1

        # --- Signal 2: Asia open vs London close (only when cutoff >= 12:45) ---
        s2 = 0
        if cutoff_mins >= 12 * 60 + 45:
            asia_bars   = today_bars[today_bars["bar_mins"] < 7 * 60 + 45]
            london_bars = today_bars[
                (today_bars["bar_mins"] >= 8 * 60) & (today_bars["bar_mins"] + 15 <= cutoff_mins)
            ]
            if len(asia_bars) >= 4 and len(london_bars) >= 4 and today_atr > 0:
                a_open  = float(asia_bars.iloc[0]["open"])
                l_close = float(london_bars.iloc[-1]["close"])
                diff    = l_close - a_open
                thresh  = 0.3 * today_atr
                if diff > thresh:
                    s2 = 1
                elif diff < -thresh:
                    s2 = -1

        # --- Signal 3: close[t-1] vs close[t-2] ---
        s3 = 0
        close_t1 = float(complete.loc[prev_str,  "close"])
        close_t2 = float(complete.loc[prev2_str, "close"])
        if close_t2 > 0:
            pct = (close_t1 - close_t2) / close_t2
            if pct > 0.003:
                s3 = 1
            elif pct < -0.003:
                s3 = -1

        bias = _vote([s1, s2, s3])
        rows.append({
            "date": today_str, "auto_bias": bias,
            "signals": [s1, s2, s3], "cutoff": cutoff_hhmm,
            "n_buy":  sum(s == 1  for s in [s1, s2, s3]),
            "n_sell": sum(s == -1 for s in [s1, s2, s3]),
        })

    return rows


# ---------------------------------------------------------------------------
# Invariance test — post-cutoff bar change must not alter label
# ---------------------------------------------------------------------------

def run_invariance_test() -> bool:
    """
    Build a synthetic M15 dataset. Two checks:
    1. Target date classified when ONLY pre-cutoff bars are present (truncated day).
    2. Label and signals unchanged after adding a post-cutoff bar.
    """
    print("Running invariance test...")

    # 30 complete days of synthetic BTC data (96 bars each, starting 2024-01-01)
    rng = pd.date_range("2024-01-01", periods=30 * 96, freq="15min")
    prices = 50000 + np.cumsum(np.random.default_rng(42).normal(0, 50, len(rng)))
    prices = np.maximum(prices, 1.0)

    def make_df(timestamps, closes):
        opens  = closes * 0.999
        highs  = closes * 1.002
        lows   = closes * 0.998
        df = pd.DataFrame({
            "timestamp": timestamps,
            "open": opens, "high": highs, "low": lows, "close": closes,
        })
        df["date_str"] = df["timestamp"].dt.date.astype(str)
        df["bar_mins"] = df["timestamp"].dt.hour * 60 + df["timestamp"].dt.minute
        return df

    base_df = make_df(rng, prices)

    # target date = day 18 (index 17, 0-based), ensures >= 14 complete prior days
    target_date = base_df["date_str"].unique()[17]

    # --- Check 1: truncated day (only pre-cutoff bars) must appear in results ---
    # Strip the target date down to only bars with bar_mins + 15 <= cutoff (07:45 = 465)
    cutoff_mins = 7 * 60 + 45
    other_days = base_df[base_df["date_str"] != target_date]
    target_pre = base_df[
        (base_df["date_str"] == target_date) & (base_df["bar_mins"] + 15 <= cutoff_mins)
    ]
    truncated_df = pd.concat([other_days, target_pre], ignore_index=True)
    truncated_df = truncated_df.sort_values("timestamp").reset_index(drop=True)

    rows_pre = classify_day(truncated_df, cutoff_hhmm="07:45")
    row_pre = next((r for r in rows_pre if r["date"] == target_date), None)

    if row_pre is None:
        print(f"  FAIL — target date {target_date} not in results when only pre-cutoff bars present")
        return False
    if row_pre["auto_bias"] in ("INVALID_DATA", "WARM_UP_INCOMPLETE"):
        print(f"  FAIL — target date {target_date} classified as {row_pre['auto_bias']} "
              f"(pre-cutoff only); check warm-up or bar count: {row_pre.get('reason','')}")
        return False
    print(f"  CHECK 1 PASS — {target_date} appears with pre-cutoff bars only: {row_pre['auto_bias']}")

    # --- Check 2: adding a post-cutoff bar must not change label or signals ---
    # Use the full base_df (all bars present for other days) plus a wild post-cutoff bar
    post_bar = pd.DataFrame([{
        "timestamp": pd.Timestamp(f"{target_date} 08:00:00"),
        "open": 999999.0, "high": 999999.0, "low": 1.0, "close": 999999.0,
    }])
    post_bar["date_str"] = post_bar["timestamp"].dt.date.astype(str)
    post_bar["bar_mins"] = post_bar["timestamp"].dt.hour * 60 + post_bar["timestamp"].dt.minute

    # Build dataset with full prior days + truncated target + the post-cutoff bar
    modified_df = pd.concat([truncated_df, post_bar], ignore_index=True)
    rows_post = classify_day(modified_df, cutoff_hhmm="07:45")
    row_post = next((r for r in rows_post if r["date"] == target_date), None)

    if row_post is None:
        print(f"  FAIL — target date {target_date} missing after post-cutoff bar added")
        return False

    if row_pre["auto_bias"] != row_post["auto_bias"] or row_pre["signals"] != row_post["signals"]:
        print(f"  FAIL — label changed after post-cutoff bar added")
        print(f"    before: {row_pre['auto_bias']} signals={row_pre['signals']}")
        print(f"    after:  {row_post['auto_bias']} signals={row_post['signals']}")
        return False

    print(f"  CHECK 2 PASS — label stable after post-cutoff bar added ({target_date}: {row_pre['auto_bias']})")
    return True


# ---------------------------------------------------------------------------
# Human brief comparison
# ---------------------------------------------------------------------------

def load_human_biases(symbol: str) -> dict:
    out = {}
    for path in sorted(BRIEFS.glob("*_levels.json")):
        try:
            data = json.loads(path.read_text())
            date = data.get("date")
            sym_data = data.get(symbol, {})
            bias = sym_data.get("daily_bias")
            if date and bias:
                out[date] = bias.upper()
        except Exception:
            pass
    return out


def compare_vs_human(rows: list, symbol: str) -> None:
    human = load_human_biases(symbol)
    rows_map = {r["date"]: r for r in rows}

    agree = disagree = skip = 0
    for date_str, hbias in sorted(human.items()):
        if date_str not in rows_map:
            skip += 1
            continue
        r = rows_map[date_str]
        abias = r["auto_bias"]
        if abias in ("INVALID_DATA", "WARM_UP_INCOMPLETE"):
            skip += 1
            continue
        match = "✓" if hbias == abias else "✗"
        note  = "  ← DISAGREE" if hbias != abias else ""
        print(f"  {date_str}  human={hbias:<8} auto={abias:<8} {match}{note}")
        if hbias == abias:
            agree += 1
        else:
            disagree += 1

    total_cmp = agree + disagree
    if total_cmp:
        print(f"\n  Agreement: {agree}/{total_cmp} = {100*agree/total_cmp:.1f}%  "
              f"(skipped {skip} — no data or incomplete)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff",  default="07:45",
                    help="As-of cutoff HH:MM UTC (default 07:45 = Asia close)")
    ap.add_argument("--test",    action="store_true", help="Run invariance test only")
    ap.add_argument("--compare", action="store_true", help="Compare vs human brief biases")
    args = ap.parse_args()

    if args.test:
        ok = run_invariance_test()
        sys.exit(0 if ok else 1)

    results = {}
    for sym, path in SYMBOLS.items():
        print(f"\nProcessing {sym} (cutoff={args.cutoff})...")
        df = load_m15(path)
        rows = classify_day(df, cutoff_hhmm=args.cutoff)

        counts = {}
        for r in rows:
            counts[r["auto_bias"]] = counts.get(r["auto_bias"], 0) + 1
        total = len(rows)
        buy  = counts.get("BUY",  0)
        sell = counts.get("SELL", 0)
        neut = counts.get("NEUTRAL", 0)
        inv  = counts.get("INVALID_DATA", 0)
        wu   = counts.get("WARM_UP_INCOMPLETE", 0)
        print(f"  {total} days classified  "
              f"BUY={buy} ({100*buy/total:.1f}%)  "
              f"SELL={sell} ({100*sell/total:.1f}%)  "
              f"NEUTRAL={neut} ({100*neut/total:.1f}%)  "
              f"INVALID={inv}  WARM_UP={wu}")

        results[sym] = {r["date"]: {k: v for k, v in r.items() if k != "date"}
                        for r in rows}

        if args.compare:
            print(f"\n  === vs human briefs ({sym}) ===")
            compare_vs_human(rows, sym)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2))
    print(f"\nResults written to {OUT}")


if __name__ == "__main__":
    main()

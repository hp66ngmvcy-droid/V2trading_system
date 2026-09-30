#!/usr/bin/env python3
"""Pattern sweep — brute-force pattern discovery on M15 price data.

Usage:
    venv/bin/python scripts/pattern_sweep.py          # BTC (default)
    venv/bin/python scripts/pattern_sweep.py --btc    # BTC
    venv/bin/python scripts/pattern_sweep.py --xau    # XAU
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PARQUET = {
    "btc": ROOT / "data" / "validated" / "BTCUSD_M15.parquet",
    "xau": ROOT / "data" / "validated" / "XAUUSD_M15.parquet",
}

# ── Zone model constants ──────────────────────────────────────────────────────
ATR_ZONE_SELL_TOP   =  0.3   # zone_top  = anchor_high + 0.3×ATR
ATR_ZONE_SELL_DEPTH =  1.0   # zone_low  = anchor_high - 1.0×ATR
ATR_ZONE_BUY_DEPTH  =  0.3   # zone_low  = anchor_low  - 0.3×ATR
ATR_ZONE_BUY_TOP    =  1.0   # zone_high = anchor_low  + 1.0×ATR
ATR_STOP            =  2.0   # stop  = anchor ± 2.0×ATR
ATR_TARGET          =  3.0   # T1    = anchor ± 3.0×ATR (from anchor)
MIN_N               = 30


# ── Data loading ──────────────────────────────────────────────────────────────

def load_m15(symbol: str) -> pd.DataFrame:
    path = PARQUET[symbol]
    df = pd.read_parquet(path, columns=["timestamp", "open", "high", "low", "close"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["date"] = df["timestamp"].dt.normalize()
    return df


def build_daily(m15: pd.DataFrame) -> pd.DataFrame:
    """Derive daily OHLC from M15 bars."""
    daily = (
        m15.groupby("date")
        .agg(open=("open", "first"), high=("high", "max"),
             low=("low", "min"), close=("close", "last"))
        .reset_index()
    )
    # ATR-14 on daily bars (true range)
    h = daily["high"].values
    l = daily["low"].values
    c = daily["close"].values
    prev_c = np.roll(c, 1)
    prev_c[0] = c[0]
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    atr = pd.Series(tr).rolling(14, min_periods=1).mean().values
    daily["tr"] = tr
    daily["atr14"] = atr
    daily["range"] = h - l
    return daily


# ── Simulation core ───────────────────────────────────────────────────────────

def simulate_day_zones(
    day_bars: pd.DataFrame,
    prior_high: float,
    prior_low: float,
    atr: float,
    side: str,
) -> dict | None:
    """
    Simulate one zone-entry trade for a given day and side.
    Returns dict with zone_hit, outcome, r_multiple — or None if no zone defined.
    """
    if atr <= 0 or len(day_bars) == 0:
        return None

    if side == "SELL":
        zone_top   = prior_high + ATR_ZONE_SELL_TOP   * atr
        zone_low   = prior_high - ATR_ZONE_SELL_DEPTH * atr
        stop       = prior_high + ATR_STOP            * atr
        target     = prior_high - ATR_TARGET          * atr
        # entry at zone_low (lower boundary — price enters from above)
        entry      = zone_low
        risk       = abs(stop - entry)
    else:  # BUY
        zone_low   = prior_low  - ATR_ZONE_BUY_DEPTH  * atr
        zone_high  = prior_low  + ATR_ZONE_BUY_TOP    * atr
        stop       = prior_low  - ATR_STOP            * atr
        target     = prior_low  + ATR_TARGET          * atr
        entry      = zone_high  # upper boundary — price enters from below
        risk       = abs(stop - entry)

    if risk <= 0:
        return None

    zone_hit = False
    outcome  = "OPEN_EOD"
    r_multiple = 0.0

    for _, bar in day_bars.iterrows():
        if not zone_hit:
            # Check if this bar touches the entry zone
            if side == "SELL":
                if bar["high"] >= zone_low and bar["low"] <= zone_top:
                    zone_hit = True
            else:
                if bar["low"] <= zone_high and bar["high"] >= zone_low:
                    zone_hit = True

            if not zone_hit:
                continue

        # Zone is hit — now check TP/SL on this and subsequent bars
        if side == "SELL":
            if bar["low"] <= target:
                outcome = "TP"
                r_multiple = (entry - target) / risk
                break
            if bar["high"] >= stop:
                outcome = "SL"
                r_multiple = -(stop - entry) / risk
                break
        else:
            if bar["high"] >= target:
                outcome = "TP"
                r_multiple = (target - entry) / risk
                break
            if bar["low"] <= stop:
                outcome = "SL"
                r_multiple = -(entry - stop) / risk
                break

    if zone_hit and outcome == "OPEN_EOD":
        # Close at last bar's close
        last_close = day_bars["close"].iloc[-1]
        if side == "SELL":
            r_multiple = (entry - last_close) / risk
        else:
            r_multiple = (last_close - entry) / risk

    return {"zone_hit": zone_hit, "outcome": outcome, "r_multiple": r_multiple}


# ── Group statistics ──────────────────────────────────────────────────────────

def group_stats(records: list[dict]) -> dict:
    hits = [r for r in records if r["zone_hit"]]
    if not hits:
        return {"N": 0, "wr": 0.0, "avg_r": 0.0, "total_r": 0.0}
    n = len(hits)
    wins = [r for r in hits if r["r_multiple"] > 0]
    total_r = sum(r["r_multiple"] for r in hits)
    return {
        "N": n,
        "wr": len(wins) / n * 100,
        "avg_r": total_r / n,
        "total_r": total_r,
    }


def fmt_row(label: str, s: dict) -> str:
    if s["N"] < MIN_N:
        return f"  {label:<40} N={s['N']:>4}  (below min N={MIN_N})"
    sign = "+" if s["avg_r"] >= 0 else ""
    sign2 = "+" if s["total_r"] >= 0 else ""
    return (
        f"  {label:<40} N={s['N']:>4}  WR={s['wr']:>5.1f}%"
        f"  AvgR={sign}{s['avg_r']:>+.2f}R"
        f"  TotalR={sign2}{s['total_r']:>+.1f}R"
    )


# ── Main sweep ────────────────────────────────────────────────────────────────

def run_sweep(symbol: str) -> None:
    print(f"Loading {symbol.upper()} M15 data …", end=" ", flush=True)
    m15   = load_m15(symbol)
    daily = build_daily(m15)
    sym_label = "BTCUSD" if symbol == "btc" else "XAUUSD"
    date_from = m15["date"].min().strftime("%Y-%m")
    date_to   = m15["date"].max().strftime("%Y-%m")
    print(f"{len(m15):,} bars | {len(daily)} days")
    print()
    print(f"=== PATTERN SWEEP — {sym_label} M15 ({date_from} to {date_to}) ===")
    print()

    # Index M15 by date for fast lookup
    m15_by_date = {d: grp for d, grp in m15.groupby("date")}

    # Build per-day trade records with metadata
    records_all: list[dict] = []

    for i in range(1, len(daily)):
        row       = daily.iloc[i]
        prev      = daily.iloc[i - 1]
        trade_date = row["date"]
        atr        = prev["atr14"]
        day_bars   = m15_by_date.get(trade_date, pd.DataFrame())

        if len(day_bars) == 0:
            continue

        dow = trade_date.weekday()  # 0=Mon … 4=Fri

        # Session buckets (UTC hours)
        asia_bars   = day_bars[day_bars["timestamp"].dt.hour.between( 0,  7)]
        london_bars = day_bars[day_bars["timestamp"].dt.hour.between( 8, 15)]
        ny_bars     = day_bars[day_bars["timestamp"].dt.hour.between(13, 20)]

        # Compression flag
        compressed = prev["range"] < 0.8 * atr

        # Prior day direction
        prior_up = prev["close"] > prev["open"]
        pct_move = (prev["close"] - prev["open"]) / prev["open"] * 100

        for side in ("SELL", "BUY"):
            anchor_high = prev["high"]
            anchor_low  = prev["low"]

            # Full day
            res_full = simulate_day_zones(day_bars, anchor_high, anchor_low, atr, side)
            if res_full:
                records_all.append({
                    **res_full, "side": side, "dow": dow,
                    "session": "ALL",
                    "compressed": compressed,
                    "prior_up": prior_up,
                    "big_move": abs(pct_move) > 0.5,
                    "date": trade_date,
                })

            # Session entries
            for sess_label, sess_bars in [("Asia", asia_bars), ("London", london_bars), ("NY", ny_bars)]:
                if len(sess_bars) == 0:
                    continue
                res_sess = simulate_day_zones(sess_bars, anchor_high, anchor_low, atr, side)
                if res_sess:
                    records_all.append({
                        **res_sess, "side": side, "dow": dow,
                        "session": sess_label,
                        "compressed": compressed,
                        "prior_up": prior_up,
                        "big_move": abs(pct_move) > 0.5,
                        "date": trade_date,
                    })

    # ── Day of week ──────────────────────────────────────────────────────────
    dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    all_findings: list[dict] = []

    for side in ("SELL", "BUY"):
        print(f"[DAY OF WEEK — {side} zones]")
        recs_side = [r for r in records_all if r["side"] == side and r["session"] == "ALL"]
        for d, name in enumerate(dow_names):
            s = group_stats([r for r in recs_side if r["dow"] == d])
            print(fmt_row(name, s))
            if s["N"] >= MIN_N:
                all_findings.append({"label": f"DoW {name} {side}", **s})
        print()

    # ── Session entry ────────────────────────────────────────────────────────
    for side in ("SELL", "BUY"):
        print(f"[SESSION ENTRY — {side} zones]")
        for sess in ("Asia", "London", "NY"):
            recs = [r for r in records_all if r["side"] == side and r["session"] == sess]
            s = group_stats(recs)
            print(fmt_row(sess, s))
            if s["N"] >= MIN_N:
                all_findings.append({"label": f"Session {sess} {side}", **s})
        print()

    # ── Compression-expansion ────────────────────────────────────────────────
    print("[COMPRESSION-EXPANSION]")
    for side in ("SELL", "BUY"):
        recs_side = [r for r in records_all if r["side"] == side and r["session"] == "ALL"]
        s_comp   = group_stats([r for r in recs_side if r["compressed"]])
        s_normal = group_stats([r for r in recs_side if not r["compressed"]])
        label_c = f"Compressed prior day (range<0.8×ATR)  {side}"
        label_n = f"Normal prior day                       {side}"
        print(fmt_row(label_c, s_comp))
        print(fmt_row(label_n, s_normal))
        for lbl, s in [(label_c, s_comp), (label_n, s_normal)]:
            if s["N"] >= MIN_N:
                all_findings.append({"label": lbl, **s})
    print()

    # ── Fade vs Follow ───────────────────────────────────────────────────────
    print("[FADE vs FOLLOW — prior day direction (>0.5% move)]")
    recs_big = [r for r in records_all if r["session"] == "ALL" and r["big_move"]]
    fade_sell  = group_stats([r for r in recs_big if r["prior_up"]  and r["side"] == "SELL"])
    follow_buy = group_stats([r for r in recs_big if r["prior_up"]  and r["side"] == "BUY"])
    fade_buy   = group_stats([r for r in recs_big if not r["prior_up"] and r["side"] == "BUY"])
    follow_sell= group_stats([r for r in recs_big if not r["prior_up"] and r["side"] == "SELL"])
    print(fmt_row("Prior day UP   → SELL (fade)",    fade_sell))
    print(fmt_row("Prior day UP   → BUY  (follow)",  follow_buy))
    print(fmt_row("Prior day DOWN → BUY  (fade)",    fade_buy))
    print(fmt_row("Prior day DOWN → SELL (follow)",  follow_sell))
    for lbl, s in [
        ("Fade SELL after UP day", fade_sell),
        ("Follow BUY after UP day", follow_buy),
        ("Fade BUY after DOWN day", fade_buy),
        ("Follow SELL after DOWN day", follow_sell),
    ]:
        if s["N"] >= MIN_N:
            all_findings.append({"label": lbl, **s})
    print()

    # ── Top 5 findings ───────────────────────────────────────────────────────
    print("=== TOP 5 FINDINGS (by AvgR, min N=30) ===")
    ranked = sorted(all_findings, key=lambda x: x["avg_r"], reverse=True)
    for rank, f in enumerate(ranked[:5], 1):
        sign = "+" if f["avg_r"] >= 0 else ""
        sign2 = "+" if f["total_r"] >= 0 else ""
        print(
            f"  {rank}. {f['label']:<52}"
            f"N={f['N']:>4}  WR={f['wr']:>5.1f}%"
            f"  AvgR={sign}{f['avg_r']:>+.2f}R"
            f"  TotalR={sign2}{f['total_r']:>+.1f}R"
        )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pattern sweep on M15 data")
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--btc", action="store_true", help="BTC (default)")
    grp.add_argument("--xau", action="store_true", help="XAU")
    args = parser.parse_args()

    symbol = "xau" if args.xau else "btc"
    if not PARQUET[symbol].exists():
        sys.exit(f"Parquet not found: {PARQUET[symbol]}")

    run_sweep(symbol)


if __name__ == "__main__":
    main()

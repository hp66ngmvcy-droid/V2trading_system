#!/usr/bin/env python3
"""Quick sandbox: signal count + naive edge check for 6 new strategy ideas.
No full backtest — counts signals and checks raw next-N-bar returns."""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path

VALIDATED = Path(__file__).parents[1] / "data" / "validated"

def load(sym_tf: str) -> pd.DataFrame:
    p = VALIDATED / f"{sym_tf}.parquet"
    df = pd.read_parquet(p)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # normalise volume col name
    if "<TICKVOL>" in df.columns:
        df.rename(columns={"<TICKVOL>": "tickvol"}, inplace=True)
    elif "tickvol" not in df.columns:
        df["tickvol"] = 1
    return df.sort_values("timestamp").reset_index(drop=True)

def naive_edge(df: pd.DataFrame, signals: pd.Series, hold_bars: int, atr_col="atr") -> dict:
    """For each signal bar, check return over next hold_bars. Raw, no costs."""
    idxs = df.index[signals]
    if len(idxs) == 0:
        return {"signals": 0}
    results = []
    for i in idxs:
        end = min(i + hold_bars, len(df) - 1)
        ret = (df.at[end, "close"] - df.at[i, "close"]) / df.at[i, "close"] * 100
        results.append(ret)
    arr = np.array(results)
    return {
        "signals": len(arr),
        "win_rate": round((arr > 0).mean() * 100, 1),
        "avg_ret_pct": round(arr.mean(), 3),
        "median_ret_pct": round(np.median(arr), 3),
    }

# ── IDEA 1: Asian Range Fade/Breakout (H1) ──────────────────────────────────
def idea1_asian_range():
    df = load("XAUUSD_H1")
    df["hour"] = df["timestamp"].dt.hour
    df["date"] = df["timestamp"].dt.date
    df["atr"] = df["close"].diff().abs().rolling(14).mean()

    # Asian session: 00-06 UTC; London open bar: 07 UTC
    asian = df[df["hour"].between(0, 5)].groupby("date").agg(
        asian_high=("high","max"), asian_low=("low","min")
    )
    asian["asian_range"] = asian["asian_high"] - asian["asian_low"]
    range_50 = asian["asian_range"].rolling(20, min_periods=10).median()
    range_75 = asian["asian_range"].rolling(20, min_periods=10).quantile(0.75)
    asian["narrow"] = asian["asian_range"] < range_50
    asian["wide"] = asian["asian_range"] > range_75

    london = df[df["hour"] == 7].copy()
    london["date"] = london["timestamp"].dt.date
    london = london.join(asian[["narrow","wide","asian_high","asian_low"]], on="date")

    fade_signals = london["narrow"].fillna(False)
    follow_signals = london["wide"].fillna(False)

    fade_edge = naive_edge(london.reset_index(drop=True),
                           pd.Series(fade_signals.values), hold_bars=4)
    follow_edge = naive_edge(london.reset_index(drop=True),
                             pd.Series(follow_signals.values), hold_bars=4)
    return {"fade": fade_edge, "follow": follow_edge}

# ── IDEA 2: PM Fix Fade (M15, 15:00 UTC) ────────────────────────────────────
def idea2_pm_fix():
    df = load("XAUUSD_M15")
    df["hour"] = df["timestamp"].dt.hour
    df["minute"] = df["timestamp"].dt.minute
    df["date"] = df["timestamp"].dt.date
    df["atr"] = df["close"].diff().abs().rolling(14*4).mean()  # daily ATR proxy

    # Pre-fix window: 14:15-14:45; fix bar: 15:00
    pre_fix = df[df["timestamp"].dt.strftime("%H:%M").isin(["14:15","14:30","14:45"])]
    pre_fix_move = pre_fix.groupby("date").agg(
        pf_open=("open","first"), pf_close=("close","last")
    )
    pre_fix_move["pf_ret"] = pre_fix_move["pf_close"] - pre_fix_move["pf_open"]

    fix_bar = df[(df["hour"] == 15) & (df["minute"] == 0)].copy()
    fix_bar["date"] = fix_bar["timestamp"].dt.date
    fix_bar = fix_bar.join(pre_fix_move[["pf_ret"]], on="date")

    threshold = fix_bar["atr"] * 0.4
    signal = fix_bar["pf_ret"].abs() > threshold.values
    edge = naive_edge(fix_bar.reset_index(drop=True), pd.Series(signal.values), hold_bars=4)
    return edge

# ── IDEA 3: EMA Pullback State Machine (H1) ──────────────────────────────────
def idea3_ema_pullback():
    df = load("XAUUSD_H1")
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()
    df["atr"] = df["close"].diff().abs().rolling(14).mean()
    df["vol_med"] = df["tickvol"].rolling(20).median()

    signals = []
    state = "SCANNING"
    pullback_high = None

    for i in range(50, len(df)):
        row = df.iloc[i]
        # State machine
        if state == "SCANNING":
            if row["ema20"] > row["ema50"]:
                state = "ARMED_WATCH"
        elif state == "ARMED_WATCH":
            if row["ema20"] <= row["ema50"]:
                state = "SCANNING"
            elif row["close"] < row["ema20"] + row["atr"] * 0.5:
                pullback_high = row["high"]
                state = "WINDOW"
        elif state == "WINDOW":
            if row["close"] < row["ema50"]:
                state = "SCANNING"
                pullback_high = None
            elif row["high"] > pullback_high and row["tickvol"] > row["vol_med"]:
                signals.append(i)
                state = "SCANNING"
                pullback_high = None

    sig_series = pd.Series(False, index=df.index)
    sig_series.iloc[signals] = True
    return naive_edge(df, sig_series, hold_bars=6)

# ── IDEA 4: Day-of-Week Edge Check (D1) ──────────────────────────────────────
def idea4_dow():
    df = load("XAUUSD_D1")
    df["ret"] = df["close"].pct_change() * 100
    df["dow"] = df["timestamp"].dt.day_name()
    stats = df.groupby("dow")["ret"].agg(
        avg_ret="mean", win_rate=lambda x: (x > 0).mean() * 100, count="count"
    ).round(3)
    return stats.to_dict()

# ── IDEA 5: Safe-Haven Composite (D1) ────────────────────────────────────────
def idea5_safe_haven():
    gold = load("XAUUSD_D1")[["timestamp","close"]].rename(columns={"close":"gold"})
    vix  = load("VIX_D1")[["timestamp","close"]].rename(columns={"close":"vix"})
    dxy  = load("DXY_D1")[["timestamp","close"]].rename(columns={"close":"dxy"})

    df = gold.merge(vix, on="timestamp", how="inner").merge(dxy, on="timestamp", how="inner")
    df = df.sort_values("timestamp").reset_index(drop=True)

    df["vix_z"]  = (df["vix"].diff() / df["vix"].rolling(20).std())
    df["dxy_z"]  = (df["dxy"].pct_change() / df["dxy"].pct_change().rolling(20).std())
    df["composite"] = df["vix_z"] - df["dxy_z"]
    df["comp_z"] = (df["composite"] - df["composite"].rolling(60).mean()) / df["composite"].rolling(60).std()

    # Signal: composite z > 1.5 for 2 consecutive days
    df["signal_raw"] = df["comp_z"] > 1.5
    df["signal"] = df["signal_raw"] & df["signal_raw"].shift(1).fillna(False)

    # edge check using gold column
    idxs = df.index[df["signal"]]
    results = []
    for i in idxs:
        end = min(i + 5, len(df) - 1)
        ret = (df.at[end, "gold"] - df.at[i, "gold"]) / df.at[i, "gold"] * 100
        results.append(ret)
    arr = np.array(results)
    if len(arr) == 0:
        return {"signals": 0}
    return {"signals": len(arr), "win_rate": round((arr>0).mean()*100,1),
            "avg_ret_pct": round(arr.mean(),3), "median_ret_pct": round(np.median(arr),3)}

# ── IDEA 6: HMM skip — no hmmlearn ──────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== IDEA 1: Asian Range Fade/Follow (H1) ===")
    r = idea1_asian_range()
    print(f"  Fade  (narrow range): {r['fade']}")
    print(f"  Follow (wide range):  {r['follow']}")

    print("\n=== IDEA 2: PM Fix Fade (M15 15:00 UTC) ===")
    print(f"  {idea2_pm_fix()}")

    print("\n=== IDEA 3: EMA Pullback State Machine (H1) ===")
    print(f"  {idea3_ema_pullback()}")

    print("\n=== IDEA 4: Day-of-Week Edge (D1) ===")
    dow = idea4_dow()
    for day, stats in sorted(dow["avg_ret"].items()):
        print(f"  {day:10s} avg={dow['avg_ret'][day]:+.3f}%  win={dow['win_rate'][day]:.1f}%  n={int(dow['count'][day])}")

    print("\n=== IDEA 5: Safe-Haven Composite (D1) ===")
    print(f"  {idea5_safe_haven()}")

    print("\n=== IDEA 6: HMM Regime Gate — SKIP (hmmlearn not installed) ===")
    print("  Install: pip install hmmlearn, then rebuild")

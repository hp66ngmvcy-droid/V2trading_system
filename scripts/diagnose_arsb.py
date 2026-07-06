"""Diagnostic: arsb_v1 Asian range / ATR compression analysis.

Run with: python scripts/diagnose_arsb.py
(venv must be active)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/validated/XAUUSD_M15.parquet")

if not DATA_PATH.exists():
    print(f"ERROR: {DATA_PATH} not found. Run import + validate first.")
    sys.exit(1)

df = pd.read_parquet(DATA_PATH)
print(f"Loaded {len(df)} rows from {DATA_PATH}")

# Ensure UTC timestamps
ts = pd.to_datetime(df["timestamp"], utc=True)
df = df.copy()
df["_ts"] = ts
df["_date"] = ts.dt.date

# 14-period ATR
high = df["high"]
low = df["low"]
close = df["close"]
prev_close = close.shift(1)
tr = pd.concat([
    high - low,
    (high - prev_close).abs(),
    (low - prev_close).abs(),
], axis=1).max(axis=1)
df["atr14"] = tr.rolling(14).mean()

# Asian session 01:00-06:45 UTC (hours 1-6 inclusive)
asian_mask = (ts.dt.hour >= 1) & (ts.dt.hour < 7)
asian_bars = df[asian_mask].copy()
asian_daily = asian_bars.groupby("_date").agg(
    asian_high=("high", "max"),
    asian_low=("low", "min"),
).reset_index()
asian_daily["asian_range"] = asian_daily["asian_high"] - asian_daily["asian_low"]

df = df.merge(asian_daily[["_date", "asian_range"]], on="_date", how="left")

# Only rows where both ATR and asian_range are valid
valid = df.dropna(subset=["atr14", "asian_range"]).copy()
valid = valid[valid["atr14"] > 0]
valid["ratio"] = valid["asian_range"] / valid["atr14"]

ratio = valid["ratio"]
print(f"\nAsian range / ATR14 ratio — {len(ratio)} valid bars:")
print(f"  min:    {ratio.min():.3f}")
print(f"  max:    {ratio.max():.3f}")
print(f"  mean:   {ratio.mean():.3f}")
print(f"  median: {ratio.median():.3f}")
print("\nPercentile distribution:")
for p in [5, 10, 20, 25, 33, 40, 50, 60, 67, 75, 80, 90, 95]:
    print(f"  p{p:02d}: {ratio.quantile(p/100):.3f}")

# Asian range absolute distribution
ar = asian_daily["asian_range"].dropna()
print(f"\nAsian range (absolute $) — {len(ar)} daily observations:")
print(f"  min:    {ar.min():.2f}")
print(f"  max:    {ar.max():.2f}")
print(f"  mean:   {ar.mean():.2f}")
print(f"  median: {ar.median():.2f}")
for p in [10, 25, 50, 75, 90]:
    print(f"  p{p:02d}: {ar.quantile(p/100):.2f}")

# Signal count simulation: how many London-open bars pass various thresholds
london_mask = (ts.dt.hour >= 8) & (ts.dt.hour < 17)
london_valid = valid[london_mask].copy()

range_min, range_max = 6.0, 20.0
london_in_range = london_valid[
    (london_valid["asian_range"] >= range_min) &
    (london_valid["asian_range"] <= range_max)
].copy()

print(f"\nLondon-open bars (08-17 UTC): {len(london_valid)}")
print(f"  After range_min/max filter ($6-$20): {len(london_in_range)}")

print("\nSignal count by compression_atr_mult threshold (ratio < thresh = COMPRESSED):")
print(f"  {'threshold':>10} | {'compressed bars':>16} | {'approx daily signals':>20}")
thresholds = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
total_days = len(asian_daily)
for thresh in thresholds:
    compressed = london_in_range[london_in_range["ratio"] < thresh]
    count = len(compressed)
    daily_avg = count / max(total_days, 1)
    print(f"  {thresh:>10.2f} | {count:>16} | {daily_avg:>20.3f}")

print("\nRECOMMENDATION:")
# Target ~100-200 signals over full dataset
target_low, target_high = 100, 200
for thresh in thresholds:
    compressed = london_in_range[london_in_range["ratio"] < thresh]
    count = len(compressed)
    if target_low <= count <= target_high:
        print(f"  compression_atr_mult = {thresh:.2f} gives {count} potential signal bars (in target range)")
        break
else:
    # find closest
    counts = [(thresh, len(london_in_range[london_in_range["ratio"] < thresh])) for thresh in thresholds]
    best = min(counts, key=lambda x: abs(x[1] - 150))
    print(f"  No threshold hits exactly {target_low}-{target_high}.")
    print(f"  Closest: compression_atr_mult = {best[0]:.2f} gives {best[1]} bars.")
    print(f"  Current value 0.60 gives: {len(london_in_range[london_in_range['ratio'] < 0.60])} bars.")
    print(f"  Also check: range_min_pts and range_max_pts may be too restrictive.")
    ar_filtered = london_valid[(london_valid["asian_range"] >= range_min) & (london_valid["asian_range"] <= range_max)]
    print(f"  London bars passing range filter: {len(ar_filtered)} / {len(london_valid)} ({100*len(ar_filtered)/max(len(london_valid),1):.1f}%)")

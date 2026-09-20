#!/usr/bin/env python3
"""Extend XAUUSD and BTCUSD M15 raw CSVs using Twelve Data API.

Reads the last timestamp from each CSV and fetches forward to today.
Appends new rows in the exact format the importer expects.

Usage:
    secrets_run_trading -- venv/bin/python scripts/extend_m15_data.py
    secrets_run_trading -- venv/bin/python scripts/extend_m15_data.py --symbol XAUUSD
    secrets_run_trading -- venv/bin/python scripts/extend_m15_data.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

# Twelve Data symbol map
TD_SYMBOLS = {
    "XAUUSD": "XAU/USD",
    "BTCUSD": "BTC/USD",
}

# Max bars per Twelve Data request
TD_BATCH = 5000
TD_BASE = "https://api.twelvedata.com/time_series"


def _api_key() -> str:
    key = os.environ.get("TWELVE_DATA_KEY", "")
    if not key:
        sys.exit("ERROR: TWELVE_DATA_KEY not set. Run via secrets_run_trading.")
    return key


def _last_timestamp(csv_path: Path, symbol: str) -> datetime:
    """Return the last datetime in the CSV."""
    last_line = ""
    with csv_path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                last_line = line.strip()
    if not last_line or last_line.startswith("<DATE>") or last_line.startswith("date"):
        sys.exit(f"ERROR: could not read last row from {csv_path}")
    sep = "\t" if "\t" in last_line else ","
    parts = last_line.split(sep)
    date_str = parts[0].replace(".", "-")
    time_str = parts[1]
    return datetime.fromisoformat(f"{date_str} {time_str}").replace(tzinfo=timezone.utc)


def _fetch_batch(td_symbol: str, start: datetime, end: datetime, api_key: str) -> list[dict]:
    params = {
        "symbol": td_symbol,
        "interval": "15min",
        "start_date": start.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": end.strftime("%Y-%m-%d %H:%M:%S"),
        "outputsize": TD_BATCH,
        "format": "JSON",
        "timezone": "UTC",
        "apikey": api_key,
    }
    r = httpx.get(TD_BASE, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("status") == "error":
        sys.exit(f"Twelve Data error: {data.get('message')}")
    values = data.get("values", [])
    # API returns newest-first — reverse to chronological
    return list(reversed(values))


def _format_xauusd_row(bar: dict) -> str:
    dt = datetime.fromisoformat(bar["datetime"])
    date = dt.strftime("%Y.%m.%d")
    time = dt.strftime("%H:%M:%S")
    ts = dt.strftime("%Y-%m-%d %H:%M:%S")
    o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
    vol = bar.get("volume", "0") or "0"
    return f"{date},{time},{o},{h},{l},{c},{vol},0,0,{ts},XAUUSD,M15"


def _format_btcusd_row(bar: dict) -> str:
    dt = datetime.fromisoformat(bar["datetime"])
    date = dt.strftime("%Y.%m.%d")
    time = dt.strftime("%H:%M:%S")
    o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
    vol = bar.get("volume", "0") or "0"
    return f"{date}\t{time}\t{o}\t{h}\t{l}\t{c}\t{vol}\t0\t0"


FORMATTERS = {
    "XAUUSD": _format_xauusd_row,
    "BTCUSD": _format_btcusd_row,
}


def extend_symbol(symbol: str, dry_run: bool) -> None:
    csv_path = RAW_DIR / f"{symbol}_M15.csv"
    if not csv_path.exists():
        print(f"SKIP {symbol}: {csv_path} not found")
        return

    last_ts = _last_timestamp(csv_path, symbol)
    now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    # Round down to last complete 15-min bar
    minutes = (now_utc.minute // 15) * 15
    now_utc = now_utc.replace(minute=minutes)

    if last_ts >= now_utc - timedelta(minutes=15):
        print(f"{symbol}: already current (last={last_ts.isoformat()})")
        return

    print(f"{symbol}: fetching {last_ts.isoformat()} → {now_utc.isoformat()}")

    api_key = _api_key()
    td_symbol = TD_SYMBOLS[symbol]
    all_bars: list[dict] = []

    # Batch forward in TD_BATCH-sized windows
    fetch_start = last_ts + timedelta(minutes=15)
    while fetch_start < now_utc:
        fetch_end = min(fetch_start + timedelta(minutes=15 * TD_BATCH), now_utc)
        print(f"  batch {fetch_start.date()} → {fetch_end.date()} ...", end=" ", flush=True)
        bars = _fetch_batch(td_symbol, fetch_start, fetch_end, api_key)
        print(f"{len(bars)} bars")
        all_bars.extend(bars)
        fetch_start = fetch_end + timedelta(minutes=15)
        if fetch_start < now_utc:
            time.sleep(1)  # rate-limit courtesy pause

    if not all_bars:
        print(f"{symbol}: no new bars returned")
        return

    # Append to validated parquet directly (bypasses csv_importer duplicate-column bug)
    append_to_validated_parquet(symbol, all_bars, dry_run)

    # Also append to raw CSV for record-keeping
    formatter = FORMATTERS[symbol]
    new_rows = [formatter(b) for b in all_bars]
    print(f"{symbol}: {len(new_rows)} rows {'(dry-run — not written to CSV)' if dry_run else 'appended to raw CSV'}")
    if not dry_run:
        with csv_path.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(new_rows) + "\n")


def append_to_validated_parquet(symbol: str, bars: list[dict], dry_run: bool) -> None:
    """Append new bars directly to the validated parquet, bypassing csv_importer."""
    import hashlib
    import pandas as pd

    validated_path = ROOT / "data" / "validated" / f"{symbol}_M15.parquet"
    if not validated_path.exists():
        print(f"WARNING: {validated_path} not found — skipping parquet append")
        return

    existing = pd.read_parquet(validated_path)
    last_ts = existing["timestamp"].max()

    rows = []
    for bar in bars:
        dt = datetime.fromisoformat(bar["datetime"])
        ts = pd.Timestamp(dt)
        if ts <= last_ts:
            continue
        rows.append({
            "date": dt.strftime("%Y.%m.%d"),
            "time": dt.strftime("%H:%M:%S"),
            "open": float(bar["open"]),
            "high": float(bar["high"]),
            "low": float(bar["low"]),
            "close": float(bar["close"]),
            "<TICKVOL>": int(float(bar.get("volume") or 0)),
            "volume": 0,
            "spread": 0,
            "timestamp": ts,
            "symbol": symbol,
            "timeframe": "M15",
            "data_hash": hashlib.sha256(f"{symbol}M15{dt.isoformat()}".encode()).hexdigest(),
        })

    if not rows:
        print(f"{symbol}: no new rows after dedup")
        return

    print(f"{symbol}: {len(rows)} rows to append {'(dry-run)' if dry_run else ''}")
    if dry_run:
        return

    new_df = pd.DataFrame(rows)
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    combined.to_parquet(validated_path, index=False)
    print(f"{symbol}: validated parquet updated → {len(combined)} rows")


def rebuild_features(symbol: str, dry_run: bool) -> None:
    if dry_run:
        print(f"{symbol}: would rebuild features (skipped — dry-run)")
        return
    import subprocess
    env = os.environ.copy()
    env["SYMBOL"] = symbol
    env["TIMEFRAME"] = "M15"
    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "build_features_all.sh")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"WARNING: feature build stderr:\n{result.stderr[-500:]}")
    else:
        print(f"{symbol}: features rebuilt")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extend M15 raw CSVs via Twelve Data")
    parser.add_argument("--symbol", choices=["XAUUSD", "BTCUSD"], help="single symbol (default: both)")
    parser.add_argument("--dry-run", action="store_true", help="fetch and count but do not write")
    parser.add_argument("--no-rebuild", action="store_true", help="skip feature rebuild after append")
    args = parser.parse_args()

    symbols = [args.symbol] if args.symbol else ["XAUUSD", "BTCUSD"]
    for sym in symbols:
        extend_symbol(sym, args.dry_run)
        if not args.no_rebuild:
            rebuild_features(sym, args.dry_run)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fetch daily VIX, NQ, DXY, Gold data from Yahoo Finance → MT5 CSV format.

Symbols fetched:
  ^VIX   → VIX_D1.csv
  NQ=F   → NQ_D1.csv
  DX-Y.NYB → DXY_D1.csv
  GC=F   → GOLD_D1.csv

Usage:
  python scripts/fetch_cross_asset_data.py
  python scripts/fetch_cross_asset_data.py --years 10
"""
from __future__ import annotations

import argparse
import csv
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

REPO = Path(__file__).parent.parent
RAW_DIR = REPO / "data" / "raw"

SYMBOLS = {
    "^VIX":      "VIX_D1.csv",
    "NQ=F":      "NQ_D1.csv",
    "DX-Y.NYB":  "DXY_D1.csv",
    "GC=F":      "GOLD_D1.csv",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def fetch_yahoo(ticker: str, years: int) -> list[dict]:
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{ticker.replace('^', '%5E')}?interval=1d&range={years}y"
    )
    r = httpx.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    quotes = result["indicators"]["quote"][0]
    rows = []
    for i, ts in enumerate(timestamps):
        o = quotes["open"][i]
        h = quotes["high"][i]
        l = quotes["low"][i]
        c = quotes["close"][i]
        v = quotes.get("volume", [None] * len(timestamps))[i]
        if None in (o, h, l, c):
            continue
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        rows.append({
            "date": dt.strftime("%Y.%m.%d"),
            "time": "00:00:00",
            "open": round(float(o), 5),
            "high": round(float(h), 5),
            "low":  round(float(l), 5),
            "close": round(float(c), 5),
            "tickvol": int(v) if v else 0,
            "vol": 0,
            "spread": 0,
        })
    return rows


def write_mt5_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>",
                    "<TICKVOL>", "<VOL>", "<SPREAD>"])
        for r in rows:
            w.writerow([r["date"], r["time"], r["open"], r["high"],
                        r["low"], r["close"], r["tickvol"], r["vol"], r["spread"]])
    log.info("wrote %d bars → %s", len(rows), path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=7,
                        help="Years of history to fetch (default: 7)")
    args = parser.parse_args()

    for ticker, filename in SYMBOLS.items():
        log.info("fetching %s (%d years)...", ticker, args.years)
        try:
            rows = fetch_yahoo(ticker, args.years)
            write_mt5_csv(rows, RAW_DIR / filename)
        except Exception as e:
            log.error("failed %s: %s", ticker, e)


if __name__ == "__main__":
    main()

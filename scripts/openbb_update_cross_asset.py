#!/usr/bin/env python3
"""Update cross-asset D1 parquets via yfinance (openbb-yfinance provider).

Fetches only missing days since last parquet date and appends.
DXY, VIX, NQ, Gold — all instruments needed by cross_asset_correlation_v1.

Usage:
    source venv/bin/activate
    python scripts/openbb_update_cross_asset.py [--force]
"""
from __future__ import annotations

import argparse
import hashlib
import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

REPO = Path(__file__).parent.parent
VALIDATED = REPO / "data" / "validated"

TARGETS = {
    "DX-Y.NYB": ("DXY",  "D1"),
    "^VIX":     ("VIX",  "D1"),
    "NQ=F":     ("NQ",   "D1"),
    "GC=F":     ("GOLD", "D1"),
}


def last_parquet_date(symbol: str, timeframe: str) -> date | None:
    path = VALIDATED / f"{symbol}_{timeframe}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["timestamp"])
    return pd.to_datetime(df["timestamp"]).max().date()


def fetch(ticker: str, start: date, end: date) -> pd.DataFrame:
    t = yf.Ticker(ticker)
    raw = t.history(start=start.isoformat(), end=end.isoformat(), auto_adjust=False)
    raw.index = raw.index.tz_localize(None)
    raw.index = raw.index.normalize()
    return raw


def to_schema(raw: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    df = pd.DataFrame()
    df["date"] = raw.index.strftime("%Y.%m.%d")
    df["time"] = "00:00:00"
    df["open"] = raw["Open"].values.round(5)
    df["high"] = raw["High"].values.round(5)
    df["low"] = raw["Low"].values.round(5)
    df["close"] = raw["Close"].values.round(5)
    df["volume"] = raw.get("Volume", pd.Series(0, index=raw.index)).fillna(0).astype("int64").values
    df["<VOL>"] = 0
    df["spread"] = 0
    df["timestamp"] = pd.to_datetime(df["date"], format="%Y.%m.%d")
    src = f"yfinance:{symbol}_{timeframe}:{df['date'].iloc[0]}:{df['date'].iloc[-1]}"
    df["data_hash"] = pd.array([hashlib.sha256(src.encode()).hexdigest()] * len(df), dtype="string")
    df["symbol"] = pd.array([symbol] * len(df), dtype="string")
    df["timeframe"] = pd.array([timeframe] * len(df), dtype="string")
    return df[["date", "time", "open", "high", "low", "close",
               "volume", "<VOL>", "spread", "timestamp", "symbol", "timeframe", "data_hash"]]


def append_parquet(new_rows: pd.DataFrame, symbol: str, timeframe: str) -> int:
    path = VALIDATED / f"{symbol}_{timeframe}.parquet"
    existing = pd.read_parquet(path)
    existing["timestamp"] = pd.to_datetime(existing["timestamp"])
    combined = (
        pd.concat([existing, new_rows], ignore_index=True)
        .drop_duplicates(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    combined.to_parquet(path, index=False)
    return len(new_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="Re-fetch even if parquet appears current")
    args = parser.parse_args()

    today = date.today()
    yesterday = today - timedelta(days=1)

    for ticker, (symbol, timeframe) in TARGETS.items():
        last = last_parquet_date(symbol, timeframe)

        if last and last >= yesterday and not args.force:
            log.info("%s_%s already current (%s)", symbol, timeframe, last)
            continue

        start = (last + timedelta(days=1)) if last else (today - timedelta(days=365 * 7))
        log.info("fetching %s  %s → %s", ticker, start, today)

        try:
            raw = fetch(ticker, start, today)
            if raw.empty:
                log.warning("%s: no new data returned", ticker)
                continue
            rows = to_schema(raw, symbol, timeframe)
            n = append_parquet(rows, symbol, timeframe)
            log.info("%s_%s: +%d rows  new end: %s", symbol, timeframe, n, rows["date"].iloc[-1])
        except Exception as e:
            log.error("%s failed: %s", ticker, e)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Real bar-walking backtest for key_level_sweep_v1.

Uses the event-driven backtest engine (TP/SL hit on actual M15 OHLC bars),
restricted to dates covered by daily brief JSON files.

Usage:
    secrets_run_trading -- venv/bin/python scripts/run_key_level_sweep_real_backtest.py
    secrets_run_trading -- venv/bin/python scripts/run_key_level_sweep_real_backtest.py --symbol BTCUSD
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from tar_system.backtest.engine import run_backtest
from tar_system.brokers.registry import load_broker_profile
from tar_system.data.daily_brief_loader import load_daily_levels
from tar_system.strategies.key_level_sweep_v1 import KeyLevelSweepV1

BRIEFS_DIR = ROOT / "data" / "daily_briefs"
FEATURES_DIR = ROOT / "data" / "features"
RESULTS_DIR = ROOT / "data" / "results"
TIMEFRAME = "M15"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD", choices=["XAUUSD", "BTCUSD"])
    args = parser.parse_args()
    symbol = args.symbol

    # Collect dates that have a valid brief for this symbol
    brief_dates = sorted(
        bf.stem.replace("_levels", "")
        for bf in BRIEFS_DIR.glob("*_levels.json")
        if load_daily_levels(bf.stem.replace("_levels", ""), symbol, BRIEFS_DIR) is not None
    )
    if not brief_dates:
        print(f"No valid briefs found for {symbol}")
        return 1

    print(f"{symbol}: {len(brief_dates)} brief dates — {brief_dates[0]} to {brief_dates[-1]}")

    # Load feature parquet and slice to brief dates only
    parquet = FEATURES_DIR / f"{symbol}_{TIMEFRAME}.parquet"
    features = pd.read_parquet(parquet)
    features["_date"] = features["timestamp"].dt.date.astype(str)
    slice_df = features[features["_date"].isin(brief_dates)].drop(columns=["_date"]).copy()
    slice_df = slice_df.reset_index(drop=True)
    print(f"{symbol}: {len(slice_df)} real M15 bars across brief dates")

    if slice_df.empty:
        print("ERROR: no bars found for brief dates — check parquet date range")
        return 1

    # Run real backtest — TP/SL resolved on actual bar OHLC
    # BTCUSD has no session cutoff (24h); XAUUSD uses default 12:00 UTC London close.
    session_end = None if symbol == "BTCUSD" else "12:00"
    strategy = KeyLevelSweepV1(
        symbol=symbol,
        briefs_dir=BRIEFS_DIR,
        min_confidence=0.55,
        session_end_utc=session_end,
    )
    broker_profile = load_broker_profile("current_broker_demo")
    result = run_backtest(slice_df, strategy, broker_profile=broker_profile, audit_decisions=False)

    m = result.metrics
    trades = result.trades
    win_rate = m.get("win_rate", 0.0)
    pf = m.get("profit_factor", 0.0)
    dd = m.get("max_drawdown", 0.0)

    print(f"\n{'='*50}")
    print(f"strategy      : {strategy.name} v{strategy.version}")
    print(f"symbol        : {symbol} {TIMEFRAME}")
    print(f"data_source   : REAL M15 bars")
    print(f"brief dates   : {len(brief_dates)}")
    print(f"bars in slice : {len(slice_df)}")
    print(f"total trades  : {trades}")
    print(f"win_rate      : {win_rate:.1%}")
    print(f"profit_factor : {pf:.3f}")
    print(f"max_drawdown  : {dd:.1%}")
    print(f"final_equity  : {result.final_equity:.2f}")
    print(f"{'='*50}")

    output = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper_only": True,
        "real_bars": True,
        "strategy": strategy.name,
        "version": strategy.version,
        "symbol": symbol,
        "timeframe": TIMEFRAME,
        "brief_dates": brief_dates,
        "bars_in_slice": len(slice_df),
        "total_trades": trades,
        "win_rate": round(win_rate, 4),
        "profit_factor": round(pf, 4),
        "max_drawdown": round(dd, 4),
        "final_equity": round(result.final_equity, 2),
        "metrics": {k: (round(v, 6) if isinstance(v, float) else v)
                    for k, v in m.items() if not isinstance(v, list)},
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"key_level_sweep_v1_{symbol}_{TIMEFRAME}_real.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"results saved : {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

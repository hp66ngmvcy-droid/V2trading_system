#!/usr/bin/env python3
"""MT5 paper-mode live feed for key_level_sweep_v1.

Pulls live M15 bars from a running MT5 terminal, runs the strategy,
and logs any BUY/SELL signals to data/live_signals/. No orders are
ever placed — paper-mode only, LIVE_TRADING_ENABLED = False.

Requirements:
    pip install MetaTrader5
    MT5 terminal must be open and logged into a demo or live account.

Usage:
    secrets_run_trading -- venv/bin/python scripts/run_mt5_live_paper.py
    secrets_run_trading -- venv/bin/python scripts/run_mt5_live_paper.py --symbol BTCUSD
    secrets_run_trading -- venv/bin/python scripts/run_mt5_live_paper.py --once
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from tar_system.strategies.key_level_sweep_v1 import KeyLevelSweepV1

BRIEFS_DIR = ROOT / "data" / "daily_briefs"
SIGNALS_DIR = ROOT / "data" / "live_signals"
TIMEFRAME = "M15"
POLL_SECONDS = 60          # check every 60s; MT5 bar closes every 900s
ATR_PERIOD = 14
BARS_TO_FETCH = 50         # enough to compute ATR and catch current bar

LIVE_TRADING_ENABLED = False  # hard gate — never flip without approval


def _require_mt5():
    try:
        import MetaTrader5 as mt5
        return mt5
    except ImportError:
        print("MetaTrader5 package not installed.")
        print("Install with: venv/bin/pip install MetaTrader5")
        print("MT5 terminal must be running on this machine.")
        sys.exit(1)


def _mt5_timeframe(mt5, tf: str):
    return {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
    }[tf]


def _fetch_bars(mt5, symbol: str, tf: str, n: int) -> pd.DataFrame:
    rates = mt5.copy_rates_from_pos(symbol, _mt5_timeframe(mt5, tf), 0, n)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"MT5 returned no bars for {symbol} {tf}")
    df = pd.DataFrame(rates)
    df["timestamp"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.rename(columns={"tick_volume": "volume"})
    df["symbol"] = symbol
    df["timeframe"] = tf
    # Compute ATR (Wilder's, approximated as rolling true-range mean)
    df["prev_close"] = df["close"].shift(1)
    df["tr"] = df[["high", "low", "prev_close"]].apply(
        lambda r: max(r["high"] - r["low"],
                      abs(r["high"] - (r["prev_close"] or r["close"])),
                      abs(r["low"] - (r["prev_close"] or r["close"]))),
        axis=1,
    )
    df["atr"] = df["tr"].ewm(alpha=1 / ATR_PERIOD, adjust=False).mean()
    return df.drop(columns=["prev_close", "tr", "time"])


def _log_signal(signal, signals_dir: Path) -> None:
    signals_dir.mkdir(parents=True, exist_ok=True)
    date_str = str(signal.timestamp.date())
    path = signals_dir / f"{date_str}_live_paper_signals.jsonl"
    record = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "timestamp": signal.timestamp.isoformat(),
        "symbol": signal.symbol,
        "timeframe": signal.timeframe,
        "strategy": signal.strategy,
        "version": signal.version,
        "side": signal.side,
        "confidence": signal.confidence,
        "entry": signal.entry,
        "stop_loss": signal.stop_loss,
        "take_profit": signal.take_profit,
        "reason_code": signal.reason_code,
        "metadata": signal.metadata,
        "paper_only": True,
        "live_trading_enabled": LIVE_TRADING_ENABLED,
    }
    with path.open("a") as f:
        f.write(json.dumps(record, default=str) + "\n")
    print(f"  SIGNAL LOGGED → {path.name}")


def run_once(mt5, strategy: KeyLevelSweepV1, symbol: str) -> None:
    df = _fetch_bars(mt5, symbol, TIMEFRAME, BARS_TO_FETCH)
    # Use the last completed bar (index -2); bar -1 is still forming
    bar = df.iloc[-2]
    ts = bar["timestamp"]
    signal = strategy.generate_signal(bar, regime="NEUTRAL")
    status = f"[{ts.strftime('%H:%M UTC')}] {symbol} → {signal.side} ({signal.reason_code})"
    print(status)
    if signal.side in ("BUY", "SELL"):
        _log_signal(signal, SIGNALS_DIR)


def main() -> int:
    assert not LIVE_TRADING_ENABLED, "LIVE_TRADING_ENABLED must stay False"

    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD", choices=["XAUUSD", "BTCUSD"])
    parser.add_argument("--once", action="store_true", help="Run one bar then exit")
    args = parser.parse_args()
    symbol = args.symbol

    mt5 = _require_mt5()

    if not mt5.initialize():
        print(f"MT5 initialize() failed: {mt5.last_error()}")
        print("Ensure MT5 terminal is open and logged in (demo account is fine).")
        return 1

    info = mt5.terminal_info()
    print(f"MT5 connected: {info.name if info else 'unknown'}")
    print(f"Mode: PAPER ONLY — no orders will be placed")

    session_end = None if symbol == "BTCUSD" else "12:00"
    strategy = KeyLevelSweepV1(
        symbol=symbol,
        briefs_dir=BRIEFS_DIR,
        min_confidence=0.55,
        session_end_utc=session_end,
    )

    print(f"Strategy: {strategy.name} v{strategy.version} | {symbol} {TIMEFRAME}")
    print(f"Polling every {POLL_SECONDS}s — Ctrl-C to stop\n")

    try:
        while True:
            try:
                run_once(mt5, strategy, symbol)
            except Exception as exc:
                print(f"  ERROR: {exc}")
            if args.once:
                break
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        mt5.shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

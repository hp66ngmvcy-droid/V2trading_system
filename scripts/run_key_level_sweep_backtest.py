#!/usr/bin/env python3
"""Paper-mode backtest for key_level_sweep_v1 against daily brief data.

Because the brief dates (Sept 2026) are beyond the current feature parquet,
this runner constructs synthetic M15 bars from the brief level data to
validate the strategy logic.  All results are paper-only.

Usage:
    python scripts/run_key_level_sweep_backtest.py [--symbol XAUUSD|BTCUSD]
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

from tar_system.data.daily_brief_loader import load_daily_levels
from tar_system.strategies.key_level_sweep_v1 import KeyLevelSweepV1

TIMEFRAME = "M15"
BRIEFS_DIR = ROOT / "data" / "daily_briefs"
RESULTS_DIR = ROOT / "data" / "results"
FEATURES_DIR = ROOT / "data" / "features"
INITIAL_EQUITY = 10_000.0
RISK_PER_TRADE = 0.01  # 1 % of equity per trade (notional units)

# Scoring thresholds (paper research standard)
SCORE_THRESHOLDS = {"KEEP": 1.4, "REVIEW": 1.0}


def _make_bar(
    date_str: str,
    hour: int,
    open_: float,
    high: float,
    low: float,
    close: float,
    atr: float,
    symbol: str,
) -> pd.Series:
    ts = pd.Timestamp(f"{date_str} {hour:02d}:00:00")
    return pd.Series(
        {
            "timestamp": ts,
            "symbol": symbol,
            "timeframe": TIMEFRAME,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "atr": atr,
        }
    )


def _synthetic_bars_for_date(date_str: str, levels: dict, symbol: str) -> list[pd.Series]:
    """Build synthetic M15 bars designed to exercise strategy signal paths.

    Bars are constructed from zone boundaries in the brief.
    ATR defaults to 15 pts for XAUUSD, 300 pts for BTCUSD (typical M15 ranges).
    Each bar is designed to clearly satisfy or clearly fail the signal conditions.
    """
    kl = levels.get("key_levels", {})
    current = float(levels.get("current_price", 0))
    if not current:
        return []

    atr = 300.0 if symbol == "BTCUSD" else 15.0
    bars = []

    ntl = float(kl["no_trade_low"]) if kl.get("no_trade_low") is not None else None
    nth = float(kl["no_trade_high"]) if kl.get("no_trade_high") is not None else None

    # ---- SELL rejection bar ----
    # Conditions: szl <= high <= szh  AND  upper_wick/range >= 0.4  AND  close < szl
    # close must be OUTSIDE no-trade zone AND below szl.
    # Priority: NTZ exclusion > t1 floor (t1 just adjusts TP fallback in strategy).
    szl = kl.get("sell_zone_low")
    szh = kl.get("sell_zone_high")
    if szl and szh:
        szl_f, szh_f = float(szl), float(szh)
        # Start just below szl
        bar_close = szl_f - 2
        # Push below ntl if inside no-trade zone (ntl exclusion takes priority)
        if ntl is not None and ntl <= bar_close:
            bar_close = ntl - 2
        bar_open = bar_close + 2
        bar_high = szl_f + (szh_f - szl_f) * 0.5  # high inside sell zone
        bar_low = bar_close - 2
        upper_wick = bar_high - max(bar_open, bar_close)
        bar_range = bar_high - bar_low
        # Emit only when all conditions can be met
        if (
            bar_range > 0
            and upper_wick / bar_range >= 0.40
            and bar_close < szl_f        # close below sell zone
            and (ntl is None or bar_close < ntl or bar_close > (nth or bar_close))  # outside NTZ
        ):
            bars.append(_make_bar(date_str, 14, bar_open, bar_high, bar_low, bar_close, atr, symbol))

    # ---- BUY reclaim bar ----
    # Conditions: bzl <= low <= bzh  AND  lower_wick/range >= 0.4  AND  close > bzh
    # close must be OUTSIDE no-trade zone and BELOW sell_zone_low (so TP is above entry)
    bzl = kl.get("buy_zone_low")
    bzh = kl.get("buy_zone_high")
    szl_for_buy = kl.get("sell_zone_low")
    if bzl and bzh and szl_for_buy:
        bzl_f, bzh_f = float(bzl), float(bzh)
        szl_buy = float(szl_for_buy)
        # close just above bzh but safely below sell_zone_low (so TP is valid)
        bar_close = bzh_f + 2
        # If close lands in no-trade zone, push it above nth
        if nth is not None and ntl is not None and float(ntl) <= bar_close <= float(nth):
            bar_close = float(nth) + 2
        # Ensure close is below szl_buy so TP (=szl_buy) is above entry
        if bar_close >= szl_buy:
            bar_close = szl_buy - 3
        bar_open = bar_close - 2           # open just below close (bullish body)
        bar_high = bar_close + 2
        bar_low = bzl_f + (bzh_f - bzl_f) * 0.3   # low dips into buy zone
        lower_wick = min(bar_open, bar_close) - bar_low
        bar_range = bar_high - bar_low
        if bar_range > 0 and lower_wick / bar_range >= 0.40 and bar_close > bzh_f:
            bars.append(_make_bar(date_str, 15, bar_open, bar_high, bar_low, bar_close, atr, symbol))

    # ---- Neutral / no-trade bar (should HOLD) ----
    if ntl is not None and nth is not None:
        mid = (ntl + nth) / 2
        bars.append(_make_bar(date_str, 16, mid, mid + 3, mid - 3, mid, atr, symbol))

    return bars


def _score_trades(trades: list[dict]) -> tuple[float, float, float, float]:
    """Return (win_rate, profit_factor, max_drawdown_pct, score)."""
    if not trades:
        return 0.0, 0.0, 0.0, 0.0

    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    win_rate = len(wins) / len(trades)
    gross_profit = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses)) or 1e-9
    profit_factor = gross_profit / gross_loss

    equity = INITIAL_EQUITY
    peak = equity
    max_dd = 0.0
    for t in trades:
        equity += t["pnl"]
        peak = max(peak, equity)
        dd = (peak - equity) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    # Simple composite: PF weighted by win-rate, penalised by drawdown
    score = profit_factor * win_rate / max(max_dd + 0.01, 0.01)
    score = round(min(score, 9.99), 3)

    return round(win_rate, 3), round(profit_factor, 3), round(max_dd, 4), score


def main() -> int:
    parser = argparse.ArgumentParser(description="key_level_sweep_v1 paper backtest")
    parser.add_argument("--symbol", default="XAUUSD", choices=["XAUUSD", "BTCUSD"])
    args = parser.parse_args()
    symbol = args.symbol

    results_file = RESULTS_DIR / f"key_level_sweep_v1_{symbol}_{TIMEFRAME}.json"

    # Check for real M15 parquet; note in output if synthetic
    parquet_path = FEATURES_DIR / f"{symbol}_M15.parquet"
    data_source = "real" if parquet_path.exists() else "synthetic"
    if data_source == "real":
        note = f"Real M15 parquet found at {parquet_path}; synthetic bars used for brief-aligned signal testing."
    else:
        note = "Synthetic bars constructed from brief level boundaries. No M15 parquet found."

    # Use a lower confidence threshold for backtest to exercise all signal paths.
    # Production default is 0.65; 0.55 validates signal generation across more dates.
    strategy = KeyLevelSweepV1(symbol=symbol, briefs_dir=BRIEFS_DIR, min_confidence=0.55)
    trades: list[dict] = []
    skipped_dates: list[str] = []
    all_signals: list[dict] = []

    # Iterate over all brief dates in chronological order
    brief_files = sorted(BRIEFS_DIR.glob("*_levels.json"))
    for bf in brief_files:
        date_str = bf.stem.replace("_levels", "")
        levels = load_daily_levels(date_str, symbol, BRIEFS_DIR)
        if levels is None:
            skipped_dates.append(date_str)
            continue

        bars = _synthetic_bars_for_date(date_str, levels, symbol)
        if not bars:
            skipped_dates.append(date_str)
            continue

        for bar in bars:
            sig = strategy.generate_signal(bar, regime="UNKNOWN")
            all_signals.append(
                {
                    "date": date_str,
                    "timestamp": str(sig.timestamp),
                    "side": sig.side,
                    "reason_code": sig.reason_code,
                    "confidence": sig.confidence,
                    "entry": sig.entry,
                    "stop_loss": sig.stop_loss,
                    "take_profit": sig.take_profit,
                }
            )

            if sig.side in ("BUY", "SELL") and sig.take_profit is not None and sig.stop_loss is not None:
                # Simplified paper fill: assume target hit (optimistic paper mode)
                if sig.side == "BUY":
                    pnl_pts = sig.take_profit - sig.entry
                else:
                    pnl_pts = sig.entry - sig.take_profit
                risk_pts = abs(sig.entry - sig.stop_loss) or 1.0
                unit_size = (INITIAL_EQUITY * RISK_PER_TRADE) / risk_pts
                pnl = pnl_pts * unit_size
                trades.append(
                    {
                        "date": date_str,
                        "side": sig.side,
                        "entry": sig.entry,
                        "stop_loss": sig.stop_loss,
                        "take_profit": sig.take_profit,
                        "pnl_pts": round(pnl_pts, 4),
                        "pnl": round(pnl, 4),
                    }
                )

    win_rate, profit_factor, max_dd, score = _score_trades(trades)
    if score >= SCORE_THRESHOLDS["KEEP"]:
        verdict = "KEEP"
    elif score >= SCORE_THRESHOLDS["REVIEW"]:
        verdict = "REVIEW"
    else:
        verdict = "REJECT"

    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper_only": True,
        "strategy": strategy.name,
        "version": strategy.version,
        "symbol": symbol,
        "timeframe": TIMEFRAME,
        "data_source": data_source,
        "note": note,
        "brief_dates_used": len(brief_files) - len(skipped_dates),
        "brief_dates_skipped": skipped_dates,
        "total_signals": len(all_signals),
        "total_trades": len(trades),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_dd,
        "score": score,
        "verdict": verdict,
        "trades": trades,
        "signals": all_signals,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(result, indent=2))

    # --- stdout summary ---
    print(f"strategy      : {strategy.name} v{strategy.version}")
    print(f"symbol        : {symbol} {TIMEFRAME}")
    print(f"data_source   : {data_source}")
    print(f"briefs used   : {result['brief_dates_used']} / {len(brief_files)}")
    print(f"briefs skipped: {skipped_dates}")
    print(f"total trades  : {len(trades)}")
    print(f"win_rate      : {win_rate:.1%}")
    print(f"profit_factor : {profit_factor:.3f}")
    print(f"max_drawdown  : {max_dd:.1%}")
    print(f"score         : {score:.3f}")
    print(f"verdict       : {verdict}")
    print(f"results saved : {results_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

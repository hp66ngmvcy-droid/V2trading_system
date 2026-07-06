"""TPBR_v1 — Trend Pullback Breakout Retest.

Debate consensus (Claude + OpenRouter Gemma, 2026-06-21):
- After London open breakout, price retests the broken swing high before resuming
- Entry: pullback to prior swing high (now support) + ATR buffer confirmation
- Direction filter: D1 trend only (uptrend bias for gold 2022-2026)
- Stop: 1.5× ATR below retest candle low
- Target: 2.5× ATR from entry (R:R ~1.67)
- Session: 08:00-15:30 UTC (London + NY overlap)
- No VWAP — tick-volume proxy on MT5 is brittle
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal


def _f(val, default=0.0):
    return float(val) if val is not None and not pd.isna(val) else float(default)


@dataclass
class TpbrV1:
    # Swing high lookback for breakout level (bars)
    swing_lookback: int = 8
    # Pullback: price must retrace within this fraction of ATR above swing high
    retest_band_atr: float = 0.50
    # Confirmation: close must be above swing_high - retest_band for BUY
    confirm_atr: float = 0.20
    # Stop: ATR multiple below retest low
    stop_atr_mult: float = 1.5
    # Target: ATR multiple from entry
    target_atr_mult: float = 2.5
    # Session window UTC
    entry_start_hour: int = 8
    entry_end_hour: int = 16
    # ATR cap — skip extreme volatility
    atr_cap: float = 15.0
    # Minimum ATR to avoid flat/dead markets
    atr_min: float = 2.0

    name: str = "tpbr_v1"
    version: str = "0.1.0"

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        entry = float(row["close"])
        atr = _f(row.get("atr"))
        base = {
            "timestamp": pd.Timestamp(row["timestamp"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {"regime": regime},
        }

        # ATR filters
        if atr <= 0 or atr < self.atr_min:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        if self.atr_cap > 0 and atr > self.atr_cap:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.ATR_TOO_HIGH_EXTREME_VOLATILITY, **base)

        # Session filter
        hour = int(_f(row.get("hour_utc"), 12))
        if not (self.entry_start_hour <= hour < self.entry_end_hour):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SESSION_FILTER_BLOCK, **base)

        # Require trending regime (gold structural uptrend 2022-2026)
        if regime not in ("TRENDING", "uptrend", "neutral"):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        # Prior swing high = rolling high over lookback bars (excluding current)
        prior_high = _f(row.get("prior_rolling_high"), 0)
        if prior_high <= 0:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        # BUY: price has pulled back to retest prior swing high (now support)
        # Entry zone: within retest_band_atr × ATR above prior_high
        retest_upper = prior_high + self.retest_band_atr * atr
        retest_lower = prior_high - self.retest_band_atr * atr

        if retest_lower <= entry <= retest_upper:
            # Confirm close is above prior_high - confirm_atr×ATR (not deep below)
            if entry >= prior_high - self.confirm_atr * atr:
                stop = entry - self.stop_atr_mult * atr
                take_profit = entry + self.target_atr_mult * atr
                confidence = min(0.82, 0.62 + (atr / max(self.atr_cap, 1)) * 0.15)
                return Signal(
                    side="BUY",
                    confidence=confidence,
                    stop_loss=stop,
                    take_profit=take_profit,
                    reason_code=rc.SIGNAL_BUY,
                    **base,
                )

        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                     reason_code=rc.SIGNAL_HOLD, **base)

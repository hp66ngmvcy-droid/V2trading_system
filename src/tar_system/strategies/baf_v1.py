"""BAF_v1 — 4H false breakout fade strategy."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal


def _f(val, default=0.0):
    return float(val) if val is not None and not pd.isna(val) else float(default)


@dataclass
class BafV1:
    # 4H window = 16 M15 bars
    lookback_bars: int = 16
    breakout_atr_mult: float = 0.3
    stop_atr_mult: float = 1.5
    rsi_low: float = 40.0
    rsi_high: float = 60.0
    atr_spike_floor: float = 0.4
    atr_spike_ceil: float = 2.5
    reward_risk: float = 1.5
    session_start: int = 7
    session_end: int = 19

    name: str = "baf_v1"
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

        # Session filter
        hour = int(_f(row.get("hour_utc"), 12))
        if not (self.session_start <= hour < self.session_end):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SESSION_FILTER_BLOCK, **base)

        # ATR spike filter vs median
        atr_median = _f(row.get("atr_median_50"), atr)
        if atr_median > 0:
            spike_ratio = atr / atr_median if atr > 0 else 0
            if spike_ratio < self.atr_spike_floor or spike_ratio > self.atr_spike_ceil:
                return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                             reason_code=rc.ATR_TOO_LOW_COMPRESSION if spike_ratio < self.atr_spike_floor
                             else rc.ATR_TOO_HIGH_EXTREME_VOLATILITY, **base)

        # Block during trending — false breakouts only work in consolidation
        if regime in {"TRENDING"}:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.REGIME_FILTER_BLOCK, **base)

        rsi = _f(row.get("rsi"), 50)
        # RSI must be neutral — not already overbought/oversold
        if not (self.rsi_low <= rsi <= self.rsi_high):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        prior_high = _f(row.get("prior_rolling_high"), 0)
        prior_low = _f(row.get("prior_rolling_low"), 0)
        bar_high = _f(row.get("high"), entry)
        bar_low = _f(row.get("low"), entry)

        if prior_high <= 0 or prior_low <= 0:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        stop_distance = atr * self.stop_atr_mult if atr > 0 else entry * 0.005
        confidence = min(0.88, 0.60 + abs(rsi - 50) / 200)

        # False breakout: bar high probed above prior range, close rejected back below
        if bar_high > prior_high and entry < prior_high - atr * self.breakout_atr_mult:
            return Signal(
                side="SELL",
                confidence=confidence,
                stop_loss=entry + stop_distance,
                take_profit=entry - stop_distance * self.reward_risk,
                reason_code=rc.SIGNAL_SELL,
                **base,
            )

        # False breakdown: bar low probed below prior range, close rejected back above
        if bar_low < prior_low and entry > prior_low + atr * self.breakout_atr_mult:
            return Signal(
                side="BUY",
                confidence=confidence,
                stop_loss=entry - stop_distance,
                take_profit=entry + stop_distance * self.reward_risk,
                reason_code=rc.SIGNAL_BUY,
                **base,
            )

        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                     reason_code=rc.SIGNAL_HOLD, **base)

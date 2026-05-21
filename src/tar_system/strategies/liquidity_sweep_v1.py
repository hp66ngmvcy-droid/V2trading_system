"""Liquidity sweep paper strategy."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal


@dataclass
class LiquiditySweepV1:
    lookback: int = 20
    wick_ratio: float = 0.45
    reward_risk: float = 2.0
    atr_multiplier: float = 1.2
    min_confidence: float = 0.6
    name: str = "liquidity_sweep_v1"
    version: str = "0.1.0"

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        entry = float(row["close"])
        high = float(row["high"])
        low = float(row["low"])
        open_price = float(row["open"])
        atr = float(row.get("atr", 0) or 0)
        rolling_high = float(row.get("prior_rolling_high", row.get("rolling_high", high)) or high)
        rolling_low = float(row.get("prior_rolling_low", row.get("rolling_low", low)) or low)
        bar_range = max(high - low, 1e-9)
        upper_wick = high - max(open_price, entry)
        lower_wick = min(open_price, entry) - low
        stop_distance = max(atr * self.atr_multiplier, entry * 0.002)
        base = {
            "timestamp": pd.Timestamp(row["timestamp"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {
                "regime": regime,
                "rolling_high": rolling_high,
                "rolling_low": rolling_low,
                "upper_wick_ratio": upper_wick / bar_range,
                "lower_wick_ratio": lower_wick / bar_range,
            },
        }

        swept_low = low < rolling_low and entry > rolling_low and lower_wick / bar_range >= self.wick_ratio
        if swept_low:
            confidence = self._confidence(lower_wick / bar_range, atr, entry)
            return Signal(
                side="BUY",
                confidence=confidence,
                stop_loss=entry - stop_distance,
                take_profit=entry + stop_distance * self.reward_risk,
                reason_code=rc.SIGNAL_BUY,
                **base,
            )

        swept_high = high > rolling_high and entry < rolling_high and upper_wick / bar_range >= self.wick_ratio
        if swept_high:
            confidence = self._confidence(upper_wick / bar_range, atr, entry)
            return Signal(
                side="SELL",
                confidence=confidence,
                stop_loss=entry + stop_distance,
                take_profit=entry - stop_distance * self.reward_risk,
                reason_code=rc.SIGNAL_SELL,
                **base,
            )

        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)

    def _confidence(self, wick_strength: float, atr: float, entry: float) -> float:
        atr_component = min(max((atr / max(entry, 1e-9)) * 100, 0.0), 0.2)
        return min(0.9, max(self.min_confidence, self.min_confidence + (wick_strength - self.wick_ratio) * 0.5 + atr_component))

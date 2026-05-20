"""Gold V2 baseline strategy."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.regime.detector import Regime
from tar_system.strategies.base import Signal


@dataclass
class GoldV2:
    fast_ema: int = 12
    slow_ema: int = 26
    rsi_buy_threshold: float = 55
    rsi_sell_threshold: float = 45
    atr_multiplier: float = 1.5
    reward_risk: float = 2.0
    session_filter: bool = True
    atr_floor_multiplier: float = 0.5
    atr_ceil_multiplier: float = 3.0
    ema_slope_threshold: float = 0.0002

    name: str = "gold_v2"
    version: str = "0.1.0"

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        entry = float(row["close"])
        atr = float(row.get("atr", 0) or 0)
        base = {
            "timestamp": pd.Timestamp(row["timestamp"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {"regime": regime},
        }
        if self.session_filter and _session_blocked(row):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SESSION_FILTER_BLOCK, **base)
        if regime not in {Regime.TRENDING.value, "TRENDING"}:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)
        ema_fast = float(row.get("ema_fast", 0) or 0)
        ema_slow = float(row.get("ema_slow", 0) or 0)
        ema_fast_slope = float(row.get("ema_fast_slope", 0) or 0)
        ema_slow_slope = float(row.get("ema_slow_slope", 0) or 0)
        rsi = float(row.get("rsi", 50) or 50)
        atr_median = float(row.get("atr_median_50", atr) or 0)
        if atr_median > 0 and atr < self.atr_floor_multiplier * atr_median:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.ATR_TOO_LOW_COMPRESSION, **base)
        if atr_median > 0 and atr > self.atr_ceil_multiplier * atr_median:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.ATR_TOO_HIGH_EXTREME_VOLATILITY, **base)
        confidence = min(0.95, 0.55 + abs(ema_fast - ema_slow) / entry * 20 + abs(rsi - 50) / 100)
        stop_distance = atr * self.atr_multiplier if atr > 0 else entry * 0.005
        if ema_fast > ema_slow and rsi >= self.rsi_buy_threshold:
            if ema_fast_slope <= self.ema_slope_threshold or ema_slow_slope <= 0:
                return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.EMA_SLOPE_TOO_FLAT, **base)
            return Signal(
                side="BUY",
                confidence=confidence,
                stop_loss=entry - stop_distance,
                take_profit=entry + stop_distance * self.reward_risk,
                reason_code=rc.SIGNAL_BUY,
                **base,
            )
        if ema_fast < ema_slow and rsi <= self.rsi_sell_threshold:
            if ema_fast_slope >= -self.ema_slope_threshold or ema_slow_slope >= 0:
                return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.EMA_SLOPE_TOO_FLAT, **base)
            return Signal(
                side="SELL",
                confidence=confidence,
                stop_loss=entry + stop_distance,
                take_profit=entry - stop_distance * self.reward_risk,
                reason_code=rc.SIGNAL_SELL,
                **base,
            )
        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)


def _session_blocked(row: pd.Series) -> bool:
    if "is_liquid_session" in row.index:
        value = row.get("is_liquid_session", True)
        if isinstance(value, str):
            return value.strip().lower() in {"false", "0", "no", "off"}
        return not bool(value)
    if "hour_utc" in row.index:
        hour = int(float(row.get("hour_utc", 0) or 0))
        return not (7 <= hour < 20)
    return False

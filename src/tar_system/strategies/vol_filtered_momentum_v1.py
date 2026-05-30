"""Volatility-filtered EMA momentum strategy."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.regime.detector import Regime
from tar_system.strategies.base import Signal


@dataclass
class VolFilteredMomentumV1:
    min_body_atr: float = 0.20
    atr_floor_multiplier: float = 0.55
    atr_ceil_multiplier: float = 2.75
    ema_slope_threshold: float = 0.00015
    rsi_buy_threshold: float = 54.0
    rsi_sell_threshold: float = 46.0
    atr_multiplier: float = 2.0
    reward_risk: float = 2.5
    session_filter: bool = True

    name: str = "vol_filtered_momentum_v1"
    version: str = "0.1.0"

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        entry = float(row["close"])
        open_price = float(row.get("open", entry) or entry)
        atr = float(row.get("atr", 0) or 0)
        atr_median = float(row.get("atr_median_50", atr) or atr)
        ema_fast = float(row.get("ema_fast", entry) or entry)
        ema_slow = float(row.get("ema_slow", entry) or entry)
        ema_fast_slope = float(row.get("ema_fast_slope", 0) or 0)
        ema_slow_slope = float(row.get("ema_slow_slope", 0) or 0)
        rsi = float(row.get("rsi", 50) or 50)
        body_atr = abs(entry - open_price) / atr if atr > 0 else 0.0
        stop_distance = atr * self.atr_multiplier if atr > 0 else entry * 0.01
        confidence = min(0.95, 0.50 + abs(ema_fast - ema_slow) / max(entry, 1e-9) * 25 + abs(rsi - 50) / 100)
        base = {
            "timestamp": pd.Timestamp(row["timestamp"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {
                "regime": regime,
                "body_atr": round(body_atr, 4),
                "atr_to_median": round(atr / atr_median, 4) if atr_median > 0 else None,
                "rsi": rsi,
                "ema_fast_slope": ema_fast_slope,
                "ema_slow_slope": ema_slow_slope,
            },
        }

        if self.session_filter and _session_blocked(row):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SESSION_FILTER_BLOCK, **base)
        if regime in {Regime.VOLATILE.value, "VOLATILE"}:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.VOLATILE_REGIME_BLOCK, **base)
        if regime not in {Regime.TRENDING.value, "TRENDING", Regime.UNKNOWN.value, "UNKNOWN"}:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.REGIME_FILTER_BLOCK, **base)
        if atr_median > 0 and atr < self.atr_floor_multiplier * atr_median:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.ATR_TOO_LOW_COMPRESSION, **base)
        if atr_median > 0 and atr > self.atr_ceil_multiplier * atr_median:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.ATR_TOO_HIGH_EXTREME_VOLATILITY, **base)
        if body_atr < self.min_body_atr:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.EMA_SLOPE_TOO_FLAT, **base)

        if ema_fast > ema_slow and ema_fast_slope > self.ema_slope_threshold and ema_slow_slope >= 0 and rsi >= self.rsi_buy_threshold:
            return Signal(
                side="BUY",
                confidence=confidence,
                stop_loss=entry - stop_distance,
                take_profit=entry + stop_distance * self.reward_risk,
                reason_code=rc.SIGNAL_BUY,
                **base,
            )
        if ema_fast < ema_slow and ema_fast_slope < -self.ema_slope_threshold and ema_slow_slope <= 0 and rsi <= self.rsi_sell_threshold:
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

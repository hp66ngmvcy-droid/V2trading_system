"""RSI and Bollinger mean-reversion strategy for ranging markets."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.regime.detector import Regime
from tar_system.strategies.base import Signal


@dataclass
class RsiReversionV1:
    rsi_period: int = 14
    oversold: float = 30
    overbought: float = 70
    bb_period: int = 20
    session_filter: bool = True
    atr_multiplier: float = 1.2
    reward_risk: float = 1.2

    name: str = "rsi_reversion_v1"
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
            "metadata": {"regime": regime, "bb_period": self.bb_period, "rsi_period": self.rsi_period},
        }
        if self.session_filter and _session_blocked(row):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SESSION_FILTER_BLOCK, **base)
        if regime not in {Regime.RANGING.value, "RANGING"}:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.REGIME_FILTER_BLOCK, **base)

        rsi = float(row.get("rsi", 50) or 50)
        price_in_band = float(row.get("price_in_band", 0.5) or 0.5)
        stop_distance = atr * self.atr_multiplier if atr > 0 else entry * 0.004
        confidence = min(0.92, 0.58 + abs(50 - rsi) / 100 + abs(0.5 - price_in_band) / 2)

        if rsi < self.oversold and price_in_band < 0.2:
            return Signal(
                side="BUY",
                confidence=confidence,
                stop_loss=entry - stop_distance,
                take_profit=entry + stop_distance * self.reward_risk,
                reason_code=rc.SIGNAL_BUY,
                **base,
            )
        if rsi > self.overbought and price_in_band > 0.8:
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

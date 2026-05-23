"""RSI + EMA Trend + Session Filter Strategy v4."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal


@dataclass
class RSITrendV4:
    rsi_period: int = 14
    rsi_buy_level: float = 35
    rsi_sell_level: float = 65
    atr_multiplier: float = 2.0
    reward_risk: float = 3.0
    liquid_sessions_only: bool = True
    name: str = "rsi_trend_v4"
    version: str = "0.4.0"

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        entry = float(row["close"])
        atr = float(row.get("atr", 0) or 0)
        rsi = float(row.get("rsi", 50) or 50)
        ema_slope = float(row.get("ema_fast_slope", 0) or 0)
        liquid = bool(row.get("is_liquid_session", True))

        base = {
            "timestamp": pd.Timestamp(row["timestamp"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {"regime": regime, "rsi": rsi, "ema_slope": ema_slope},
        }

        hold = Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                      reason_code=rc.SIGNAL_HOLD, **base)

        if self.liquid_sessions_only and not liquid:
            return hold

        confidence = min(0.95, 0.5 + abs(rsi - 50) / 100)
        stop_distance = atr * self.atr_multiplier if atr > 0 else entry * 0.01

        if rsi <= self.rsi_buy_level and ema_slope > 0:
            return Signal(side="BUY", confidence=confidence,
                          stop_loss=entry - stop_distance,
                          take_profit=entry + stop_distance * self.reward_risk,
                          reason_code=rc.SIGNAL_BUY, **base)

        if rsi >= self.rsi_sell_level and ema_slope < 0:
            return Signal(side="SELL", confidence=confidence,
                          stop_loss=entry + stop_distance,
                          take_profit=entry - stop_distance * self.reward_risk,
                          reason_code=rc.SIGNAL_SELL, **base)

        return hold

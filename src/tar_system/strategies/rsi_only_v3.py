"""RSI-Only Strategy"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal

@dataclass
class RSIOnlyV3:
    rsi_period: int = 14
    rsi_buy_level: float = 40
    rsi_sell_level: float = 60
    atr_multiplier: float = 1.5
    reward_risk: float = 2.0
    name: str = "rsi_only_v3"
    version: str = "0.3.0"
    
    def generate_signal(self, row: pd.Series, regime: str):
        from tar_system.strategies.base import Signal
        entry = float(row["close"])
        atr = float(row.get("atr", 0) or 0)
        rsi = float(row.get("rsi", 50) or 50)
        
        base = {
            "timestamp": pd.Timestamp(row["timestamp"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {"regime": regime, "rsi": rsi},
        }
        
        confidence = min(0.95, 0.5 + abs(rsi - 50) / 100)
        stop_distance = atr * self.atr_multiplier if atr > 0 else entry * 0.005
        
        if rsi <= self.rsi_buy_level:
            return Signal(side="BUY", confidence=confidence, stop_loss=entry - stop_distance, take_profit=entry + stop_distance * self.reward_risk, reason_code=rc.SIGNAL_BUY, **base)

        if rsi >= self.rsi_sell_level:
            return Signal(side="SELL", confidence=confidence, stop_loss=entry + stop_distance, take_profit=entry - stop_distance * self.reward_risk, reason_code=rc.SIGNAL_SELL, **base)
        
        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)

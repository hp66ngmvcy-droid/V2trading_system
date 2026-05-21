"""ATR Breakout Strategy - Phase 3 Variant 3"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal

@dataclass
class ATRBreakoutV3:
    lookback: int = 20
    atr_multiplier: float = 2.0
    reward_risk: float = 2.5
    name: str = "atr_breakout_v3"
    version: str = "0.3.0"
    
    def generate_signal(self, row: pd.Series, regime: str):
        from tar_system.strategies.base import Signal
        entry = float(row["close"])
        atr = float(row.get("atr", 0) or 0)
        high_20 = float(row.get("rolling_high", entry) or entry)
        low_20 = float(row.get("rolling_low", entry) or entry)
        atr_median = float(row.get("atr_median_50", atr) or atr)
        
        base = {
            "timestamp": pd.Timestamp(row["timestamp"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {"regime": regime, "atr": atr},
        }
        
        confidence = 0.7 if atr > atr_median else 0.5
        stop_distance = atr * self.atr_multiplier if atr > 0 else entry * 0.01
        
        # BUY: Breakout above 20-bar high with elevated ATR
        if entry > high_20 and atr > atr_median:
            return Signal(side="BUY", confidence=confidence, stop_loss=entry - stop_distance, take_profit=entry + stop_distance * self.reward_risk, reason_code=rc.SIGNAL_BUY, **base)
        
        # SELL: Breakdown below 20-bar low with elevated ATR
        if entry < low_20 and atr > atr_median:
            return Signal(side="SELL", confidence=confidence, stop_loss=entry + stop_distance, take_profit=entry - stop_distance * self.reward_risk, reason_code=rc.SIGNAL_SELL, **base)
        
        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)

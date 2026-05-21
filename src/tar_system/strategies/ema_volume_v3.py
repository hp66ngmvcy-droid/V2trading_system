"""EMA+Volume Strategy - Phase 3 Variant 2"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal

@dataclass
class EMAVolumeV3:
    fast_ema: int = 12
    slow_ema: int = 26
    volume_multiplier: float = 1.5
    atr_multiplier: float = 1.5
    reward_risk: float = 2.0
    name: str = "ema_volume_v3"
    version: str = "0.3.0"
    
    def generate_signal(self, row: pd.Series, regime: str):
        from tar_system.strategies.base import Signal
        entry = float(row["close"])
        atr = float(row.get("atr", 0) or 0)
        ema_fast = float(row.get("ema_fast", 0) or 0)
        ema_slow = float(row.get("ema_slow", 0) or 0)
        volume = float(row.get("volume", 0) or 0)
        volume_sma = float(row.get("volume", 1) or 1)
        
        base = {
            "timestamp": pd.Timestamp(row["timestamp"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {"regime": regime},
        }
        
        confidence = min(0.95, 0.6 + abs(ema_fast - ema_slow) / entry * 20)
        stop_distance = atr * self.atr_multiplier if atr > 0 else entry * 0.005
        volume_confirmed = volume > (volume_sma * self.volume_multiplier)
        
        if ema_fast > ema_slow and volume_confirmed:
            return Signal(side="BUY", confidence=confidence, stop_loss=entry - stop_distance, take_profit=entry + stop_distance * self.reward_risk, reason_code=rc.SIGNAL_BUY, **base)
        
        if ema_fast < ema_slow and volume_confirmed:
            return Signal(side="SELL", confidence=confidence, stop_loss=entry + stop_distance, take_profit=entry - stop_distance * self.reward_risk, reason_code=rc.SIGNAL_SELL, **base)
        
        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)

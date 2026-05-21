"""EMA+Volume Strategy - FIXED"""
from dataclasses import dataclass
import pandas as pd
from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal

@dataclass
class EMAVolumeFixed:
    name: str = "ema_volume_fixed"
    version: str = "0.3.1"
    
    def generate_signal(self, row: pd.Series, regime: str):
        entry = float(row["close"])
        ema_fast = float(row.get("ema_fast", 0) or 0)
        ema_slow = float(row.get("ema_slow", 0) or 0)
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
        
        stop_distance = atr * 1.5 if atr > 0 else entry * 0.01
        
        if ema_fast > ema_slow:
            return Signal(side="BUY", confidence=0.7, stop_loss=entry - stop_distance, 
                         take_profit=entry + stop_distance * 2.0, reason_code=rc.SIGNAL_BUY, **base)
        
        if ema_fast < ema_slow:
            return Signal(side="SELL", confidence=0.7, stop_loss=entry + stop_distance,
                         take_profit=entry - stop_distance * 2.0, reason_code=rc.SIGNAL_SELL, **base)
        
        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)
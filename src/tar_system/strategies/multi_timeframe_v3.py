"""Multi-Timeframe Strategy - Phase 3 Variant 5"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal

@dataclass
class MultiTimeframeV3:
    fast_ema: int = 12
    slow_ema: int = 26
    rsi_buy: int = 40
    rsi_sell: int = 60
    atr_multiplier: float = 1.5
    reward_risk: float = 2.0
    name: str = "multi_timeframe_v3"
    version: str = "0.3.0"
    
    def generate_signal(self, row: pd.Series, regime: str):
        from tar_system.strategies.base import Signal
        entry = float(row["close"])
        atr = float(row.get("atr", 0) or 0)
        ema_fast = float(row.get("ema_fast", 0) or 0)
        ema_slow = float(row.get("ema_slow", 0) or 0)
        rsi = float(row.get("rsi", 50) or 50)
        
        base = {
            "timestamp": pd.Timestamp(row["timestamp"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {"regime": regime, "ema_cross": ema_fast > ema_slow},
        }
        
        confidence = 0.7
        stop_distance = atr * self.atr_multiplier if atr > 0 else entry * 0.005
        
        # BUY: EMA cross + RSI confirmation (oversold recovery)
        if ema_fast > ema_slow and rsi >= self.rsi_buy and rsi <= 70:
            return Signal(side="BUY", confidence=confidence, stop_loss=entry - stop_distance, take_profit=entry + stop_distance * self.reward_risk, reason_code=rc.SIGNAL_BUY, **base)
        
        # SELL: EMA cross + RSI confirmation (overbought pullback)
        if ema_fast < ema_slow and rsi <= self.rsi_sell and rsi >= 30:
            return Signal(side="SELL", confidence=confidence, stop_loss=entry + stop_distance, take_profit=entry - stop_distance * self.reward_risk, reason_code=rc.SIGNAL_SELL, **base)
        
        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)

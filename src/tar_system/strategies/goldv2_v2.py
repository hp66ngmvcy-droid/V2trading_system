"""GoldV2 V2 - Refined Strategy"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal

@dataclass
class GoldV2V2:
    fast_ema: int = 12
    slow_ema: int = 26
    rsi_buy_threshold: float = 50
    rsi_sell_threshold: float = 50
    atr_multiplier: float = 1.5
    reward_risk: float = 2.0
    name: str = "goldv2_v2"
    version: str = "0.2.0"
    
    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
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
            "metadata": {"regime": regime},
        }
        
        confidence = min(0.95, 0.55 + abs(ema_fast - ema_slow) / entry * 20)
        stop_distance = atr * self.atr_multiplier if atr > 0 else entry * 0.005
        
        # BUY: Fast EMA > Slow EMA + RSI > 50
        if ema_fast > ema_slow and rsi >= self.rsi_buy_threshold:
            return Signal(
                side="BUY",
                confidence=confidence,
                stop_loss=entry - stop_distance,
                take_profit=entry + stop_distance * self.reward_risk,
                reason_code=rc.SIGNAL_BUY,
                **base,
            )
        
        # SELL: Fast EMA < Slow EMA + RSI < 50
        if ema_fast < ema_slow and rsi <= self.rsi_sell_threshold:
            return Signal(
                side="SELL",
                confidence=confidence,
                stop_loss=entry + stop_distance,
                take_profit=entry - stop_distance * self.reward_risk,
                reason_code=rc.SIGNAL_SELL,
                **base,
            )
        
        # HOLD
        return Signal(
            side="HOLD",
            confidence=0.0,
            stop_loss=None,
            take_profit=None,
            reason_code=rc.SIGNAL_HOLD,
            **base,
        )

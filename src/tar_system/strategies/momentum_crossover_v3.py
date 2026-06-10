"""Momentum Crossover Strategy - Phase 3 Variant 4"""
from __future__ import annotations
from dataclasses import dataclass, field
import pandas as pd
from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal

@dataclass
class MomentumCrossoverV3:
    fast_period: int = 10
    slow_period: int = 20
    atr_multiplier: float = 1.5
    reward_risk: float = 2.0
    entry_threshold: float = 0.0
    min_hold_bars: int = 0
    name: str = "momentum_crossover_v3"
    version: str = "0.3.0"
    _last_entry_index: int = field(default=-10**9, init=False, repr=False)
    
    def generate_signal(self, row: pd.Series, regime: str):
        from tar_system.strategies.base import Signal
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
        
        confidence = 0.65
        stop_distance = atr * self.atr_multiplier if atr > 0 else entry * 0.005
        
        # Simple momentum: close above/below EMA(20)
        ema_20 = float(row.get("ema_slow", entry) or entry)
        
        row_index = row.name if isinstance(row.name, int) else None
        if row_index is not None and row_index <= self._last_entry_index:
            self._last_entry_index = -10**9
        if row_index is not None and self.min_hold_bars > 0 and row_index - self._last_entry_index < self.min_hold_bars:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)

        # BUY: Price > EMA(20) and RSI > 50 (upward momentum)
        rsi = float(row.get("rsi", 50) or 50)
        if abs(rsi - 50.0) < self.entry_threshold:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)
        if entry > ema_20 and rsi > 50:
            if row_index is not None:
                self._last_entry_index = row_index
            return Signal(side="BUY", confidence=confidence, stop_loss=entry - stop_distance, take_profit=entry + stop_distance * self.reward_risk, reason_code=rc.SIGNAL_BUY, **base)
        
        # SELL: Price < EMA(20) and RSI < 50 (downward momentum)
        if entry < ema_20 and rsi < 50:
            if row_index is not None:
                self._last_entry_index = row_index
            return Signal(side="SELL", confidence=confidence, stop_loss=entry + stop_distance, take_profit=entry - stop_distance * self.reward_risk, reason_code=rc.SIGNAL_SELL, **base)
        
        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)

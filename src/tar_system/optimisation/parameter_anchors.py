"""Research-validated starting anchors for controlled parameter tests."""

from __future__ import annotations

GOLD_V2_ANCHORS = [
    {"fast_ema": 8, "slow_ema": 21, "rsi_period": 14, "rsi_threshold": 55, "note": "8/21 most cited M15 Gold"},
    {"fast_ema": 9, "slow_ema": 21, "rsi_period": 14, "rsi_threshold": 55, "note": "9/21 classic short-term"},
    {"fast_ema": 12, "slow_ema": 26, "rsi_period": 14, "rsi_threshold": 55, "note": "12/26 MACD default"},
    {"fast_ema": 13, "slow_ema": 34, "rsi_period": 14, "rsi_threshold": 50, "note": "13/34 Fibonacci-based"},
    {"fast_ema": 14, "slow_ema": 21, "rsi_period": 14, "rsi_threshold": 55, "note": "14/21 validated Gold 5yr"},
    {"fast_ema": 10, "slow_ema": 50, "rsi_period": 14, "rsi_threshold": 55, "note": "10/50 medium-term trend"},
]

RSI_REVERSION_ANCHORS = [
    {"rsi_period": 14, "oversold": 30, "overbought": 70, "bb_period": 20, "note": "Wilder default, most published"},
    {"rsi_period": 9, "oversold": 28, "overbought": 72, "bb_period": 20, "note": "faster signal for M15"},
    {"rsi_period": 14, "oversold": 25, "overbought": 75, "bb_period": 14, "note": "wider extremes"},
    {"rsi_period": 21, "oversold": 30, "overbought": 70, "bb_period": 25, "note": "smoother signal"},
]

ATR_GATE_ANCHORS = [
    {"atr_floor_multiplier": 0.5, "atr_ceil_multiplier": 3.0, "note": "standard balanced gate"},
    {"atr_floor_multiplier": 0.7, "atr_ceil_multiplier": 2.5, "note": "tighter volatility band"},
    {"atr_floor_multiplier": 0.3, "atr_ceil_multiplier": 4.0, "note": "wider allows more signals"},
]

ATR_STOP_ANCHORS = {
    "XAUUSD": {"atr_period": 14, "atr_multiplier": 2.0, "note": "2 ATR standard Gold stop"},
    "EURUSD": {"atr_period": 14, "atr_multiplier": 1.5},
    "GBPUSD": {"atr_period": 14, "atr_multiplier": 1.5},
    "USDJPY": {"atr_period": 14, "atr_multiplier": 1.5},
    "USDCAD": {"atr_period": 14, "atr_multiplier": 1.5},
    "AUDUSD": {"atr_period": 14, "atr_multiplier": 1.5},
    "BTCUSD": {"atr_period": 14, "atr_multiplier": 3.0, "note": "wider stop for crypto volatility"},
    "USOUSD": {"atr_period": 14, "atr_multiplier": 2.5},
}

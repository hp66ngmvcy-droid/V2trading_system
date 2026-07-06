"""LSMR_v1 — London Session Mean Reversion (07:00-07:45 UTC window)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal


def _f(val, default=0.0):
    return float(val) if val is not None and not pd.isna(val) else float(default)


@dataclass
class LsmrV1:
    # Debate: narrow window — 07:00-07:45 only
    session_start: int = 7
    session_end: int = 8   # bars starting at 07:xx only (M15: 07:00, 07:15, 07:30, 07:45)
    spike_atr_mult: float = 1.5
    rsi_overbought: float = 65.0
    rsi_oversold: float = 35.0
    stop_atr_mult: float = 1.5
    reward_risk: float = 2.0

    name: str = "lsmr_v1"
    version: str = "0.1.0"

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        entry = float(row["close"])
        atr = _f(row.get("atr"))
        base = {
            "timestamp": pd.Timestamp(row["timestamp"]),
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {"regime": regime},
        }

        # London open window only — debate tightened to 07:00-07:45
        hour = int(_f(row.get("hour_utc"), 12))
        if not (self.session_start <= hour < self.session_end):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SESSION_FILTER_BLOCK, **base)

        # London spike reversion — only valid in volatile/ranging, not clean trends
        if regime in {"TRENDING"}:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.REGIME_FILTER_BLOCK, **base)

        if atr <= 0:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.ATR_TOO_LOW_COMPRESSION, **base)

        ema_fast = _f(row.get("ema_fast"), entry)
        rsi = _f(row.get("rsi"), 50)
        spike_threshold = atr * self.spike_atr_mult
        stop_distance = atr * self.stop_atr_mult
        confidence = min(0.85, 0.58 + abs(rsi - 50) / 100)

        min_target = stop_distance * self.reward_risk

        # Spike above EMA + overbought RSI → SELL
        if entry > ema_fast + spike_threshold and rsi >= self.rsi_overbought:
            tp = entry - max(min_target, entry - ema_fast)
            return Signal(
                side="SELL",
                confidence=confidence,
                stop_loss=entry + stop_distance,
                take_profit=tp,
                reason_code=rc.SIGNAL_SELL,
                **base,
            )

        # Spike below EMA + oversold RSI → BUY
        if entry < ema_fast - spike_threshold and rsi <= self.rsi_oversold:
            tp = entry + max(min_target, ema_fast - entry)
            return Signal(
                side="BUY",
                confidence=confidence,
                stop_loss=entry - stop_distance,
                take_profit=tp,
                reason_code=rc.SIGNAL_BUY,
                **base,
            )

        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                     reason_code=rc.SIGNAL_HOLD, **base)

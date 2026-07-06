"""VWMR_v1 — Volatility-weighted Bollinger Band mean reversion."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal


def _f(val, default=0.0):
    return float(val) if val is not None and not pd.isna(val) else float(default)


@dataclass
class VwmrV1:
    spike_ratio_floor: float = 2.0
    spike_ratio_ceil: float = 2.8   # debate: cap here, above = trend-continuation risk
    stop_atr_mult: float = 1.5
    reward_risk: float = 2.0
    session_filter: bool = True
    buy_only: bool = True  # trend-aligned: only buy dips below BB lower

    name: str = "vwmr_v1"
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

        if self.session_filter:
            hour = int(_f(row.get("hour_utc"), 12))
            if not (7 <= hour < 20):
                return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                             reason_code=rc.SESSION_FILTER_BLOCK, **base)

        # Block during trending — mean reversion only in ranging/volatile
        if regime in {"TRENDING"}:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.REGIME_FILTER_BLOCK, **base)

        atr_median = _f(row.get("atr_median_50"), atr)
        if atr_median <= 0 or atr <= 0:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.ATR_TOO_LOW_COMPRESSION, **base)

        spike_ratio = atr / atr_median
        if spike_ratio < self.spike_ratio_floor:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.ATR_TOO_LOW_COMPRESSION, **base)
        if spike_ratio > self.spike_ratio_ceil:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.ATR_TOO_HIGH_EXTREME_VOLATILITY, **base)

        bb_upper = _f(row.get("bollinger_upper"), 0)
        bb_lower = _f(row.get("bollinger_lower"), 0)
        bb_mid = _f(row.get("bollinger_mid"), entry)

        if bb_upper <= 0 or bb_lower <= 0:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        stop_distance = atr * self.stop_atr_mult
        # Inverted sizing: bigger spike = smaller size (debate consensus)
        size_factor = 1.2 if spike_ratio <= 2.0 else (1.0 if spike_ratio <= 2.5 else 0.8)
        confidence = min(0.90, 0.58 + (spike_ratio - self.spike_ratio_floor) / 4) * size_factor

        min_target = stop_distance * self.reward_risk

        if not self.buy_only and entry > bb_upper:
            tp = entry - max(min_target, entry - bb_mid)
            return Signal(
                side="SELL",
                confidence=confidence,
                stop_loss=entry + stop_distance,
                take_profit=tp,
                reason_code=rc.SIGNAL_SELL,
                **base,
            )

        if entry < bb_lower:
            tp = entry + max(min_target, bb_mid - entry)
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

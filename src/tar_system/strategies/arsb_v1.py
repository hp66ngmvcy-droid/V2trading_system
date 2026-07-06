"""ARSB_v1 — Asian Range Session Breakout.

Debate consensus (Claude + OpenRouter Gemma, 2026-06-18):
- Asian session 01:00-06:45 UTC builds a compression box
- London open (07:00-09:30 UTC) trades the breakout of that box
- Stop: Asian range midpoint
- Filter: Asian range must be compressed relative to 24h ATR

Uses 24-bar rolling high/low (6 hours of M15) as Asian box proxy.
Entry only valid at London open hour (07:00-09:30 UTC).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal


def _f(val, default=0.0):
    return float(val) if val is not None and not pd.isna(val) else float(default)


@dataclass
class ArsbV1:
    # Asian box: prior 24 M15 bars ≈ 6 hours (01:00-06:45 UTC proxy)
    asian_lookback: int = 24
    # Compression: Asian range < compression_atr_mult × M15 ATR — selects ~p25 compressed sessions
    compression_atr_mult: float = 12.5
    # Box validity: absolute floor only ($6 minimum to avoid noise); ceiling handled by ATR mult above
    range_min_pts: float = 6.0
    range_max_pts: float = 200.0
    # Breakout buffer: range × buffer_mult above/below box
    buffer_mult: float = 0.15
    # Stop: from entry back to Asian midpoint (+ buffer)
    stop_atr_mult: float = 1.0
    # Target: 2× range from breakout
    reward_risk: float = 2.0
    # Entry window: London open only
    entry_start_hour: int = 8   # tuned: 08:00 UTC (London core, skip pre-market)
    entry_end_hour: int = 17   # tuned: close at NY overlap end
    atr_cap: float = 11.97     # tuned: 95th percentile ATR filter

    name: str = "arsb_v1"
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

        # ATR cap filter — skip extreme volatility bars
        if self.atr_cap > 0 and atr > self.atr_cap:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.ATR_TOO_HIGH_EXTREME_VOLATILITY, **base)

        # Session window
        hour = int(_f(row.get("hour_utc"), 12))
        if not (self.entry_start_hour <= hour < self.entry_end_hour):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SESSION_FILTER_BLOCK, **base)

        # Use daily Asian session range (01:00-06:45 UTC) computed in feature engineering
        asian_high = _f(row.get("asian_high"), 0)
        asian_low = _f(row.get("asian_low"), 0)

        if asian_high <= 0 or asian_low <= 0:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        asian_range = _f(row.get("asian_range"), asian_high - asian_low)
        asian_mid = _f(row.get("asian_mid"), (asian_high + asian_low) / 2)

        # Box validity: absolute floor
        if asian_range < self.range_min_pts or asian_range > self.range_max_pts:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        # Compression filter: Asian range must be tight relative to M15 ATR
        if atr > 0 and asian_range > self.compression_atr_mult * atr:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        buffer = asian_range * self.buffer_mult
        breakout_long = asian_high + buffer
        breakout_short = asian_low - buffer

        target_distance = asian_range * self.reward_risk
        confidence = min(0.88, 0.65 + (1 - asian_range / max(self.range_max_pts, 1)) * 0.2)

        # Breakout BUY: close above Asian high + buffer
        if entry > breakout_long:
            stop = asian_mid  # stop at box midpoint
            return Signal(
                side="BUY",
                confidence=confidence,
                stop_loss=stop,
                take_profit=entry + target_distance,
                reason_code=rc.SIGNAL_BUY,
                **base,
            )

        # Breakout SELL: close below Asian low - buffer
        if entry < breakout_short:
            stop = asian_mid
            return Signal(
                side="SELL",
                confidence=confidence,
                stop_loss=stop,
                take_profit=entry - target_distance,
                reason_code=rc.SIGNAL_SELL,
                **base,
            )

        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                     reason_code=rc.SIGNAL_HOLD, **base)

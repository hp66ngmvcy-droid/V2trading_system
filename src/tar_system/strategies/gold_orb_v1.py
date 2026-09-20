"""gold_orb_v1 — Opening Range Breakout for XAUUSD.

Inspired by GOLD_ORB EA (github.com/yulz008/GOLD_ORB).

Key differences from arsb_v1:
- Shorter range window: first 1 hour after market open (01:00-02:00 UTC, 4 M15 bars)
- No compression filter (range tightness not required)
- Stop: opposite edge of ORB (not midpoint)
- Reward:risk 3.0 (vs arsb_v1's 2.0)
- Trades from 06:00 UTC (after consolidation window) through end of NY session

Range formation:
  01:00-02:00 UTC → orb_high, orb_low, orb_range (precomputed in feature engineering)
Entry:
  close > orb_high + buffer → BUY
  close < orb_low  - buffer → SELL
Stop:
  BUY:  stop = orb_low  (opposite edge)
  SELL: stop = orb_high (opposite edge)
TP:
  entry ± orb_range × reward_risk
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal


def _f(val, default=0.0):
    return float(val) if val is not None and not pd.isna(val) else float(default)


@dataclass
class GoldOrbV1:
    # Breakout buffer: range × buffer_mult above/below ORB edges
    buffer_mult: float = 0.10
    # Target: reward_risk × orb_range from entry
    reward_risk: float = 3.0
    # ATR cap: skip bars with extreme volatility
    atr_cap: float = 8.0
    # Minimum ORB range to avoid noise ($)
    range_min_pts: float = 4.0
    # Maximum ORB range (very wide range = low-quality ORB)
    range_max_pts: float = 60.0
    # Session: trade after ORB formation + consolidation, through NY close
    entry_start_hour: int = 6    # UTC — after 4-hour consolidation window
    entry_end_hour: int = 20     # UTC — NY session end

    name: str = "gold_orb_v1"
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

        # ATR cap filter
        if self.atr_cap > 0 and atr > self.atr_cap:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.ATR_TOO_HIGH_EXTREME_VOLATILITY, **base)

        # Session window
        hour = int(_f(row.get("hour_utc"), 12))
        if not (self.entry_start_hour <= hour < self.entry_end_hour):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SESSION_FILTER_BLOCK, **base)

        # ORB values (precomputed in feature engineering)
        orb_high = _f(row.get("orb_high"), 0)
        orb_low = _f(row.get("orb_low"), 0)
        orb_range = _f(row.get("orb_range"), orb_high - orb_low)

        if orb_high <= 0 or orb_low <= 0 or orb_range <= 0:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        # Range validity
        if orb_range < self.range_min_pts or orb_range > self.range_max_pts:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                         reason_code=rc.SIGNAL_HOLD, **base)

        buffer = orb_range * self.buffer_mult
        breakout_long = orb_high + buffer
        breakout_short = orb_low - buffer
        target_dist = orb_range * self.reward_risk

        # Confidence: tighter range = cleaner breakout
        confidence = min(0.85, 0.60 + (1 - orb_range / max(self.range_max_pts, 1)) * 0.25)

        # BUY breakout
        if entry > breakout_long:
            return Signal(
                side="BUY",
                confidence=confidence,
                stop_loss=orb_low,
                take_profit=entry + target_dist,
                reason_code=rc.SIGNAL_BUY,
                **base,
            )

        # SELL breakdown
        if entry < breakout_short:
            return Signal(
                side="SELL",
                confidence=confidence,
                stop_loss=orb_high,
                take_profit=entry - target_dist,
                reason_code=rc.SIGNAL_SELL,
                **base,
            )

        return Signal(side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                     reason_code=rc.SIGNAL_HOLD, **base)

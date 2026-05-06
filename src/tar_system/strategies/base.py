"""Strategy protocol and signal contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import pandas as pd


@dataclass
class Signal:
    timestamp: pd.Timestamp
    symbol: str
    timeframe: str
    strategy: str
    version: str
    side: str
    confidence: float
    entry: float
    stop_loss: float | None
    take_profit: float | None
    reason_code: str
    metadata: dict[str, object] = field(default_factory=dict)


class Strategy(Protocol):
    name: str
    version: str

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        """Generate BUY, SELL or HOLD for the current bar."""

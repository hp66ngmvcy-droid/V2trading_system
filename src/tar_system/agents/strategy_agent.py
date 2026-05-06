"""Strategy resolution agent wrapper."""

from __future__ import annotations

from tar_system.strategies.resolver import resolve_strategy


class StrategyAgent:
    def run(self, strategy: str, symbol: str, timeframe: str, broker: str = "current_broker_demo") -> object:
        return resolve_strategy(strategy, symbol, timeframe, broker, audit=True)

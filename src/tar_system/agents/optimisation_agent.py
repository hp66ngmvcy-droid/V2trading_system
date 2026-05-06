"""Optimisation agent wrapper."""

from __future__ import annotations

from tar_system.optimisation.optimiser import optimise_asset


class OptimisationAgent:
    def run(self, strategy: str, symbol: str, timeframe: str, broker: str = "current_broker_demo") -> object:
        return optimise_asset(strategy, symbol, timeframe, broker)

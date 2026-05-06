"""Backtest agent wrapper."""

from __future__ import annotations

from tar_system.backtest.engine import run_backtest


class BacktestAgent:
    def run(self, features: object, strategy: object) -> object:
        return run_backtest(features, strategy)  # type: ignore[arg-type]

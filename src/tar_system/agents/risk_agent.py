"""Risk agent wrapper."""

from __future__ import annotations

from tar_system.risk.engine import RiskEngine


class RiskAgent:
    def __init__(self) -> None:
        self.engine = RiskEngine()

    def run(self, signal: object, **kwargs: object) -> object:
        return self.engine.evaluate(signal, **kwargs)  # type: ignore[arg-type]

"""Memory agent wrapper."""

from __future__ import annotations

from tar_system.memory.strategy_memory import record_strategy_memory


class MemoryAgent:
    def run(self, **kwargs: object) -> None:
        record_strategy_memory(**kwargs)  # type: ignore[arg-type]

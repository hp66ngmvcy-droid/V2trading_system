"""Walk-forward agent wrapper."""

from __future__ import annotations

from tar_system.validation.walk_forward import run_walk_forward


class WalkForwardAgent:
    def run(self, features: object, strategy: object) -> object:
        return run_walk_forward(features, strategy)  # type: ignore[arg-type]

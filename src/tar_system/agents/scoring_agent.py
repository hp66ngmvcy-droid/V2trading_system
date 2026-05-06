"""Scoring agent wrapper."""

from __future__ import annotations

from tar_system.scoring.scorer import score_strategy


class ScoringAgent:
    def run(self, metrics: dict[str, float]) -> object:
        return score_strategy(metrics)

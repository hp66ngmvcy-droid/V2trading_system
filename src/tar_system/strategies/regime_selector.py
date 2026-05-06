"""Regime-aware strategy recommendation for paper research loops."""

from __future__ import annotations

from dataclasses import dataclass

from tar_system import reason_codes as rc


@dataclass(frozen=True)
class RegimeStrategyRecommendation:
    recommended_strategy: str
    reason: str
    confidence: float
    fallback_strategy: str | None = None


def recommend_strategy_for_regime(regime: str) -> RegimeStrategyRecommendation:
    value = str(regime).upper()
    if value == "TRENDING":
        return RegimeStrategyRecommendation("gold_v2", "TRENDING_REGIME", 0.8, "rsi_reversion_v1")
    if value == "RANGING":
        return RegimeStrategyRecommendation("rsi_reversion_v1", "RANGING_REGIME", 0.8, "gold_v2")
    if value == "VOLATILE":
        return RegimeStrategyRecommendation("HOLD", rc.VOLATILE_REGIME_BLOCK, 0.9, "gold_v2")
    return RegimeStrategyRecommendation("HOLD", rc.REGIME_UNKNOWN, 0.5, "gold_v2")

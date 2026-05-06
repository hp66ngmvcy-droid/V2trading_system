"""Promotion gate for candidate strategies."""

from __future__ import annotations

from dataclasses import dataclass, field

from tar_system import reason_codes as rc


@dataclass
class PromotionDecision:
    approved: bool
    reason_codes: list[str] = field(default_factory=list)
    message: str = ""


def evaluate_promotion(
    verdict: str,
    has_walk_forward: bool,
    has_monte_carlo: bool,
    has_parameter_sensitivity: bool,
    environment_state: str,
    human_approval: bool,
) -> PromotionDecision:
    reasons: list[str] = []
    if verdict != "KEEP":
        reasons.append("VERDICT_NOT_KEEP")
    if not has_walk_forward:
        reasons.append("MISSING_WALK_FORWARD")
    if not has_monte_carlo:
        reasons.append("MISSING_MONTE_CARLO")
    if not has_parameter_sensitivity:
        reasons.append("MISSING_PARAMETER_SENSITIVITY")
    if environment_state == rc.ENV_BLOCK_TRADING:
        reasons.append("ENVIRONMENT_BLOCK_TRADING")
    if not human_approval:
        reasons.append("MISSING_HUMAN_APPROVAL")
    return PromotionDecision(not reasons, reasons, "Promotion approved" if not reasons else "Promotion blocked")

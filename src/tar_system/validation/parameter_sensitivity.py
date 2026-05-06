"""Lean one-parameter-at-a-time sensitivity checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParameterSensitivityResult:
    stability_score: float
    fragile: bool
    tested_parameters: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def neighbouring_parameters(parameters: dict[str, Any], step_ratio: float = 0.1) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for key, value in parameters.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            step = max(abs(float(value)) * step_ratio, 1.0 if isinstance(value, int) else 0.1)
            for direction in (-1, 1):
                variant = dict(parameters)
                changed = float(value) + direction * step
                variant[key] = int(round(changed)) if isinstance(value, int) else changed
                variants.append(variant)
    return variants


def assess_parameter_sensitivity(base_score: float, neighbouring_scores: list[float], tested_parameters: list[str]) -> ParameterSensitivityResult:
    if not neighbouring_scores:
        return ParameterSensitivityResult(0.0, True, tested_parameters, ["NO_VARIANTS"])
    average_drop = sum(max(0.0, base_score - score) for score in neighbouring_scores) / len(neighbouring_scores)
    stability = max(0.0, min(100.0, 100.0 - average_drop))
    fragile = stability < 60.0
    warnings = ["UNSTABLE_PARAMETERS"] if fragile else []
    return ParameterSensitivityResult(round(stability, 2), fragile, tested_parameters, warnings)

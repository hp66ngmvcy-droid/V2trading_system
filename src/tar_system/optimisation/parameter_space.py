"""Small parameter spaces for one-parameter-at-a-time optimisation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParameterMutation:
    name: str
    parameters: dict[str, Any]
    changed_parameter: str
    direction: str


def one_parameter_mutations(parameters: dict[str, Any], step_ratio: float = 0.1, max_variants: int = 12) -> list[ParameterMutation]:
    variants: list[ParameterMutation] = []
    for key, value in parameters.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        step = max(abs(float(value)) * step_ratio, 1.0 if isinstance(value, int) else 0.1)
        for direction, sign in (("down", -1), ("up", 1)):
            changed = max(1.0, float(value) + sign * step)
            mutation = dict(parameters)
            mutation[key] = int(round(changed)) if isinstance(value, int) else round(changed, 4)
            variants.append(ParameterMutation(f"{key}_{direction}", mutation, key, direction))
            if len(variants) >= max_variants:
                return variants
    return variants

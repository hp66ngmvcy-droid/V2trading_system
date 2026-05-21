"""Parameter stability analyzer for walk-forward optimisation results."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ParameterChange:
    """Track one parameter across walk-forward windows."""

    param_name: str
    values: list[float]
    mean: float
    min: float
    max: float
    range: float
    std: float
    change_pct: float


class ParameterStabilityAnalyzer:
    def __init__(self, walkforward_results: list[dict[str, Any]]) -> None:
        self.results = walkforward_results
        self.param_changes: dict[str, ParameterChange] = {}

    def analyze(self) -> dict[str, Any]:
        if not self.results:
            return {"error": "No walk-forward results provided"}

        parameter_names = sorted(
            {
                name
                for result in self.results
                for name in dict(result.get("optimal_params", {})).keys()
            }
        )
        if not parameter_names:
            return {"error": "No optimal_params found"}

        for parameter_name in parameter_names:
            values = [
                float(result["optimal_params"][parameter_name])
                for result in self.results
                if parameter_name in result.get("optimal_params", {})
            ]
            if not values:
                continue
            mean_value = statistics.fmean(values)
            min_value = min(values)
            max_value = max(values)
            range_value = max_value - min_value
            std_value = statistics.pstdev(values) if len(values) > 1 else 0.0
            change_pct = (range_value / abs(mean_value) * 100) if mean_value else 0.0
            self.param_changes[parameter_name] = ParameterChange(
                param_name=parameter_name,
                values=values,
                mean=mean_value,
                min=min_value,
                max=max_value,
                range=range_value,
                std=std_value,
                change_pct=change_pct,
            )

        changes = [asdict(change) for change in self.param_changes.values()]
        unstable = [change for change in changes if change["change_pct"] > 50]
        stable = [change for change in changes if change["change_pct"] <= 20]
        return {
            "parameter_count": len(changes),
            "stable_parameters": stable,
            "unstable_parameters": unstable,
            "all_parameters": changes,
            "stability_score": self.stability_score(),
        }

    def stability_score(self) -> float:
        if not self.param_changes:
            return 0.0
        penalties = [min(change.change_pct / 100, 1.0) for change in self.param_changes.values()]
        return round(max(0.0, 1.0 - statistics.fmean(penalties)), 3)

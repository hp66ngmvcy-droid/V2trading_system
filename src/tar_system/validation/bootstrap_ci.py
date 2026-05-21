"""Bootstrap confidence intervals for strategy trade returns."""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np


def bootstrap_mean_ci(
    trade_returns: Iterable[float],
    n_iterations: int = 2000,
    confidence: float = 0.95,
    seed: int = 42,
) -> dict[str, Any]:
    """Return a percentile bootstrap confidence interval for the mean.

    This follows the standard percentile bootstrap procedure used by
    scipy.stats.bootstrap, implemented locally to avoid adding dependency
    surface to the gate path.
    """

    values = _clean_returns(trade_returns)
    if values.size == 0:
        return {
            "mean": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "spans_zero": True,
            "sample_size": 0,
            "confidence": confidence,
            "n_iterations": n_iterations,
        }

    if values.size == 1 or n_iterations <= 0:
        mean = float(np.mean(values))
        return {
            "mean": mean,
            "ci_lower": mean,
            "ci_upper": mean,
            "spans_zero": mean <= 0.0 <= mean,
            "sample_size": int(values.size),
            "confidence": confidence,
            "n_iterations": max(0, int(n_iterations)),
        }

    confidence = min(max(float(confidence), 0.0), 1.0)
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(int(n_iterations), values.size), replace=True)
    means = np.mean(samples, axis=1)
    alpha = 1.0 - confidence
    lower, upper = np.quantile(means, [alpha / 2.0, 1.0 - alpha / 2.0])
    return {
        "mean": float(np.mean(values)),
        "ci_lower": float(lower),
        "ci_upper": float(upper),
        "spans_zero": bool(lower <= 0.0 <= upper),
        "sample_size": int(values.size),
        "confidence": confidence,
        "n_iterations": int(n_iterations),
    }


def _clean_returns(trade_returns: Iterable[float]) -> np.ndarray:
    values = np.asarray(list(trade_returns), dtype=float)
    if values.size == 0:
        return values
    return values[np.isfinite(values)]

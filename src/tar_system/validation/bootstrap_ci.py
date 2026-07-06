"""Bootstrap confidence intervals for strategy trade returns."""

from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np


def _norm_cdf(x: float) -> float:
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


def _norm_ppf(p: float) -> float:
    """Rational approximation for inverse normal CDF (Abramowitz & Stegun 26.2.17)."""
    if p <= 0.0:
        return float("-inf")
    if p >= 1.0:
        return float("inf")
    if p < 0.5:
        return -_norm_ppf(1.0 - p)
    t = math.sqrt(-2.0 * math.log(1.0 - p))
    num = 2.515517 + 0.802853 * t + 0.010328 * t ** 2
    den = 1.0 + 1.432788 * t + 0.189269 * t ** 2 + 0.001308 * t ** 3
    return t - num / den


def deflated_sharpe_ratio(
    trade_returns: Iterable[float],
    n_trials: int = 1,
) -> dict[str, Any]:
    """Compute the Deflated Sharpe Ratio (DSR) p-value.

    Adjusts the Sharpe ratio for selection bias when multiple candidates
    are tested. Low dsr_p_value (<0.05) = strategy unlikely to be noise
    even after correcting for number of trials run.

    Based on Bailey & Lopez de Prado (2014).
    No scipy dependency — pure numpy + math.
    """
    values = _clean_returns(trade_returns)
    n = values.size
    if n < 4:
        return {"sr": 0.0, "dsr": 0.0, "dsr_p_value": 1.0, "n_trials": n_trials, "sample_size": int(n)}

    sr = float(np.mean(values)) / float(np.std(values, ddof=1))
    skew = float(np.mean(((values - np.mean(values)) / np.std(values, ddof=1)) ** 3))
    kurt_excess = float(np.mean(((values - np.mean(values)) / np.std(values, ddof=1)) ** 4)) - 3.0

    # SR variance under non-normality (Mertens 2002)
    sr_var = (1.0 + 0.5 * sr ** 2 - skew * sr + ((kurt_excess + 3.0 - 1.0) / 4.0) * sr ** 2) / max(n - 1, 1)
    sr_std = float(math.sqrt(max(sr_var, 1e-12)))

    # Expected max SR across n_trials independent tests
    expected_max_sr = _norm_ppf(1.0 - 1.0 / max(n_trials, 1)) * sr_std if n_trials > 1 else 0.0

    dsr = (sr - expected_max_sr) / sr_std if sr_std > 0 else 0.0
    p_value = 1.0 - _norm_cdf(dsr)

    return {
        "sr": round(sr, 4),
        "dsr": round(dsr, 4),
        "dsr_p_value": round(p_value, 4),
        "n_trials": n_trials,
        "sample_size": int(n),
    }


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

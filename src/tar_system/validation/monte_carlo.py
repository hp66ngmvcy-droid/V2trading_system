"""Lean Monte Carlo robustness checks for trade returns."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class MonteCarloResult:
    robustness_score: float
    worst_drawdown: float
    median_return: float
    warnings: list[str] = field(default_factory=list)


def _max_drawdown(equity: list[float]) -> float:
    peak = equity[0] if equity else 0.0
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak:
            worst = max(worst, (peak - value) / peak)
    return worst


def run_monte_carlo(trade_returns: list[float], iterations: int = 200, seed: int = 42) -> MonteCarloResult:
    warnings: list[str] = []
    if not trade_returns:
        return MonteCarloResult(0.0, 0.0, 0.0, ["NO_TRADES"])
    if len(trade_returns) < 20:
        warnings.append("LOW_TRADE_COUNT")
    rng = random.Random(seed)
    totals: list[float] = []
    drawdowns: list[float] = []
    for _ in range(iterations):
        sample = [rng.choice(trade_returns) for _ in trade_returns]
        rng.shuffle(sample)
        equity = [1.0]
        for value in sample:
            equity.append(equity[-1] * (1.0 + value))
        totals.append(equity[-1] - 1.0)
        drawdowns.append(_max_drawdown(equity))
    totals.sort()
    median = totals[len(totals) // 2]
    worst_dd = max(drawdowns)
    score = max(0.0, min(100.0, 100 - worst_dd * 200 + median * 100))
    if worst_dd > 0.25:
        warnings.append("HIGH_DRAWDOWN_STRESS")
    return MonteCarloResult(round(score, 2), round(worst_dd, 4), round(median, 4), warnings)

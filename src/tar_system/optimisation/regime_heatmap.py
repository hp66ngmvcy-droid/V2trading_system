"""Regime performance heatmap summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

REGIMES = ["TRENDING", "RANGING", "VOLATILE", "UNKNOWN"]


@dataclass
class RegimeSummary:
    trade_count: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    drawdown: float = 0.0
    expectancy: float = 0.0
    average_return: float = 0.0
    flag: str = "insufficient data"


@dataclass
class RegimeHeatmap:
    regimes: dict[str, RegimeSummary] = field(default_factory=dict)
    best_regime: str = "UNKNOWN"
    avoid_regimes: list[str] = field(default_factory=list)


def build_regime_heatmap(trades: Iterable[dict[str, object]], min_trades: int = 5) -> RegimeHeatmap:
    grouped: dict[str, list[float]] = {regime: [] for regime in REGIMES}
    for trade in trades:
        regime = str(trade.get("regime", "UNKNOWN")).upper()
        grouped.setdefault(regime if regime in REGIMES else "UNKNOWN", []).append(float(trade.get("return", trade.get("pnl", 0.0))))
    summaries: dict[str, RegimeSummary] = {}
    for regime in REGIMES:
        returns = grouped.get(regime, [])
        wins = [value for value in returns if value > 0]
        losses = [value for value in returns if value < 0]
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        count = len(returns)
        expectancy = sum(returns) / count if count else 0.0
        summary = RegimeSummary(
            trade_count=count,
            win_rate=len(wins) / count if count else 0.0,
            profit_factor=gross_win / gross_loss if gross_loss else (gross_win if gross_win else 0.0),
            drawdown=max(0.0, abs(min(returns)) if returns else 0.0),
            expectancy=expectancy,
            average_return=expectancy,
        )
        if count < min_trades:
            summary.flag = "insufficient data"
        elif summary.profit_factor >= 1.5 and summary.expectancy > 0:
            summary.flag = "strong regime"
        elif summary.profit_factor < 1.0 or summary.expectancy < 0:
            summary.flag = "avoid regime"
        else:
            summary.flag = "weak regime"
        summaries[regime] = summary
    best = max(summaries, key=lambda key: summaries[key].expectancy)
    avoid = [regime for regime, summary in summaries.items() if summary.flag == "avoid regime"]
    return RegimeHeatmap(summaries, best, avoid)

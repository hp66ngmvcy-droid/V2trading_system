"""Strategy ranking without win-rate-only shortcuts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class RankedStrategy:
    strategy: str
    symbol: str
    timeframe: str
    balanced_score: float
    metrics: dict[str, float]


def balanced_score(metrics: dict[str, float]) -> float:
    win_rate = metrics.get("win_rate", 0.0)
    profit_factor = metrics.get("profit_factor", 0.0)
    drawdown = metrics.get("max_drawdown", 1.0)
    trade_count = metrics.get("total_trades", 0.0)
    expectancy = metrics.get("expectancy", 0.0)
    robustness = metrics.get("robustness_score", 50.0)
    stability = metrics.get("parameter_stability", 50.0)
    score = 0.0
    score += min(win_rate, 0.75) / 0.75 * 15
    score += min(profit_factor, 3.0) / 3.0 * 20
    score += max(0.0, 1 - drawdown / 0.3) * 20
    score += min(trade_count, 50) / 50 * 15
    score += (15 if expectancy > 0 else 0)
    score += robustness / 100 * 10
    score += stability / 100 * 5
    return round(max(0.0, min(100.0, score)), 2)


def rank_strategies(results: Iterable[dict[str, object]], mode: str = "balanced") -> list[RankedStrategy]:
    ranked: list[RankedStrategy] = []
    for item in results:
        metrics = dict(item.get("metrics", {}))  # type: ignore[arg-type]
        ranked.append(
            RankedStrategy(
                strategy=str(item.get("strategy", "unknown")),
                symbol=str(item.get("symbol", "")),
                timeframe=str(item.get("timeframe", "")),
                balanced_score=balanced_score(metrics),
                metrics=metrics,
            )
        )
    key_map = {
        "win_rate": lambda row: row.metrics.get("win_rate", 0.0),
        "profit_factor": lambda row: row.metrics.get("profit_factor", 0.0),
        "lowest_drawdown": lambda row: -row.metrics.get("max_drawdown", 1.0),
        "stable": lambda row: row.metrics.get("parameter_stability", 0.0),
        "balanced": lambda row: row.balanced_score,
    }
    return sorted(ranked, key=key_map.get(mode, key_map["balanced"]), reverse=True)


def best_by_symbol(results: Iterable[dict[str, object]]) -> dict[str, RankedStrategy]:
    output: dict[str, RankedStrategy] = {}
    for row in rank_strategies(results):
        output.setdefault(row.symbol, row)
    return output


def best_by_timeframe(results: Iterable[dict[str, object]]) -> dict[str, RankedStrategy]:
    output: dict[str, RankedStrategy] = {}
    for row in rank_strategies(results):
        output.setdefault(row.timeframe, row)
    return output

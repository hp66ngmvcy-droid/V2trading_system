"""Broker-aware local cost sensitivity analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from tar_system.backtest.engine import run_backtest
from tar_system.data.store import load_feature_data
from tar_system.scoring.scorer import score_strategy
from tar_system.strategies.resolver import resolve_strategy


@dataclass(frozen=True)
class CostAnalysisResult:
    strategy: str
    symbol: str
    timeframe: str
    broker: str
    gross_score: float
    realistic_score: float
    stressed_score: float
    extreme_score: float
    cost_breakeven: float
    cost_sensitive: bool
    swap_drag: float
    tiers: dict[str, dict[str, float]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_cost_analysis(strategy_name: str, symbol: str, timeframe: str, broker: str = "current_broker_demo") -> CostAnalysisResult:
    features = load_feature_data(symbol, timeframe)
    resolved = resolve_strategy(strategy_name, symbol, timeframe, broker)
    tiers: dict[str, dict[str, float]] = {}
    scores: dict[str, float] = {}
    for name, multiplier in {"gross": 0.0, "realistic": 1.0, "stressed": 2.0, "extreme": 3.0}.items():
        result = run_backtest(
            features,
            resolved.strategy,
            audit_decisions=False,
            broker_profile=resolved.broker_profile,
            asset_profile=resolved.asset_profile,
            cost_multiplier=multiplier,
        )
        score = score_strategy(result.metrics).score
        tiers[name] = result.metrics
        scores[name] = score
    gross_score = scores["gross"]
    realistic_score = scores["realistic"]
    gross_profit = max(tiers["gross"].get("gross_profit", 0.0), 0.0)
    swap_drag = tiers["realistic"].get("swap_cost", 0.0) / gross_profit if gross_profit else 0.0
    return CostAnalysisResult(
        strategy=strategy_name,
        symbol=symbol,
        timeframe=timeframe,
        broker=broker,
        gross_score=gross_score,
        realistic_score=realistic_score,
        stressed_score=scores["stressed"],
        extreme_score=scores["extreme"],
        cost_breakeven=realistic_score / gross_score if gross_score else 0.0,
        cost_sensitive=realistic_score < 0.7 * gross_score if gross_score else False,
        swap_drag=swap_drag,
        tiers=tiers,
    )

"""Bounded mutate/retest loop for strategy parameters."""

from __future__ import annotations

import inspect
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tar_system.backtest.engine import run_backtest
from tar_system.data.store import load_feature_data
from tar_system.optimisation.parameter_space import one_parameter_mutations
from tar_system.scoring.scorer import score_strategy
from tar_system.strategies.registry import REGISTRY, get_strategy
from tar_system.strategies.resolver import resolve_strategy


@dataclass
class MutateRetestIteration:
    iteration: int
    variant_name: str
    parameters: dict[str, Any]
    changed_parameter: str | None
    direction: str | None
    metrics: dict[str, float]
    score: float
    verdict: str
    reason_codes: list[str]


@dataclass
class MutateRetestResult:
    strategy: str
    symbol: str
    timeframe: str
    broker: str
    max_iterations: int
    row_count: int
    iterations: list[MutateRetestIteration]

    @property
    def best(self) -> MutateRetestIteration | None:
        if not self.iterations:
            return None
        return max(self.iterations, key=lambda item: item.score)


def mutate_retest_loop(
    strategy_name: str,
    symbol: str,
    timeframe: str,
    broker: str = "current_broker_demo",
    max_iterations: int = 5,
    max_rows: int = 0,
    require_walk_forward: bool = False,
) -> MutateRetestResult:
    """Run at most ``max_iterations`` parameter candidates through backtest + scorer."""
    capped_iterations = max(1, min(int(max_iterations), 5))
    resolved = resolve_strategy(strategy_name, symbol, timeframe, broker, audit=True)
    features = load_feature_data(symbol, timeframe).sort_values("timestamp")
    if max_rows > 0 and len(features) > max_rows:
        features = features.tail(max_rows).copy()

    base_parameters = _base_parameters(strategy_name, resolved.variant.parameters)
    mutations = one_parameter_mutations(base_parameters, max_variants=max(0, capped_iterations - 1))
    candidates: list[tuple[str, dict[str, Any], str | None, str | None]] = [
        ("base", base_parameters, None, None)
    ]
    candidates.extend(
        (mutation.name, mutation.parameters, mutation.changed_parameter, mutation.direction)
        for mutation in mutations
    )

    iterations: list[MutateRetestIteration] = []
    for index, (name, parameters, changed_parameter, direction) in enumerate(candidates[:capped_iterations], start=1):
        strategy = get_strategy(strategy_name, **parameters)
        backtest = run_backtest(features, strategy, audit_decisions=False)
        score = score_strategy(backtest.metrics, None, timeframe, require_walk_forward=require_walk_forward)
        iterations.append(
            MutateRetestIteration(
                iteration=index,
                variant_name=f"{resolved.variant.variant_name}_{name}",
                parameters=parameters,
                changed_parameter=changed_parameter,
                direction=direction,
                metrics=backtest.metrics,
                score=score.score,
                verdict=score.verdict,
                reason_codes=score.reason_codes,
            )
        )

    result = MutateRetestResult(
        strategy=strategy_name,
        symbol=symbol,
        timeframe=timeframe,
        broker=broker,
        max_iterations=capped_iterations,
        row_count=len(features),
        iterations=iterations,
    )
    _save_result(result)
    return result


def _base_parameters(strategy_name: str, variant_parameters: dict[str, Any]) -> dict[str, Any]:
    if variant_parameters:
        return dict(variant_parameters)
    cls = REGISTRY.get(strategy_name)
    if cls is None:
        return {}
    signature = inspect.signature(cls)
    return {
        name: parameter.default
        for name, parameter in signature.parameters.items()
        if parameter.default is not inspect.Parameter.empty and name not in {"name", "version"}
    }


def _save_result(result: MutateRetestResult) -> Path:
    path = Path("data/results") / f"{result.strategy}_{result.symbol}_{result.timeframe}_mutate_retest_loop.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    best = result.best
    payload["best"] = asdict(best) if best else None
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path

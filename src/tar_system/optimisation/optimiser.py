"""Asset-aware local strategy optimiser."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tar_system.backtest.engine import run_backtest
from tar_system.data.store import load_feature_data
from tar_system.memory.strategy_memory import record_strategy_memory
from tar_system.optimisation.parameter_anchors import ATR_GATE_ANCHORS, ATR_STOP_ANCHORS, GOLD_V2_ANCHORS
from tar_system.optimisation.parameter_space import one_parameter_mutations
from tar_system.scoring.scorer import score_strategy
from tar_system.strategies.registry import get_strategy
from tar_system.strategies.resolver import resolve_strategy
from tar_system.validation.walk_forward import run_walk_forward


@dataclass
class OptimisedVariant:
    variant_name: str
    parameters: dict[str, Any]
    metrics: dict[str, float]
    walk_forward_metrics: dict[str, Any]
    score: float
    verdict: str
    reason_codes: list[str]


@dataclass
class OptimiseAssetResult:
    strategy: str
    symbol: str
    timeframe: str
    broker: str
    ranked_variants: list[OptimisedVariant]
    narrowed_from_walk_forward: bool = False
    parameter_source: str = "anchors"
    search_ranges: dict[str, tuple[float, float]] | None = None


def optimise_asset(
    strategy_name: str,
    symbol: str,
    timeframe: str,
    broker: str = "current_broker_demo",
    max_variants: int = 8,
    max_rows: int = 20_000,
) -> OptimiseAssetResult:
    resolved = resolve_strategy(strategy_name, symbol, timeframe, broker, audit=True)
    features = load_feature_data(symbol, timeframe).sort_values("timestamp")
    if max_rows > 0 and len(features) > max_rows:
        features = features.tail(max_rows).copy()
    base_parameters = resolved.variant.parameters
    search_ranges = _load_walk_forward_ranges(strategy_name, symbol, timeframe)
    narrowed = bool(search_ranges)
    if not narrowed:
        base_parameters = {**base_parameters, **_anchor_parameters(symbol)}
    mutations = [("base", base_parameters)] + [(mutation.name, mutation.parameters) for mutation in one_parameter_mutations(base_parameters, max_variants=max_variants)]
    ranked: list[OptimisedVariant] = []
    for mutation_name, parameters in mutations:
        strategy = get_strategy(strategy_name, **parameters)
        backtest = run_backtest(features, strategy, audit_decisions=False)
        wf_metrics: dict[str, Any] = {}
        if len(features) >= 250:
            wf = run_walk_forward(features, strategy, 200, 50, audit_decisions=False, max_splits=25)
            wf_metrics = {
                "split_count": len(wf.splits),
                "ran": wf.ran,
                "window_count": wf.window_count,
                "wf_verdict": wf.wf_verdict,
                "wf_reason": wf.wf_reason,
                "stitched_metrics": wf.stitched_metrics,
                "parameter_stability": wf.parameter_stability,
                "stable_parameter_ranges": wf.stable_parameter_ranges,
                "parameter_stability_score": wf.parameter_stability_score,
                "recommended_search_range": wf.recommended_search_range,
                "bootstrap_ci": wf.bootstrap_ci,
            }
        score = score_strategy(backtest.metrics, wf_metrics, timeframe, require_walk_forward=True)
        verdict = "KEEP" if score.verdict == "KEEP" else "REVISE" if score.verdict == "REVIEW" else "KILL"
        variant_name = resolved.variant.variant_name if mutation_name == "base" else f"{resolved.variant.variant_name}_{mutation_name}"
        row = OptimisedVariant(variant_name, parameters, backtest.metrics, wf_metrics, score.score, verdict, score.reason_codes)
        ranked.append(row)
        record_strategy_memory(
            base_strategy=strategy_name,
            variant_name=variant_name,
            version=getattr(strategy, "version", ""),
            symbol=symbol,
            timeframe=timeframe,
            broker=broker,
            asset_profile=resolved.asset_profile.to_dict(),
            broker_profile=resolved.broker_profile.symbol_profile(symbol).to_dict(),
            parameters=parameters,
            backtest_metrics=backtest.metrics,
            walk_forward_metrics=wf_metrics,
            forward_test_metrics={},
            score=score.score,
            verdict=verdict,
            reason_codes=score.reason_codes,
            promoted=False,
            notes="optimise_asset",
        )
    ranked.sort(key=lambda item: item.score, reverse=True)
    result = OptimiseAssetResult(strategy_name, symbol, timeframe, broker, ranked, narrowed, "walk_forward" if narrowed else "anchors", search_ranges or {})
    output = Path("data/results") / f"{strategy_name}_{symbol}_{timeframe}_optimisation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({**asdict(result), "row_count": len(features), "max_rows": max_rows}, indent=2, default=str), encoding="utf-8")
    return result


def _load_walk_forward_ranges(strategy: str, symbol: str, timeframe: str) -> dict[str, tuple[float, float]]:
    path = Path("data/results") / f"{strategy}_{symbol}_{timeframe}_walk_forward.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get("stable_parameter_ranges", {})
    return {key: (float(value[0]), float(value[1])) for key, value in raw.items()} if isinstance(raw, dict) else {}


def _anchor_parameters(symbol: str) -> dict[str, object]:
    anchor = GOLD_V2_ANCHORS[0]
    atr_stop = ATR_STOP_ANCHORS.get(symbol.upper(), {})
    atr_gate = ATR_GATE_ANCHORS[0]
    return {
        "fast_ema": anchor["fast_ema"],
        "slow_ema": anchor["slow_ema"],
        "rsi_buy_threshold": anchor["rsi_threshold"],
        "rsi_sell_threshold": 100 - float(anchor["rsi_threshold"]),
        "atr_multiplier": atr_stop.get("atr_multiplier", 1.5),
        "atr_floor_multiplier": atr_gate["atr_floor_multiplier"],
        "atr_ceil_multiplier": atr_gate["atr_ceil_multiplier"],
    }

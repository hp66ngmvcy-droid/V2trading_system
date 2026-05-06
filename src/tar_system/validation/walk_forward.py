"""Lean walk-forward validation."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class WalkForwardSplit:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


@dataclass
class WalkForwardResult:
    splits: list[WalkForwardSplit]
    stitched_metrics: dict[str, float]
    parameter_stability: dict[str, float | str] = field(default_factory=dict)
    stopped: bool = False
    partial: bool = False
    reason_code: str | None = None
    stable_parameter_ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    parameter_stability_score: float = 0.0
    recommended_search_range: dict[str, tuple[float, float]] = field(default_factory=dict)


def rolling_splits(row_count: int, train_window: int, test_window: int) -> list[WalkForwardSplit]:
    splits: list[WalkForwardSplit] = []
    start = 0
    while start + train_window + test_window <= row_count:
        train_end = start + train_window
        test_end = train_end + test_window
        splits.append(WalkForwardSplit(start, train_end, train_end, test_end))
        start += test_window
    return splits


def cap_splits(splits: list[WalkForwardSplit], max_splits: int | None) -> list[WalkForwardSplit]:
    if max_splits is None or max_splits <= 0 or len(splits) <= max_splits:
        return splits
    return splits[-max_splits:]


def run_walk_forward(
    features: pd.DataFrame,
    strategy: object,
    train_window: int = 200,
    test_window: int = 50,
    audit_decisions: bool = True,
    max_splits: int | None = None,
) -> WalkForwardResult:
    from tar_system.backtest.engine import run_backtest

    splits = cap_splits(rolling_splits(len(features), train_window, test_window), max_splits)
    split_metrics: list[dict[str, float]] = []
    completed_splits: list[WalkForwardSplit] = []
    fold_parameters: list[dict[str, float]] = []
    stopped = False
    for split in splits:
        test_df = features.iloc[split.test_start : split.test_end].copy()
        result = run_backtest(test_df, strategy, audit_decisions=audit_decisions)
        if result.stopped:
            stopped = True
            break
        split_metrics.append(result.metrics)
        completed_splits.append(split)
        fold_parameters.append(_strategy_parameters(strategy))
    metrics = stitch_metrics(split_metrics)
    ranges, stability = derive_stable_parameter_ranges(fold_parameters)
    return WalkForwardResult(
        splits=completed_splits,
        stitched_metrics=metrics,
        parameter_stability={"status": "stable" if stability >= 70 else "unstable", "stability_score": stability},
        stopped=stopped,
        partial=stopped,
        reason_code="STOP_REQUESTED" if stopped else None,
        stable_parameter_ranges=ranges,
        parameter_stability_score=stability,
        recommended_search_range=ranges,
    )


def stitch_metrics(metrics: list[dict[str, float]]) -> dict[str, float]:
    total_trades = sum(item.get("total_trades", 0.0) for item in metrics)
    if not metrics:
        return {
            "total_trades": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.0,
            "expectancy": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
        }
    wins = sum(item.get("win_rate", 0.0) * item.get("total_trades", 0.0) for item in metrics)
    weighted_expectancy = sum(item.get("expectancy", 0.0) * item.get("total_trades", 0.0) for item in metrics)
    return {
        "total_trades": total_trades,
        "win_rate": wins / total_trades if total_trades else 0.0,
        "profit_factor": sum(item.get("profit_factor", 0.0) for item in metrics) / len(metrics),
        "max_drawdown": max(item.get("max_drawdown", 0.0) for item in metrics),
        "expectancy": weighted_expectancy / total_trades if total_trades else 0.0,
        "average_win": sum(item.get("average_win", 0.0) for item in metrics) / len(metrics),
        "average_loss": sum(item.get("average_loss", 0.0) for item in metrics) / len(metrics),
    }


def derive_stable_parameter_ranges(fold_parameters: list[dict[str, float]]) -> tuple[dict[str, tuple[float, float]], float]:
    if not fold_parameters:
        return {}, 0.0
    keys = sorted(set().union(*(params.keys() for params in fold_parameters)))
    ranges: dict[str, tuple[float, float]] = {}
    stable = 0
    for key in keys:
        values = [float(params[key]) for params in fold_parameters if key in params]
        if not values:
            continue
        low, high = min(values), max(values)
        ranges[key] = (low, high)
        mean = sum(values) / len(values)
        if mean == 0 or (high - low) / abs(mean) <= 0.2:
            stable += 1
    return ranges, round(stable / len(ranges) * 100, 2) if ranges else 0.0


def _strategy_parameters(strategy: object) -> dict[str, float]:
    keys = ["fast_ema", "slow_ema", "rsi_buy_threshold", "rsi_sell_threshold", "atr_multiplier", "reward_risk"]
    return {key: float(getattr(strategy, key)) for key in keys if isinstance(getattr(strategy, key, None), (int, float))}

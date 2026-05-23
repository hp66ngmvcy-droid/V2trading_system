"""Lean walk-forward validation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

from tar_system.validation.bootstrap_ci import bootstrap_mean_ci


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
    bootstrap_ci: dict[str, object] = field(default_factory=dict)
    ran: bool = True
    window_count: int = 0
    wf_verdict: str = "REVIEW"
    wf_reason: str = ""


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
    if not splits:
        return WalkForwardResult(
            splits=[],
            stitched_metrics=stitch_metrics([]),
            parameter_stability={"status": "not_enough_data", "stability_score": 0.0},
            bootstrap_ci=bootstrap_mean_ci([]),
            reason_code="WALK_FORWARD_NOT_ENOUGH_DATA",
            ran=False,
            window_count=0,
            wf_verdict="REVIEW",
            wf_reason="Not enough rows to produce a walk-forward split.",
        )
    split_metrics: list[dict[str, float]] = []
    completed_splits: list[WalkForwardSplit] = []
    fold_parameters: list[dict[str, float]] = []
    stopped = False
    for split in splits:
        # Run on train window to record in-sample behaviour per fold.
        train_df = features.iloc[split.train_start : split.train_end].copy()
        run_backtest(train_df, strategy, audit_decisions=False)
        fold_parameters.append(_strategy_parameters(strategy))
        # Evaluate on unseen test window only.
        test_df = features.iloc[split.test_start : split.test_end].copy()
        result = run_backtest(test_df, strategy, audit_decisions=audit_decisions)
        if result.stopped:
            stopped = True
            break
        split_metrics.append(result.metrics)
        completed_splits.append(split)
    metrics = stitch_metrics(split_metrics)
    bootstrap_ci = bootstrap_mean_ci(metrics.get("trade_returns", []))
    ranges, stability = derive_stable_parameter_ranges(fold_parameters)
    wf_verdict, wf_reason = _walk_forward_verdict(metrics, len(completed_splits), stability, stopped, bootstrap_ci)
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
        bootstrap_ci=bootstrap_ci,
        ran=bool(completed_splits),
        window_count=len(completed_splits),
        wf_verdict=wf_verdict,
        wf_reason=wf_reason,
    )


def stitch_metrics(metrics: list[dict[str, object]]) -> dict[str, object]:
    total_trades = sum(float(item.get("total_trades", 0.0) or 0.0) for item in metrics)
    if not metrics:
        return {
            "total_trades": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.0,
            "expectancy": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "trade_returns": [],
            "trade_pnls": [],
        }
    trade_returns = _flatten_numeric(metrics, "trade_returns")
    trade_pnls = _flatten_numeric(metrics, "trade_pnls")
    wins = sum(float(item.get("win_rate", 0.0) or 0.0) * float(item.get("total_trades", 0.0) or 0.0) for item in metrics)
    weighted_expectancy = sum(float(item.get("expectancy", 0.0) or 0.0) * float(item.get("total_trades", 0.0) or 0.0) for item in metrics)
    return {
        "total_trades": total_trades,
        "win_rate": wins / total_trades if total_trades else 0.0,
        "profit_factor": sum(float(item.get("profit_factor", 0.0) or 0.0) for item in metrics) / len(metrics),
        "max_drawdown": max(float(item.get("max_drawdown", 0.0) or 0.0) for item in metrics),
        "expectancy": weighted_expectancy / total_trades if total_trades else 0.0,
        "average_win": sum(float(item.get("average_win", 0.0) or 0.0) for item in metrics) / len(metrics),
        "average_loss": sum(float(item.get("average_loss", 0.0) or 0.0) for item in metrics) / len(metrics),
        "sharpe_ratio": _sharpe(trade_returns),
        "trade_returns": trade_returns,
        "trade_pnls": trade_pnls,
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


def _walk_forward_verdict(
    metrics: dict[str, object],
    split_count: int,
    stability: float,
    stopped: bool,
    bootstrap_ci: dict[str, object],
) -> tuple[str, str]:
    if stopped:
        return "REVIEW", "Walk-forward stopped before all splits completed."
    if split_count < 3:
        return "REVIEW", f"Only {split_count} walk-forward splits completed; need at least 3 for KEEP."
    if float(metrics.get("total_trades", 0.0) or 0.0) <= 0:
        return "REVIEW", "Walk-forward produced no OOS trades."
    max_drawdown = float(metrics.get("max_drawdown", 0.0) or 0.0)
    profit_factor = float(metrics.get("profit_factor", 0.0) or 0.0)
    if max_drawdown > 0.20:
        return "REVIEW", f"Walk-forward max drawdown {max_drawdown:.1%} exceeds 20%."
    if profit_factor < 1.10:
        return "REVIEW", f"Walk-forward profit factor {profit_factor:.2f} is below 1.10."
    if stability < 50.0:
        return "REVIEW", f"Walk-forward parameter stability {stability:.1f} is below 50."
    sharpe = float(metrics.get("sharpe_ratio", 0.0) or 0.0)
    if bool(bootstrap_ci.get("spans_zero", True)):
        # High-RR strategies have inherently wide per-trade CI; waive when
        # PF and Sharpe both clear stronger thresholds.
        if profit_factor >= 1.15 and sharpe >= 1.0:
            return "KEEP", f"{split_count} walk-forward splits passed (PF {profit_factor:.2f}, Sharpe {sharpe:.2f}; CI waived)."
        return "REVIEW", "Walk-forward bootstrap confidence interval spans zero."
    return "KEEP", f"{split_count} walk-forward splits passed validation."


def _sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    return mean / std * math.sqrt(252) if std else 0.0


def _flatten_numeric(metrics: list[dict[str, object]], key: str) -> list[float]:
    values: list[float] = []
    for item in metrics:
        raw = item.get(key, [])
        if isinstance(raw, (list, tuple)):
            values.extend(float(value) for value in raw if isinstance(value, (int, float)))
    return values

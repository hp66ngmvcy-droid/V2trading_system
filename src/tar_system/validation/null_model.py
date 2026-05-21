"""Advisory null-model comparison for strategy trade results."""

from __future__ import annotations

from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd


def run_null_model(
    real_trades: list[dict[str, Any]],
    strategy_runner: Callable[[pd.DataFrame, dict[str, Any]], Any],
    df: pd.DataFrame,
    params: dict[str, Any],
    n_permutations: int = 500,
    seed: int = 42,
) -> dict[str, Any]:
    """Compare real trades against randomized runner outputs.

    The runner is expected to respect the injected ``random_seed`` parameter
    and return either a trade list or a dict containing ``trades``/``metrics``.
    This module is advisory only; promotion gates use bootstrap CI instead.
    """

    real_mean_r, real_pnl = _trade_stats(real_trades)
    null_mean_r: list[float] = []
    null_pnl: list[float] = []
    rng = np.random.default_rng(seed)
    for _ in range(max(0, int(n_permutations))):
        randomized_params = {**params, "random_seed": int(rng.integers(0, 2**31 - 1))}
        payload = strategy_runner(df, randomized_params)
        trades = _extract_trades(payload)
        mean_r, pnl = _trade_stats(trades)
        null_mean_r.append(mean_r)
        null_pnl.append(pnl)

    p_value_mean_r = _right_tail_p_value(real_mean_r, null_mean_r)
    p_value_pnl = _right_tail_p_value(real_pnl, null_pnl)
    return {
        "real_mean_r": real_mean_r,
        "real_net_pnl": real_pnl,
        "null_mean_r_mean": float(np.mean(null_mean_r)) if null_mean_r else 0.0,
        "null_pnl_mean": float(np.mean(null_pnl)) if null_pnl else 0.0,
        "p_value_mean_r": p_value_mean_r,
        "p_value_pnl": p_value_pnl,
        "beats_null": bool(p_value_mean_r < 0.05 and p_value_pnl < 0.05),
        "n_permutations": max(0, int(n_permutations)),
    }


def _extract_trades(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        trades = payload.get("trades")
        if isinstance(trades, list):
            return [item for item in trades if isinstance(item, dict)]
        metrics = payload.get("metrics")
        if isinstance(metrics, dict):
            return [{"return_r": metrics.get("expectancy", 0.0), "pnl": metrics.get("net_profit", 0.0)}]
    trades = getattr(payload, "trades", None)
    if isinstance(trades, list):
        return [item for item in trades if isinstance(item, dict)]
    metrics = getattr(payload, "metrics", None)
    if isinstance(metrics, dict):
        return [{"return_r": metrics.get("expectancy", 0.0), "pnl": metrics.get("net_profit", 0.0)}]
    return []


def _trade_stats(trades: Iterable[dict[str, Any]]) -> tuple[float, float]:
    returns: list[float] = []
    pnls: list[float] = []
    for trade in trades:
        returns.append(float(trade.get("return_r", trade.get("return", trade.get("pnl", 0.0))) or 0.0))
        pnls.append(float(trade.get("pnl", trade.get("net_pnl", trade.get("pnl_absolute", 0.0))) or 0.0))
    return (float(np.mean(returns)) if returns else 0.0, float(np.sum(pnls)) if pnls else 0.0)


def _right_tail_p_value(real_value: float, null_values: list[float]) -> float:
    if not null_values:
        return 1.0
    null = np.asarray(null_values, dtype=float)
    return float((np.sum(null >= real_value) + 1.0) / (len(null) + 1.0))

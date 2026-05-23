"""Structural promotion gates for paper strategy candidates."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

Verdict = Literal["KEEP", "REVIEW", "KILL"]

MIN_TRADES_BY_TIMEFRAME = {
    "M1": 50,
    "M5": 40,
    "M15": 30,
    "M30": 20,
    "H1": 15,
    "H4": 10,
    "D1": 8,
}


@dataclass(frozen=True)
class GateResult:
    verdict: Verdict
    failed_gate: str | None
    reason: str
    reason_codes: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)


def run_gates(
    metrics: dict[str, float],
    timeframe: str = "M15",
    *,
    min_trades: int | None = None,
    max_drawdown: float = 0.20,
    min_profit_factor: float = 1.40,
    min_oos_sharpe: float = 1.0,
    min_param_stability: float = 0.70,
    min_win_rate: float = 0.40,
    max_consecutive_loss_ratio: float = 0.95,
    require_oos: bool = True,
) -> GateResult:
    """Return the structural promotion verdict for a candidate.

    Hard gates produce KILL. Soft gates produce REVIEW. KEEP is only possible
    when every required gate passes.
    """

    timeframe_key = timeframe.upper()
    required_trades = min_trades if min_trades is not None else MIN_TRADES_BY_TIMEFRAME.get(timeframe_key, 30)
    trade_count = _metric(metrics, "total_trades", "trade_count")
    drawdown = _metric(metrics, "max_drawdown", default=1.0)
    profit_factor = _metric(metrics, "profit_factor")
    win_rate = _metric(metrics, "win_rate")
    max_consecutive_losses = _metric(metrics, "max_consecutive_losses", "consecutive_losses")
    consecutive_loss_ratio = max_consecutive_losses / trade_count if trade_count else 0.0
    scores = {
        "trade_count": trade_count,
        "min_trades": float(required_trades),
        "max_drawdown": drawdown,
        "profit_factor": profit_factor,
        "win_rate": win_rate,
        "consecutive_loss_ratio": consecutive_loss_ratio,
    }

    if trade_count < required_trades:
        return GateResult(
            verdict="KILL",
            failed_gate="min_trades",
            reason=f"Only {trade_count:.0f} trades; minimum is {required_trades}. Low-trade winner blocked.",
            reason_codes=["SEARCH_MIN_TRADES_NOT_MET"],
            scores=scores,
        )

    if drawdown > max_drawdown:
        return GateResult(
            verdict="KILL",
            failed_gate="max_drawdown",
            reason=f"Drawdown {drawdown:.1%} exceeds {max_drawdown:.1%} hard limit.",
            reason_codes=["SEARCH_DRAWDOWN_TOO_HIGH"],
            scores=scores,
        )

    if trade_count >= required_trades and consecutive_loss_ratio >= max_consecutive_loss_ratio:
        return GateResult(
            verdict="KILL",
            failed_gate="consecutive_loss_ratio",
            reason=f"Consecutive loss ratio {consecutive_loss_ratio:.1%} exceeds {max_consecutive_loss_ratio:.1%} hard limit.",
            reason_codes=["SEARCH_DIRECTIONAL_FAILURE"],
            scores=scores,
        )

    soft_fails: list[str] = []
    reason_codes: list[str] = []
    if profit_factor < min_profit_factor:
        soft_fails.append(f"profit_factor {profit_factor:.2f} < {min_profit_factor:.2f}")
        reason_codes.append("SEARCH_PROFIT_FACTOR_NOT_MET")

    has_oos = "sharpe_oos" in metrics or "oos_sharpe" in metrics
    if require_oos or has_oos:
        oos_sharpe = _metric(metrics, "sharpe_oos", "oos_sharpe")
        scores["sharpe_oos"] = oos_sharpe
        if oos_sharpe < min_oos_sharpe:
            soft_fails.append(f"OOS sharpe {oos_sharpe:.2f} < {min_oos_sharpe:.2f}")
            reason_codes.append("SEARCH_OOS_SHARPE_NOT_MET")

    has_stability = "param_stability" in metrics or "parameter_stability" in metrics
    if require_oos or has_stability:
        stability = _metric(metrics, "param_stability", "parameter_stability")
        scores["param_stability"] = stability
        if stability < min_param_stability:
            soft_fails.append(f"parameter stability {stability:.2f} < {min_param_stability:.2f}")
            reason_codes.append("SEARCH_PARAMETER_STABILITY_NOT_MET")

    has_bootstrap = "bootstrap_ci_spans_zero" in metrics or "bootstrap_ci_lower" in metrics or "bootstrap_ci_upper" in metrics
    if require_oos and has_bootstrap:
        ci_lower = _metric(metrics, "bootstrap_ci_lower", default=0.0)
        ci_upper = _metric(metrics, "bootstrap_ci_upper", default=0.0)
        spans_zero = bool(metrics.get("bootstrap_ci_spans_zero", ci_lower <= 0.0 <= ci_upper))
        scores["bootstrap_ci_lower"] = ci_lower
        scores["bootstrap_ci_upper"] = ci_upper
        scores["bootstrap_ci_spans_zero"] = 1.0 if spans_zero else 0.0
        if spans_zero:
            soft_fails.append("bootstrap CI spans zero")
            reason_codes.append("BOOTSTRAP_CI_SPANS_ZERO")

    if win_rate < min_win_rate:
        soft_fails.append(f"win_rate {win_rate:.1%} < {min_win_rate:.1%}")
        reason_codes.append("SEARCH_WIN_RATE_NOT_MET")

    if soft_fails:
        return GateResult(
            verdict="REVIEW",
            failed_gate="soft_gates",
            reason="; ".join(soft_fails),
            reason_codes=reason_codes,
            scores=scores,
        )

    return GateResult(
        verdict="KEEP",
        failed_gate=None,
        reason="All structural gates passed.",
        reason_codes=[],
        scores=scores,
    )


def _metric(metrics: dict[str, float], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = metrics.get(key)
        if value is not None:
            try:
                f = float(value)
                return f if math.isfinite(f) else default
            except (TypeError, ValueError):
                return default
    return default

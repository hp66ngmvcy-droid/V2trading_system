"""Strategy scoring and verdicts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScoreResult:
    score: float
    verdict: str
    reason_codes: list[str]


def score_strategy(
    metrics: dict[str, float],
    walk_forward_metrics: dict[str, Any] | None = None,
    timeframe: str = "M15",
    require_walk_forward: bool = False,
) -> ScoreResult:
    win_rate = metrics.get("win_rate", 0.0)
    profit_factor = metrics.get("profit_factor", 0.0)
    drawdown = metrics.get("max_drawdown", 1.0)
    trade_count = metrics.get("total_trades", 0.0)
    expectancy = metrics.get("expectancy", 0.0)
    reasons: list[str] = []
    score = 0.0
    score += min(win_rate, 0.75) / 0.75 * 20
    score += min(profit_factor, 3.0) / 3.0 * 25
    score += max(0.0, 1 - drawdown / 0.3) * 25
    score += min(trade_count, 50) / 50 * 15
    score += 15 if expectancy > 0 else 0
    if trade_count < 20:
        score -= 15
        reasons.append("LOW_TRADE_COUNT")
    if drawdown > 0.2:
        score -= 20
        reasons.append("HIGH_DRAWDOWN")
    if profit_factor < 1.0:
        reasons.append("WEAK_PROFIT_FACTOR")
    if require_walk_forward:
        reasons.extend(_walk_forward_reason_codes(walk_forward_metrics))
    score = max(0.0, min(100.0, score))
    verdict = "KEEP" if score >= 70 and not reasons else "REVIEW" if score >= 45 else "KILL"
    return ScoreResult(score=round(score, 2), verdict=verdict, reason_codes=reasons)


def _walk_forward_reason_codes(walk_forward_metrics: dict[str, Any] | None) -> list[str]:
    if not walk_forward_metrics:
        return ["WF_NOT_RUN"]
    split_count = int(walk_forward_metrics.get("split_count", walk_forward_metrics.get("window_count", 0)) or 0)
    if split_count <= 0 or walk_forward_metrics.get("ran") is False:
        return ["WF_NOT_RUN"]
    stitched = walk_forward_metrics.get("stitched_metrics", walk_forward_metrics)
    reasons: list[str] = []
    if float(stitched.get("total_trades", 0.0) or 0.0) <= 0:
        reasons.append("WF_NO_TRADES")
    if float(stitched.get("max_drawdown", 0.0) or 0.0) > 0.20:
        reasons.append("WF_HIGH_DRAWDOWN")
    if float(stitched.get("profit_factor", 0.0) or 0.0) < 1.10:
        reasons.append("WF_WEAK_PROFIT_FACTOR")
    stability = float(walk_forward_metrics.get("parameter_stability_score", 0.0) or 0.0)
    if stability <= 0.0:
        stability_payload = walk_forward_metrics.get("parameter_stability", {})
        if isinstance(stability_payload, dict):
            stability = float(stability_payload.get("stability_score", 0.0) or 0.0)
    if stability < 50.0:
        reasons.append("WF_UNSTABLE_PARAMETERS")
    bootstrap_ci = walk_forward_metrics.get("bootstrap_ci", {})
    if isinstance(bootstrap_ci, dict) and bool(bootstrap_ci.get("spans_zero", False)):
        reasons.append("WF_BOOTSTRAP_CI_SPANS_ZERO")
    return reasons

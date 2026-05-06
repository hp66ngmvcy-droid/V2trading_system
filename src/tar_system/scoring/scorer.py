"""Strategy scoring and verdicts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoreResult:
    score: float
    verdict: str
    reason_codes: list[str]


def score_strategy(metrics: dict[str, float]) -> ScoreResult:
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
    score = max(0.0, min(100.0, score))
    verdict = "KEEP" if score >= 70 else "REVIEW" if score >= 45 else "KILL"
    return ScoreResult(score=round(score, 2), verdict=verdict, reason_codes=reasons)

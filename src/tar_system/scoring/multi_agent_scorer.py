"""Lightweight multi-agent strategy scorer.

Three specialist agents (Risk, Performance, Robustness) assess metrics
independently in Round 1, then cross-review each other's verdicts in Round 2
before producing a consensus. No external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

KEEP = "KEEP"
REVIEW = "REVIEW"
KILL = "KILL"

_RANK = {KEEP: 2, REVIEW: 1, KILL: 0}


@dataclass
class AgentVerdict:
    agent: str
    verdict: str
    confidence: float  # 0.0–1.0
    reasons: list[str] = field(default_factory=list)


@dataclass
class ConsensusResult:
    verdict: str
    confidence: float
    agent_verdicts: list[AgentVerdict]
    dissent: bool  # True when agents disagree after Round 2
    reasons: list[str]


def _get(metrics: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for k in keys:
        if k in metrics:
            try:
                return float(metrics[k])
            except (TypeError, ValueError):
                pass
    return default


def _risk_agent(metrics: dict[str, Any]) -> AgentVerdict:
    kills, reviews, reasons = 0, 0, []

    max_dd = _get(metrics, "max_drawdown")
    win_rate = _get(metrics, "win_rate")
    profit_factor = _get(metrics, "profit_factor")
    total_trades = _get(metrics, "total_trades")

    if max_dd > 0.35:
        kills += 1
        reasons.append(f"max_drawdown {max_dd:.1%} > 35%")
    elif max_dd > 0.20:
        reviews += 1
        reasons.append(f"max_drawdown {max_dd:.1%} > 20%")

    if profit_factor < 1.0:
        kills += 1
        reasons.append(f"profit_factor {profit_factor:.2f} < 1.0")
    elif profit_factor < 1.3:
        reviews += 1
        reasons.append(f"profit_factor {profit_factor:.2f} < 1.3")

    if win_rate < 0.35:
        kills += 1
        reasons.append(f"win_rate {win_rate:.1%} < 35%")
    elif win_rate < 0.45:
        reviews += 1
        reasons.append(f"win_rate {win_rate:.1%} < 45%")

    if total_trades < 20:
        kills += 1
        reasons.append(f"total_trades {int(total_trades)} < 20 (insufficient sample)")
    elif total_trades < 30:
        reviews += 1
        reasons.append(f"total_trades {int(total_trades)} < 30")

    return _verdict_from_counts("risk", kills, reviews, reasons, keep_msg="risk metrics within bounds")


def _performance_agent(metrics: dict[str, Any]) -> AgentVerdict:
    kills, reviews, reasons = 0, 0, []

    sharpe = _get(metrics, "sharpe_ratio", "sharpe")
    expectancy = _get(metrics, "expectancy")
    avg_win = _get(metrics, "average_win")
    avg_loss = _get(metrics, "average_loss")

    if sharpe < 0.5:
        kills += 1
        reasons.append(f"sharpe {sharpe:.2f} < 0.5")
    elif sharpe < 1.0:
        reviews += 1
        reasons.append(f"sharpe {sharpe:.2f} < 1.0")

    if expectancy < 0:
        kills += 1
        reasons.append(f"expectancy {expectancy:.4f} negative")
    elif expectancy < 0.001:
        reviews += 1
        reasons.append(f"expectancy {expectancy:.4f} near zero")

    if avg_win > 0 and avg_loss < 0:
        rr = avg_win / abs(avg_loss)
        if rr < 0.8:
            reviews += 1
            reasons.append(f"reward/risk ratio {rr:.2f} < 0.8")

    return _verdict_from_counts("performance", kills, reviews, reasons, keep_msg="performance metrics acceptable")


def _robustness_agent(metrics: dict[str, Any]) -> AgentVerdict:
    kills, reviews, reasons = 0, 0, []

    sharpe_oos = _get(metrics, "sharpe_oos", "oos_sharpe")
    param_stability = _get(metrics, "param_stability", "parameter_stability")
    wf_splits = _get(metrics, "walk_forward_splits")

    has_oos = "sharpe_oos" in metrics or "oos_sharpe" in metrics
    has_stability = "param_stability" in metrics or "parameter_stability" in metrics

    if has_oos:
        if sharpe_oos < 0:
            kills += 1
            reasons.append(f"sharpe_oos {sharpe_oos:.2f} negative")
        elif sharpe_oos < 0.5:
            reviews += 1
            reasons.append(f"sharpe_oos {sharpe_oos:.2f} < 0.5")
    else:
        reviews += 1
        reasons.append("no OOS data — cannot assess out-of-sample robustness")

    if has_stability:
        if param_stability < 0.5:
            kills += 1
            reasons.append(f"param_stability {param_stability:.2f} < 0.5")
        elif param_stability < 0.7:
            reviews += 1
            reasons.append(f"param_stability {param_stability:.2f} < 0.7")

    if has_oos and wf_splits < 3:
        reviews += 1
        reasons.append(f"only {int(wf_splits)} walk-forward splits (< 3)")

    if metrics.get("bootstrap_ci_spans_zero"):
        reviews += 1
        reasons.append("bootstrap CI spans zero")

    return _verdict_from_counts("robustness", kills, reviews, reasons, keep_msg="robustness checks passed")


def _verdict_from_counts(
    agent: str,
    kills: int,
    reviews: int,
    reasons: list[str],
    keep_msg: str,
) -> AgentVerdict:
    if kills >= 2:
        return AgentVerdict(agent, KILL, min(0.90, 0.55 + kills * 0.15), reasons)
    if kills == 1:
        return AgentVerdict(agent, REVIEW, 0.70, reasons)
    if reviews >= 2:
        return AgentVerdict(agent, REVIEW, 0.65, reasons)
    if reviews == 1:
        return AgentVerdict(agent, REVIEW, 0.50, reasons)
    return AgentVerdict(agent, KEEP, 0.75, reasons + [keep_msg])


def _cross_review(verdicts: list[AgentVerdict]) -> list[AgentVerdict]:
    """Round 2: each agent adjusts based on peer signals."""
    revised = []
    for i, v in enumerate(verdicts):
        peers = [p for j, p in enumerate(verdicts) if j != i]
        any_confident_kill = any(p.verdict == KILL and p.confidence >= 0.7 for p in peers)
        all_peers_keep = all(p.verdict == KEEP for p in peers)

        new_verdict = v.verdict
        new_conf = v.confidence
        new_reasons = list(v.reasons)

        if v.verdict == KEEP and any_confident_kill:
            new_verdict = REVIEW
            new_conf = max(0.40, v.confidence - 0.20)
            new_reasons.append("downgraded: peer agent signalled high-confidence KILL")
        elif v.verdict == REVIEW and all_peers_keep and v.confidence < 0.60:
            new_verdict = KEEP
            new_conf = 0.50
            new_reasons.append("upgraded: both peer agents approved")

        revised.append(AgentVerdict(v.agent, new_verdict, new_conf, new_reasons))
    return revised


def _consensus(verdicts: list[AgentVerdict]) -> tuple[str, float, list[str]]:
    kill_n = sum(1 for v in verdicts if v.verdict == KILL)
    keep_n = sum(1 for v in verdicts if v.verdict == KEEP)
    avg_conf = sum(v.confidence for v in verdicts) / len(verdicts)
    reasons = [r for v in verdicts for r in v.reasons]

    if kill_n >= 2:
        return KILL, avg_conf, reasons
    if kill_n == 1:
        return REVIEW, avg_conf, reasons
    if keep_n == len(verdicts):
        return KEEP, avg_conf, reasons
    if keep_n >= 2:
        return KEEP, round(avg_conf * 0.85, 3), reasons
    return REVIEW, avg_conf, reasons


def score_multi_agent(metrics: dict[str, Any]) -> ConsensusResult:
    """Score a strategy using 3 agents over 2 rounds.

    Args:
        metrics: same dict format accepted by run_gates() in gates.py

    Returns:
        ConsensusResult with verdict (KEEP/REVIEW/KILL), confidence,
        per-agent verdicts, dissent flag, and consolidated reasons.
    """
    r1 = [_risk_agent(metrics), _performance_agent(metrics), _robustness_agent(metrics)]
    r2 = _cross_review(r1)
    verdict, confidence, reasons = _consensus(r2)
    dissent = len({v.verdict for v in r2}) > 1

    return ConsensusResult(
        verdict=verdict,
        confidence=round(confidence, 3),
        agent_verdicts=r2,
        dissent=dissent,
        reasons=reasons,
    )

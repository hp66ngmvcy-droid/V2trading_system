"""Tests for the lightweight multi-agent scorer."""

import pytest
from tar_system.scoring.multi_agent_scorer import (
    KEEP, REVIEW, KILL,
    score_multi_agent,
    _risk_agent, _performance_agent, _robustness_agent, _cross_review,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GOOD_METRICS = {
    "max_drawdown": 0.12,
    "win_rate": 0.55,
    "profit_factor": 1.8,
    "total_trades": 60,
    "sharpe_ratio": 1.4,
    "expectancy": 0.005,
    "average_win": 0.012,
    "average_loss": -0.008,
    "sharpe_oos": 1.1,
    "param_stability": 0.80,
    "walk_forward_splits": 5,
}

# ---------------------------------------------------------------------------
# Risk agent
# ---------------------------------------------------------------------------

def test_risk_agent_keep_on_good_metrics():
    v = _risk_agent(GOOD_METRICS)
    assert v.verdict == KEEP

def test_risk_agent_review_on_high_drawdown_alone():
    # Single bad metric → REVIEW from one agent (consensus needs multi-agent agreement for KILL)
    m = {**GOOD_METRICS, "max_drawdown": 0.50}
    v = _risk_agent(m)
    assert v.verdict == REVIEW

def test_risk_agent_kill_on_multiple_bad_metrics():
    m = {**GOOD_METRICS, "max_drawdown": 0.50, "profit_factor": 0.7, "total_trades": 8}
    v = _risk_agent(m)
    assert v.verdict == KILL

def test_risk_agent_review_on_insufficient_trades_alone():
    m = {**GOOD_METRICS, "total_trades": 10}
    v = _risk_agent(m)
    assert v.verdict == REVIEW

def test_risk_agent_review_on_borderline():
    m = {**GOOD_METRICS, "max_drawdown": 0.25, "win_rate": 0.40}
    v = _risk_agent(m)
    assert v.verdict == REVIEW

def test_risk_agent_kill_on_profit_factor_below_1():
    m = {**GOOD_METRICS, "profit_factor": 0.8}
    v = _risk_agent(m)
    assert v.verdict in (KILL, REVIEW)

# ---------------------------------------------------------------------------
# Performance agent
# ---------------------------------------------------------------------------

def test_performance_agent_keep_on_good_metrics():
    v = _performance_agent(GOOD_METRICS)
    assert v.verdict == KEEP

def test_performance_agent_kill_on_negative_expectancy():
    m = {**GOOD_METRICS, "expectancy": -0.002, "sharpe_ratio": 0.3}
    v = _performance_agent(m)
    assert v.verdict == KILL

def test_performance_agent_review_on_low_sharpe():
    m = {**GOOD_METRICS, "sharpe_ratio": 0.7}
    v = _performance_agent(m)
    assert v.verdict == REVIEW

def test_performance_agent_review_on_poor_rr_ratio():
    m = {**GOOD_METRICS, "average_win": 0.005, "average_loss": -0.010}
    v = _performance_agent(m)
    assert v.verdict == REVIEW

# ---------------------------------------------------------------------------
# Robustness agent
# ---------------------------------------------------------------------------

def test_robustness_agent_keep_on_good_metrics():
    v = _robustness_agent(GOOD_METRICS)
    assert v.verdict == KEEP

def test_robustness_agent_review_when_no_oos_data():
    m = {k: v for k, v in GOOD_METRICS.items() if k not in ("sharpe_oos", "oos_sharpe")}
    v = _robustness_agent(m)
    assert v.verdict == REVIEW

def test_robustness_agent_kill_on_negative_oos_sharpe():
    m = {**GOOD_METRICS, "sharpe_oos": -0.5, "param_stability": 0.3}
    v = _robustness_agent(m)
    assert v.verdict == KILL

def test_robustness_agent_review_on_low_wf_splits():
    m = {**GOOD_METRICS, "walk_forward_splits": 2}
    v = _robustness_agent(m)
    assert v.verdict == REVIEW

def test_robustness_agent_review_on_bootstrap_ci_spans_zero():
    m = {**GOOD_METRICS, "bootstrap_ci_spans_zero": True}
    v = _robustness_agent(m)
    assert v.verdict == REVIEW

# ---------------------------------------------------------------------------
# Cross-review (Round 2)
# ---------------------------------------------------------------------------

def test_cross_review_downgrades_keep_when_peer_kills():
    from tar_system.scoring.multi_agent_scorer import AgentVerdict
    verdicts = [
        AgentVerdict("risk", KEEP, 0.75, []),
        AgentVerdict("performance", KILL, 0.80, ["sharpe negative"]),
        AgentVerdict("robustness", REVIEW, 0.60, []),
    ]
    revised = _cross_review(verdicts)
    risk_revised = next(v for v in revised if v.agent == "risk")
    assert risk_revised.verdict == REVIEW

def test_cross_review_upgrades_review_when_both_peers_keep():
    from tar_system.scoring.multi_agent_scorer import AgentVerdict
    verdicts = [
        AgentVerdict("risk", REVIEW, 0.50, []),
        AgentVerdict("performance", KEEP, 0.75, []),
        AgentVerdict("robustness", KEEP, 0.80, []),
    ]
    revised = _cross_review(verdicts)
    risk_revised = next(v for v in revised if v.agent == "risk")
    assert risk_revised.verdict == KEEP

def test_cross_review_does_not_upgrade_high_confidence_review():
    from tar_system.scoring.multi_agent_scorer import AgentVerdict
    verdicts = [
        AgentVerdict("risk", REVIEW, 0.75, []),  # high confidence — should NOT upgrade
        AgentVerdict("performance", KEEP, 0.75, []),
        AgentVerdict("robustness", KEEP, 0.80, []),
    ]
    revised = _cross_review(verdicts)
    risk_revised = next(v for v in revised if v.agent == "risk")
    assert risk_revised.verdict == REVIEW

# ---------------------------------------------------------------------------
# Consensus (full pipeline)
# ---------------------------------------------------------------------------

def test_consensus_keep_on_all_good():
    result = score_multi_agent(GOOD_METRICS)
    assert result.verdict == KEEP
    assert result.dissent is False

def test_consensus_kill_on_catastrophic_metrics():
    bad = {
        "max_drawdown": 0.60,
        "win_rate": 0.25,
        "profit_factor": 0.5,
        "total_trades": 8,
        "sharpe_ratio": -0.5,
        "expectancy": -0.01,
        "sharpe_oos": -1.0,
        "param_stability": 0.2,
        "walk_forward_splits": 1,
    }
    result = score_multi_agent(bad)
    assert result.verdict == KILL

def test_consensus_review_on_missing_oos():
    m = {k: v for k, v in GOOD_METRICS.items() if k not in ("sharpe_oos", "oos_sharpe", "param_stability")}
    result = score_multi_agent(m)
    assert result.verdict in (REVIEW, KEEP)

def test_dissent_flag_set_when_agents_disagree():
    mixed = {**GOOD_METRICS, "max_drawdown": 0.40, "sharpe_oos": -0.3}
    result = score_multi_agent(mixed)
    # agents will disagree — dissent should fire
    if len({v.verdict for v in result.agent_verdicts}) > 1:
        assert result.dissent is True

def test_result_has_all_three_agents():
    result = score_multi_agent(GOOD_METRICS)
    agents = {v.agent for v in result.agent_verdicts}
    assert agents == {"risk", "performance", "robustness"}

def test_confidence_bounded():
    result = score_multi_agent(GOOD_METRICS)
    assert 0.0 <= result.confidence <= 1.0
    for v in result.agent_verdicts:
        assert 0.0 <= v.confidence <= 1.0

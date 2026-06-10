from __future__ import annotations

import pandas as pd

from tar_system.scoring.gates import run_gates
from tar_system.validation.bootstrap_ci import bootstrap_mean_ci
from tar_system.validation.null_model import run_null_model


def test_bootstrap_ci_spans_zero_for_noise() -> None:
    returns = [-1.0, 1.0] * 100

    result = bootstrap_mean_ci(returns, n_iterations=1000, seed=7)

    assert result["spans_zero"] is True
    assert result["ci_lower"] < 0 < result["ci_upper"]


def test_bootstrap_ci_blocks_clear_positive_edge_less_often() -> None:
    returns = [0.20, 0.35, 0.40, 0.15, 0.30] * 40

    result = bootstrap_mean_ci(returns, n_iterations=1000, seed=7)

    assert result["spans_zero"] is False
    assert result["ci_lower"] > 0


def test_gate_reviews_when_bootstrap_ci_spans_zero() -> None:
    metrics = {
        "total_trades": 60,
        "win_rate": 0.58,
        "profit_factor": 1.8,
        "max_drawdown": 0.08,
        "sharpe_oos": 1.4,
        "param_stability": 0.85,
        "bootstrap_ci_lower": -0.01,
        "bootstrap_ci_upper": 0.05,
        "bootstrap_ci_spans_zero": True,
    }

    gate = run_gates(metrics, "M15", require_oos=True)

    assert gate.verdict == "REVIEW"
    assert "BOOTSTRAP_CI_SPANS_ZERO" in gate.reason_codes


def test_gate_keeps_when_statistical_validation_passes() -> None:
    metrics = {
        "total_trades": 60,
        "win_rate": 0.58,
        "profit_factor": 1.8,
        "max_drawdown": 0.08,
        "sharpe_oos": 1.4,
        "param_stability": 0.85,
        "bootstrap_ci_lower": 0.01,
        "bootstrap_ci_upper": 0.05,
        "bootstrap_ci_spans_zero": False,
    }

    gate = run_gates(metrics, "M15", require_oos=True)

    assert gate.verdict == "KEEP"


def test_gate_keeps_when_no_bootstrap_data_but_oos_passes() -> None:
    # Regression: require_oos=True with no bootstrap keys must not produce a
    # false BOOTSTRAP_CI_SPANS_ZERO soft-fail. Previously, the gate defaulted
    # ci_lower=0.0/ci_upper=0.0 and evaluated spans_zero=True unconditionally.
    metrics = {
        "total_trades": 60,
        "win_rate": 0.58,
        "profit_factor": 1.8,
        "max_drawdown": 0.08,
        "sharpe_oos": 1.4,
        "param_stability": 0.85,
    }

    gate = run_gates(metrics, "M15", require_oos=True)

    assert gate.verdict == "KEEP"
    assert "BOOTSTRAP_CI_SPANS_ZERO" not in gate.reason_codes


def test_null_model_reports_p_values() -> None:
    real_trades = [{"return_r": 0.5, "pnl": 50.0}, {"return_r": 0.4, "pnl": 40.0}]

    def runner(df: pd.DataFrame, params: dict[str, object]) -> list[dict[str, float]]:
        seed = int(params["random_seed"])
        value = -0.1 if seed % 2 else 0.1
        return [{"return_r": value, "pnl": value * 100}]

    result = run_null_model(real_trades, runner, pd.DataFrame({"close": [1, 2]}), {}, n_permutations=20, seed=1)

    assert 0.0 < result["p_value_mean_r"] <= 1.0
    assert 0.0 < result["p_value_pnl"] <= 1.0
    assert result["beats_null"] is True

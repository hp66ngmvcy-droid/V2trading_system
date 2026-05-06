"""GO / NO-GO gate for paper-only strategy research."""

from __future__ import annotations

from dataclasses import dataclass, field

from tar_system import settings


@dataclass
class CriterionResult:
    name: str
    passed: bool
    reason_code: str
    message: str


@dataclass
class GoNoGoResult:
    status: str
    passed: bool
    reason_codes: list[str] = field(default_factory=list)
    criteria: list[CriterionResult] = field(default_factory=list)


def evaluate_go_no_go(
    verdict: str,
    metrics: dict[str, float],
    walk_forward_exists: bool,
    monte_carlo: dict[str, float | bool | str] | None,
    parameter_sensitivity: dict[str, float | bool | str] | None,
    environment_state: str,
    beats_baseline_after_costs: bool = True,
    regime_count: int = 2,
    audit_trail_exists: bool = True,
    min_trades: int = 20,
    min_profit_factor: float = 1.1,
    max_drawdown: float = settings.DEFAULT_MAX_DRAWDOWN,
    walk_forward_oos_is_ratio: float = 1.0,
    realistic_score: float | None = 1.0,
    cost_sensitive: bool = False,
    positioning_context: dict[str, object] | None = None,
    waived_criteria: dict[str, str] | None = None,
) -> GoNoGoResult:
    criteria: list[CriterionResult] = []
    waived = waived_criteria or {}

    def add(name: str, passed: bool, reason: str, message: str) -> None:
        if not passed and name in waived:
            criteria.append(CriterionResult(name, True, f"WAIVED_{reason}", waived[name]))
        else:
            criteria.append(CriterionResult(name, passed, "" if passed else reason, message))

    if not settings.PAPER_MODE:
        add("paper_mode", False, "PAPER_MODE_DISABLED", "Paper mode must be enabled")
    if settings.LIVE_TRADING_ALLOWED:
        add("live_trading_disabled", False, "LIVE_TRADING_ENABLED", "Live trading must be disabled")
    if verdict not in {"KEEP", "REVIEW"}:
        add("verdict_allowed", False, "VERDICT_NOT_ALLOWED", "Verdict must be KEEP or REVIEW")
    average_loss = abs(metrics.get("average_loss", 0.0))
    exit_ratio = metrics.get("average_win", 0.0) / average_loss if average_loss else metrics.get("profit_factor", 0.0)
    add("C1_edge_plausibility", metrics.get("profit_factor", 0.0) > 1.2, "C1_EDGE_PLAUSIBILITY_FAIL", "Profit factor must be > 1.2")
    add("C2_overfitting_risk", walk_forward_oos_is_ratio > 0.6, "C2_OVERFITTING_RISK_FAIL", "Walk-forward OOS/IS ratio must be > 0.6")
    add("C3_sample_adequacy", metrics.get("total_trades", 0.0) >= 30, "C3_SAMPLE_ADEQUACY_FAIL", "Trade count must be >= 30")
    add("C4_regime_dependency", regime_count >= 2, "C4_REGIME_DEPENDENCY_FAIL", "Must perform in at least 2 regimes")
    add("C5_exit_calibration", exit_ratio >= 1.0, "C5_EXIT_CALIBRATION_FAIL", "Average win / average loss must be >= 1.0")
    add("C6_risk_concentration", metrics.get("max_drawdown", 1.0) < 0.2, "C6_RISK_CONCENTRATION_FAIL", "Max drawdown must be < 0.2")
    add("C7_execution_realism", realistic_score is not None and realistic_score > 0, "C7_EXECUTION_REALISM_FAIL", "Realistic cost score must exist and be > 0")
    add("C8_cost_sensitivity", cost_sensitive is False, "C8_COST_SENSITIVITY_FAIL", "Cost sensitive flag must be false")
    if not walk_forward_exists:
        add("walk_forward_exists", False, "MISSING_WALK_FORWARD", "Walk-forward artifact must exist")
    if not monte_carlo or float(monte_carlo.get("robustness_score", 0.0)) < 60.0:
        add("monte_carlo_robust", False, "WEAK_MONTE_CARLO", "Monte Carlo robustness must be acceptable")
    if not parameter_sensitivity or bool(parameter_sensitivity.get("fragile", True)):
        add("parameter_stability", False, "FRAGILE_PARAMETERS", "Parameters must not be fragile")
    if environment_state in {"HOLD_TRADING", "BLOCK_TRADING"}:
        add("environment_safe", False, f"ENVIRONMENT_{environment_state}", "Environment must not block testing")
    if not beats_baseline_after_costs:
        add("beats_baseline_after_costs", False, "FAILS_AFTER_COSTS", "Strategy must beat baseline after costs")
    if not audit_trail_exists:
        add("audit_trail_exists", False, "MISSING_AUDIT_TRAIL", "Audit trail must exist")
    if positioning_context and abs(float(positioning_context.get("positioning_score", 0.0) or 0.0)) >= 70.0:
        criteria.append(
            CriterionResult(
                "positioning_context_extreme",
                True,
                "POSITIONING_CONTEXT_ONLY",
                "Extreme positioning detected; context only, no automatic trade trigger",
            )
        )
    reasons = [item.reason_code for item in criteria if not item.passed and item.reason_code]
    if "C6_RISK_CONCENTRATION_FAIL" in reasons:
        reasons.append("HIGH_DRAWDOWN")
    passed = not reasons
    return GoNoGoResult("GO" if passed else "NO_GO", passed, reasons, criteria)

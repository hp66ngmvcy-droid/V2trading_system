"""Generate practical strategy improvement recommendations."""

from __future__ import annotations


def detect_pivot_triggers(
    optimiser_scores: list[float] | None = None,
    walk_forward: dict[str, float] | None = None,
    cost_sensitive: bool = False,
    metrics: dict[str, float] | None = None,
) -> dict[str, object]:
    triggers: list[str] = []
    scores = optimiser_scores or []
    if len(scores) >= 3:
        last_three = scores[-3:]
        baseline = max(abs(sum(last_three) / 3), 1.0)
        if (max(last_three) - min(last_three)) / baseline <= 0.05:
            triggers.append("IMPROVEMENT_PLATEAU")
    wf = walk_forward or {}
    if wf.get("is_sharpe", 0.0) and wf.get("oos_sharpe", 0.0) < 0.5 * wf.get("is_sharpe", 0.0):
        triggers.append("OVERFITTING_PROXY")
    if cost_sensitive:
        triggers.append("COST_DEFEAT")
    if (metrics or {}).get("max_consecutive_losses", 0.0) >= 5:
        triggers.append("TAIL_RISK")
    recommendation = ""
    if "COST_DEFEAT" in triggers:
        recommendation = "OBJECTIVE_REFRAME"
    elif "OVERFITTING_PROXY" in triggers:
        recommendation = "ARCHETYPE_SWITCH"
    elif triggers:
        recommendation = "ASSUMPTION_INVERSION"
    return {"pivot_required": bool(triggers), "triggers": triggers, "recommendation": recommendation}


def build_improvement_plan(
    metrics: dict[str, float],
    reason_codes: list[str],
    regime_flags: dict[str, str] | None = None,
    walk_forward_weak: bool = False,
    parameter_fragile: bool = False,
    optimiser_scores: list[float] | None = None,
    walk_forward: dict[str, float] | None = None,
    cost_sensitive: bool = False,
) -> list[str]:
    plan: list[str] = []
    if metrics.get("max_drawdown", 0.0) > 0.15 or "HIGH_DRAWDOWN" in reason_codes:
        plan.append("Reduce position size, add a volatility cap, and widen the validation window.")
    if metrics.get("total_trades", 0.0) < 20 or "LOW_TRADE_COUNT" in reason_codes:
        plan.append("Review timeframe selection or loosen the entry filter slightly.")
    if "SPREAD_SENSITIVE" in reason_codes or "FAILS_AFTER_COSTS" in reason_codes:
        plan.append("Add a max spread filter and retest after costs.")
    flags = regime_flags or {}
    if flags.get("VOLATILE") == "avoid regime":
        plan.append("Block this strategy during VOLATILE regime.")
    if flags.get("RANGING") == "avoid regime":
        plan.append("Add a trend-only filter to avoid ranging chop.")
    if walk_forward_weak:
        plan.append("KILL or RETEST with simpler parameters because walk-forward is weak.")
    if parameter_fragile:
        plan.append("Reduce optimisation range or simplify the strategy parameters.")
    pivot = detect_pivot_triggers(optimiser_scores, walk_forward, cost_sensitive, metrics)
    if pivot["pivot_required"]:
        plan.append(f"Pivot required: {', '.join(pivot['triggers'])}. Recommended action: {pivot['recommendation']}.")
    if not plan:
        plan.append("Keep monitoring with paper-only forward tests and stable validation windows.")
    return plan

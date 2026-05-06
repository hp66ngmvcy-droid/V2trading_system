"""Risk + strategy optimiser for local paper-only research."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.optimisation.artifacts import load_regime_trades, load_validation_artifacts
from tar_system.optimisation.go_no_go_gate import evaluate_go_no_go
from tar_system.optimisation.regime_heatmap import RegimeHeatmap, build_regime_heatmap
from tar_system.optimisation.strategy_improvement_planner import build_improvement_plan
from tar_system.reporting.review_log import load_review_results
from tar_system.settings import LOG_DIR

DECISIONS = {"KEEP", "REVIEW", "KILL", "RETEST", "REDUCE_RISK", "PAUSE", "PROMOTE_CANDIDATE"}


@dataclass
class OptimiserResult:
    optimiser_score: float
    optimiser_decision: str
    risk_adjustment: str
    improvement_plan: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    go_no_go_status: str = "NO_GO"
    regime_heatmap: dict[str, Any] = field(default_factory=dict)
    positioning_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskStrategyOptimiser:
    min_trades: int = 20

    def optimise(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        latest_metrics: dict[str, float],
        verdict: str = "REVIEW",
        walk_forward_metrics: dict[str, float] | None = None,
        monte_carlo: dict[str, float | bool | str] | None = None,
        parameter_sensitivity: dict[str, float | bool | str] | None = None,
        environment_state: str = "REVIEW_ONLY",
        regime_trades: list[dict[str, object]] | None = None,
        beats_baseline_after_costs: bool = True,
        audit_trail_exists: bool = True,
        write_outputs: bool = True,
    ) -> OptimiserResult:
        try:
            from tar_system.positioning.scorer import get_positioning_context

            positioning = get_positioning_context(symbol)
        except Exception:
            positioning = {}
        heatmap = build_regime_heatmap(regime_trades or [])
        go = evaluate_go_no_go(
            verdict,
            latest_metrics,
            walk_forward_exists=walk_forward_metrics is not None,
            monte_carlo=monte_carlo,
            parameter_sensitivity=parameter_sensitivity,
            environment_state=environment_state,
            beats_baseline_after_costs=beats_baseline_after_costs,
            regime_count=sum(1 for item in heatmap.regimes.values() if item.trade_count >= 5),
            audit_trail_exists=audit_trail_exists,
            min_trades=self.min_trades,
            positioning_context=positioning,
        )
        score = _optimiser_score(latest_metrics, monte_carlo, parameter_sensitivity, go.reason_codes)
        decision = _decision(score, go.reason_codes, environment_state, verdict)
        risk_adjustment = _risk_adjustment(decision, environment_state, latest_metrics)
        regime_flags = {regime: summary.flag for regime, summary in heatmap.regimes.items()}
        plan = build_improvement_plan(
            latest_metrics,
            go.reason_codes,
            regime_flags,
            walk_forward_weak="MISSING_WALK_FORWARD" in go.reason_codes,
            parameter_fragile="FRAGILE_PARAMETERS" in go.reason_codes,
        )
        next_actions = _next_actions(decision)
        if abs(float(positioning.get("positioning_score", 0.0) or 0.0)) >= 70.0:
            plan.append("Review extreme positioning context before changing strategy assumptions")
            next_actions.append("REVIEW_POSITIONING_CONTEXT")
        result = OptimiserResult(
            optimiser_score=score,
            optimiser_decision=decision,
            risk_adjustment=risk_adjustment,
            improvement_plan=plan,
            reason_codes=go.reason_codes,
            next_actions=next_actions,
            go_no_go_status=go.status,
            regime_heatmap={key: asdict(value) for key, value in heatmap.regimes.items()},
            positioning_context=positioning,
        )
        if write_outputs:
            append_optimiser_review(strategy, symbol, timeframe, result)
            export_optimiser_note(strategy, symbol, timeframe, result)
        return result

    def optimise_from_logs(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        environment_state: str = "REVIEW_ONLY",
        write_outputs: bool = True,
    ) -> OptimiserResult:
        rows = [
            row
            for row in load_review_results()
            if row.get("strategy") == strategy and row.get("symbol") == symbol and row.get("timeframe") == timeframe
        ]
        latest = rows[-1] if rows else {"metrics": {}, "verdict": "REVIEW"}
        artifacts = load_validation_artifacts(strategy, symbol, timeframe)
        return self.optimise(
            strategy,
            symbol,
            timeframe,
            dict(latest.get("metrics", {})),
            str(latest.get("verdict", "REVIEW")),
            walk_forward_metrics=artifacts["walk_forward_metrics"],
            monte_carlo=artifacts["monte_carlo"],
            parameter_sensitivity=artifacts["parameter_sensitivity"],
            environment_state=environment_state,
            regime_trades=load_regime_trades(strategy, symbol, timeframe),
            audit_trail_exists=bool(rows),
            write_outputs=write_outputs,
        )


def append_optimiser_review(strategy: str, symbol: str, timeframe: str, result: OptimiserResult) -> Path:
    path = Path(LOG_DIR) / "review_log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "symbol": symbol,
        "timeframe": timeframe,
        "optimiser_score": result.optimiser_score,
        "optimiser_decision": result.optimiser_decision,
        "risk_adjustment": result.risk_adjustment,
        "reason_codes": result.reason_codes,
        "next_actions": result.next_actions,
        "positioning_context": result.positioning_context,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=str) + "\n")
    return path


def export_optimiser_note(strategy: str, symbol: str, timeframe: str, result: OptimiserResult, root: str | Path = "obsidian") -> Path:
    vault = Path(root)
    folder = vault / "60_Optimiser"
    folder.mkdir(parents=True, exist_ok=True)
    decision_tag = result.optimiser_decision.lower()
    tags = ["#type/optimiser", f"#decision/{decision_tag}"]
    if result.risk_adjustment == "REDUCE_RISK":
        tags.append("#risk/reduce")
    if result.risk_adjustment == "PAUSE":
        tags.append("#risk/pause")
    if "VOLATILE" in [code.replace("AVOID_", "") for code in result.reason_codes]:
        tags.append("#regime/avoid_volatile")
    content = [
        "---",
        f'type: "optimiser"',
        f'strategy: "{strategy}"',
        f'asset: "{symbol}"',
        f'timeframe: "{timeframe}"',
        f"score: {result.optimiser_score}",
        f'decision: "{result.optimiser_decision}"',
        f"tags: {json.dumps(tags)}",
        "---",
        "",
        f"# Optimiser {strategy} {symbol} {timeframe}",
        "",
        f"- Strategy note: [[{strategy}_{symbol}_{timeframe}]]",
        f"- GO / NO-GO: {result.go_no_go_status}",
        f"- Risk adjustment: {result.risk_adjustment}",
        f"- Positioning context: {result.positioning_context.get('bias', 'NEUTRAL')} score={result.positioning_context.get('positioning_score', 0.0)}",
        "",
        "## Improvement Plan",
    ]
    content.extend(f"- {item}" for item in result.improvement_plan)
    path = folder / f"{strategy}_{symbol}_{timeframe}_optimiser.md"
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def _optimiser_score(
    metrics: dict[str, float],
    monte_carlo: dict[str, float | bool | str] | None,
    parameter_sensitivity: dict[str, float | bool | str] | None,
    reason_codes: list[str],
) -> float:
    score = 100.0
    score -= max(0.0, metrics.get("max_drawdown", 0.0) - 0.05) * 150
    score -= max(0.0, 20 - metrics.get("total_trades", 0.0)) * 1.5
    score += min(metrics.get("profit_factor", 0.0), 2.0) * 8
    if monte_carlo:
        score += (float(monte_carlo.get("robustness_score", 0.0)) - 60.0) * 0.25
    if parameter_sensitivity:
        score += (float(parameter_sensitivity.get("stability_score", 0.0)) - 60.0) * 0.2
    score -= len(reason_codes) * 6
    return round(max(0.0, min(100.0, score)), 2)


def _decision(score: float, reasons: list[str], environment_state: str, verdict: str) -> str:
    if environment_state == "BLOCK_TRADING":
        return "PAUSE"
    if "HIGH_DRAWDOWN" in reasons or "FAILS_AFTER_COSTS" in reasons:
        return "REDUCE_RISK"
    if "FRAGILE_PARAMETERS" in reasons or "MISSING_WALK_FORWARD" in reasons:
        return "RETEST"
    if verdict == "KILL" or score < 35:
        return "KILL"
    if score >= 75 and verdict == "KEEP":
        return "PROMOTE_CANDIDATE"
    if score >= 60:
        return "KEEP"
    return "REVIEW"


def _risk_adjustment(decision: str, environment_state: str, metrics: dict[str, float]) -> str:
    if environment_state in {"HOLD_TRADING", "BLOCK_TRADING"} or decision == "PAUSE":
        return "PAUSE"
    if decision == "REDUCE_RISK" or metrics.get("max_drawdown", 0.0) > 0.12:
        return "REDUCE_RISK"
    return "STANDARD_PAPER_RISK"


def _next_actions(decision: str) -> list[str]:
    if decision == "PROMOTE_CANDIDATE":
        return ["REQUEST_HUMAN_APPROVAL", "EXPORT_OBSIDIAN", "KEEP_PAPER_ONLY"]
    if decision == "RETEST":
        return ["RUN_WALK_FORWARD", "RUN_MONTE_CARLO", "RUN_PARAMETER_SENSITIVITY"]
    if decision == "REDUCE_RISK":
        return ["REDUCE_SIZE", "ADD_VOLATILITY_CAP", "RETEST"]
    if decision == "PAUSE":
        return ["WAIT_FOR_ENVIRONMENT_CLEARANCE", "HUMAN_REVIEW"]
    if decision == "KILL":
        return ["ARCHIVE_CANDIDATE", "WRITE_FAILURE_NOTE"]
    return ["CONTINUE_PAPER_FORWARD_TEST", "REVIEW_NEXT_BATCH"]

"""Paper-only multi-agent research committee.

This module is deliberately offline and rule based. It borrows the useful
committee shape from public multi-agent trading research, but it does not
scrape, fetch news, connect to brokers, or place orders.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.audit.writer import append_audit_event
from tar_system.positioning.scorer import get_positioning_context
from tar_system.scoring.gates import run_gates
from tar_system.scoring.scorer import score_strategy

KEEP = "KEEP"
REVIEW = "REVIEW"
KILL = "KILL"

PAPER_ONLY_GUARDRAILS = [
    "Paper-only research. Do not place trades.",
    "Do not recommend live execution or broker API use.",
    "Use supplied local metrics and manual notes only.",
    "Human review is required before any external action.",
]


@dataclass(frozen=True)
class CommitteeInput:
    strategy: str
    symbol: str
    timeframe: str
    metrics: dict[str, Any]
    walk_forward: dict[str, Any] = field(default_factory=dict)
    positioning: dict[str, Any] = field(default_factory=dict)
    manual_notes: str = ""
    report_path: str | None = None


@dataclass(frozen=True)
class AgentReport:
    role: str
    stance: str
    score: float
    summary: str
    evidence: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CommitteeResult:
    generated_at: str
    paper_only: bool
    strategy: str
    symbol: str
    timeframe: str
    recommendation: str
    confidence: float
    guardrails: list[str]
    agents: list[AgentReport]
    debate: list[AgentReport]
    synthesis: AgentReport
    risk_review: AgentReport
    required_next_actions: list[str]
    output_markdown: str
    output_json: str


def run_research_committee(
    strategy: str,
    symbol: str,
    timeframe: str,
    *,
    metrics: dict[str, Any] | None = None,
    walk_forward: dict[str, Any] | None = None,
    manual_notes: str = "",
    output_dir: str | Path = "runtime",
) -> CommitteeResult:
    """Run the local paper-only research committee for one candidate."""

    metrics = dict(metrics or _load_metrics(strategy, symbol, timeframe))
    walk_forward = dict(walk_forward or _load_walk_forward(strategy, symbol, timeframe))
    positioning = _safe_positioning(symbol)
    report_path = Path("reports") / f"{symbol}_{timeframe}_{strategy}_report.md"
    committee_input = CommitteeInput(
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        metrics=metrics,
        walk_forward=walk_forward,
        positioning=positioning,
        manual_notes=manual_notes,
        report_path=str(report_path) if report_path.exists() else None,
    )

    analyst_reports = [
        _fundamental_analyst(committee_input),
        _sentiment_analyst(committee_input),
        _news_analyst(committee_input),
        _technical_analyst(committee_input),
    ]
    bull = _bull_researcher(committee_input, analyst_reports)
    bear = _bear_researcher(committee_input, analyst_reports)
    synthesis = _trader_synthesis(committee_input, analyst_reports, bull, bear)
    risk_review = _risk_reviewer(committee_input, synthesis)
    recommendation, confidence, required_next_actions = _final_recommendation(synthesis, risk_review)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"research_committee_{symbol}_{timeframe}_{strategy}"
    md_path = output_dir / f"{stem}.md"
    json_path = output_dir / f"{stem}.json"
    result = CommitteeResult(
        generated_at=datetime.now(timezone.utc).isoformat(),
        paper_only=True,
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        recommendation=recommendation,
        confidence=confidence,
        guardrails=PAPER_ONLY_GUARDRAILS,
        agents=analyst_reports,
        debate=[bull, bear],
        synthesis=synthesis,
        risk_review=risk_review,
        required_next_actions=required_next_actions,
        output_markdown=str(md_path),
        output_json=str(json_path),
    )
    md_path.write_text(render_committee_markdown(result, committee_input), encoding="utf-8")
    json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    append_audit_event(
        "research_committee",
        strategy,
        symbol,
        timeframe,
        recommendation,
        "PAPER_ONLY_RESEARCH_COMMITTEE",
        {"markdown": str(md_path), "json": str(json_path), "confidence": confidence},
    )
    return result


def render_committee_markdown(result: CommitteeResult, committee_input: CommitteeInput) -> str:
    lines = [
        f"# Research Committee: {result.strategy} {result.symbol} {result.timeframe}",
        "",
        f"- Generated: {result.generated_at}",
        "- Mode: paper-only research",
        f"- Recommendation: {result.recommendation}",
        f"- Confidence: {result.confidence}",
        "",
        "## Guardrails",
    ]
    lines.extend(f"- {item}" for item in result.guardrails)
    lines.extend(["", "## Inputs", f"- Source report: {committee_input.report_path or 'not found'}"])
    for key in ("total_trades", "win_rate", "profit_factor", "max_drawdown", "expectancy", "net_profit", "sharpe_ratio"):
        if key in committee_input.metrics:
            lines.append(f"- {key}: {committee_input.metrics[key]}")
    if committee_input.positioning:
        lines.extend(
            [
                f"- positioning_bias: {committee_input.positioning.get('bias', 'NEUTRAL')}",
                f"- positioning_confidence: {committee_input.positioning.get('confidence', 0.0)}",
            ]
        )
    if committee_input.manual_notes:
        lines.extend(["", "## Manual Notes", committee_input.manual_notes.strip()])
    lines.extend(["", "## Analyst Reports"])
    for agent in result.agents:
        _append_agent(lines, agent)
    lines.extend(["", "## Bull/Bear Debate"])
    for agent in result.debate:
        _append_agent(lines, agent)
    lines.extend(["", "## Trader Synthesis"])
    _append_agent(lines, result.synthesis)
    lines.extend(["", "## Risk Review"])
    _append_agent(lines, result.risk_review)
    lines.extend(["", "## Required Next Actions"])
    lines.extend(f"- {item}" for item in result.required_next_actions)
    return "\n".join(lines) + "\n"


def _append_agent(lines: list[str], report: AgentReport) -> None:
    lines.extend([f"### {report.role}", f"- Stance: {report.stance}", f"- Score: {report.score}", f"- Summary: {report.summary}"])
    if report.evidence:
        lines.append("- Evidence:")
        lines.extend(f"  - {item}" for item in report.evidence)
    if report.concerns:
        lines.append("- Concerns:")
        lines.extend(f"  - {item}" for item in report.concerns)


def _fundamental_analyst(payload: CommitteeInput) -> AgentReport:
    metrics = payload.metrics
    score = 0.0
    evidence: list[str] = []
    concerns: list[str] = []
    pf = _metric(metrics, "profit_factor")
    expectancy = _metric(metrics, "expectancy")
    trades = _metric(metrics, "total_trades")
    if pf >= 1.4:
        score += 35
        evidence.append(f"profit factor {pf:.2f} is above the structural target")
    else:
        concerns.append(f"profit factor {pf:.2f} is below the structural target")
    if expectancy > 0:
        score += 30
        evidence.append(f"positive expectancy {expectancy:.4f}")
    else:
        concerns.append(f"expectancy {expectancy:.4f} is not positive")
    if trades >= 40:
        score += 20
        evidence.append(f"sample size has {int(trades)} trades")
    else:
        concerns.append(f"sample size has only {int(trades)} trades")
    if _metric(metrics, "total_cost") <= max(1.0, abs(_metric(metrics, "net_profit")) * 0.5):
        score += 15
    else:
        concerns.append("trading costs are large relative to net result")
    return AgentReport("Fundamental Analyst", _stance(score), round(score, 2), "Checks whether the result has an economic base after costs.", evidence, concerns)


def _sentiment_analyst(payload: CommitteeInput) -> AgentReport:
    positioning = payload.positioning or {}
    bias = str(positioning.get("bias", "NEUTRAL")).upper()
    confidence = _as_float(positioning.get("confidence", 0.0))
    score = 50.0
    evidence: list[str] = []
    concerns: list[str] = []
    if bias in {"BULLISH", "BEARISH"} and confidence >= 0.5:
        score += 20
        evidence.append(f"manual positioning context is {bias} with confidence {confidence:.2f}")
    elif bias == "NEUTRAL":
        concerns.append("manual positioning context is neutral")
    else:
        concerns.append("manual positioning context is weak or unavailable")
    if payload.manual_notes:
        score += 10
        evidence.append("manual research notes were supplied")
    else:
        concerns.append("no manual sentiment or market notes supplied")
    return AgentReport("Sentiment Analyst", _stance(score), round(score, 2), "Uses only local/manual positioning context, never scraped social data.", evidence, concerns)


def _news_analyst(payload: CommitteeInput) -> AgentReport:
    score = 55.0
    evidence: list[str] = []
    concerns: list[str] = []
    notes = payload.manual_notes.lower()
    risk_words = ["fed", "cpi", "nfp", "rate", "war", "earnings", "election", "shock", "volatility"]
    matched = sorted({word for word in risk_words if word in notes})
    if matched:
        score -= 15
        concerns.append(f"manual notes mention event risk: {', '.join(matched)}")
    else:
        evidence.append("no explicit event-risk words found in manual notes")
    if not payload.manual_notes:
        concerns.append("no supplied news notes; analyst cannot infer current news backdrop")
    return AgentReport("News Analyst", _stance(score), round(score, 2), "Reviews manually supplied news context only.", evidence, concerns)


def _technical_analyst(payload: CommitteeInput) -> AgentReport:
    metrics = _metrics_with_walk_forward(payload.metrics, payload.walk_forward)
    score_result = score_strategy({k: _as_float(v) for k, v in payload.metrics.items() if isinstance(v, (int, float))}, payload.walk_forward, payload.timeframe, require_walk_forward=bool(payload.walk_forward))
    gate = run_gates({k: _as_float(v) for k, v in metrics.items() if isinstance(v, (int, float, bool))}, payload.timeframe, require_oos=bool(payload.walk_forward))
    evidence = [f"score_strategy={score_result.score}"]
    concerns = list(score_result.reason_codes) + list(gate.reason_codes)
    if gate.verdict == KEEP:
        evidence.append("structural_gate=KEEP")
    else:
        concerns.append(f"structural_gate={gate.verdict}: {gate.reason}")
    return AgentReport("Technical Analyst", score_result.verdict, score_result.score, "Reads the local backtest, walk-forward and gate metrics.", evidence, concerns)


def _bull_researcher(payload: CommitteeInput, analysts: list[AgentReport]) -> AgentReport:
    positives = [item for report in analysts for item in report.evidence]
    score = min(100.0, 30.0 + len(positives) * 8.0)
    if _metric(payload.metrics, "net_profit") > 0:
        score += 10
    return AgentReport(
        "Bull Researcher",
        _stance(score),
        round(min(score, 100.0), 2),
        "Builds the strongest paper-only case for further research.",
        positives[:8] or ["No strong positive evidence found."],
        [],
    )


def _bear_researcher(payload: CommitteeInput, analysts: list[AgentReport]) -> AgentReport:
    concerns = [item for report in analysts for item in report.concerns]
    score = min(100.0, 30.0 + len(concerns) * 8.0)
    if _metric(payload.metrics, "max_consecutive_losses", "consecutive_losses") >= 5:
        score += 15
        concerns.append("consecutive loss cluster is large")
    return AgentReport(
        "Bear Researcher",
        "KILL" if score >= 70 else "REVIEW",
        round(min(score, 100.0), 2),
        "Builds the strongest objection before any strategy is trusted.",
        [],
        concerns[:10] or ["No major objection found."],
    )


def _trader_synthesis(payload: CommitteeInput, analysts: list[AgentReport], bull: AgentReport, bear: AgentReport) -> AgentReport:
    metrics = _metrics_with_walk_forward(payload.metrics, payload.walk_forward)
    gate = run_gates({k: _as_float(v) for k, v in metrics.items() if isinstance(v, (int, float, bool))}, payload.timeframe, require_oos=bool(payload.walk_forward))
    analyst_score = sum(report.score for report in analysts) / len(analysts)
    score = max(0.0, min(100.0, analyst_score + (bull.score - bear.score) * 0.25))
    concerns = [gate.reason] if gate.failed_gate else []
    if gate.verdict == KILL:
        stance = KILL
    elif score >= 70 and gate.verdict == KEEP:
        stance = KEEP
    else:
        stance = REVIEW
    return AgentReport(
        "Trader Synthesizer",
        stance,
        round(score, 2),
        "Synthesizes the committee into a paper-only research recommendation.",
        [f"bull_score={bull.score}", f"bear_score={bear.score}", f"gate={gate.verdict}"],
        concerns,
    )


def _risk_reviewer(payload: CommitteeInput, synthesis: AgentReport) -> AgentReport:
    metrics = _metrics_with_walk_forward(payload.metrics, payload.walk_forward)
    gate = run_gates({k: _as_float(v) for k, v in metrics.items() if isinstance(v, (int, float, bool))}, payload.timeframe, require_oos=True)
    concerns = list(gate.reason_codes)
    if _metric(metrics, "total_cost") > abs(_metric(metrics, "net_profit")) and _metric(metrics, "total_cost") > 0:
        concerns.append("costs exceed absolute net result")
    if synthesis.stance == KEEP and gate.verdict != KEEP:
        concerns.append("synthesis cannot override structural gate")
    score = 100.0 if gate.verdict == KEEP else 55.0 if gate.verdict == REVIEW else 20.0
    return AgentReport("Risk Reviewer", gate.verdict, score, "Applies structural gates and keeps the result paper-only.", [gate.reason], concerns)


def _final_recommendation(synthesis: AgentReport, risk: AgentReport) -> tuple[str, float, list[str]]:
    actions = [
        "Keep result in paper-only research.",
        "Human review required before any promotion or external export.",
    ]
    if risk.stance == KILL:
        actions.append("Archive or redesign before further testing.")
        return KILL, 0.85, actions
    if risk.stance == REVIEW or synthesis.stance == REVIEW:
        actions.append("Run more validation or add manual market notes before trusting the setup.")
        return REVIEW, 0.65, actions
    actions.append("Eligible for more paper-watch review, not live trading.")
    return KEEP, 0.60, actions


def _load_metrics(strategy: str, symbol: str, timeframe: str) -> dict[str, Any]:
    path = Path("data/results") / f"{strategy}_{symbol}_{timeframe}_metrics.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_walk_forward(strategy: str, symbol: str, timeframe: str) -> dict[str, Any]:
    path = Path("data/results") / f"{strategy}_{symbol}_{timeframe}_walk_forward.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _metrics_with_walk_forward(metrics: dict[str, Any], walk_forward: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(metrics)
    if not walk_forward:
        return enriched
    stitched = walk_forward.get("stitched_metrics", {}) or {}
    if isinstance(stitched, dict):
        enriched["sharpe_oos"] = _as_float(stitched.get("sharpe_ratio", stitched.get("sharpe", 0.0)))
    raw_stability = _as_float(walk_forward.get("parameter_stability_score", 0.0))
    enriched["param_stability"] = raw_stability / 100.0 if raw_stability > 1.0 else raw_stability
    enriched["walk_forward_splits"] = _as_float(walk_forward.get("split_count", walk_forward.get("window_count", 0)))
    bootstrap_ci = walk_forward.get("bootstrap_ci", {}) or {}
    if isinstance(bootstrap_ci, dict):
        enriched["bootstrap_ci_lower"] = _as_float(bootstrap_ci.get("ci_lower", 0.0))
        enriched["bootstrap_ci_upper"] = _as_float(bootstrap_ci.get("ci_upper", 0.0))
        enriched["bootstrap_ci_spans_zero"] = bool(bootstrap_ci.get("spans_zero", True))
    return enriched


def _safe_positioning(symbol: str) -> dict[str, Any]:
    try:
        return dict(get_positioning_context(symbol))
    except Exception:
        return {}


def _metric(metrics: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key in metrics:
            return _as_float(metrics[key], default)
    return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _stance(score: float) -> str:
    if score >= 70:
        return KEEP
    if score >= 40:
        return REVIEW
    return KILL

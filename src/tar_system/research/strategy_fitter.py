"""Paper-only strategy filter fitter.

The fitter converts repeated committee/backtest failure patterns into explicit
filter recommendations. It never edits strategy code, places trades, or
promotes a candidate; it writes a review plan for human approval and retesting.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.audit.writer import append_audit_event
from tar_system.research.committee import run_research_committee
from tar_system.scoring.gates import MIN_TRADES_BY_TIMEFRAME


@dataclass(frozen=True)
class MetricCandidate:
    strategy: str
    symbol: str
    timeframe: str
    path: str
    metrics: dict[str, Any]
    blockers: list[str]
    severity: float


@dataclass(frozen=True)
class FilterRecommendation:
    strategy: str
    symbol: str
    timeframe: str
    committee_recommendation: str
    blockers: list[str]
    filters: list[str]
    parameter_tests: dict[str, Any] = field(default_factory=dict)
    retest_command: str = ""
    rationale: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StrategyFilterPlan:
    generated_at: str
    paper_only: bool
    candidates_reviewed: int
    blocker_counts: dict[str, int]
    strategy_counts: dict[str, int]
    recommendations: list[FilterRecommendation]
    next_actions: list[str]
    output_markdown: str
    output_json: str


def build_strategy_filter_plan(
    *,
    limit: int = 12,
    results_dir: str | Path = "data/results",
    output_dir: str | Path = "runtime",
    run_committee: bool = True,
) -> StrategyFilterPlan:
    candidates = load_metric_candidates(results_dir)
    selected = sorted(candidates, key=lambda row: row.severity, reverse=True)[:limit]
    recommendations: list[FilterRecommendation] = []
    for candidate in selected:
        committee_recommendation = "REVIEW"
        if run_committee:
            committee_recommendation = run_research_committee(
                candidate.strategy,
                candidate.symbol,
                candidate.timeframe,
                metrics=candidate.metrics,
                output_dir=output_dir,
            ).recommendation
        recommendations.append(_recommend_filters(candidate, committee_recommendation))

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / "strategy_filter_plan.md"
    json_path = output_dir / "strategy_filter_plan.json"
    blocker_counts = Counter(blocker for candidate in candidates for blocker in candidate.blockers)
    strategy_counts = Counter(candidate.strategy for candidate in candidates)
    plan = StrategyFilterPlan(
        generated_at=datetime.now(timezone.utc).isoformat(),
        paper_only=True,
        candidates_reviewed=len(selected),
        blocker_counts=dict(blocker_counts),
        strategy_counts=dict(strategy_counts),
        recommendations=recommendations,
        next_actions=[
            "Treat this as a retest plan, not a promotion decision.",
            "Apply one filter hypothesis at a time and rerun the full paper pipeline.",
            "Archive any candidate that still shows directional failure after the first retest.",
        ],
        output_markdown=str(md_path),
        output_json=str(json_path),
    )
    md_path.write_text(render_filter_plan(plan), encoding="utf-8")
    json_path.write_text(json.dumps(asdict(plan), indent=2, default=str), encoding="utf-8")
    append_audit_event(
        "strategy_filter_fitter",
        "portfolio",
        "",
        "",
        "COMPLETED",
        "PAPER_ONLY_FILTER_PLAN_WRITTEN",
        {"markdown": str(md_path), "json": str(json_path), "limit": limit},
    )
    return plan


def load_metric_candidates(results_dir: str | Path = "data/results") -> list[MetricCandidate]:
    rows: list[MetricCandidate] = []
    for path in Path(results_dir).glob("*_metrics.json"):
        parsed = _parse_metrics_name(path)
        if not parsed:
            continue
        try:
            metrics = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        blockers = _blockers(metrics, parsed["timeframe"])
        rows.append(
            MetricCandidate(
                strategy=parsed["strategy"],
                symbol=parsed["symbol"],
                timeframe=parsed["timeframe"],
                path=str(path),
                metrics=metrics,
                blockers=blockers,
                severity=_severity(metrics, blockers),
            )
        )
    return rows


def render_filter_plan(plan: StrategyFilterPlan) -> str:
    lines = [
        "# Strategy Filter Plan",
        "",
        f"- Generated: {plan.generated_at}",
        "- Mode: paper-only research",
        f"- Candidates reviewed: {plan.candidates_reviewed}",
        "",
        "## Blocker Counts",
    ]
    if not plan.blocker_counts:
        lines.append("- None")
    for blocker, count in sorted(plan.blocker_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {blocker}: {count}")
    lines.extend(["", "## Recommendations"])
    if not plan.recommendations:
        lines.append("- No metric candidates found.")
    for rec in plan.recommendations:
        lines.extend(
            [
                f"### {rec.strategy} {rec.symbol} {rec.timeframe}",
                f"- Committee: {rec.committee_recommendation}",
                f"- Blockers: {', '.join(rec.blockers) if rec.blockers else 'None'}",
                "- Filters:",
            ]
        )
        lines.extend(f"  - {item}" for item in rec.filters)
        if rec.parameter_tests:
            lines.append("- Parameter tests:")
            for key, value in rec.parameter_tests.items():
                lines.append(f"  - {key}: {value}")
        if rec.rationale:
            lines.append("- Rationale:")
            lines.extend(f"  - {item}" for item in rec.rationale)
        if rec.retest_command:
            lines.extend(["- Retest command:", f"  `{rec.retest_command}`"])
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {item}" for item in plan.next_actions)
    return "\n".join(lines) + "\n"


def _recommend_filters(candidate: MetricCandidate, committee_recommendation: str) -> FilterRecommendation:
    strategy = candidate.strategy
    symbol = candidate.symbol
    timeframe = candidate.timeframe
    blockers = candidate.blockers
    filters: list[str] = []
    params: dict[str, Any] = {}
    rationale: list[str] = []

    if "DIRECTIONAL_FAILURE" in blockers:
        filters.append("directional_sanity_gate: block this strategy/symbol/timeframe after >=95% consecutive-loss ratio")
        filters.append("inverse_direction_hypothesis: paper-test an inverted signal variant, but do not auto-flip live decisions")
        rationale.append("A high consecutive-loss ratio suggests either inverted edge, regime mismatch, or broken signal assumptions.")
    if "HIGH_DRAWDOWN" in blockers:
        filters.append("drawdown_guard: require max_drawdown <= 20% before any KEEP")
        filters.append("risk_cut: retest at half paper risk before considering more optimisation")
        rationale.append("Drawdown exceeded the structural promotion threshold.")
    if "WEAK_PF" in blockers or "LOW_WIN_RATE" in blockers:
        filters.append("quality_gate: require profit_factor >= 1.40 and win_rate >= 40% before committee can recommend KEEP")
        rationale.append("Weak profit factor or low win rate means parameter fitting alone is unlikely to be enough.")
    if "LOW_SAMPLE" in blockers:
        filters.append("sample_gate: gather the minimum trade count for this timeframe before judging edge")
        rationale.append("Low sample size blocks reliable inference.")

    if strategy == "gold_v2":
        filters.extend(
            [
                "trend_confirmation: require higher-timeframe trend agreement before entry",
                "slope_confirmation: increase EMA slope threshold on failed FX/commodity variants",
                "volatility_window: avoid ATR extremes and compression before trend entries",
            ]
        )
        params.update(
            {
                "rsi_buy_threshold": [58, 60, 62],
                "rsi_sell_threshold": [42, 40, 38],
                "ema_slope_threshold": [0.0003, 0.0005],
                "atr_floor_multiplier": [0.7, 0.9],
                "atr_ceil_multiplier": [2.0, 2.5],
            }
        )
    elif strategy == "rsi_reversion_v1":
        filters.extend(
            [
                "mean_reversion_confirmation: require price_in_band <= 0.10 for buys and >= 0.90 for sells",
                "trend_block: block reversion trades when EMA slopes confirm trend continuation",
                "volume_or_session_filter: avoid thin-session reversal entries",
            ]
        )
        params.update(
            {
                "oversold": [25, 28],
                "overbought": [72, 75],
                "price_in_band_buy_max": [0.10, 0.15],
                "price_in_band_sell_min": [0.85, 0.90],
                "reward_risk": [1.0, 1.5],
            }
        )
    else:
        filters.extend(
            [
                "regime_confirmation: only trade in the strategy's intended regime",
                "volume_confirmation: require current volume above recent average where volume is meaningful",
                "higher_timeframe_confirmation: require non-conflicting higher timeframe direction",
            ]
        )

    if committee_recommendation == "KILL":
        filters.insert(0, "kill_guard: do not optimise toward promotion until a clean paper retest removes hard blockers")

    return FilterRecommendation(
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        committee_recommendation=committee_recommendation,
        blockers=blockers,
        filters=_dedupe(filters),
        parameter_tests=params,
        retest_command=_retest_command(strategy, symbol, timeframe),
        rationale=_dedupe(rationale),
    )


def _blockers(metrics: dict[str, Any], timeframe: str) -> list[str]:
    blockers: list[str] = []
    trades = _metric(metrics, "total_trades")
    win_rate = _metric(metrics, "win_rate")
    profit_factor = _metric(metrics, "profit_factor")
    drawdown = _metric(metrics, "max_drawdown")
    consecutive_losses = _metric(metrics, "max_consecutive_losses", "consecutive_losses")
    min_trades = MIN_TRADES_BY_TIMEFRAME.get(timeframe.upper(), 30)
    if trades < min_trades:
        blockers.append("LOW_SAMPLE")
    if profit_factor < 1.0:
        blockers.append("WEAK_PF")
    if win_rate < 0.35:
        blockers.append("LOW_WIN_RATE")
    if drawdown > 0.20:
        blockers.append("HIGH_DRAWDOWN")
    if trades and consecutive_losses / trades >= 0.95:
        blockers.append("DIRECTIONAL_FAILURE")
    return blockers


def _severity(metrics: dict[str, Any], blockers: list[str]) -> float:
    weights = {
        "DIRECTIONAL_FAILURE": 50.0,
        "HIGH_DRAWDOWN": 25.0,
        "WEAK_PF": 15.0,
        "LOW_WIN_RATE": 10.0,
        "LOW_SAMPLE": 5.0,
    }
    score = sum(weights.get(blocker, 0.0) for blocker in blockers)
    score += max(0.0, -_metric(metrics, "net_profit")) / 1000.0
    return round(score, 3)


def _parse_metrics_name(path: Path) -> dict[str, str] | None:
    stem = path.stem
    if not stem.endswith("_metrics"):
        return None
    parts = stem.removesuffix("_metrics").split("_")
    if len(parts) < 3:
        return None
    return {"strategy": "_".join(parts[:-2]), "symbol": parts[-2], "timeframe": parts[-1]}


def _metric(metrics: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key in metrics:
            try:
                return float(metrics[key])
            except (TypeError, ValueError):
                return default
    return default


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


def _retest_command(strategy: str, symbol: str, timeframe: str) -> str:
    raw = f"data/raw/{symbol}_{timeframe}.csv"
    return (
        "PYTHONPATH=src venv/bin/python -m tar_system.cli run-full-pipeline "
        f"--strategy {strategy} --symbol {symbol} --timeframe {timeframe} --file {raw} "
        "--broker current_broker_demo --force"
    )

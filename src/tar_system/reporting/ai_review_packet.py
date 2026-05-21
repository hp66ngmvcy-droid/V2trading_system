"""AI review packet export for cheap external strategy review.

The packet is intentionally read-only: it summarizes local TAR state for a
human or low-cost AI reviewer without running tests, writing memory, exporting
MT5 files, or promoting strategies.
"""

from __future__ import annotations

import json
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.audit.writer import append_audit_event
from tar_system.controller.job_queue import queue_stats, read_jobs
from tar_system.controller.research_loop import recommend_next_actions
from tar_system.reporting.review_log import load_review_results
from tar_system.scoring.scorer import score_strategy
from tar_system.settings import LOG_DIR, REPORT_DIR


DEFAULT_PACKET_PATH = Path("runtime/ai_review_packet.md")
DEFAULT_METRICS_CACHE_PATH = Path("runtime/ai_review_metrics_cache.json")
METRIC_KEYS = (
    "total_trades",
    "win_rate",
    "profit_factor",
    "max_drawdown",
    "expectancy",
    "net_profit",
    "total_cost",
    "swap_cost",
    "sharpe_ratio",
    "sortino_ratio",
    "max_consecutive_losses",
)


@dataclass(frozen=True)
class AIReviewPacketConfig:
    results_dir: Path = Path("data/results")
    reports_dir: Path = Path(REPORT_DIR)
    log_dir: Path = Path(LOG_DIR)
    metrics_cache_path: Path = DEFAULT_METRICS_CACHE_PATH
    guardrails: list[str] = field(
        default_factory=lambda: [
            "Do not recommend live trading.",
            "Do not recommend automatic MT5 promotion.",
            "Only recommend paper research, review, or rejection actions.",
            "Treat low sample size, weak walk-forward evidence, and cost sensitivity as review blockers.",
        ]
    )


def export_ai_review_packet(output: str | Path = DEFAULT_PACKET_PATH, limit: int = 10, config: AIReviewPacketConfig | None = None) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = build_ai_review_snapshot(limit=limit, config=config)
    output_path.write_text(render_ai_review_packet(snapshot), encoding="utf-8")
    output_path.with_suffix(".json").write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
    append_audit_event(
        "ai_review_packet_export",
        "reporting",
        "",
        "",
        "COMPLETED",
        "AI_REVIEW_PACKET_EXPORTED",
        {"path": str(output_path), "json_path": str(output_path.with_suffix(".json")), "limit": limit},
    )
    return output_path


def build_ai_review_snapshot(limit: int = 10, config: AIReviewPacketConfig | None = None) -> dict[str, Any]:
    cfg = config or AIReviewPacketConfig()
    jobs = read_jobs()
    metric_load = _load_metric_summaries(cfg)
    metrics = metric_load["rows"]
    review_rows = _load_review_rows(limit)
    summary_stats = _summary_statistics(jobs, metrics)
    failure_diagnosis = _failure_diagnosis(jobs, metrics, cfg, limit)
    risk_assessment = _risk_assessment(jobs, metrics, limit)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "paper_only": True,
        "guardrails": cfg.guardrails,
        "warnings": metric_load["warnings"],
        "summary_statistics": summary_stats,
        "failure_diagnosis": failure_diagnosis,
        "risk_assessment": risk_assessment,
        "queue_stats": queue_stats(),
        "queue_summary": _summarize_jobs(jobs, limit),
        "next_actions": recommend_next_actions(limit),
        "best_metric_candidates": metrics[:limit],
        "worst_metric_candidates": list(reversed(metrics[-limit:])),
        "recent_review_log": review_rows,
        "recent_audit_events": _load_recent_audit_events(limit, cfg),
        "latest_reports": _latest_reports(limit, cfg),
        "requested_review_output": _requested_review_output(summary_stats, failure_diagnosis, risk_assessment),
    }


def render_ai_review_packet(snapshot: dict[str, Any]) -> str:
    lines = [
        "# TAR AI Review Packet",
        "",
        f"- Generated: {snapshot['generated_at']}",
        "- Mode: paper-only research",
        "- Purpose: cheap AI or human review of local TAR results",
        "",
        "## Reviewer Instructions",
    ]
    lines.extend(f"- {item}" for item in snapshot["guardrails"])
    lines.extend(["", "## Warnings"])
    if not snapshot["warnings"]:
        lines.append("- None")
    for warning in snapshot["warnings"]:
        lines.append(f"- {warning['path']}: {warning['reason']}")
    lines.extend(["", "## Summary Statistics"])
    stats = snapshot["summary_statistics"]
    lines.extend(
        [
            f"- Total jobs: {stats['total_jobs']}",
            f"- Failure rate: {stats['failure_rate_pct']}%",
            f"- Metric files loaded: {stats['metric_files']}",
            f"- Metric verdicts: KEEP={stats['metric_verdict_counts'].get('KEEP', 0)} REVIEW={stats['metric_verdict_counts'].get('REVIEW', 0)} KILL={stats['metric_verdict_counts'].get('KILL', 0)}",
            f"- Average trades per metric file: {stats['avg_trades']}",
            f"- Average max drawdown: {stats['avg_drawdown']}",
        ]
    )
    lines.extend(["", "## Failure Diagnosis"])
    failure = snapshot["failure_diagnosis"]
    lines.append(f"- Failed jobs: {failure['failed_jobs']}")
    lines.append(f"- Estimated wasted queue capacity: {failure['failed_jobs']} failed job slots")
    lines.extend(_counter_lines("Top failed stages", failure["top_failed_stages"]))
    lines.extend(_counter_lines("Top failed strategy/symbol/timeframe", failure["top_failed_targets"]))
    lines.extend(_counter_lines("Top audit failure reasons", failure["top_audit_failure_reasons"]))
    lines.extend(_counter_lines("Top metric blockers", failure["top_metric_blockers"]))
    lines.extend(["", "## Risk Assessment"])
    risk = snapshot["risk_assessment"]
    lines.append(f"- Stalled running jobs: {len(risk['stalled_running_jobs'])}")
    lines.append(f"- Low-sample metric candidates: {len(risk['low_sample_candidates'])}")
    lines.append(f"- High-drawdown metric candidates: {len(risk['high_drawdown_candidates'])}")
    lines.append(f"- Cost-sensitive completed jobs: {len(risk['cost_sensitive_jobs'])}")
    lines.extend(["", "## Queue Stats"])
    for status, count in sorted(snapshot["queue_stats"].items()):
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in snapshot["next_actions"])
    lines.extend(["", "## Queue Summary"])
    for status, rows in snapshot["queue_summary"].items():
        lines.append(f"### {status}")
        if not rows:
            lines.append("- None")
        for row in rows:
            lines.append(_job_line(row))
    lines.extend(["", "## Best Metric Candidates"])
    lines.extend(_metric_table(snapshot["best_metric_candidates"]))
    lines.extend(["", "## Worst Metric Candidates"])
    lines.extend(_metric_table(snapshot["worst_metric_candidates"]))
    lines.extend(["", "## Recent Review Log"])
    if not snapshot["recent_review_log"]:
        lines.append("- No review log rows found.")
    for row in snapshot["recent_review_log"]:
        lines.append(
            f"- {row.get('timestamp', '')}: {row.get('strategy')} {row.get('symbol')} {row.get('timeframe')} "
            f"verdict={row.get('verdict')} score={row.get('score')} next={row.get('next_action')}"
        )
    lines.extend(["", "## Recent Audit Events"])
    if not snapshot["recent_audit_events"]:
        lines.append("- No audit events found.")
    for row in snapshot["recent_audit_events"]:
        lines.append(
            f"- {row.get('timestamp', '')}: {row.get('event_type')} decision={row.get('decision')} "
            f"reason={row.get('reason_code')} {row.get('strategy', '')} {row.get('symbol', '')} {row.get('timeframe', '')}"
        )
    lines.extend(["", "## Latest Reports"])
    if not snapshot["latest_reports"]:
        lines.append("- No report files found.")
    for report in snapshot["latest_reports"]:
        lines.append(f"- {report['modified_at']}: {report['path']}")
    lines.extend(["", "## Requested Review Output"])
    lines.extend(f"- {item}" for item in snapshot["requested_review_output"])
    return "\n".join(lines) + "\n"


def _load_metric_summaries(config: AIReviewPacketConfig) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    cache = _load_metrics_cache(config.metrics_cache_path)
    next_cache: dict[str, Any] = {"version": 1, "files": {}}
    for path in config.results_dir.glob("*_metrics.json"):
        parsed = _parse_metrics_name(path)
        if not parsed:
            warnings.append({"path": str(path), "reason": "METRICS_NAME_NOT_RECOGNISED"})
            continue
        cache_key = str(path)
        stat = path.stat()
        cached = cache.get("files", {}).get(cache_key)
        if cached and cached.get("mtime_ns") == stat.st_mtime_ns and cached.get("size") == stat.st_size:
            rows.append(cached["summary"])
            next_cache["files"][cache_key] = cached
            continue
        try:
            metrics = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            warnings.append({"path": str(path), "reason": "METRICS_JSON_LOAD_FAILED"})
            continue
        missing = [key for key in ("total_trades", "profit_factor", "max_drawdown") if key not in metrics]
        if missing:
            warnings.append({"path": str(path), "reason": f"METRICS_MISSING_FIELDS:{','.join(missing)}"})
        score = score_strategy({key: _as_float(value) for key, value in metrics.items() if key in METRIC_KEYS})
        summary = {
            **parsed,
            "path": str(path),
            "score": score.score,
            "verdict": score.verdict,
            "severity": _severity(score.verdict, score.reason_codes),
            "reason_codes": score.reason_codes,
            "metrics": {key: metrics.get(key) for key in METRIC_KEYS if key in metrics},
        }
        rows.append(summary)
        next_cache["files"][cache_key] = {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size, "summary": summary}
    _save_metrics_cache(config.metrics_cache_path, next_cache)
    return {"rows": sorted(rows, key=lambda row: float(row["score"]), reverse=True), "warnings": warnings}


def _load_metrics_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "files": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "files": {}}


def _save_metrics_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _parse_metrics_name(path: Path) -> dict[str, str] | None:
    stem = path.stem
    if not stem.endswith("_metrics"):
        return None
    parts = stem.removesuffix("_metrics").split("_")
    if len(parts) < 3:
        return None
    return {"strategy": "_".join(parts[:-2]), "symbol": parts[-2], "timeframe": parts[-1]}


def _load_review_rows(limit: int) -> list[dict[str, Any]]:
    return load_review_results()[-limit:]


def _load_recent_audit_events(limit: int, config: AIReviewPacketConfig) -> list[dict[str, Any]]:
    path = config.log_dir / "audit" / "audit.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in _tail_jsonl_lines(path, limit):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _latest_reports(limit: int, config: AIReviewPacketConfig) -> list[dict[str, str]]:
    reports = [path for path in config.reports_dir.glob("*") if path.is_file() and path.suffix in {".md", ".json", ".pdf"}]
    reports.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [{"path": str(path), "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()} for path in reports[:limit]]


def _tail_jsonl_lines(path: Path, limit: int) -> list[str]:
    lines: deque[str] = deque(maxlen=limit)
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            lines.append(line.rstrip("\n"))
    return list(lines)


def _summarize_jobs(jobs: list[dict[str, Any]], limit: int) -> dict[str, list[dict[str, Any]]]:
    wanted = ("QUEUED", "RUNNING", "COMPLETED", "FAILED", "SKIPPED")
    grouped: dict[str, list[dict[str, Any]]] = {status: [] for status in wanted}
    for job in jobs:
        status = str(job.get("status") or "UNKNOWN")
        if status not in grouped:
            continue
        grouped[status].append(job)
    return {status: rows[-limit:] for status, rows in grouped.items()}


def _summary_statistics(jobs: list[dict[str, Any]], metrics: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(job.get("status") or "UNKNOWN") for job in jobs)
    total_jobs = sum(status_counts.values())
    failed = status_counts.get("FAILED", 0)
    trades = [_as_float(row.get("metrics", {}).get("total_trades")) for row in metrics]
    drawdowns = [_as_float(row.get("metrics", {}).get("max_drawdown")) for row in metrics]
    verdicts = Counter(str(row.get("verdict") or "UNKNOWN") for row in metrics)
    return {
        "total_jobs": total_jobs,
        "failed_jobs": failed,
        "failure_rate_pct": round((failed / total_jobs * 100.0) if total_jobs else 0.0, 2),
        "metric_files": len(metrics),
        "metric_verdict_counts": dict(verdicts),
        "avg_trades": round(sum(trades) / len(trades), 2) if trades else 0.0,
        "avg_drawdown": round(sum(drawdowns) / len(drawdowns), 4) if drawdowns else 0.0,
    }


def _failure_diagnosis(jobs: list[dict[str, Any]], metrics: list[dict[str, Any]], config: AIReviewPacketConfig, limit: int) -> dict[str, Any]:
    failed_jobs = [job for job in jobs if job.get("status") == "FAILED"]
    failed_stages = Counter(str(job.get("research_stage") or "unknown") for job in failed_jobs)
    failed_targets = Counter(
        f"{job.get('strategy')} {job.get('symbol')} {job.get('timeframe')}"
        for job in failed_jobs
    )
    metric_blockers: Counter[str] = Counter()
    for row in metrics:
        metric_blockers.update(row.get("reason_codes", []))
    audit_reasons = Counter(
        str(row.get("reason_code") or "UNKNOWN")
        for row in _load_recent_audit_events(max(limit * 10, 50), config)
        if row.get("decision") in {"FAILED", "BLOCKED", "SKIPPED"}
    )
    return {
        "failed_jobs": len(failed_jobs),
        "top_failed_stages": failed_stages.most_common(limit),
        "top_failed_targets": failed_targets.most_common(limit),
        "top_audit_failure_reasons": audit_reasons.most_common(limit),
        "top_metric_blockers": metric_blockers.most_common(limit),
    }


def _risk_assessment(jobs: list[dict[str, Any]], metrics: list[dict[str, Any]], limit: int) -> dict[str, list[dict[str, Any]]]:
    now = datetime.now(timezone.utc)
    stalled: list[dict[str, Any]] = []
    for job in jobs:
        if job.get("status") != "RUNNING" or not job.get("started_at"):
            continue
        try:
            started = datetime.fromisoformat(str(job["started_at"]).replace("Z", "+00:00"))
        except ValueError:
            continue
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        if (now - started).total_seconds() > 7200:
            stalled.append(job)
    low_sample = [row for row in metrics if _as_float(row.get("metrics", {}).get("total_trades")) < 20][:limit]
    high_drawdown = [row for row in metrics if _as_float(row.get("metrics", {}).get("max_drawdown")) > 0.2][:limit]
    cost_sensitive = [job for job in jobs if bool(job.get("cost_sensitive"))][:limit]
    return {
        "stalled_running_jobs": stalled[:limit],
        "low_sample_candidates": low_sample,
        "high_drawdown_candidates": high_drawdown,
        "cost_sensitive_jobs": cost_sensitive,
    }


def _job_line(row: dict[str, Any]) -> str:
    fields = [
        row.get("job_id", "")[:8],
        row.get("strategy", ""),
        row.get("symbol", ""),
        row.get("timeframe", ""),
        f"recommendation={row.get('recommendation')}",
        f"stage={row.get('research_stage')}",
        f"result={row.get('result_path')}",
    ]
    return "- " + " ".join(str(field) for field in fields if field not in {None, ""})


def _metric_table(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["- No metrics found."]
    lines: list[str] = []
    lines.append("| Severity | Strategy | Symbol | TF | Score | Verdict | Trades | PF | DD | Net | Reasons |")
    lines.append("| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |")
    for row in rows:
        metrics = row["metrics"]
        lines.append(
            f"| {row.get('severity', 'UNKNOWN')} | {row['strategy']} | {row['symbol']} | {row['timeframe']} | "
            f"{row['score']} | {row['verdict']} | {metrics.get('total_trades')} | {metrics.get('profit_factor')} | "
            f"{metrics.get('max_drawdown')} | {metrics.get('net_profit')} | {','.join(row['reason_codes']) or 'NONE'} |"
        )
    return lines


def _counter_lines(title: str, rows: list[tuple[str, int]]) -> list[str]:
    lines = [f"### {title}"]
    if not rows:
        return [*lines, "- None"]
    lines.append("| Item | Count |")
    lines.append("| --- | ---: |")
    lines.extend(f"| {item} | {count} |" for item, count in rows)
    return lines


def _requested_review_output(summary: dict[str, Any], failure: dict[str, Any], risk: dict[str, list[dict[str, Any]]]) -> list[str]:
    prompts = [
        "Top 3 candidates worth more paper-only testing, with reasons.",
        "Top 3 candidates to kill or pause, with reasons.",
    ]
    if failure["failed_jobs"]:
        prompts.append("Diagnose the highest-count failed-job patterns before recommending broad reruns.")
    if risk["low_sample_candidates"]:
        prompts.append("Flag any candidate whose score is inflated by low trade count.")
    if risk["high_drawdown_candidates"]:
        prompts.append("Call out candidates blocked by excessive drawdown.")
    if summary["failure_rate_pct"] > 50:
        prompts.append("Recommend a small conservative next test batch instead of a full sweep.")
    prompts.append("List any data, cost, walk-forward, or sample-size blockers.")
    return prompts


def _severity(verdict: str, reason_codes: list[str]) -> str:
    blockers = {"HIGH_DRAWDOWN", "WEAK_PROFIT_FACTOR", "WF_NOT_RUN", "WF_HIGH_DRAWDOWN", "WF_WEAK_PROFIT_FACTOR"}
    if verdict == "KILL" or any(code in blockers for code in reason_codes):
        return "BLOCKER"
    if verdict == "REVIEW" or reason_codes:
        return "WARNING"
    return "PASS"


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

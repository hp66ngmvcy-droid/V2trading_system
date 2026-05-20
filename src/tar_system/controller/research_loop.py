"""Local research loop orchestration.

The loop queues missing paper research jobs, runs a bounded worker, and writes
a human-readable summary. It never promotes, exports MT5 files or trades live.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.audit.writer import append_audit_event
from tar_system.controller.data_watcher import scan_raw_data
from tar_system.controller.job_queue import queue_stats, read_jobs
from tar_system.controller.worker import run_worker
from tar_system.reporting.review_log import load_review_results
from tar_system.settings import REPORT_DIR


@dataclass
class ResearchLoopResult:
    queued_jobs: int
    processed_jobs: int
    queue_stats: dict[str, int]
    next_actions: list[str] = field(default_factory=list)
    summary_path: str = ""
    paper_only: bool = True


def run_research_loop(
    raw_dir: str | Path = "data/raw",
    broker: str = "current_broker_demo",
    force: bool = False,
    process_limit: int = 1,
    run_worker_now: bool = True,
    research_stage: str = "smoke",
    window_months: int = 6,
    skip_walk_forward: bool | None = None,
    skip_forward_test: bool | None = None,
    max_walk_forward_splits: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    max_jobs: int | None = None,
    no_live: bool = True,
    no_mt5_promotion: bool = True,
    require_walk_forward: bool = True,
    require_min_trades: bool = False,
    min_trades: int = 30,
) -> ResearchLoopResult:
    queued = scan_raw_data(
        raw_dir=raw_dir,
        force=force,
        broker=broker,
        research_stage=research_stage,
        window_months=window_months,
        skip_walk_forward=skip_walk_forward,
        skip_forward_test=skip_forward_test,
        max_walk_forward_splits=max_walk_forward_splits,
        from_date=from_date,
        to_date=to_date,
        max_jobs=max_jobs,
        no_live=no_live,
        no_mt5_promotion=no_mt5_promotion,
        require_walk_forward=require_walk_forward,
        require_min_trades=require_min_trades,
        min_trades=min_trades,
    )
    worker_result = run_worker(process_limit, max_queued=max_jobs) if run_worker_now and process_limit > 0 else None
    stats = queue_stats()
    actions = recommend_next_actions()
    summary_path = write_research_loop_summary(queued, worker_result, stats, actions)
    result = ResearchLoopResult(
        queued_jobs=len(queued),
        processed_jobs=worker_result.processed if worker_result else 0,
        queue_stats=stats,
        next_actions=actions,
        summary_path=str(summary_path),
    )
    append_audit_event(
        "research_loop",
        "controller",
        "",
        "",
        "COMPLETED",
        "RESEARCH_LOOP_COMPLETED",
        asdict(result),
    )
    return result


def recommend_next_actions(limit: int = 5) -> list[str]:
    jobs = read_jobs()
    stats = queue_stats()
    actions: list[str] = []
    if stats.get("QUEUED", 0) > 0:
        actions.append(f"Run worker for {stats['QUEUED']} queued paper research jobs")
    if stats.get("FAILED", 0) > 0:
        actions.append(f"Review {stats['FAILED']} failed jobs before rerunning")
    best = _best_review_result()
    if best:
        actions.append(f"Review best scored candidate: {best['strategy']} {best['symbol']} {best['timeframe']} score={best['score']}")
    else:
        actions.append("No KEEP or strong REVIEW candidate is ready yet")
    completed_keep = [job for job in jobs if job.get("status") == "COMPLETED" and job.get("recommendation") == "KEEP"]
    if completed_keep:
        latest = completed_keep[-1]
        actions.append(f"Consider manual MT5 review gate for {latest['strategy']} {latest['symbol']} {latest['timeframe']}")
    if not actions:
        actions.append("No urgent action; import fresh CSV data or queue a targeted backtest")
    return actions[:limit]


def write_research_loop_summary(
    queued: list[dict[str, Any]],
    worker_result: Any,
    stats: dict[str, int],
    actions: list[str],
) -> Path:
    output = Path(REPORT_DIR) / "research_loop_summary.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TAR Research Loop Summary",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        "- Mode: paper-only",
        f"- Newly queued jobs: {len(queued)}",
        f"- Worker processed: {getattr(worker_result, 'processed', 0) if worker_result else 0}",
        "",
        "## Queue Stats",
    ]
    for status, count in sorted(stats.items()):
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in actions)
    if queued:
        lines.extend(["", "## Newly Queued"])
        for job in queued[:25]:
            lines.append(f"- {job['strategy']} {job['symbol']} {job['timeframe']} {job['file']}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = output.with_suffix(".json")
    json_path.write_text(
        json.dumps(
            {
                "queued_jobs": queued,
                "worker_result": asdict(worker_result) if worker_result else None,
                "queue_stats": stats,
                "next_actions": actions,
                "paper_only": True,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    return output


def _best_review_result() -> dict[str, Any] | None:
    rows = [
        row
        for row in load_review_results()
        if "score" in row
        and str(row.get("verdict", "")).upper() in {"KEEP", "REVIEW"}
        and float(row.get("score", 0.0) or 0.0) >= 45.0
    ]
    if not rows:
        return None
    return max(rows, key=lambda row: float(row.get("score", 0.0) or 0.0))

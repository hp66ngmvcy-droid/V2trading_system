"""Online strategy finder and queue integrity checker.

This module builds on the existing local research controller and raw data
watcher. It scans raw CSV market data, queues eligible paper research jobs,
and performs queue-level verification of job mechanics.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from tar_system.controller.data_watcher import scan_raw_data
from tar_system.controller.job_queue import active_job_keys, make_active_job_key, read_jobs, queue_stats, update_job
from tar_system.strategies.registry import STRATEGIES


def _run_broad_sweep(topics: list[str]) -> dict:
    try:
        from tar_system.research.exa_searcher import broad_sweep
        return broad_sweep(topics)
    except RuntimeError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"exa_sweep failed: {exc}"}


def find_and_queue_strategies(
    raw_dir: str | Path = "data/raw",
    force: bool = False,
    broker: str = "current_broker_demo",
    research_stage: str = "smoke",
    window_months: int = 6,
    skip_walk_forward: bool | None = None,
    skip_forward_test: bool | None = None,
    max_walk_forward_splits: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    web_topics: list[str] | None = None,
) -> dict[str, Any]:
    """Scan raw data and queue online strategy research jobs."""
    raw_dir = Path(raw_dir)
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
    )
    return {
        "status": "QUEUED",
        "raw_dir": str(raw_dir),
        "force": force,
        "research_stage": research_stage,
        "window_months": window_months,
        "skip_walk_forward": skip_walk_forward,
        "skip_forward_test": skip_forward_test,
        "max_walk_forward_splits": max_walk_forward_splits,
        "from_date": from_date,
        "to_date": to_date,
        "queued_jobs": len(queued),
        "queue_stats": queue_stats(),
        "available_strategies": sorted(STRATEGIES.keys()),
        "active_job_count": len(active_job_keys()),
        "queued_preview": [
            {
                "strategy": job["strategy"],
                "symbol": job["symbol"],
                "timeframe": job["timeframe"],
                "file": job["file"],
                "research_stage": job["research_stage"],
            }
            for job in queued[:25]
        ],
        "exa_sweep": _run_broad_sweep(web_topics) if web_topics else None,
    }


def verify_online_strategy_finder(
    raw_dir: str | Path = "data/raw",
    force: bool = False,
    broker: str = "current_broker_demo",
    research_stage: str = "smoke",
    window_months: int = 6,
    skip_walk_forward: bool | None = None,
    skip_forward_test: bool | None = None,
    max_walk_forward_splits: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    """Queue new jobs and run an integrity check on the research queue."""
    result = find_and_queue_strategies(
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
    )
    jobs = read_jobs()
    invalid_jobs: list[dict[str, Any]] = []
    duplicate_keys: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str, str, str, str, str, str]] = set()

    active_statuses = {"QUEUED", "RUNNING"}
    for job in jobs:
        strategy = str(job.get("strategy", ""))
        if strategy not in STRATEGIES:
            invalid_jobs.append({"job_id": job.get("job_id"), "reason": "unknown_strategy", "strategy": strategy})

        file_path = Path(str(job.get("file", "")))
        if not file_path.exists():
            invalid_jobs.append({"job_id": job.get("job_id"), "reason": "missing_file", "file": str(file_path)})

        if str(job.get("status", "")) in active_statuses:
            key = make_active_job_key(
                strategy,
                str(job.get("symbol", "")),
                str(job.get("timeframe", "")),
                str(job.get("file", "")),
                job_type=str(job.get("type", "full_pipeline")),
                data_hash=job.get("data_hash"),
                from_date=job.get("from_date"),
                to_date=job.get("to_date"),
                research_stage=str(job.get("research_stage", "full")),
            )
            if key in seen_keys:
                duplicate_keys.append({"job_id": job.get("job_id"), "key": key})
            seen_keys.add(key)

    if duplicate_keys:
        duplicate_cleanup = cleanup_duplicate_active_jobs()
    else:
        duplicate_cleanup = {"cleaned_duplicate_active_jobs": 0, "cleaned_job_ids": []}

    job_stats = queue_stats()
    active_count = len(active_job_keys())
    return {
        "status": "PASS" if not invalid_jobs else "FAIL",
        "queued_summary": result,
        "queue_stats": job_stats,
        "active_job_count": active_count,
        "invalid_jobs": invalid_jobs,
        "duplicate_keys": duplicate_keys,
        "duplicate_cleanup": duplicate_cleanup,
        "loaded_raw_files": sorted(str(path) for path in Path(raw_dir).glob("*.csv")),
        "available_strategies": sorted(STRATEGIES.keys()),
    }


def cleanup_duplicate_active_jobs() -> dict[str, Any]:
    active_jobs = [job for job in read_jobs() if job["status"] in {"QUEUED", "RUNNING"}]
    seen_keys: set[tuple[str, str, str, str, str, str, str, str]] = set()
    cleaned: list[str] = []

    for job in sorted(active_jobs, key=lambda job: job.get("created_at") or job.get("job_id")):
        key = make_active_job_key(
            str(job.get("strategy", "")),
            str(job.get("symbol", "")),
            str(job.get("timeframe", "")),
            str(job.get("file", "")),
            job_type=str(job.get("type", "full_pipeline")),
            data_hash=job.get("data_hash"),
            from_date=job.get("from_date"),
            to_date=job.get("to_date"),
            research_stage=str(job.get("research_stage", "full")),
        )
        if key in seen_keys:
            update_job(
                job["job_id"],
                status="SKIPPED",
                completed_at=datetime.datetime.utcnow().isoformat(),
                result_path="duplicate_active_job",
            )
            cleaned.append(str(job.get("job_id")))
        else:
            seen_keys.add(key)

    return {
        "cleaned_duplicate_active_jobs": len(cleaned),
        "cleaned_job_ids": cleaned,
    }

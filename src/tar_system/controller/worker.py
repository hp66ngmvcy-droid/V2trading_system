"""Background worker for queued local research jobs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tar_system.controller.job_queue import queue_stats
from tar_system.controller.research_controller import run_controller_once


@dataclass(frozen=True)
class WorkerResult:
    processed: int
    stats: dict[str, int]
    last_result: dict[str, Any] | None = None


def run_worker(limit: int = 1) -> WorkerResult:
    processed = 0
    last: dict[str, Any] | None = None
    for _ in range(max(1, limit)):
        result = run_controller_once()
        last = result
        if result.get("status") == "idle":
            break
        processed += 1
    return WorkerResult(processed=processed, stats=queue_stats(), last_result=last)


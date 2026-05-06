"""Synthetic scale checks for the local queue/cache layer."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from time import perf_counter

from tar_system.cache.artifact_cache import artifact_stats, make_artifact_key, record_artifact
from tar_system.controller.job_queue import add_job, delete_jobs_by_data_hash_prefix, next_queued_job, queue_stats, update_job


@dataclass(frozen=True)
class LoadTestResult:
    jobs_created: int
    artifacts_created: int
    queue_insert_seconds: float
    artifact_insert_seconds: float
    next_job_lookup_seconds: float
    queue_stats: dict[str, int]
    artifact_stats: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_load_test(job_count: int = 1000, artifact_count: int = 1000) -> LoadTestResult:
    delete_jobs_by_data_hash_prefix("load-test-")
    job_ids: list[str] = []
    started = perf_counter()
    for index in range(job_count):
        symbol = "XAUUSD" if index % 2 == 0 else "BTCUSD"
        job = add_job("gold_v2", symbol, "M15", f"data/raw/{symbol}_M15.csv", priority=index % 10, data_hash=f"load-test-{index}")
        job_ids.append(job["job_id"])
    queue_seconds = perf_counter() - started

    started = perf_counter()
    for index in range(artifact_count):
        key = make_artifact_key("synthetic", "gold_v2", "XAUUSD", "M15", f"hash-{index}")
        record_artifact(key, "synthetic", f"data/results/synthetic_{index}.json", "gold_v2", "XAUUSD", "M15", f"hash-{index}")
    artifact_seconds = perf_counter() - started

    started = perf_counter()
    next_queued_job()
    lookup_seconds = perf_counter() - started
    for job_id in job_ids:
        update_job(job_id, status="SKIPPED", recommendation="LOAD_TEST_ONLY")

    result = LoadTestResult(
        jobs_created=job_count,
        artifacts_created=artifact_count,
        queue_insert_seconds=round(queue_seconds, 4),
        artifact_insert_seconds=round(artifact_seconds, 4),
        next_job_lookup_seconds=round(lookup_seconds, 6),
        queue_stats=queue_stats(),
        artifact_stats=artifact_stats(),
    )
    delete_jobs_by_data_hash_prefix("load-test-")
    return result

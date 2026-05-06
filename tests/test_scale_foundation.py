from __future__ import annotations

import json
from pathlib import Path

from tar_system.cache.artifact_cache import artifact_stats, get_artifact, has_valid_artifact, make_artifact_key, record_artifact, save_json_artifact
from tar_system.controller.job_queue import add_job, clear_completed, next_queued_job, queue_stats, read_jobs, update_job
from tar_system.controller.load_test import run_load_test
from tar_system.controller.worker import run_worker


def test_duckdb_queue_add_next_update_and_stats(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv", priority=10)
    fast = add_job("gold_v2", "BTCUSD", "M15", "data/raw/BTCUSD_M15.csv", priority=1)
    assert next_queued_job()["job_id"] == fast["job_id"]
    update_job(fast["job_id"], status="COMPLETED", recommendation="KEEP")
    assert queue_stats()["COMPLETED"] == 1
    assert len(read_jobs()) == 2


def test_clear_completed_keeps_active_jobs(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    first = add_job("gold_v2", "XAUUSD", "M15", "file.csv")
    second = add_job("gold_v2", "BTCUSD", "M15", "file.csv")
    update_job(first["job_id"], status="COMPLETED")
    clear_completed()
    jobs = read_jobs()
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == second["job_id"]


def test_artifact_cache_records_and_validates_path(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    key = make_artifact_key("backtest", "gold_v2", "XAUUSD", "M15", "hash")
    path = save_json_artifact(key, "backtest", "data/results/example.json", {"ok": True}, strategy="gold_v2")
    assert path.exists()
    assert has_valid_artifact(key)
    assert get_artifact(key)["path"] == "data/results/example.json"
    assert artifact_stats()["backtest"] == 1


def test_artifact_cache_missing_file_is_not_valid(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    key = make_artifact_key("walk_forward", "gold_v2", "XAUUSD", "M15", "hash")
    record_artifact(key, "walk_forward", "missing.json")
    assert not has_valid_artifact(key)


def test_worker_processes_until_idle(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    import tar_system.controller.worker as worker

    calls = [{"status": "COMPLETED"}, {"status": "idle"}]
    monkeypatch.setattr(worker, "run_controller_once", lambda: calls.pop(0))
    result = run_worker(limit=5)
    assert result.processed == 1


def test_load_test_creates_indexed_rows(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_load_test(job_count=5, artifact_count=5)
    assert result.jobs_created == 5
    assert result.artifacts_created == 5
    assert result.next_job_lookup_seconds >= 0
    assert result.queue_stats["SKIPPED"] >= 5
    assert result.artifact_stats["synthetic"] == 5


def test_jsonl_mirror_written_for_manual_inspection(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    add_job("gold_v2", "XAUUSD", "M15", "file.csv")
    rows = [json.loads(line) for line in Path("runtime/job_queue.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["strategy"] == "gold_v2"

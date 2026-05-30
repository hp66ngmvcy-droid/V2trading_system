from __future__ import annotations

import argparse
import json
from pathlib import Path

from tar_system.controller.data_watcher import scan_raw_data
from tar_system.controller.job_queue import add_job, claim_next_job, has_active_job, next_queued_job, queue_health, read_jobs, update_job
from tar_system.controller.research_controller import debate_recommendation, run_controller_once
from tar_system.controller.research_loop import recommend_next_actions, run_research_loop
from tar_system.dashboard.runtime_control import mark_data_tested
from tar_system.environment.risk_state import EnvironmentDecision
from tar_system.cli import queue_health_cmd, show_queue_cmd


def _raw_file(path: Path, text: str = "timestamp,open,high,low,close,volume\n2026-01-01,1,2,1,1.5,10\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_data_watcher_detects_new_file_by_hash_change(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _raw_file(Path("data/raw/XAUUSD_M15.csv"))
    queued = scan_raw_data()
    assert {job["strategy"] for job in queued} == {"gold_v2", "rsi_reversion_v1"}


def test_data_watcher_skips_same_hash_and_force_reruns(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = _raw_file(Path("data/raw/XAUUSD_M15.csv"))
    from tar_system.data.csv_importer import hash_csv_file

    data_hash = hash_csv_file(path)
    mark_data_tested("gold_v2", "XAUUSD", "M15", data_hash, "full_pipeline")
    assert [job["strategy"] for job in scan_raw_data()] == ["rsi_reversion_v1"]
    forced = scan_raw_data(force=True)
    assert [job["strategy"] for job in forced] == ["gold_v2"]


def test_data_watcher_skips_per_strategy_not_whole_hash(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = _raw_file(Path("data/raw/XAUUSD_M15.csv"))
    from tar_system.data.csv_importer import hash_csv_file

    data_hash = hash_csv_file(path)
    mark_data_tested("gold_v2", "XAUUSD", "M15", data_hash, "full_pipeline")
    queued = scan_raw_data()
    assert [job["strategy"] for job in queued] == ["rsi_reversion_v1"]


def test_data_watcher_does_not_duplicate_active_jobs(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _raw_file(Path("data/raw/XAUUSD_M15.csv"))
    assert len(scan_raw_data()) == 2
    assert scan_raw_data() == []


def test_data_watcher_smoke_stage_queues_recent_slice(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _raw_file(
        Path("data/raw/XAUUSD_M15.csv"),
        "timestamp,open,high,low,close,volume\n"
        "2026-01-01,1,2,1,1.5,10\n"
        "2026-03-15,1,2,1,1.5,10\n",
    )

    queued = scan_raw_data(research_stage="smoke", window_months=1)

    assert queued
    assert {job["research_stage"] for job in queued} == {"smoke"}
    assert {job["from_date"] for job in queued} == {"2026-02-15"}
    assert {job["to_date"] for job in queued} == {"2026-03-15"}
    assert all(job["skip_walk_forward"] is False for job in queued)
    assert all(job["skip_forward_test"] for job in queued)
    assert all(job["max_walk_forward_splits"] == 10 for job in queued)
    assert all(job["priority"] == 10 for job in queued)


def test_data_watcher_dashboard_batch_skips_forward_test(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _raw_file(Path("data/raw/XAUUSD_M15.csv"))

    queued = scan_raw_data(
        research_stage="dashboard_batch",
        from_date="2026-01-01",
        to_date="2026-03-31",
        skip_walk_forward=True,
        skip_forward_test=True,
    )

    assert queued
    assert all(job["from_date"] == "2026-01-01" for job in queued)
    assert all(job["to_date"] == "2026-03-31" for job in queued)
    assert all(job["skip_walk_forward"] is True for job in queued)
    assert all(job["skip_forward_test"] is True for job in queued)
    assert all(job["research_stage"] == "dashboard_batch" for job in queued)


def test_job_queue_add_read_update(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    job = add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv")
    assert next_queued_job()["job_id"] == job["job_id"]
    update_job(job["job_id"], status="COMPLETED", recommendation="KEEP")
    assert read_jobs()[0]["recommendation"] == "KEEP"


def test_queue_health_classifies_failed_jobs(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    fast = add_job(
        "gold_v2",
        "XAUUSD",
        "M15",
        "data/raw/XAUUSD_M15.csv",
        research_stage="dashboard_batch",
        skip_walk_forward=True,
        skip_forward_test=True,
    )
    update_job(fast["job_id"], status="FAILED", completed_at="2026-05-24T00:00:00")
    incomplete = add_job("gold_v2", "EURUSD", "M15", "data/raw/EURUSD_M15.csv", research_stage="full")
    update_job(incomplete["job_id"], status="FAILED")

    health = queue_health()

    assert health["queue_stats"]["FAILED"] == 2
    assert health["failed_buckets"]["failed_dashboard_or_fast_batch_no_result"] == 1
    assert health["failed_buckets"]["failed_no_completion_timestamp"] == 1
    assert health["failed_by_stage"][0] in [("dashboard_batch", 1), ("full", 1)]


def test_queue_health_cmd_can_write_report(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    job = add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv")
    update_job(job["job_id"], status="FAILED", completed_at="2026-05-24T00:00:00")

    queue_health_cmd(argparse.Namespace(limit=5, output="runtime/queue-health.json"))

    payload = json.loads(Path("runtime/queue-health.json").read_text(encoding="utf-8"))
    assert payload["failed_jobs"] == 1
    assert json.loads(capsys.readouterr().out)["failed_jobs"] == 1


def test_job_queue_claim_marks_running_atomically(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    job = add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv")

    claimed = claim_next_job()

    assert claimed is not None
    assert claimed["job_id"] == job["job_id"]
    assert claimed["status"] == "RUNNING"
    assert claimed["started_at"] is not None
    assert next_queued_job() is None


def test_active_job_dedupe_uses_hash_before_file_path(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv", data_hash="same-hash")

    assert has_active_job("gold_v2", "XAUUSD", "M15", "/abs/path/XAUUSD_M15.csv", data_hash="same-hash")
    assert not has_active_job("gold_v2", "XAUUSD", "M15", "/abs/path/XAUUSD_M15.csv", data_hash="other-hash")


def test_add_job_blocks_duplicate_active_hash_job(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    first = add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv", data_hash="same-hash")
    second = add_job("gold_v2", "XAUUSD", "M15", "/absolute/XAUUSD_M15.csv", data_hash="same-hash")

    jobs = read_jobs()
    assert first["job_id"] == second["job_id"]
    assert len(jobs) == 1


def test_add_job_allows_same_hash_after_active_job_completes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    first = add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv", data_hash="same-hash")
    update_job(first["job_id"], status="COMPLETED")

    second = add_job("gold_v2", "XAUUSD", "M15", "/absolute/XAUUSD_M15.csv", data_hash="same-hash")

    assert second["job_id"] != first["job_id"]
    assert len(read_jobs()) == 2


def test_add_job_allows_distinct_research_windows(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv", data_hash="same-hash", from_date="2026-01-01")
    add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv", data_hash="same-hash", from_date="2026-02-01")

    assert len(read_jobs()) == 2


def test_controller_picks_next_queued_job_and_completes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("data/features").mkdir(parents=True)
    Path("data/features/XAUUSD_M15.parquet").write_text("feature", encoding="utf-8")
    add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv")

    def pipeline_runner(args: argparse.Namespace) -> None:
        Path("data/results/gold_v2_XAUUSD_M15_metrics.json").write_text(
            json.dumps({"profit_factor": 1.5, "sharpe_ratio": 1.0, "win_rate": 0.6, "max_drawdown": 0.05, "max_consecutive_losses": 1}),
            encoding="utf-8",
        )

    class Cost:
        def to_dict(self) -> dict[str, object]:
            return {"cost_sensitive": False, "swap_drag": 0.0}

    result = run_controller_once(pipeline_runner=pipeline_runner, cost_runner=lambda *_: Cost())
    assert result["status"] == "COMPLETED"
    assert result["recommendation"] == "KEEP"
    assert any(job["strategy"] == "rsi_reversion_v1" for job in read_jobs())


def test_controller_passes_staged_job_window_to_pipeline(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    captured: dict[str, object] = {}
    add_job(
        "gold_v2",
        "XAUUSD",
        "M15",
        "data/raw/XAUUSD_M15.csv",
        from_date="2026-01",
        to_date="2026-03",
        skip_walk_forward=True,
        skip_forward_test=True,
        max_walk_forward_splits=3,
        research_stage="smoke",
        require_walk_forward=False,
    )

    def pipeline_runner(args: argparse.Namespace) -> None:
        captured.update(vars(args))
        Path("data/results/gold_v2_XAUUSD_M15_metrics.json").write_text(
            json.dumps({"profit_factor": 1.5, "sharpe_ratio": 1.0, "win_rate": 0.6}),
            encoding="utf-8",
        )

    result = run_controller_once(pipeline_runner=pipeline_runner, cost_runner=lambda *_: {"cost_sensitive": False, "swap_drag": 0.0})

    assert result["status"] == "COMPLETED"
    assert captured["from_date"] == "2026-01"
    assert captured["to_date"] == "2026-03"
    assert captured["skip_walk_forward"] is True
    assert captured["skip_forward_test"] is True
    assert captured["max_walk_forward_splits"] == 3


def test_controller_marks_failed_on_bad_data_and_does_not_continue(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    add_job("gold_v2", "XAUUSD", "M15", "bad.csv")
    called = {"cost": False}

    def bad_pipeline(args: argparse.Namespace) -> None:
        raise SystemExit("bad data")

    def cost_runner(*args: object) -> dict[str, object]:
        called["cost"] = True
        return {}

    result = run_controller_once(pipeline_runner=bad_pipeline, cost_runner=cost_runner)
    assert result["status"] == "FAILED"
    assert called["cost"] is False


def test_controller_skips_block_and_hold_environment(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    import tar_system.controller.research_controller as rc

    add_job("gold_v2", "XAUUSD", "M15", "file.csv")
    monkeypatch.setattr(rc, "evaluate_environment", lambda *args, **kwargs: EnvironmentDecision("BLOCK_TRADING"))
    assert run_controller_once()["status"] == "SKIPPED"
    add_job("gold_v2", "XAUUSD", "M15", "file.csv")
    monkeypatch.setattr(rc, "evaluate_environment", lambda *args, **kwargs: EnvironmentDecision("HOLD_TRADING"))
    result = run_controller_once()
    assert result["status"] == "SKIPPED"
    assert result["recommendation"] == "REVIEW"


def test_controller_runs_queued_paper_signal_without_full_pipeline(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    add_job(
        "gold_v2",
        "XAUUSD",
        "M15",
        "data/raw/XAUUSD_M15.csv",
        job_type="paper_signal",
        require_walk_forward=False,
        skip_walk_forward=True,
        skip_forward_test=True,
    )

    def paper_signal_runner(*args: object) -> dict[str, object]:
        return {"alert_ready": True, "risk_approved": True, "risk_reason": "APPROVED"}

    result = run_controller_once(
        pipeline_runner=lambda *_: (_ for _ in ()).throw(AssertionError("full pipeline should not run")),
        paper_signal_runner=paper_signal_runner,
    )

    assert result["status"] == "COMPLETED"
    assert result["recommendation"] == "KEEP"
    assert result["result_path"] == "runtime/latest_paper_signal.json"


def test_bull_bear_debate_and_cost_override() -> None:
    strong = {"profit_factor": 1.6, "sharpe_ratio": 1.0, "win_rate": 0.6, "max_drawdown": 0.05, "max_consecutive_losses": 1}
    assert debate_recommendation(strong, False).recommendation == "KEEP"
    assert debate_recommendation(strong, True).recommendation == "REVIEW"


def test_controller_never_writes_mt5_or_auto_promotes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv")

    def pipeline_runner(args: argparse.Namespace) -> None:
        Path("data/results/gold_v2_XAUUSD_M15_metrics.json").write_text(json.dumps({"profit_factor": 0.5}), encoding="utf-8")

    run_controller_once(pipeline_runner=pipeline_runner, cost_runner=lambda *_: {"cost_sensitive": True, "swap_drag": 0.0})
    assert not Path("runtime/mt5_promotion_log.json").exists()


def test_show_queue_prints_state(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    add_job("gold_v2", "XAUUSD", "M15", "file.csv")
    show_queue_cmd(argparse.Namespace())
    assert "gold_v2" in capsys.readouterr().out


def test_research_loop_queue_only_writes_summary(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _raw_file(Path("data/raw/XAUUSD_M15.csv"))

    result = run_research_loop(run_worker_now=False)

    assert result.queued_jobs == 2
    assert result.processed_jobs == 0
    assert Path(result.summary_path).exists()
    assert "paper-only" in Path(result.summary_path).read_text(encoding="utf-8")


def test_research_loop_next_actions_mentions_queue(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    add_job("gold_v2", "XAUUSD", "M15", "file.csv")

    actions = recommend_next_actions()

    assert any("queued" in action for action in actions)


def test_research_loop_does_not_recommend_low_score_kill(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()
    Path("logs/review_log.jsonl").write_text(
        json.dumps(
            {
                "strategy": "rsi_reversion_v1",
                "symbol": "EURUSD",
                "timeframe": "M15",
                "score": 17.84,
                "verdict": "KILL",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    actions = recommend_next_actions()

    assert not any("best scored candidate" in action for action in actions)
    assert any("No KEEP or strong REVIEW" in action for action in actions)

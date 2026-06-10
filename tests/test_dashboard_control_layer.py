from __future__ import annotations

from datetime import datetime, time
from pathlib import Path

from tar_system.dashboard.pages.leaderboard import load_leaderboard_rows
from tar_system.dashboard.runtime_control import (
    begin_task,
    approve_next_mt5_test,
    finish_task,
    has_tested_data,
    mark_data_tested,
    read_activity,
    read_backtest_status,
    read_forward_status,
    read_global_status,
    read_run_history,
    read_schedule,
    read_tested_data_registry,
    request_start_backtest,
    request_start_forward_test,
    request_stop_active_task,
    request_stop_backtest,
    request_stop_forward_test,
    reset_global_status,
    schedule_research_run,
    write_schedule_jobs,
    write_status,
)


def test_runtime_status_write_read(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    write_status("backtest", {"running": True, "symbol": "XAUUSD", "timeframe": "M15", "strategy": "gold_v2"})
    status = read_backtest_status()
    assert status["running"] is True
    assert status["symbol"] == "XAUUSD"


def test_stop_flag_creation(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    request_start_backtest({"symbol": "XAUUSD", "timeframe": "M15", "strategy": "gold_v2"})
    request_stop_backtest()
    request_start_forward_test({"symbol": "XAUUSD", "timeframe": "M15", "strategy": "gold_v2"})
    request_stop_forward_test()
    assert read_backtest_status()["stop_requested"] is True
    assert read_forward_status()["stop_requested"] is True


def test_dashboard_imports() -> None:
    import tar_system.dashboard.app as app
    import tar_system.dashboard.pages.asset_data as asset_data
    import tar_system.dashboard.pages.environment as environment
    import tar_system.dashboard.pages.overview as overview
    import tar_system.dashboard.pages.run_control as run_control
    import tar_system.dashboard.pages.strategy_detail as strategy_detail

    assert callable(app.main)
    assert callable(overview.render)
    assert callable(run_control.render)
    assert callable(asset_data.render)
    assert callable(strategy_detail.render)
    assert callable(environment.render)


def test_asset_data_live_reference_url_points_to_tradingview() -> None:
    from tar_system.dashboard.pages.asset_data import live_reference_url

    assert live_reference_url("XAUUSD", "M15") == "https://www.tradingview.com/chart/?symbol=OANDA%3AXAUUSD&interval=15"
    assert live_reference_url("BTCUSD", "H1") == "https://www.tradingview.com/chart/?symbol=BITSTAMP%3ABTCUSD&interval=60"


def test_leaderboard_loads_empty_state_safely(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert load_leaderboard_rows() == []


def test_security_page_imports() -> None:
    import tar_system.dashboard.pages.security as security

    assert callable(security.render)


def test_run_control_auto_refresh_helper_is_safe() -> None:
    from tar_system.dashboard.pages.run_control import _auto_refresh_while_active

    _auto_refresh_while_active({"status": "IDLE"})


def test_runtime_files_exist() -> None:
    assert Path("runtime/backtest_status.json").exists()
    assert Path("runtime/forward_test_status.json").exists()


def test_schedule_and_duplicate_registry(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    schedule_research_run({"strategy": "gold_v2", "symbol": "XAUUSD", "timeframe": "M15", "run_at": "2026-06-12T09:00:00"})
    assert read_schedule()["scheduled"] is True
    assert read_schedule()["jobs"][0]["paper_only"] is True

    assert not has_tested_data("gold_v2", "XAUUSD", "M15", "abc", "full_pipeline", "2026-01", "2026-03")
    mark_data_tested("gold_v2", "XAUUSD", "M15", "abc", "full_pipeline", "reports/example.md", "2026-01", "2026-03")
    assert has_tested_data("gold_v2", "XAUUSD", "M15", "abc", "full_pipeline", "2026-01", "2026-03")
    assert not has_tested_data("gold_v2", "XAUUSD", "M15", "abc", "full_pipeline", "2026-04", "2026-06")
    assert read_tested_data_registry()[0]["result_path"] == "reports/example.md"


def test_green_light_mt5_review_is_manual_only(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = approve_next_mt5_test({"strategy": "gold_v2", "symbol": "XAUUSD", "timeframe": "M15"})
    text = path.read_text(encoding="utf-8")
    assert "manual_review_required" in text
    assert "paper_only" in text


def test_schedule_writer_marks_unscheduled_when_complete(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    write_schedule_jobs([{"status": "completed"}])
    assert read_schedule()["scheduled"] is False


def test_global_run_lock_and_reset(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    task = begin_task("backtest", "Start Backtest", {"symbol": "XAUUSD", "timeframe": "M15", "strategy": "gold_v2"})

    assert read_global_status()["status"] == "RUNNING"
    assert read_global_status()["run_id"] == task["run_id"]

    stopped = request_stop_active_task()
    assert stopped["status"] == "STOPPING"
    finished = finish_task("STOPPED", "Backtest stopped safely")
    assert finished["status"] == "STOPPED"
    assert read_run_history()[0]["status"] == "STOPPED"

    reset_global_status()
    assert read_global_status()["status"] == "IDLE"


def test_activity_feed_records_task_events(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    begin_task("feature_build", "Build Features", {"symbol": "XAUUSD", "timeframe": "M15", "strategy": "gold_v2"})
    finish_task("COMPLETED", "Feature build completed")

    events = read_activity()

    assert [event["event_type"] for event in events] == ["task_started", "task_completed"]


def test_next_daily_run_at_rolls_to_tomorrow_when_time_passed() -> None:
    from tar_system.dashboard.pages.run_control import _next_daily_run_at

    result = _next_daily_run_at(time(2, 5), datetime(2026, 5, 4, 3, 0))

    assert result == datetime(2026, 5, 5, 2, 5)


def test_schedule_daily_all_tests_payload(tmp_path, monkeypatch) -> None:
    from tar_system.dashboard.pages.run_control import _schedule_daily_all_tests

    monkeypatch.chdir(tmp_path)
    _schedule_daily_all_tests(
        {
            "broker": "current_broker_demo",
            "from_date": "2026-01-01",
            "to_date": "2026-03-31",
            "force_all_tests": False,
        },
        datetime(2026, 5, 5, 2, 5),
    )

    job = read_schedule()["jobs"][0]
    assert job["job_type"] == "all_tests"
    assert job["repeat_daily"] is True
    assert job["paper_only"] is True
    assert job["from_date"] == "2026-01-01"
    assert job["to_date"] == "2026-03-31"

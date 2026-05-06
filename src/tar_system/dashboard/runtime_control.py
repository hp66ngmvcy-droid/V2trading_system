"""Runtime status controls for dashboard-triggered paper workflows."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUNTIME_DIR = Path("runtime")
SCHEDULE_PATH = RUNTIME_DIR / "automation_schedule.json"
TESTED_DATA_PATH = RUNTIME_DIR / "tested_data_registry.json"
MT5_REVIEW_PATH = RUNTIME_DIR / "mt5_next_test.json"
MT5_PROMOTION_LOG_PATH = RUNTIME_DIR / "mt5_promotion_log.json"
GLOBAL_STATUS_PATH = RUNTIME_DIR / "dashboard_run_status.json"
ACTIVITY_PATH = RUNTIME_DIR / "dashboard_activity.jsonl"
RUN_HISTORY_PATH = RUNTIME_DIR / "dashboard_run_history.json"

FINAL_STATES = {"STOPPED", "COMPLETED", "FAILED"}
ACTIVE_STATES = {"RUNNING", "STOPPING"}


def default_status(mode: str) -> dict[str, Any]:
    return {
        "running": False,
        "stop_requested": False,
        "started_at": None,
        "stopped_at": None,
        "symbol": None,
        "timeframe": None,
        "strategy": None,
        "mode": mode,
        "latest_message": "idle",
        "latest_result_path": None,
    }


def default_global_status() -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "run_id": None,
        "task_type": None,
        "task_name": "No active task",
        "status": "IDLE",
        "symbol": None,
        "timeframe": None,
        "strategy": None,
        "from_date": None,
        "to_date": None,
        "created_at": None,
        "started_at": None,
        "finished_at": None,
        "last_update": now,
        "last_heartbeat": None,
        "progress_pct": 0.0,
        "bars_processed": 0,
        "total_bars": 0,
        "current_date": None,
        "trades_opened": 0,
        "trades_closed": 0,
        "current_equity": None,
        "current_drawdown": None,
        "current_regime": None,
        "last_signal": None,
        "last_risk_decision": None,
        "latest_message": "idle",
        "latest_result_path": None,
        "command": None,
        "terminal": [],
    }


def read_global_status() -> dict[str, Any]:
    if not GLOBAL_STATUS_PATH.exists():
        return default_global_status()
    return {**default_global_status(), **json.loads(GLOBAL_STATUS_PATH.read_text(encoding="utf-8"))}


def write_global_status(status: dict[str, Any]) -> Path:
    GLOBAL_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {**read_global_status(), **status, "last_update": datetime.now(timezone.utc).isoformat()}
    GLOBAL_STATUS_PATH.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return GLOBAL_STATUS_PATH


def is_task_active(status: dict[str, Any] | None = None) -> bool:
    return str((status or read_global_status()).get("status", "IDLE")).upper() in ACTIVE_STATES


def begin_task(task_type: str, task_name: str, config: dict[str, Any]) -> dict[str, Any]:
    current = read_global_status()
    if is_task_active(current):
        raise RuntimeError(f"Another task is currently running: {current.get('task_name')}. Stop or wait for completion.")
    now = datetime.now(timezone.utc).isoformat()
    run_id = uuid.uuid4().hex[:12]
    status = {
        **default_global_status(),
        **config,
        "run_id": run_id,
        "task_type": task_type,
        "task_name": task_name,
        "status": "RUNNING",
        "created_at": now,
        "started_at": now,
        "last_heartbeat": now,
        "latest_message": f"{task_name} started",
    }
    write_global_status(status)
    append_activity("task_started", f"{task_name} started", status)
    return status


def heartbeat(message: str | None = None, progress_pct: float | None = None, **metrics: Any) -> Path:
    now = datetime.now(timezone.utc).isoformat()
    status = {**metrics, "last_heartbeat": now}
    if message:
        status["latest_message"] = message
        append_activity("progress_update", message, {**read_global_status(), **status})
    if progress_pct is not None:
        status["progress_pct"] = progress_pct
    return write_global_status(status)


def request_stop_active_task() -> dict[str, Any]:
    status = read_global_status()
    if not is_task_active(status):
        return status
    payload = {
        **status,
        "status": "STOPPING",
        "stop_requested": True,
        "latest_message": "Stop requested",
    }
    write_global_status(payload)
    append_activity("task_stopped", "Stop requested", payload)
    return payload


def finish_task(status_name: str, message: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
    current = read_global_status()
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        **current,
        **(result or {}),
        "status": status_name,
        "finished_at": now,
        "last_heartbeat": now,
        "latest_message": message,
    }
    write_global_status(payload)
    append_activity("task_completed" if status_name == "COMPLETED" else "task_failed", message, payload)
    append_run_history(payload)
    return payload


def reset_global_status() -> Path:
    status = read_global_status()
    if is_task_active(status):
        raise RuntimeError(f"Cannot reset while task is active: {status.get('task_name')}")
    append_activity("task_reset", "Run state reset", status)
    return write_global_status(default_global_status())


def append_activity(event_type: str, message: str, metadata: dict[str, Any] | None = None) -> Path:
    ACTIVITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "message": message,
        "metadata": metadata or {},
    }
    with ACTIVITY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, default=str) + "\n")
    return ACTIVITY_PATH


def read_activity(limit: int = 50) -> list[dict[str, Any]]:
    if not ACTIVITY_PATH.exists():
        return []
    rows = [json.loads(line) for line in ACTIVITY_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows[-limit:]


def append_run_history(run: dict[str, Any]) -> Path:
    history = read_run_history(limit=500)
    history.append(run)
    RUN_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_HISTORY_PATH.write_text(json.dumps({"runs": history[-500:]}, indent=2, default=str), encoding="utf-8")
    return RUN_HISTORY_PATH


def read_run_history(limit: int = 25) -> list[dict[str, Any]]:
    if not RUN_HISTORY_PATH.exists():
        return []
    rows = list(json.loads(RUN_HISTORY_PATH.read_text(encoding="utf-8")).get("runs", []))
    return rows[-limit:]


def status_path(kind: str) -> Path:
    if kind not in {"backtest", "forward_test"}:
        raise ValueError(f"Unknown runtime status kind: {kind}")
    return RUNTIME_DIR / f"{kind}_status.json"


def read_status(kind: str) -> dict[str, Any]:
    path = status_path(kind)
    if not path.exists():
        return default_status(kind)
    return {**default_status(kind), **json.loads(path.read_text(encoding="utf-8"))}


def write_status(kind: str, status: dict[str, Any]) -> Path:
    path = status_path(kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**default_status(kind), **status}
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def request_start_backtest(config: dict[str, Any]) -> Path:
    return write_status(
        "backtest",
        {
            **config,
            "running": True,
            "stop_requested": False,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "stopped_at": None,
            "mode": "backtest",
            "latest_message": "start requested from dashboard",
        },
    )


def request_stop_backtest() -> Path:
    status = read_backtest_status()
    return write_status("backtest", {**status, "stop_requested": True, "stopped_at": datetime.now(timezone.utc).isoformat(), "latest_message": "stop requested"})


def request_start_forward_test(config: dict[str, Any]) -> Path:
    return write_status(
        "forward_test",
        {
            **config,
            "running": True,
            "stop_requested": False,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "stopped_at": None,
            "mode": "forward_test",
            "latest_message": "start requested from dashboard",
        },
    )


def request_stop_forward_test() -> Path:
    status = read_forward_status()
    return write_status("forward_test", {**status, "stop_requested": True, "stopped_at": datetime.now(timezone.utc).isoformat(), "latest_message": "stop requested"})


def read_backtest_status() -> dict[str, Any]:
    return read_status("backtest")


def read_forward_status() -> dict[str, Any]:
    return read_status("forward_test")


def read_schedule() -> dict[str, Any]:
    if not SCHEDULE_PATH.exists():
        return {"scheduled": False, "jobs": []}
    return {"scheduled": False, "jobs": [], **json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))}


def schedule_research_run(config: dict[str, Any]) -> Path:
    schedule = read_schedule()
    jobs = list(schedule.get("jobs", []))
    job = {
        **config,
        "paper_only": True,
        "status": "scheduled",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    jobs.append(job)
    SCHEDULE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_PATH.write_text(json.dumps({"scheduled": True, "jobs": jobs}, indent=2, default=str), encoding="utf-8")
    return SCHEDULE_PATH


def write_schedule_jobs(jobs: list[dict[str, Any]]) -> Path:
    SCHEDULE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_PATH.write_text(json.dumps({"scheduled": any(job.get("status") == "scheduled" for job in jobs), "jobs": jobs}, indent=2, default=str), encoding="utf-8")
    return SCHEDULE_PATH


def cancel_scheduled_job(index: int) -> Path:
    schedule = read_schedule()
    jobs = list(schedule.get("jobs", []))
    if 0 <= index < len(jobs):
        jobs.pop(index)
    return write_schedule_jobs(jobs)


def request_run_scheduled_job_now(index: int) -> Path:
    schedule = read_schedule()
    jobs = list(schedule.get("jobs", []))
    if 0 <= index < len(jobs):
        jobs[index] = {**jobs[index], "status": "run_now", "requested_at": datetime.now(timezone.utc).isoformat()}
    return write_schedule_jobs(jobs)


def read_tested_data_registry() -> list[dict[str, Any]]:
    if not TESTED_DATA_PATH.exists():
        return []
    payload = json.loads(TESTED_DATA_PATH.read_text(encoding="utf-8"))
    return list(payload.get("runs", []))


def has_tested_data(
    strategy: str,
    symbol: str,
    timeframe: str,
    data_hash: str | None,
    mode: str,
    from_date: str | None = None,
    to_date: str | None = None,
) -> bool:
    return any(
        run.get("strategy") == strategy
        and run.get("symbol") == symbol
        and run.get("timeframe") == timeframe
        and run.get("data_hash") == data_hash
        and run.get("mode") == mode
        and run.get("from_date") == from_date
        and run.get("to_date") == to_date
        for run in read_tested_data_registry()
    )


def mark_data_tested(
    strategy: str,
    symbol: str,
    timeframe: str,
    data_hash: str | None,
    mode: str,
    result_path: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> Path:
    runs = read_tested_data_registry()
    if not has_tested_data(strategy, symbol, timeframe, data_hash, mode, from_date, to_date):
        runs.append(
            {
                "strategy": strategy,
                "symbol": symbol,
                "timeframe": timeframe,
                "data_hash": data_hash,
                "mode": mode,
                "from_date": from_date,
                "to_date": to_date,
                "result_path": result_path,
                "tested_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    TESTED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    TESTED_DATA_PATH.write_text(json.dumps({"runs": runs}, indent=2, default=str), encoding="utf-8")
    return TESTED_DATA_PATH


def approve_next_mt5_test(config: dict[str, Any]) -> Path:
    payload = {
        **config,
        "paper_only": True,
        "manual_review_required": True,
        "approved_for_next_mt5_review": True,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "latest_message": "green-lighted for next manual MT5 review file",
    }
    MT5_REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    MT5_REVIEW_PATH.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return MT5_REVIEW_PATH


def append_mt5_promotion_log(entry: dict[str, Any]) -> Path:
    payload = {"entries": []}
    if MT5_PROMOTION_LOG_PATH.exists():
        payload = {"entries": [], **json.loads(MT5_PROMOTION_LOG_PATH.read_text(encoding="utf-8"))}
    entries = list(payload.get("entries", []))
    entries.append({**entry, "paper_only": True, "created_at": datetime.now(timezone.utc).isoformat()})
    MT5_PROMOTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    MT5_PROMOTION_LOG_PATH.write_text(json.dumps({"entries": entries}, indent=2, default=str), encoding="utf-8")
    return MT5_PROMOTION_LOG_PATH


def read_mt5_promotion_log() -> list[dict[str, Any]]:
    if not MT5_PROMOTION_LOG_PATH.exists():
        return []
    return list(json.loads(MT5_PROMOTION_LOG_PATH.read_text(encoding="utf-8")).get("entries", []))

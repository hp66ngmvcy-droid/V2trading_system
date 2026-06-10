"""Small JSON checkpoint for resumable local research pipelines."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUNTIME_PATH = Path("runtime") / "pipeline_status.json"


def make_run_id(strategy: str, symbol: str, timeframe: str) -> str:
    return f"{strategy}_{symbol}_{timeframe}"


def default_checkpoint(run_id: str, strategy: str, symbol: str, timeframe: str, file: str, data_hash: str | None) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "strategy": strategy,
        "symbol": symbol,
        "timeframe": timeframe,
        "file": file,
        "data_hash": data_hash,
        "current_stage": None,
        "completed_stages": [],
        "status": "new",
        "safe_to_resume": True,
        "last_completed_split": None,
        "last_processed_timestamp": None,
        "latest_message": "new",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def read_checkpoint() -> dict[str, Any] | None:
    if not RUNTIME_PATH.exists():
        return None
    try:
        return json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        corrupt_path = RUNTIME_PATH.with_suffix(".corrupt.json")
        corrupt_path.write_text(RUNTIME_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        return None


def write_checkpoint(status: dict[str, Any]) -> Path:
    RUNTIME_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {**status, "updated_at": datetime.now(timezone.utc).isoformat()}
    RUNTIME_PATH.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return RUNTIME_PATH


def start_checkpoint(run_id: str, strategy: str, symbol: str, timeframe: str, file: str, data_hash: str | None, resume: bool) -> dict[str, Any]:
    existing = read_checkpoint()
    if resume and existing and existing.get("run_id") == run_id and existing.get("data_hash") == data_hash and existing.get("safe_to_resume", False):
        return write_and_return({**existing, "status": "running", "latest_message": "resumed"})
    return write_and_return(default_checkpoint(run_id, strategy, symbol, timeframe, file, data_hash) | {"status": "running", "latest_message": "started"})


def mark_stage_started(status: dict[str, Any], stage: str) -> dict[str, Any]:
    return write_and_return({**status, "current_stage": stage, "status": "running", "latest_message": f"running {stage}"})


def mark_stage_completed(status: dict[str, Any], stage: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    completed = list(status.get("completed_stages", []))
    if stage not in completed:
        completed.append(stage)
    payload = {**status, "current_stage": None, "completed_stages": completed, "status": "running", "latest_message": f"completed {stage}"}
    if extra:
        payload.update(extra)
    return write_and_return(payload)


def mark_pipeline_stopped(status: dict[str, Any], message: str, safe_to_resume: bool = True) -> dict[str, Any]:
    return write_and_return({**status, "status": "stopped", "safe_to_resume": safe_to_resume, "latest_message": message})


def mark_pipeline_failed(status: dict[str, Any], message: str) -> dict[str, Any]:
    return write_and_return({**status, "status": "failed", "safe_to_resume": False, "latest_message": message})


def mark_pipeline_completed(status: dict[str, Any], report_path: str) -> dict[str, Any]:
    return write_and_return({**status, "status": "completed", "safe_to_resume": False, "latest_message": "completed", "latest_result_path": report_path})


def write_and_return(status: dict[str, Any]) -> dict[str, Any]:
    write_checkpoint(status)
    return status

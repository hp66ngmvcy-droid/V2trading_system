"""Rule-based paper-only research controller."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from tar_system import settings
from tar_system.audit.writer import append_audit_event
from tar_system.cache import result_index as _result_index
from tar_system.controller import job_queue
from tar_system.environment.event_calendar import load_events
from tar_system.environment.risk_state import evaluate_environment
from tar_system.strategies.asset_variants import default_variant


@dataclass(frozen=True)
class DebateResult:
    bull_score: int
    bear_score: int
    recommendation: str
    reasons: list[str]


def bull_case(metrics: dict[str, float]) -> int:
    score = 0
    score += 1 if metrics.get("profit_factor", 0.0) > 1.2 else 0
    score += 1 if metrics.get("sharpe_ratio", 0.0) > 0.5 else 0
    score += 1 if metrics.get("win_rate", 0.0) > 0.5 else 0
    return score


def bear_case(metrics: dict[str, float], cost_sensitive: bool) -> int:
    score = 0
    score += 1 if metrics.get("max_drawdown", 0.0) > settings.DEFAULT_MAX_DRAWDOWN else 0
    score += 1 if cost_sensitive else 0
    score += 1 if metrics.get("max_consecutive_losses", metrics.get("consecutive_losses", 0.0)) >= 5 else 0
    return score


def debate_recommendation(metrics: dict[str, float], cost_sensitive: bool) -> DebateResult:
    bull = bull_case(metrics)
    bear = bear_case(metrics, cost_sensitive)
    reasons: list[str] = [f"bull={bull}", f"bear={bear}"]
    if cost_sensitive:
        return DebateResult(bull, bear, "REVIEW", [*reasons, "cost_sensitive_override"])
    return DebateResult(bull, bear, "KEEP" if bull > bear else "REVIEW", reasons)


def run_controller_once(
    pipeline_runner: Callable[[argparse.Namespace], None] | None = None,
    cost_runner: Callable[[str, str, str, str], Any] | None = None,
    paper_signal_runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    job = job_queue.claim_next_job()
    if job is None:
        return {"status": "idle", "message": "no queued jobs"}
    return run_job(job, pipeline_runner=pipeline_runner, cost_runner=cost_runner, paper_signal_runner=paper_signal_runner)


def run_job(
    job: dict[str, Any],
    pipeline_runner: Callable[[argparse.Namespace], None] | None = None,
    cost_runner: Callable[[str, str, str, str], Any] | None = None,
    paper_signal_runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    from tar_system.cli import run_full_pipeline_cmd
    from tar_system.validation.cost_analysis import run_cost_analysis

    pipeline_runner = pipeline_runner or run_full_pipeline_cmd
    cost_runner = cost_runner or run_cost_analysis
    strategy = str(job["strategy"])
    symbol = str(job["symbol"])
    timeframe = str(job["timeframe"])
    broker = str(job.get("broker") or "current_broker_demo")
    job_id = str(job["job_id"])

    if not settings.PAPER_MODE:
        append_audit_event("research_controller", strategy, symbol, timeframe, "FAILED", "PAPER_MODE_DISABLED", {"job_id": job_id})
        return job_queue.update_job(job_id, status="FAILED", completed_at=_now(), recommendation="REVIEW", result_path=None)

    env = evaluate_environment(symbol, datetime.now(), load_events())
    if env.state == "BLOCK_TRADING":
        append_audit_event("research_controller", strategy, symbol, timeframe, "SKIPPED", "BLOCK_TRADING", {"job_id": job_id})
        return job_queue.update_job(job_id, status="SKIPPED", completed_at=_now(), recommendation="REVIEW", result_path=None)
    if env.state == "HOLD_TRADING":
        append_audit_event("research_controller", strategy, symbol, timeframe, "SKIPPED", "HOLD_TRADING_ANALYSIS_ONLY", {"job_id": job_id})
        return job_queue.update_job(job_id, status="SKIPPED", completed_at=_now(), recommendation="REVIEW", result_path=None)

    if str(job.get("type") or "full_pipeline") == "paper_signal":
        return _run_paper_signal_job(job, paper_signal_runner=paper_signal_runner)

    require_wf = bool(job.get("require_walk_forward", True))
    skip_wf = bool(job.get("skip_walk_forward", False))
    if require_wf and skip_wf:
        append_audit_event("research_controller", strategy, symbol, timeframe, "SKIPPED", "WALK_FORWARD_REQUIRED", {"job_id": job_id})
        return job_queue.update_job(job_id, status="SKIPPED", completed_at=_now(), recommendation="REVIEW", result_path=None)

    append_audit_event("research_controller", strategy, symbol, timeframe, "STARTED", "CONTROLLER_JOB_STARTED", {"job_id": job_id})
    try:
        pipeline_runner(
            argparse.Namespace(
                strategy=strategy,
                symbol=symbol,
                timeframe=timeframe,
                file=job["file"],
                skip_walk_forward=skip_wf,
                skip_forward_test=bool(job.get("skip_forward_test", False)) or str(job.get("research_stage") or "") == "smoke",
                force=True,
                broker=broker,
                resume=False,
                max_walk_forward_splits=int(job.get("max_walk_forward_splits") or 100),
                from_date=job.get("from_date"),
                to_date=job.get("to_date"),
                forward_from_date=job.get("forward_from_date"),
                no_live=bool(job.get("no_live", True)),
                no_mt5_promotion=bool(job.get("no_mt5_promotion", True)),
            )
        )
        cost = cost_runner(strategy, symbol, timeframe, broker)
        cost_dict = cost.to_dict() if hasattr(cost, "to_dict") else dict(cost)
        metrics = _load_metrics(strategy, symbol, timeframe)
        if bool(job.get("require_min_trades", False)):
            min_trades = int(job.get("min_trades") or 30)
            total_trades = int(metrics.get("total_trades", 0))
            if total_trades < min_trades:
                append_audit_event("research_controller", strategy, symbol, timeframe, "SKIPPED", "MIN_TRADES_NOT_MET", {"job_id": job_id, "trades": total_trades, "required": min_trades})
                return job_queue.update_job(job_id, status="SKIPPED", completed_at=_now(), recommendation="REVIEW", result_path=None)
        debate = debate_recommendation(metrics, bool(cost_dict.get("cost_sensitive", False)))
        try:
            from tar_system.scoring.scorer import score_strategy
            scored = score_strategy({k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))})
            _result_index.upsert_result(
                strategy=strategy,
                symbol=symbol,
                timeframe=timeframe,
                stage=str(job.get("research_stage") or "full"),
                score=float(scored.score),
                verdict=scored.verdict,
                total_trades=int(metrics.get("total_trades", 0)),
                profit_factor=float(metrics.get("profit_factor", 0.0)),
                max_drawdown=float(metrics.get("max_drawdown", 0.0)),
                sharpe_ratio=float(metrics.get("sharpe_ratio", 0.0)),
                data_hash=str(job["data_hash"]) if job.get("data_hash") else None,
            )
        except Exception:
            pass
        variant = default_variant(strategy, symbol, timeframe)
        result_path = f"reports/{symbol}_{timeframe}_{strategy}_report.md"
        updated = job_queue.update_job(
            job_id,
            status="COMPLETED",
            completed_at=_now(),
            result_path=result_path,
            recommendation=debate.recommendation,
            cost_sensitive=bool(cost_dict.get("cost_sensitive", False)),
            swap_drag=float(cost_dict.get("swap_drag", 0.0)),
            session_filter_used=bool(variant.parameters.get("session_filter", True)),
        )
        append_audit_event("research_controller", strategy, symbol, timeframe, "COMPLETED", debate.recommendation, {"job_id": job_id, "debate": debate.__dict__})
        _queue_second_strategy_if_needed(updated)
        return updated
    except SystemExit as exc:
        append_audit_event("research_controller", strategy, symbol, timeframe, "FAILED", "CONTROLLER_JOB_FAILED", {"job_id": job_id, "error": str(exc)})
        return job_queue.update_job(job_id, status="FAILED", completed_at=_now(), recommendation="REVIEW", result_path=None)
    except Exception as exc:
        append_audit_event("research_controller", strategy, symbol, timeframe, "FAILED", "CONTROLLER_JOB_FAILED", {"job_id": job_id, "error": str(exc)})
        return job_queue.update_job(job_id, status="FAILED", completed_at=_now(), recommendation="REVIEW", result_path=None)


def run_controller_watch(interval_seconds: int = 60, stop_path: str | Path = "runtime/controller_stop.json") -> None:
    while True:
        if Path(stop_path).exists():
            break
        run_controller_once()
        time.sleep(interval_seconds)


def _load_metrics(strategy: str, symbol: str, timeframe: str) -> dict[str, float]:
    path = Path("data/results") / f"{strategy}_{symbol}_{timeframe}_metrics.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _queue_second_strategy_if_needed(job: dict[str, Any]) -> None:
    strategy = str(job["strategy"])
    symbol = str(job["symbol"])
    timeframe = str(job["timeframe"])
    if strategy == "rsi_reversion_v1":
        return
    if not (Path("data/features") / f"{symbol}_{timeframe}.parquet").exists():
        return
    data_hash = str(job.get("data_hash")) if job.get("data_hash") else None
    existing = [
        row
        for row in job_queue.read_jobs()
        if row.get("strategy") == "rsi_reversion_v1"
        and row.get("symbol") == symbol
        and row.get("timeframe") == timeframe
        and (row.get("data_hash") == data_hash if data_hash else row.get("file") == job.get("file"))
    ]
    if not existing:
        job_queue.add_job(
            "rsi_reversion_v1",
            symbol,
            timeframe,
            str(job["file"]),
            str(job.get("broker") or "current_broker_demo"),
            data_hash=data_hash,
            from_date=str(job.get("from_date")) if job.get("from_date") else None,
            to_date=str(job.get("to_date")) if job.get("to_date") else None,
            forward_from_date=str(job.get("forward_from_date")) if job.get("forward_from_date") else None,
            skip_walk_forward=bool(job.get("skip_walk_forward", False)),
            skip_forward_test=bool(job.get("skip_forward_test", False)) or str(job.get("research_stage") or "") == "smoke",
            max_walk_forward_splits=int(job.get("max_walk_forward_splits") or 100),
            research_stage=str(job.get("research_stage") or "full"),
        )


def _run_paper_signal_job(job: dict[str, Any], paper_signal_runner: Callable[..., Any] | None = None) -> dict[str, Any]:
    from tar_system.controller.paper_signal_runner import run_paper_signal

    runner = paper_signal_runner or run_paper_signal
    strategy = str(job["strategy"])
    symbol = str(job["symbol"])
    timeframe = str(job["timeframe"])
    broker = str(job.get("broker") or "current_broker_demo")
    job_id = str(job["job_id"])
    sizing_model = str(job.get("sizing_model") or "ATR_BASED")

    append_audit_event("research_controller", strategy, symbol, timeframe, "STARTED", "PAPER_SIGNAL_JOB_STARTED", {"job_id": job_id})
    try:
        result = runner(strategy, symbol, timeframe, broker, sizing_model)
        payload = asdict(result) if hasattr(result, "__dataclass_fields__") else dict(result)
        recommendation = "KEEP" if bool(payload.get("alert_ready")) and bool(payload.get("risk_approved")) else "REVIEW"
        updated = job_queue.update_job(
            job_id,
            status="COMPLETED",
            completed_at=_now(),
            recommendation=recommendation,
            result_path="runtime/latest_paper_signal.json",
        )
        append_audit_event("research_controller", strategy, symbol, timeframe, "COMPLETED", "PAPER_SIGNAL_JOB_COMPLETED", {"job_id": job_id, "signal": payload})
        return updated
    except SystemExit as exc:
        append_audit_event("research_controller", strategy, symbol, timeframe, "FAILED", "PAPER_SIGNAL_JOB_FAILED", {"job_id": job_id, "error": str(exc)})
        return job_queue.update_job(job_id, status="FAILED", completed_at=_now(), recommendation="REVIEW", result_path=None)
    except Exception as exc:
        append_audit_event("research_controller", strategy, symbol, timeframe, "FAILED", "PAPER_SIGNAL_JOB_FAILED", {"job_id": job_id, "error": str(exc)})
        return job_queue.update_job(job_id, status="FAILED", completed_at=_now(), recommendation="REVIEW", result_path=None)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

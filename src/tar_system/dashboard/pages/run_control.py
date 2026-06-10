"""Operator-focused dashboard run-control page."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from tar_system import settings
from tar_system.audit.writer import append_audit_event
from tar_system.cache import result_index as _result_index
from tar_system.controller.job_queue import (
    add_job,
    diagnose_failures,
    queue_stats,
    read_jobs,
    reset_stale_running,
)
from tar_system.controller.research_loop import recommend_next_actions
from tar_system.dashboard.components.controls import SYMBOLS, TIMEFRAMES
from tar_system.dashboard.components.layout import page_header, status_pill
from tar_system.dashboard.runtime_control import (
    append_activity,
    approve_next_mt5_test,
    begin_task,
    finish_task,
    heartbeat,
    read_activity,
    read_global_status,
    read_run_history,
    read_schedule,
    read_tested_data_registry,
    request_stop_active_task,
    request_stop_backtest,
    reset_global_status,
    schedule_research_run,
)
from tar_system.controller.research_loop import run_research_loop
from tar_system.data.csv_importer import detect_csv_schema, load_csv
from tar_system.data.store import load_feature_data, load_validated_data
from tar_system.environment.event_calendar import load_events
from tar_system.environment.risk_state import evaluate_environment
from tar_system.features.engineering import build_and_save_features
from tar_system.reporting.reporter import generate_report
from tar_system.scoring.scorer import score_strategy
from tar_system.strategies.registry import REGISTRY, get_strategy


PROJECT_ROOT = Path("/Users/whs1/Dev/V2trading_system")
RUN_LOG_DIR = Path("runtime/dashboard_runs")
STATUS_ORDER = ["IDLE", "RUNNING", "STOPPING", "STOPPED", "COMPLETED", "FAILED"]
_DATA_ROOT = PROJECT_ROOT / "data"


def _safe_data_path(file_path: str) -> Path:
    """Resolve file_path and confirm it stays inside data/. Raises ValueError on traversal."""
    resolved = (PROJECT_ROOT / file_path).resolve()
    if not resolved.is_relative_to(_DATA_ROOT.resolve()):
        raise ValueError(f"File path escapes data directory: {file_path!r}")
    return resolved


def render(st: object) -> None:
    _sync_background_status()
    page_header(st, "Operator Control", "Paper-only TAR research controls with visible state, run lock and audit feedback.")
    status = read_global_status()
    _auto_refresh_while_active(status)
    _render_status_panel(st, status)

    selected = _render_selectors(st)
    try:
        selected["file"] = str(_safe_data_path(selected["file"]))
    except ValueError as exc:
        st.error(f"Invalid data file path: {exc}")
        return
    dataset = _dataset_summary(selected["file"], selected["symbol"], selected["timeframe"])
    from_date, to_date = _render_date_controls(st, dataset)
    selected.update({"from_date": from_date, "to_date": to_date})
    checklist = _pre_run_check(selected, dataset, status)
    _render_primary_controls(st, selected, checklist, status)
    _render_batch_controls(st, selected, checklist, status)

    left, center, right = st.columns([0.95, 1.35, 0.9])
    with left:
        _render_dataset_card(st, dataset)
        _render_strategy_card(st, selected["strategy"], selected["broker"])
        _render_checklist(st, checklist)
        _render_secondary_controls(st, selected, status)
    with center:
        _render_progress(st, status)
        _render_terminal(st, status)
        _render_completion_summary(st, status)
    with right:
        _render_activity_feed(st)
        _render_operator_confidence(st, status)

    st.divider()
    _render_previous_runs(st)
    _render_queue(st, selected)


def _render_selectors(st: object) -> dict[str, Any]:
    st.markdown("### Configuration")
    cols = st.columns(5)
    symbols = [symbol for symbol in SYMBOLS if symbol != "USOIL"] + ["USOUSD"]
    strategy_options = sorted(REGISTRY)
    symbol = cols[0].selectbox("Symbol", symbols, index=_safe_index(symbols, st.session_state.get("tar_run_symbol", symbols[0])), key="tar_run_symbol", help="Asset symbol to test.")
    timeframe = cols[1].selectbox("Timeframe", TIMEFRAMES, index=_safe_index(TIMEFRAMES, st.session_state.get("tar_run_timeframe", TIMEFRAMES[2])), key="tar_run_timeframe", help="Candle timeframe.")
    strategy = cols[2].selectbox("Strategy", strategy_options, index=_safe_index(strategy_options, st.session_state.get("tar_run_strategy", strategy_options[0])), key="tar_run_strategy", help="Paper strategy to test.")
    broker = cols[3].selectbox("Broker", ["current_broker_demo"], index=0, key="tar_run_broker", help="Paper broker cost model.")
    auto_file = f"data/raw/{symbol}_{timeframe}.csv"
    previous_auto_file = f"data/raw/{st.session_state.get('tar_run_last_symbol', symbol)}_{st.session_state.get('tar_run_last_timeframe', timeframe)}.csv"
    if "tar_run_file" not in st.session_state or st.session_state["tar_run_file"] == previous_auto_file:
        st.session_state["tar_run_file"] = auto_file
    st.session_state["tar_run_last_symbol"] = symbol
    st.session_state["tar_run_last_timeframe"] = timeframe
    file = cols[4].text_input("Data file", key="tar_run_file", help="Local CSV or MT5 export file.")
    return {"symbol": symbol, "timeframe": timeframe, "strategy": strategy, "broker": broker, "file": file}


def _auto_refresh_while_active(status: dict[str, Any], seconds: int = 5) -> None:
    if str(status.get("status", "IDLE")).upper() not in {"RUNNING", "STOPPING"}:
        return
    try:
        import streamlit.components.v1 as components

        components.html(
            f"""
            <script>
            setTimeout(function() {{
                window.parent.location.reload();
            }}, {seconds * 1000});
            </script>
            """,
            height=0,
        )
    except Exception:
        return


def _render_status_panel(st: object, status: dict[str, Any]) -> None:
    state = str(status.get("status", "IDLE")).upper()
    elapsed = _elapsed(status.get("started_at"), status.get("finished_at"))
    stale = _heartbeat_stale(status)
    st.markdown("### System Status")
    cols = st.columns(7)
    cols[0].metric("System", state)
    cols[1].metric("Current task", status.get("task_name") or "None")
    cols[2].metric("Run ID", status.get("run_id") or "-")
    cols[3].metric("Symbol", status.get("symbol") or "-")
    cols[4].metric("Start time", _short_time(status.get("started_at")))
    cols[5].metric("Elapsed", elapsed)
    cols[6].metric("Progress", f"{float(status.get('progress_pct') or 0):.0f}%")
    status_pill(st, "State", state)
    st.caption(f"Last heartbeat: {_short_time(status.get('last_heartbeat'))} | Last update: {_short_time(status.get('last_update'))}")
    if stale:
        st.warning("Warning: task may be stalled.")


def _render_date_controls(st: object, dataset: dict[str, Any]) -> tuple[str | None, str | None]:
    start = dataset.get("start_date")
    end = dataset.get("end_date")
    if not start or not end:
        st.info("Date controls will activate when the selected dataset is readable.")
        return None, None
    min_date = pd.Timestamp(start).date()
    max_date = pd.Timestamp(end).date()
    preset = st.radio(
        "Date preset",
        ["Full dataset", "Last 1 month", "Last 3 months", "Last 6 months", "Year to date", "Custom"],
        horizontal=True,
        index=_safe_index(["Full dataset", "Last 1 month", "Last 3 months", "Last 6 months", "Year to date", "Custom"], st.session_state.get("tar_run_date_preset", "Full dataset")),
        key="tar_run_date_preset",
        help="Choose a constrained date range for the next run.",
    )
    default_from, default_to = _preset_dates(preset, min_date, max_date)
    if preset != "Custom":
        st.session_state["tar_run_from_date"] = default_from
        st.session_state["tar_run_to_date"] = default_to
    else:
        st.session_state["tar_run_from_date"] = _clamp_date(st.session_state.get("tar_run_from_date", default_from), min_date, max_date)
        st.session_state["tar_run_to_date"] = _clamp_date(st.session_state.get("tar_run_to_date", default_to), min_date, max_date)
    cols = st.columns(2)
    from_value = cols[0].date_input("From", min_value=min_date, max_value=max_date, disabled=preset != "Custom", key="tar_run_from_date")
    to_value = cols[1].date_input("To", min_value=min_date, max_value=max_date, disabled=preset != "Custom", key="tar_run_to_date")
    return from_value.isoformat(), to_value.isoformat()


def _render_dataset_card(st: object, dataset: dict[str, Any]) -> None:
    st.markdown("#### Dataset")
    st.write(
        {
            "file": dataset.get("file"),
            "symbol": dataset.get("symbol"),
            "timeframe": dataset.get("timeframe"),
            "date_range": f"{dataset.get('start_date') or '-'} -> {dataset.get('end_date') or '-'}",
            "total_bars": dataset.get("total_bars", 0),
            "missing_or_gap_estimate": dataset.get("gap_count", "unknown"),
            "last_validation": dataset.get("validation_status"),
        }
    )


def _render_strategy_card(st: object, strategy_name: str, broker: str) -> None:
    strategy = get_strategy(strategy_name)
    st.markdown("#### Strategy")
    st.write(
        {
            "strategy": strategy_name,
            "version": getattr(strategy, "version", "unknown"),
            "regime_filter": "strategy-defined",
            "risk_model": "TAR paper risk engine",
            "spread_slippage_model": broker,
            "paper_only": settings.PAPER_MODE and not settings.LIVE_TRADING_ALLOWED,
        }
    )


def _render_checklist(st: object, checklist: list[tuple[str, bool, str]]) -> None:
    st.markdown("#### Pre-run Checklist")
    for label, passed, detail in checklist:
        icon = "PASS" if passed else "BLOCK"
        st.caption(f"{icon} {label}: {detail}")


def _render_primary_controls(st: object, selected: dict[str, Any], checklist: list[tuple[str, bool, str]], status: dict[str, Any]) -> None:
    active = str(status.get("status", "IDLE")).upper() in {"RUNNING", "STOPPING"}
    can_reset = str(status.get("status", "IDLE")).upper() in {"STOPPED", "COMPLETED", "FAILED"}
    ready = all(item[1] for item in checklist)

    st.markdown("### Primary Actions")
    if active:
        st.warning(f"Another task is currently running: {status.get('task_name')}. Stop or wait for completion.")

    prep_col, env_col, start_col, stop_col, reset_col, export_col, report_col = st.columns([1, 1, 1.15, 1, 0.9, 1.2, 1])
    if prep_col.button("Build Features" if not active else "Running...", disabled=active or not Path(selected["file"]).exists(), help="Build local feature parquet from validated data for the selected symbol/timeframe.", width="stretch"):
        _run_quick_action(st, "build_features", "Build Features", selected, _build_features_action)

    if env_col.button("Check Environment" if not active else "Running...", disabled=active, help="Evaluate local event/environment risk for the selected symbol.", width="stretch"):
        _run_quick_action(st, "check_environment", "Check Environment", selected, _environment_action)

    if start_col.button("Start Backtest" if not active else "Running...", type="primary", disabled=active or not ready, help="Start a local paper-only backtest/pipeline subprocess with the selected date range.", width="stretch"):
        _start_backtest_subprocess(st, selected)
    if stop_col.button("Stop Backtest", disabled=str(status.get("status", "IDLE")).upper() != "RUNNING", help="Request a safe stop. The running task should exit cleanly before status becomes STOPPED.", width="stretch"):
        request_stop_active_task()
        request_stop_backtest()
        _audit_button("Stop Backtest", selected, "STOPPING", "STOP_REQUESTED", {"run_id": status.get("run_id")})
        st.warning("Stop requested. Waiting for the paper task to exit cleanly.")
    if reset_col.button("Reset Run", disabled=not can_reset, help="Clear the current completed/stopped/failed run state. Does not delete reports or audit logs.", width="stretch"):
        reset_global_status()
        _audit_button("Reset Run", selected, "RESET", "RUN_STATE_RESET", {})
        st.success("Run state reset.")
        st.rerun()

    latest_report = Path("reports") / f"{selected['symbol']}_{selected['timeframe']}_{selected['strategy']}_report.md"
    if export_col.button("Export MT5 Review File", disabled=active, help="Create manual MT5 review files only. This never logs in or places orders.", width="stretch"):
        _audit_button("Export MT5 Review File", selected, "REQUESTED", "MANUAL_REVIEW_ONLY", {})
        st.info("Use CLI export after a KEEP/REVIEW result. No live trading or broker execution is available from the dashboard.")
    if report_col.button("Generate Report", disabled=active or not _metrics_path(selected).exists(), help="Generate a local markdown report from latest paper metrics.", width="stretch"):
        _run_quick_action(st, "generate_report", "Generate Report", selected, _generate_report_action)

    st.caption(f"Latest report: {latest_report if latest_report.exists() else 'not available'}")


def _render_batch_controls(st: object, selected: dict[str, Any], checklist: list[tuple[str, bool, str]], status: dict[str, Any]) -> None:
    active = str(status.get("status", "IDLE")).upper() in {"RUNNING", "STOPPING"}
    ready = all(item[1] for item in checklist)
    st.markdown("### Batch Testing")
    st.caption("Run All Tests queues every recognised CSV/strategy combination for the background worker. It does not place trades and it does not keep Streamlit busy for hours.")
    cols = st.columns([1.15, 1, 1, 1.15])
    force = cols[0].checkbox("Force retest", value=False, key="tar_run_force_retest", help="Queue jobs even if the same data/date window has already been tested.")
    daily = cols[1].checkbox("Schedule daily", value=False, key="tar_run_schedule_daily", help="Create a recurring daily batch queue job.")
    daily_time = cols[2].time_input("Daily time", value=time(2, 5), key="tar_run_daily_time", help="Local time for the daily batch queue job.")

    st.markdown("#### Batch Safety Controls")
    guard_cols = st.columns([1, 1, 1, 1, 1])
    max_jobs = guard_cols[0].number_input("Max queued jobs", min_value=1, max_value=50, value=3, step=1, key="tar_batch_max_jobs", help="Cap total active+queued jobs. Prevents the 500+ job backlog problem.")
    require_wf = guard_cols[1].checkbox("Require walk-forward", value=True, key="tar_batch_require_wf", help="Skip any job that has walk-forward disabled.")
    require_mt = guard_cols[2].checkbox("Require min trades", value=True, key="tar_batch_require_min_trades", help="Skip results with too few trades to be statistically valid.")
    min_trades = guard_cols[3].number_input("Min trades", min_value=1, max_value=500, value=200, step=1, key="tar_batch_min_trades", help="Minimum trade count required when 'Require min trades' is on.", disabled=not require_mt)
    no_promote = guard_cols[4].checkbox("Block MT5 promotion", value=True, key="tar_batch_no_promote", help="Prevent any job from being promoted to MT5 live. Always on for paper batches.")

    batch_selected = {
        **selected,
        "force_all_tests": force,
        "daily_time": daily_time.isoformat(timespec="minutes"),
        "max_jobs": int(max_jobs),
        "require_walk_forward": require_wf,
        "require_min_trades": require_mt,
        "min_trades": int(min_trades),
        "no_mt5_promotion": no_promote,
        "no_live": True,
    }
    if cols[3].button("Run All Tests Now", disabled=active or not ready, type="secondary", help="Queue all paper research tests for the selected A-B date range.", width="stretch"):
        _run_quick_action(st, "queue_all_tests", "Run All Tests", batch_selected, _queue_all_tests_action)
    if daily:
        run_at = _next_daily_run_at(daily_time)
        if st.button("Save Daily Run All Tests Schedule", disabled=active or not ready, help="Schedule the batch queue to run every day at the selected local time."):
            _schedule_daily_all_tests(batch_selected, run_at)
            _audit_button("Schedule Daily Run All Tests", batch_selected, "SCHEDULED", "PAPER_ONLY", {"run_at": run_at.isoformat()})
            st.success(f"Daily Run All Tests scheduled for {run_at.strftime('%Y-%m-%d %H:%M')}.")
    st.info("To let the queue work through every data file, leave a worker running: `PYTHONPATH=src venv/bin/python -m tar_system.cli run-worker --limit 999`")


def _render_secondary_controls(st: object, selected: dict[str, Any], status: dict[str, Any]) -> None:
    active = str(status.get("status", "IDLE")).upper() in {"RUNNING", "STOPPING"}
    st.markdown("#### Queue / Maintenance")
    if st.button("Queue Paper Research Job", disabled=active, help="Queue this selection for the background paper research worker."):
        job = add_job(
            selected["strategy"],
            selected["symbol"],
            selected["timeframe"],
            selected["file"],
            selected["broker"],
            from_date=selected.get("from_date"),
            to_date=selected.get("to_date"),
            skip_walk_forward=False,
            skip_forward_test=True,
            research_stage="dashboard",
            priority=5,
        )
        append_activity("task_started", "Paper research job queued", {"job_id": job["job_id"], **selected})
        _audit_button("Queue Paper Research Job", selected, "QUEUED", "PAPER_ONLY", {"job_id": job["job_id"]})
        st.success(f"Queued paper job {job['job_id']}.")
    st.caption("Queue history is append-only from the dashboard. Use filters for review instead of deleting completed rows.")


def _render_progress(st: object, status: dict[str, Any]) -> None:
    st.markdown("### Live Run Metrics")
    progress = float(status.get("progress_pct") or 0.0)
    st.progress(min(100, max(0, int(progress))) / 100)
    cols = st.columns(4)
    cols[0].metric("Bars processed", status.get("bars_processed", 0))
    cols[1].metric("Total bars", status.get("total_bars", 0))
    cols[2].metric("Trades closed", status.get("trades_closed", 0))
    cols[3].metric("Equity", status.get("current_equity") or "-")
    st.write(
        {
            "current_date": status.get("current_date"),
            "current_drawdown": status.get("current_drawdown"),
            "current_regime": status.get("current_regime"),
            "last_signal": status.get("last_signal"),
            "last_risk_decision": status.get("last_risk_decision"),
        }
    )


def _render_terminal(st: object, status: dict[str, Any]) -> None:
    st.markdown("### Terminal / Code Output")
    log_lines = _terminal_lines(status)
    with st.expander("Current task log", expanded=str(status.get("status")) in {"RUNNING", "STOPPING"}):
        st.code("\n".join(log_lines[-120:]) if log_lines else "No terminal output yet.", language="text")
    if status.get("command"):
        st.code(_mask_sensitive(str(status["command"])), language="bash")


def _render_completion_summary(st: object, status: dict[str, Any]) -> None:
    if str(status.get("status", "IDLE")).upper() not in {"COMPLETED", "FAILED", "STOPPED"}:
        return
    metrics_path = _metrics_path(status)
    metrics = _load_json(metrics_path)
    score_path = Path("logs/review_log.jsonl")
    score = _latest_review_score(status, score_path)
    st.markdown("### Completion Summary")
    st.write(
        {
            "status": status.get("status"),
            "runtime": _elapsed(status.get("started_at"), status.get("finished_at")),
            "strategy": status.get("strategy"),
            "symbol": status.get("symbol"),
            "date_range": f"{status.get('from_date') or '-'} -> {status.get('to_date') or '-'}",
            "trades": metrics.get("total_trades"),
            "win_rate": metrics.get("win_rate"),
            "final_equity": status.get("current_equity"),
            "max_drawdown": metrics.get("max_drawdown"),
            "score": score.get("score"),
            "verdict": score.get("verdict"),
        }
    )


def _render_activity_feed(st: object) -> None:
    st.markdown("### Activity Feed")
    rows = list(reversed(read_activity(25)))
    if not rows:
        st.caption("No dashboard activity yet.")
        return
    for row in rows[:20]:
        st.caption(f"{_short_time(row.get('timestamp'))} | {row.get('event_type')} | {row.get('message')}")


def _render_operator_confidence(st: object, status: dict[str, Any]) -> None:
    st.markdown("### Operator Confidence")
    history = read_run_history(20)
    last_success = next((run for run in reversed(history) if run.get("status") == "COMPLETED"), None)
    st.write(
        {
            "last_action_taken": status.get("latest_message"),
            "last_successful_run": last_success.get("run_id") if last_success else None,
            "current_task_log": status.get("log_path"),
        }
    )
    if status.get("latest_result_path"):
        st.write({"open_latest_report": status.get("latest_result_path")})
    if st.button("Clear Terminal", help="Clear terminal lines from the current dashboard run state."):
        current = read_global_status()
        from tar_system.dashboard.runtime_control import write_global_status

        write_global_status({**current, "terminal": []})
        append_activity("progress_update", "Terminal cleared", current)
        st.success("Terminal cleared.")
    if status.get("command"):
        st.download_button("Export Run Log", data="\n".join(_terminal_lines(status)), file_name=f"{status.get('run_id') or 'run'}_log.txt", help="Download the current dashboard run log.")
        st.code(_mask_sensitive(str(status["command"])), language="bash")


def _render_previous_runs(st: object) -> None:
    st.markdown("### Previous Runs")
    rows = [
        {
            "run_id": run.get("run_id"),
            "task_type": run.get("task_type"),
            "symbol": run.get("symbol"),
            "strategy": run.get("strategy"),
            "date_range": f"{run.get('from_date') or '-'} -> {run.get('to_date') or '-'}",
            "status": run.get("status"),
            "score": _latest_review_score(run, Path("logs/review_log.jsonl")).get("score"),
            "created_at": run.get("created_at"),
            "report": run.get("latest_result_path"),
        }
        for run in reversed(read_run_history(25))
    ]
    if rows:
        st.dataframe(rows, width="stretch")
    else:
        st.caption("No previous dashboard runs yet.")


def _render_queue(st: object, selected: dict[str, Any]) -> None:
    st.markdown("### Research Queue")
    st.write({"queue_stats": queue_stats(), "next_actions": recommend_next_actions()})

    with st.expander("Failure Diagnosis", expanded=False):
        try:
            diag = diagnose_failures()
            dcols = st.columns(3)
            dcols[0].metric("Failed jobs", diag["total_failed"])
            dcols[1].metric("Skipped jobs", diag["total_skipped"])
            dcols[2].metric("Stale RUNNING", len(diag["stale_running"]))
            if diag["by_stage"]:
                st.markdown("**By stage**")
                st.dataframe([{"stage": s, "count": c} for s, c in diag["by_stage"]], width="stretch")
            if diag["by_target"]:
                st.markdown("**Top failing targets**")
                st.dataframe([{"target": t, "count": c} for t, c in diag["by_target"]], width="stretch")
            if diag["stale_running"]:
                st.warning(f"{len(diag['stale_running'])} job(s) stuck in RUNNING state.")
                if st.button("Reset stale RUNNING jobs to FAILED"):
                    n = reset_stale_running()
                    st.success(f"Reset {n} stale job(s).")
                    st.rerun()
        except Exception as exc:
            st.caption(f"Diagnosis unavailable: {exc}")

    with st.expander("Result Index (top scored)", expanded=False):
        try:
            stats = _result_index.result_index_stats()
            st.write({"indexed": stats["total"], "by_verdict": stats["by_verdict"]})
            if stats["top_5"]:
                st.dataframe(stats["top_5"], width="stretch")
            top = _result_index.get_ranked_results(min_trades=30, limit=20)
            if top:
                st.markdown("**Ranked (≥30 trades)**")
                st.dataframe(
                    [
                        {
                            "strategy": r["strategy"],
                            "symbol": r["symbol"],
                            "timeframe": r["timeframe"],
                            "score": round(float(r["score"]), 1),
                            "verdict": r["verdict"],
                            "trades": r["total_trades"],
                            "PF": round(float(r["profit_factor"]), 2),
                            "DD": round(float(r["max_drawdown"]) * 100, 1),
                        }
                        for r in top
                    ],
                    width="stretch",
                )
        except Exception as exc:
            st.caption(f"Result index unavailable: {exc}")

    scheduled = read_schedule().get("jobs", [])
    if scheduled:
        st.markdown("#### Scheduled Jobs")
        st.dataframe(
            [
                {
                    "status": job.get("status"),
                    "job_type": job.get("job_type", "single_pipeline"),
                    "run_at": job.get("run_at"),
                    "repeat_daily": job.get("repeat_daily", False),
                    "from_date": job.get("from_date"),
                    "to_date": job.get("to_date"),
                    "queued_jobs": job.get("queued_jobs"),
                }
                for job in scheduled[-20:]
            ],
            width="stretch",
        )
    rows = read_jobs()
    if rows:
        st.dataframe(
            [
                {
                    "status": row.get("status"),
                    "stage": row.get("research_stage"),
                    "strategy": row.get("strategy"),
                    "symbol": row.get("symbol"),
                    "timeframe": row.get("timeframe"),
                    "priority": row.get("priority"),
                    "recommendation": row.get("recommendation"),
                    "no_live": row.get("no_live"),
                    "no_mt5_promotion": row.get("no_mt5_promotion"),
                    "require_wf": row.get("require_walk_forward"),
                    "require_min_trades": row.get("require_min_trades"),
                    "min_trades": row.get("min_trades"),
                }
                for row in rows[-80:]
            ],
            width="stretch",
        )
    st.caption(f"Duplicate guard registry entries: {len(read_tested_data_registry())}")


def _run_quick_action(st: object, task_type: str, task_name: str, selected: dict[str, Any], action: Any) -> None:
    try:
        task = begin_task(task_type, task_name, selected)
        _audit_button(task_name, selected, "STARTED", "PAPER_ONLY", {"run_id": task["run_id"]})
        heartbeat(f"{task_name} running", 25)
        result = action(selected)
        finish_task("COMPLETED", f"{task_name} completed successfully", result)
        _audit_button(task_name, selected, "COMPLETED", "TASK_COMPLETED", result)
        st.success(f"{task_name} completed successfully.")
    except Exception as exc:
        finish_task("FAILED", f"{task_name} failed: {exc}", {"error": str(exc)})
        _audit_button(task_name, selected, "FAILED", "TASK_FAILED", {"error": str(exc)})
        st.error(f"{task_name} failed: {exc}")


def _start_backtest_subprocess(st: object, selected: dict[str, Any]) -> None:
    try:
        task = begin_task("backtest", "Start Backtest", selected)
    except RuntimeError as exc:
        st.warning(str(exc))
        return
    data_file = selected["file"]
    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = RUN_LOG_DIR / f"{task['run_id']}.log"
    command = [
        str(PROJECT_ROOT / "venv/bin/python"),
        "-m",
        "tar_system.cli",
        "run-full-pipeline",
        "--strategy",
        selected["strategy"],
        "--symbol",
        selected["symbol"],
        "--timeframe",
        selected["timeframe"],
        "--file",
        data_file,
        "--broker",
        selected["broker"],
        "--force",
        "--skip-forward-test",
    ]
    if selected.get("from_date"):
        command.extend(["--from-date", str(selected["from_date"])])
    if selected.get("to_date"):
        command.extend(["--to-date", str(selected["to_date"])])
    env = {**os.environ, "PYTHONPATH": "src"}
    with log_path.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(command, cwd=str(PROJECT_ROOT), stdout=handle, stderr=subprocess.STDOUT, env=env)
    heartbeat("Backtest subprocess started", 5, command=" ".join(command), log_path=str(log_path), pid=process.pid)
    _audit_button("Start Backtest", selected, "STARTED", "PAPER_ONLY", {"run_id": task["run_id"], "pid": process.pid, "log_path": str(log_path)})
    st.success(f"Backtest started at {_short_time(task['started_at'])}. Run ID: {task['run_id']}")


def _build_features_action(selected: dict[str, Any]) -> dict[str, Any]:
    data = load_validated_data(selected["symbol"], selected["timeframe"])
    path = build_and_save_features(data, selected["symbol"], selected["timeframe"])
    return {"latest_result_path": str(path), "progress_pct": 100}


def _environment_action(selected: dict[str, Any]) -> dict[str, Any]:
    decision = evaluate_environment(selected["symbol"], datetime.now(timezone.utc), load_events())
    return {"environment_state": decision.state, "progress_pct": 100, "latest_message": f"Environment: {decision.state}"}


def _queue_all_tests_action(selected: dict[str, Any]) -> dict[str, Any]:
    result = run_research_loop(
        raw_dir="data/raw",
        broker=selected.get("broker", "current_broker_demo"),
        force=bool(selected.get("force_all_tests", False)),
        process_limit=0,
        run_worker_now=False,
        research_stage="dashboard_batch",
        skip_walk_forward=False,
        skip_forward_test=True,
        max_walk_forward_splits=10,
        from_date=selected.get("from_date"),
        to_date=selected.get("to_date"),
        max_jobs=int(selected.get("max_jobs") or 3),
        no_live=bool(selected.get("no_live", True)),
        no_mt5_promotion=bool(selected.get("no_mt5_promotion", True)),
        require_walk_forward=bool(selected.get("require_walk_forward", True)),
        require_min_trades=bool(selected.get("require_min_trades", False)),
        min_trades=int(selected.get("min_trades") or 30),
    )
    return {
        "queued_jobs": result.queued_jobs,
        "queue_stats": result.queue_stats,
        "latest_result_path": result.summary_path,
        "progress_pct": 100,
        "latest_message": f"Queued {result.queued_jobs} paper tests",
    }


def _generate_report_action(selected: dict[str, Any]) -> dict[str, Any]:
    metrics = _load_json(_metrics_path(selected))
    scored = score_strategy(metrics)
    path = generate_report(
        selected["strategy"],
        selected["symbol"],
        selected["timeframe"],
        metrics,
        scored.score,
        scored.verdict,
        "REVIEW_ONLY",
        scored.reason_codes,
        "REVIEW",
        "md",
    )
    return {"latest_result_path": str(path), "progress_pct": 100}


def _dataset_summary(file: str, symbol: str, timeframe: str) -> dict[str, Any]:
    path = Path(file)
    summary = {
        "file": file,
        "symbol": symbol,
        "timeframe": timeframe,
        "exists": path.exists(),
        "start_date": None,
        "end_date": None,
        "total_bars": 0,
        "gap_count": "unknown",
        "validation_status": "not checked",
    }
    if not path.exists():
        return summary
    try:
        df = load_csv(path, symbol, timeframe)
        timestamps = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
        summary.update(
            {
                "start_date": timestamps.min().date().isoformat() if not timestamps.empty else None,
                "end_date": timestamps.max().date().isoformat() if not timestamps.empty else None,
                "total_bars": int(len(df)),
                "gap_count": _estimate_gap_count(timestamps, timeframe),
                "validation_status": "readable",
                "schema": detect_csv_schema(path),
            }
        )
    except Exception as exc:
        summary["validation_status"] = f"failed: {exc}"
    return summary


def _pre_run_check(selected: dict[str, Any], dataset: dict[str, Any], status: dict[str, Any]) -> list[tuple[str, bool, str]]:
    active = str(status.get("status")) in {"RUNNING", "STOPPING"}
    from_date = selected.get("from_date")
    to_date = selected.get("to_date")
    date_ok = bool(from_date and to_date and from_date <= to_date)
    return [
        ("data file exists", bool(dataset.get("exists")), selected["file"]),
        ("date range is valid", date_ok, f"{from_date} -> {to_date}"),
        ("symbol is detected", bool(selected.get("symbol")), selected.get("symbol", "")),
        ("strategy is selected", selected.get("strategy") in REGISTRY, selected.get("strategy", "")),
        ("paper mode is enabled", settings.PAPER_MODE and not settings.LIVE_TRADING_ALLOWED, "paper-only"),
        ("no task is already running", not active, str(status.get("task_name")) if active else "clear"),
        ("output folders exist", _ensure_output_dirs(), "data/results, reports, logs/audit"),
        ("audit logging is available", True, "logs/audit/audit.jsonl"),
    ]


def _ensure_output_dirs() -> bool:
    for path in [Path("data/results"), Path("reports"), Path("logs/audit"), RUN_LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    return True


def _preset_dates(preset: str, min_date: date, max_date: date) -> tuple[date, date]:
    if preset == "Full dataset":
        return min_date, max_date
    if preset == "Year to date":
        return max(min_date, date(max_date.year, 1, 1)), max_date
    months = {"Last 1 month": 1, "Last 3 months": 3, "Last 6 months": 6}.get(preset)
    if months:
        return max(min_date, (pd.Timestamp(max_date) - pd.DateOffset(months=months)).date()), max_date
    return min_date, max_date


def _safe_index(options: list[Any], value: Any) -> int:
    try:
        return options.index(value)
    except ValueError:
        return 0


def _clamp_date(value: Any, min_date: date, max_date: date) -> date:
    parsed = pd.Timestamp(value).date()
    return min(max(parsed, min_date), max_date)


def _next_daily_run_at(run_time: time, now: datetime | None = None) -> datetime:
    current = now or datetime.now()
    candidate = datetime.combine(current.date(), run_time)
    if candidate <= current:
        candidate += timedelta(days=1)
    return candidate


def _schedule_daily_all_tests(selected: dict[str, Any], run_at: datetime) -> Path:
    return schedule_research_run(
        {
            "job_type": "all_tests",
            "raw_dir": "data/raw",
            "broker": selected.get("broker", "current_broker_demo"),
            "run_at": run_at.isoformat(),
            "repeat_daily": True,
            "force": bool(selected.get("force_all_tests", False)),
            "from_date": selected.get("from_date"),
            "to_date": selected.get("to_date"),
            "skip_walk_forward": False,
            "skip_forward_test": True,
            "max_walk_forward_splits": 10,
            "research_stage": "dashboard_daily",
        }
    )


def _sync_background_status() -> None:
    status = read_global_status()
    if str(status.get("status")) not in {"RUNNING", "STOPPING"}:
        return
    log_path = Path(str(status.get("log_path") or ""))
    lines = log_path.read_text(encoding="utf-8").splitlines() if log_path.exists() else []
    if lines:
        progress = _estimate_progress(lines)
        heartbeat(lines[-1][-240:], progress, terminal=[_mask_sensitive(line) for line in lines[-160:]])
        latest = "\n".join(lines[-40:])
        if "Pipeline complete" in latest:
            finish_task("COMPLETED", "Backtest completed successfully", {"progress_pct": 100, "terminal": lines[-160:], "latest_result_path": _report_path(status)})
            return
        if "Pipeline failed" in latest or "Traceback" in latest:
            finish_task("FAILED", "Pipeline failed. Check terminal output.", {"terminal": lines[-160:]})
            return
    pid = status.get("pid")
    if pid and not _pid_alive(int(pid)):
        latest = "\n".join(lines[-40:])
        if "Pipeline complete" in latest:
            finish_task("COMPLETED", "Backtest completed successfully", {"progress_pct": 100, "terminal": lines[-160:], "latest_result_path": _report_path(status)})
        elif str(status.get("status", "IDLE")).upper() == "STOPPING":
            finish_task("STOPPED", "Backtest stopped safely", {"terminal": lines[-160:]})
        else:
            finish_task("FAILED", "Pipeline failed. Check terminal output.", {"terminal": lines[-160:]})


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _estimate_progress(lines: list[str]) -> float:
    for line in reversed(lines):
        if line.startswith("[") and "/" in line:
            try:
                current = int(line.split("[", 1)[1].split("/", 1)[0])
                total = int(line.split("/", 1)[1].split("]", 1)[0])
                return min(99.0, current / total * 100)
            except Exception:
                return 0.0
    return 0.0


def _terminal_lines(status: dict[str, Any]) -> list[str]:
    log_path = Path(str(status.get("log_path") or ""))
    if log_path.exists():
        return [_mask_sensitive(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    return list(status.get("terminal") or [])


def _metrics_path(selected: dict[str, Any]) -> Path:
    return Path("data/results") / f"{selected.get('strategy')}_{selected.get('symbol')}_{selected.get('timeframe')}_metrics.json"


def _report_path(selected: dict[str, Any]) -> str:
    return str(Path("reports") / f"{selected.get('symbol')}_{selected.get('timeframe')}_{selected.get('strategy')}_report.md")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_review_score(selected: dict[str, Any], path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for row in reversed(rows):
        if row.get("strategy") == selected.get("strategy") and row.get("symbol") == selected.get("symbol") and row.get("timeframe") == selected.get("timeframe"):
            return row
    return {}


def _estimate_gap_count(timestamps: pd.Series, timeframe: str) -> int | str:
    if len(timestamps) < 3:
        return "unknown"
    freq = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h", "H4": "4h", "D1": "1D"}.get(timeframe)
    if not freq:
        return "unknown"
    expected = pd.date_range(timestamps.min(), timestamps.max(), freq=freq)
    return max(0, len(expected) - len(timestamps.drop_duplicates()))


def _audit_button(action_name: str, selected: dict[str, Any], status: str, reason_code: str, result: dict[str, Any]) -> None:
    append_audit_event(
        "dashboard_button",
        str(selected.get("strategy") or ""),
        str(selected.get("symbol") or ""),
        str(selected.get("timeframe") or ""),
        status,
        reason_code,
        {"action_name": action_name, "timestamp": datetime.now(timezone.utc).isoformat(), "result": result},
    )


def _short_time(value: Any) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(str(value)).strftime("%H:%M:%S")
    except ValueError:
        return str(value)


def _elapsed(start: Any, finish: Any = None) -> str:
    if not start:
        return "-"
    try:
        start_dt = datetime.fromisoformat(str(start))
        end_dt = datetime.fromisoformat(str(finish)) if finish else datetime.now(start_dt.tzinfo or timezone.utc)
        seconds = max(0, int((end_dt - start_dt).total_seconds()))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"
    except ValueError:
        return "-"


def _heartbeat_stale(status: dict[str, Any]) -> bool:
    if str(status.get("status")) not in {"RUNNING", "STOPPING"} or not status.get("last_heartbeat"):
        return False
    try:
        heartbeat_time = datetime.fromisoformat(str(status["last_heartbeat"]))
        return (datetime.now(heartbeat_time.tzinfo or timezone.utc) - heartbeat_time).total_seconds() > 45
    except ValueError:
        return False


def _mask_sensitive(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["api_key", "password", "secret", "token="]):
        return "[masked sensitive output]"
    return text.replace(str(PROJECT_ROOT), "<project>")


if __name__ == "__main__":
    import streamlit as st

    from tar_system.dashboard.components.layout import apply_theme

    st.set_page_config(page_title="TAR V2 Operator Control", layout="wide")
    apply_theme(st)
    render(st)

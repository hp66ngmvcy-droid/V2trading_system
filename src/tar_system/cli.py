"""Command line interface for TAR V2."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path


def import_csv(args: argparse.Namespace) -> None:
    from tar_system.audit.writer import append_audit_event
    from tar_system import reason_codes as rc
    from tar_system.data.csv_importer import hash_csv_file, load_csv, save_raw_copy
    from tar_system.data.store import save_validated_data
    from tar_system.data.tick_converter import convert_ticks_file, detect_ohlcv_format, detect_tick_format
    from tar_system.data.validator import validate_ohlcv
    from tar_system.environment.event_calendar import load_events
    from tar_system.environment.risk_state import evaluate_environment

    original_path = Path(args.file)
    import_path = original_path
    data_hash = hash_csv_file(import_path)
    if detect_tick_format(import_path):
        append_audit_event("csv_import_schema", "data", args.symbol, args.timeframe, "DETECTED", rc.DATA_TICK_FORMAT_DETECTED, {"file": str(import_path)})
        try:
            conversion = convert_ticks_file(import_path, args.symbol, args.timeframe)
        except Exception as exc:
            append_audit_event(
                "csv_import_schema",
                "data",
                args.symbol,
                args.timeframe,
                "FAILED",
                rc.DATA_TICK_CONVERSION_FAILED,
                {"file": str(import_path), "error": str(exc)},
            )
            raise SystemExit(f"Tick conversion failed: {exc}") from exc
        append_audit_event(
            "csv_import_schema",
            "data",
            args.symbol,
            args.timeframe,
            "CONVERTED",
            rc.DATA_TICK_CONVERTED_TO_OHLCV,
            asdict(conversion),
        )
        import_path = conversion.output_path
    elif detect_ohlcv_format(import_path):
        append_audit_event("csv_import_schema", "data", args.symbol, args.timeframe, "DETECTED", rc.DATA_OHLCV_FORMAT_DETECTED, {"file": str(import_path)})
    df = load_csv(import_path, args.symbol, args.timeframe)
    canonical_raw = Path("data/raw") / f"{args.symbol}_{args.timeframe}.csv"
    if original_path.resolve() != canonical_raw.resolve():
        save_raw_copy(df, args.symbol, args.timeframe, source_path=import_path)
    result = validate_ohlcv(df, data_hash)
    if not result.passed:
        append_audit_event("csv_import_validation", "data", args.symbol, args.timeframe, "FAILED", ",".join(result.reason_codes), {"errors": result.errors})
        raise SystemExit(f"Validation failed: {result.errors}")
    latest_date = df["timestamp"].max().to_pydatetime()
    env = evaluate_environment(args.symbol, latest_date, load_events())
    append_audit_event("csv_import_environment", "data", args.symbol, args.timeframe, env.state, ",".join(env.reason_codes), {"latest_bar": latest_date})
    path = save_validated_data(df, args.symbol, args.timeframe, data_hash)
    print(f"Imported and validated {len(df)} rows to {path}; environment={env.state}")


def convert_ticks_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system import reason_codes as rc
    from tar_system.audit.writer import append_audit_event
    from tar_system.data.tick_converter import convert_ticks_file, detect_tick_format

    if not detect_tick_format(args.file):
        append_audit_event("tick_conversion", "data", args.symbol, args.timeframe, "SKIPPED", rc.DATA_OHLCV_FORMAT_DETECTED, {"file": args.file})
        raise SystemExit("Input does not look like MT5 tick data")
    try:
        result = convert_ticks_file(args.file, args.symbol, args.timeframe)
    except Exception as exc:
        append_audit_event("tick_conversion", "data", args.symbol, args.timeframe, "FAILED", rc.DATA_TICK_CONVERSION_FAILED, {"file": args.file, "error": str(exc)})
        raise SystemExit(f"Tick conversion failed: {exc}") from exc
    append_audit_event("tick_conversion", "data", args.symbol, args.timeframe, "CONVERTED", rc.DATA_TICK_CONVERTED_TO_OHLCV, asdict(result))
    print(json.dumps(asdict(result), indent=2, default=str))


def validate_data(args: argparse.Namespace) -> None:
    from tar_system.data.store import load_validated_data
    from tar_system.data.validator import validate_ohlcv

    df = load_validated_data(args.symbol, args.timeframe)
    data_hash = str(df["data_hash"].iloc[0]) if "data_hash" in df.columns and len(df) else None
    result = validate_ohlcv(df, data_hash)
    print(json.dumps(result.__dict__, indent=2, default=str))
    if not result.passed:
        raise SystemExit(1)


def build_features_cmd(args: argparse.Namespace) -> None:
    from tar_system.data.store import load_validated_data
    from tar_system.features.engineering import build_and_save_features

    df = load_validated_data(args.symbol, args.timeframe)
    features = build_and_save_features(df, args.symbol, args.timeframe)
    print(f"Built {len(features.columns)} columns for {len(features)} rows")


def run_backtest_cmd(args: argparse.Namespace) -> None:
    from tar_system.backtest.engine import run_backtest
    from tar_system.cache.result_cache import load_cached_result, make_cache_key, save_cached_result
    from tar_system.data.store import filter_by_date_range, load_feature_data
    from tar_system.reporting.review_log import append_review_result
    from tar_system.strategies.resolver import resolve_strategy

    features = filter_by_date_range(load_feature_data(args.symbol, args.timeframe), args.from_date, args.to_date)
    if features.empty:
        raise SystemExit("No feature rows found inside the requested backtest date range")
    resolved = resolve_strategy(args.strategy, args.symbol, args.timeframe, getattr(args, "broker", "current_broker_demo"), audit=True)
    strategy = resolved.strategy
    data_hash = str(features["data_hash"].iloc[0]) if "data_hash" in features.columns and len(features) else None
    date_range = (str(features["timestamp"].min()), str(features["timestamp"].max())) if len(features) else (None, None)
    cache_key = make_cache_key(args.strategy, {}, args.symbol, args.timeframe, data_hash, date_range, "backtest")
    cached = load_cached_result(cache_key, force=args.force)
    if cached:
        print(json.dumps({"cached": True, **cached}, indent=2))
        return
    result = run_backtest(features, strategy)
    if result.stopped:
        raise SystemExit("Backtest stopped before completion; partial result was not cached or reviewed")
    output = Path("data/results")
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{args.strategy}_{args.symbol}_{args.timeframe}_metrics.json"
    path.write_text(json.dumps(result.metrics, indent=2), encoding="utf-8")
    payload = {"trades": result.trades, "final_equity": result.final_equity, "metrics": result.metrics}
    save_cached_result(cache_key, payload)
    append_review_result(args.strategy, strategy.version, args.symbol, args.timeframe, result.metrics, 0.0, "UNSCORED", "BACKTEST", "SCORE_STRATEGY")
    print(json.dumps(payload, indent=2))


def score_strategy_cmd(args: argparse.Namespace) -> None:
    from tar_system.memory.strategy_memory import record_strategy_result
    from tar_system.reporting.review_log import append_review_result, write_review_summary
    from tar_system.scoring.gates import run_gates
    from tar_system.scoring.multi_agent_scorer import score_multi_agent
    from tar_system.scoring.scorer import score_strategy
    from tar_system.strategies.resolver import resolve_strategy

    path = Path("data/results") / f"{args.strategy}_{args.symbol}_{args.timeframe}_metrics.json"
    walk_forward_path = Path("data/results") / f"{args.strategy}_{args.symbol}_{args.timeframe}_walk_forward.json"
    metrics = json.loads(path.read_text(encoding="utf-8"))
    walk_forward_metrics = json.loads(walk_forward_path.read_text(encoding="utf-8")) if walk_forward_path.exists() else None
    score = score_strategy(metrics, walk_forward_metrics, args.timeframe, require_walk_forward=True)
    gate_metrics = _metrics_with_walk_forward(metrics, walk_forward_metrics)
    gate = run_gates(gate_metrics, args.timeframe, require_oos=True)
    ma_result = score_multi_agent(gate_metrics)
    ma_codes = ["MULTI_AGENT_KILL"] if ma_result.verdict == "KILL" else []
    reason_codes = _merge_reason_codes(score.reason_codes, gate.reason_codes, ma_codes)
    final_verdict = "KILL" if ma_result.verdict == "KILL" else gate.verdict
    metrics = {**gate_metrics, "gate_failed": gate.failed_gate or "", "gate_reason": gate.reason}
    resolved = resolve_strategy(args.strategy, args.symbol, args.timeframe, getattr(args, "broker", "current_broker_demo"), audit=True)
    strategy = resolved.strategy
    record_strategy_result(
        args.strategy,
        strategy.version,
        args.symbol,
        args.timeframe,
        {},
        metrics,
        score.score,
        final_verdict,
        reason_codes,
        walk_forward_metrics,
    )
    append_review_result(
        args.strategy,
        strategy.version,
        args.symbol,
        args.timeframe,
        metrics,
        score.score,
        final_verdict,
        ",".join(reason_codes),
        "EXPORT_OBSIDIAN" if final_verdict in {"KEEP", "REVIEW"} else "ARCHIVE",
    )
    write_review_summary()
    print(json.dumps({
        "score": score.score,
        "verdict": final_verdict,
        "reason_codes": reason_codes,
        "gate": gate.__dict__,
        "multi_agent": {
            "verdict": ma_result.verdict,
            "confidence": ma_result.confidence,
            "dissent": ma_result.dissent,
            "agents": [{"agent": v.agent, "verdict": v.verdict, "confidence": v.confidence} for v in ma_result.agent_verdicts],
        },
    }, indent=2))


def export_mt5_cmd(args: argparse.Namespace) -> None:
    from tar_system.audit.writer import append_audit_event
    from tar_system.data.store import load_feature_data
    from tar_system.environment.event_calendar import load_events
    from tar_system.environment.risk_state import evaluate_environment
    from tar_system.exports.mt5_exporter import export_latest_signal
    from tar_system.regime.detector import detect_regime
    from tar_system.strategies.resolver import resolve_strategy

    features = load_feature_data(args.symbol, args.timeframe)
    latest = features.sort_values("timestamp").iloc[-1]
    resolved = resolve_strategy(args.strategy, args.symbol, args.timeframe, args.broker, audit=True)
    strategy = resolved.strategy
    regime = detect_regime(latest).value
    signal = strategy.generate_signal(latest, regime)
    env = evaluate_environment(args.symbol, signal.timestamp.to_pydatetime(), load_events())
    append_audit_event("mt5_export_environment", args.strategy, args.symbol, args.timeframe, env.state, ",".join(env.reason_codes), {})
    csv_path, json_path = export_latest_signal(signal, env.state)
    print(f"Exported manual MT5 review files: {csv_path}, {json_path}")


def check_environment_cmd(args: argparse.Namespace) -> None:
    from tar_system.audit.writer import append_audit_event
    from tar_system.environment.environment_reporter import write_environment_report
    from tar_system.environment.event_calendar import load_events
    from tar_system.environment.risk_state import evaluate_environment

    target = datetime.fromisoformat(args.date)
    decision = evaluate_environment(args.symbol, target, load_events())
    report_md, report_json = write_environment_report(args.symbol, args.timeframe, target, decision)
    append_audit_event("environment_check", "environment", args.symbol, args.timeframe, decision.state, ",".join(decision.reason_codes), {"report": str(report_md)})
    print(json.dumps({"symbol": args.symbol, "timeframe": args.timeframe, "date": args.date, "state": decision.state, "report": str(report_json)}, indent=2))


def check_events_cmd(args: argparse.Namespace) -> None:
    from tar_system.environment.event_calendar import events_on_date, load_events

    target = datetime.fromisoformat(args.date)
    events = events_on_date(target, load_events() or [])
    print(json.dumps([event.__dict__ for event in events], indent=2, default=str))


def forward_test_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.forward_test.engine import run_forward_test

    result = run_forward_test(args.strategy, args.symbol, args.timeframe, args.broker, getattr(args, "from_date", None), getattr(args, "reset_loss_guard", False))
    print(json.dumps(asdict(result), indent=2, default=str))
    if result.review_status == "REVIEW_ONLY" and result.environment_state in {"HOLD_TRADING", "BLOCK_TRADING", "REVIEW_ONLY"}:
        raise SystemExit(f"Forward-test is REVIEW_ONLY: {result.environment_state}")


def run_walk_forward_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.data.store import load_feature_data
    from tar_system.strategies.registry import get_strategy
    from tar_system.validation.walk_forward import run_walk_forward

    features = load_feature_data(args.symbol, args.timeframe)
    strategy = get_strategy(args.strategy)
    result = run_walk_forward(features, strategy, args.train_window, args.test_window)
    
    # Save to data/results/
    output = Path("data/results")
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{args.strategy}_{args.symbol}_{args.timeframe}_walk_forward.json"
    with open(path, "w") as f:
        json.dump(asdict(result), f, indent=2, default=str)
    
    print(f"Walk-forward results saved to: {path}")
    print(json.dumps(asdict(result), indent=2, default=str))


def rank_strategies_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.analysis.strategy_ranker import rank_strategies
    from tar_system.reporting.review_log import load_review_results

    ranked = rank_strategies(load_review_results(), mode=args.mode)
    print(json.dumps([asdict(row) for row in ranked], indent=2))


def export_obsidian_cmd(args: argparse.Namespace) -> None:
    from tar_system.obsidian.exporter import export_result
    from tar_system.reporting.review_log import load_review_results

    rows = [
        row
        for row in load_review_results()
        if row.get("strategy") == args.strategy and row.get("symbol") == args.symbol and row.get("timeframe") == args.timeframe
    ]
    if not rows:
        raise SystemExit("No review result found for requested strategy/symbol/timeframe")
    note = export_result(rows[-1])
    print(f"Exported Obsidian note: {note}")


def add_strategy_idea_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.discovery.candidate_registry import save_candidate
    from tar_system.discovery.strategy_idea_parser import parse_strategy_idea

    blueprint = parse_strategy_idea(args.file)
    path = save_candidate(blueprint)
    print(json.dumps({"saved_to": str(path), "blueprint": asdict(blueprint)}, indent=2, default=str))


def generate_candidates_cmd(args: argparse.Namespace) -> None:
    from tar_system.discovery.candidate_registry import load_candidates, save_candidate
    from tar_system.discovery.mutation_engine import mutate_blueprint
    from tar_system.discovery.strategy_blueprint import StrategyBlueprint

    generated = 0
    for row in load_candidates():
        blueprint = StrategyBlueprint(**{key: value for key, value in row.items() if key != "status"})
        for mutation in mutate_blueprint(blueprint):
            save_candidate(mutation)
            generated += 1
    print(json.dumps({"from_obsidian": args.from_obsidian, "generated": generated}, indent=2))


def run_dashboard_cmd(args: argparse.Namespace) -> None:
    print("streamlit run src/tar_system/dashboard/app.py")


def promote_candidate_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.audit.writer import append_audit_event
    from tar_system.discovery.promotion_gate import evaluate_promotion

    human_approval = args.require_human_approval == "true" and args.human_approved == "true"
    decision = evaluate_promotion("KEEP", True, True, True, "SAFE_TO_TEST", human_approval)
    append_audit_event("promotion_gate", args.candidate, "", "", "APPROVED" if decision.approved else "BLOCKED", ",".join(decision.reason_codes), {})
    print(json.dumps(asdict(decision), indent=2))


def generate_report_cmd(args: argparse.Namespace) -> None:
    from tar_system.reporting.reporter import generate_report
    from tar_system.reporting.review_log import load_review_results

    rows = [
        row
        for row in load_review_results()
        if row.get("strategy") == args.strategy and row.get("symbol") == args.symbol and row.get("timeframe") == args.timeframe
    ]
    row = rows[-1] if rows else {"metrics": {}, "score": 0, "verdict": "REVIEW", "reason": "NO_REVIEW_LOG", "next_action": "RUN_BACKTEST"}
    path = generate_report(
        args.strategy,
        args.symbol,
        args.timeframe,
        row.get("metrics", {}),
        float(row.get("score", 0)),
        str(row.get("verdict", "REVIEW")),
        "REVIEW_ONLY",
        str(row.get("reason", "")).split(",") if row.get("reason") else [],
        str(row.get("next_action", "REVIEW")),
        args.format,
    )
    print(f"Generated report: {path}")


def run_paper_signal_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.controller.paper_signal_runner import run_paper_signal

    result = run_paper_signal(
        args.strategy,
        args.symbol,
        args.timeframe,
        args.broker,
        args.sizing_model,
        force_health_check=not args.skip_health_check,
    )
    print(json.dumps(asdict(result), indent=2, default=str))


def monitor_strategy_health_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.controller.strategy_health_monitor import evaluate_strategy_health

    result = evaluate_strategy_health(
        args.strategy,
        args.symbol,
        args.timeframe,
        min_trades=args.min_trades,
        min_profit_factor=args.min_profit_factor,
        min_sharpe=args.min_sharpe,
    )
    print(json.dumps(asdict(result), indent=2, default=str))


def generate_quant_report_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.controller.strategy_health_monitor import read_strategy_health
    from tar_system.reporting.reporter import generate_quant_report

    metrics_path = Path("data/results") / f"{args.strategy}_{args.symbol}_{args.timeframe}_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    signal_path = Path("runtime") / "latest_paper_signal.json"
    signal = json.loads(signal_path.read_text(encoding="utf-8")) if signal_path.exists() else {}
    health = read_strategy_health(args.strategy, args.symbol, args.timeframe)
    path = generate_quant_report(
        args.strategy,
        args.symbol,
        args.timeframe,
        metrics,
        signal=signal,
        health=asdict(health) if health else {},
    )
    print(json.dumps({"report_path": str(path), "pdf_path": str(path.with_suffix(".pdf")), "paper_only": True}, indent=2))


def security_check_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.security.checks import run_security_checks

    print(json.dumps(asdict(run_security_checks()), indent=2))


def optimise_strategy_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.optimisation.risk_strategy_optimiser import RiskStrategyOptimiser

    result = RiskStrategyOptimiser().optimise_from_logs(args.strategy, args.symbol, args.timeframe)
    print(json.dumps(asdict(result), indent=2, default=str))


def go_no_go_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.optimisation.artifacts import load_regime_trades, load_validation_artifacts
    from tar_system.optimisation.go_no_go_gate import evaluate_go_no_go
    from tar_system.reporting.review_log import load_review_results

    rows = [
        row
        for row in load_review_results()
        if row.get("strategy") == args.strategy and row.get("symbol") == args.symbol and row.get("timeframe") == args.timeframe
    ]
    latest = rows[-1] if rows else {"metrics": {}, "verdict": "REVIEW"}
    artifacts = load_validation_artifacts(args.strategy, args.symbol, args.timeframe)
    result = evaluate_go_no_go(
        str(latest.get("verdict", "REVIEW")),
        dict(latest.get("metrics", {})),
        walk_forward_exists=artifacts["walk_forward_metrics"] is not None,
        monte_carlo=artifacts["monte_carlo"],
        parameter_sensitivity=artifacts["parameter_sensitivity"],
        environment_state="REVIEW_ONLY",
        regime_count=len({str(trade.get("regime", "UNKNOWN")).upper() for trade in load_regime_trades(args.strategy, args.symbol, args.timeframe)}),
        audit_trail_exists=bool(rows),
    )
    print(json.dumps(asdict(result), indent=2))


def regime_heatmap_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.optimisation.artifacts import load_regime_trades
    from tar_system.optimisation.regime_heatmap import build_regime_heatmap

    heatmap = build_regime_heatmap(load_regime_trades(args.strategy, args.symbol, args.timeframe))
    print(json.dumps(asdict(heatmap), indent=2))


def resolve_strategy_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.strategies.resolver import resolve_strategy

    resolved = resolve_strategy(args.strategy, args.symbol, args.timeframe, args.broker, audit=True)
    print(
        json.dumps(
            {
                "variant": resolved.variant.to_dict(),
                "asset_profile": resolved.asset_profile.to_dict(),
                "broker": resolved.broker_profile.broker_name,
                "broker_symbol": resolved.broker_profile.symbol_profile(args.symbol).to_dict(),
                "paper_only": resolved.broker_profile.paper_mode_only,
            },
            indent=2,
            default=str,
        )
    )


def show_broker_cmd(args: argparse.Namespace) -> None:
    from tar_system.brokers.registry import list_missing_symbols, load_broker_profile

    broker = load_broker_profile(args.broker, audit=False)
    print(
        json.dumps(
            {
                "broker": broker.to_dict(),
                "missing_symbols": list_missing_symbols(broker),
                "paper_only": broker.paper_mode_only,
            },
            indent=2,
            default=str,
        )
    )


def cost_analysis_cmd(args: argparse.Namespace) -> None:
    from tar_system.validation.cost_analysis import run_cost_analysis

    result = run_cost_analysis(args.strategy, args.symbol, args.timeframe, args.broker)
    print(json.dumps(result.to_dict(), indent=2, default=str))


def optimise_asset_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.optimisation.optimiser import optimise_asset

    result = optimise_asset(args.strategy, args.symbol, args.timeframe, args.broker, args.max_variants, args.max_rows)
    print(json.dumps(asdict(result), indent=2, default=str))


def compare_assets_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.analysis.asset_comparison import compare_assets

    rows = compare_assets(args.strategy, args.timeframe, args.broker)
    print(json.dumps([asdict(row) for row in rows], indent=2, default=str))


def compare_variants_cmd(args: argparse.Namespace) -> None:
    from tar_system.reporting.reporter import generate_variant_comparison_report

    path = generate_variant_comparison_report(args.symbol, args.timeframe)
    print(json.dumps({"report_path": str(path), "symbol": args.symbol, "timeframe": args.timeframe}, indent=2))


def run_scheduled_cmd(args: argparse.Namespace) -> None:
    from datetime import datetime, timedelta

    from tar_system.audit.writer import append_audit_event
    from tar_system.dashboard.runtime_control import read_schedule, write_schedule_jobs
    from tar_system.controller.research_loop import run_research_loop
    from tar_system.controller.paper_signal_runner import run_paper_signal

    now = datetime.fromisoformat(args.now) if args.now else datetime.now()
    jobs = list(read_schedule().get("jobs", []))
    ran = 0
    for index, job in enumerate(jobs):
        if job.get("status") != "scheduled":
            continue
        run_at = datetime.fromisoformat(str(job.get("run_at")))
        if run_at > now:
            continue
        jobs[index] = {**job, "status": "running", "started_at": now.isoformat()}
        write_schedule_jobs(jobs)
        append_audit_event("scheduled_worker", str(job.get("strategy", "")), str(job.get("symbol", "")), str(job.get("timeframe", "")), "STARTED", "SCHEDULED_JOB_STARTED", job)
        try:
            if job.get("job_type") == "paper_signal":
                result = run_paper_signal(
                    str(job["strategy"]),
                    str(job["symbol"]),
                    str(job["timeframe"]),
                    str(job.get("broker", "current_broker_demo")),
                    str(job.get("sizing_model", "ATR_BASED")),
                )
                metadata = {"latest_signal_path": "runtime/latest_paper_signal.json", "alert_ready": result.alert_ready}
            elif job.get("job_type") == "all_tests":
                result = run_research_loop(
                    raw_dir=job.get("raw_dir", "data/raw"),
                    broker=job.get("broker", "current_broker_demo"),
                    force=bool(job.get("force", False)),
                    process_limit=0,
                    run_worker_now=False,
                    research_stage=job.get("research_stage", "dashboard_daily"),
                    skip_walk_forward=bool(job.get("skip_walk_forward", False)),
                    skip_forward_test=bool(job.get("skip_forward_test", True)),
                    max_walk_forward_splits=int(job.get("max_walk_forward_splits", 10)),
                    from_date=job.get("from_date"),
                    to_date=job.get("to_date"),
                )
                metadata = {"queued_jobs": result.queued_jobs, "summary_path": result.summary_path}
            else:
                run_full_pipeline_cmd(
                    argparse.Namespace(
                        strategy=job["strategy"],
                        symbol=job["symbol"],
                        timeframe=job["timeframe"],
                        file=job["file"],
                        skip_walk_forward=bool(job.get("skip_walk_forward", False)),
                        force=bool(job.get("force", False)),
                        broker=job.get("broker", "current_broker_demo"),
                        resume=False,
                        max_walk_forward_splits=100,
                        from_date=job.get("from_date"),
                        to_date=job.get("to_date"),
                        forward_from_date=job.get("forward_from_date"),
                    )
                )
                metadata = {}
            completed = {**jobs[index], "status": "completed", "completed_at": datetime.now().isoformat(), **metadata}
            if completed.get("repeat_interval_minutes"):
                completed["status"] = "scheduled"
                completed["last_completed_at"] = completed.pop("completed_at")
                completed["run_at"] = (run_at + timedelta(minutes=int(completed["repeat_interval_minutes"]))).isoformat()
            elif completed.get("repeat_daily"):
                completed["status"] = "scheduled"
                completed["last_completed_at"] = completed.pop("completed_at")
                completed["run_at"] = (run_at + timedelta(days=1)).isoformat()
            jobs[index] = completed
            ran += 1
        except SystemExit as exc:
            jobs[index] = {**jobs[index], "status": "stopped", "stopped_at": datetime.now().isoformat(), "latest_message": str(exc)}
        write_schedule_jobs(jobs)
    print(json.dumps({"checked_at": now.isoformat(), "jobs_run": ran}, indent=2))


def install_paper_signal_schedule_cmd(args: argparse.Namespace) -> None:
    from datetime import datetime, timedelta

    from tar_system.dashboard.runtime_control import schedule_research_run

    run_at = datetime.now() + timedelta(minutes=max(1, args.interval_minutes))
    path = schedule_research_run(
        {
            "job_type": "paper_signal",
            "strategy": args.strategy,
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "broker": args.broker,
            "sizing_model": args.sizing_model,
            "run_at": run_at.isoformat(timespec="seconds"),
            "repeat_interval_minutes": args.interval_minutes,
        }
    )
    print(json.dumps({"schedule_path": str(path), "interval_minutes": args.interval_minutes, "paper_only": True}, indent=2))


def queue_job_cmd(args: argparse.Namespace) -> None:
    from tar_system.controller.job_queue import add_job

    job = add_job(
        args.strategy,
        args.symbol,
        args.timeframe,
        args.file,
        args.broker,
        from_date=args.from_date,
        to_date=args.to_date,
        forward_from_date=args.forward_from_date,
        skip_walk_forward=args.skip_walk_forward,
        skip_forward_test=args.skip_forward_test,
        max_walk_forward_splits=args.max_walk_forward_splits,
        research_stage=args.research_stage,
    )
    print(json.dumps(job, indent=2, default=str))


def show_queue_cmd(args: argparse.Namespace) -> None:
    from tar_system.controller.job_queue import read_jobs

    print(json.dumps(read_jobs(), indent=2, default=str))


def run_controller_cmd(args: argparse.Namespace) -> None:
    from tar_system.controller.research_controller import run_controller_once, run_controller_watch

    if getattr(args, "watch", False):
        run_controller_watch(60)
        return
    print(json.dumps(run_controller_once(), indent=2, default=str))


def run_worker_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.controller.worker import run_worker

    result = run_worker(args.limit)
    print(json.dumps(asdict(result), indent=2, default=str))


def load_test_cmd(args: argparse.Namespace) -> None:
    from tar_system.controller.load_test import run_load_test

    result = run_load_test(args.jobs, args.artifacts)
    print(json.dumps(result.to_dict(), indent=2, default=str))


def run_research_loop_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.controller.research_loop import run_research_loop

    result = run_research_loop(
        raw_dir=args.raw_dir,
        broker=args.broker,
        force=args.force,
        process_limit=args.limit,
        run_worker_now=not args.queue_only,
        research_stage=args.stage,
        window_months=args.window_months,
        skip_walk_forward=args.skip_walk_forward if args.skip_walk_forward else None,
        skip_forward_test=args.skip_forward_test if args.skip_forward_test else None,
        max_walk_forward_splits=args.max_walk_forward_splits,
        from_date=args.from_date,
        to_date=args.to_date,
    )
    print(json.dumps(asdict(result), indent=2, default=str))


def research_summary_cmd(args: argparse.Namespace) -> None:
    from tar_system.controller.job_queue import queue_stats
    from tar_system.controller.research_loop import recommend_next_actions, write_research_loop_summary

    path = write_research_loop_summary([], None, queue_stats(), recommend_next_actions(args.limit))
    print(json.dumps({"summary_path": str(path), "next_actions": recommend_next_actions(args.limit)}, indent=2))


def export_ai_review_packet_cmd(args: argparse.Namespace) -> None:
    from tar_system.reporting.ai_review_packet import export_ai_review_packet

    path = export_ai_review_packet(args.output, args.limit)
    print(json.dumps({"packet_path": str(path), "json_path": str(path.with_suffix(".json"))}, indent=2))


def run_research_committee_cmd(args: argparse.Namespace) -> None:
    from tar_system.research.committee import run_research_committee

    manual_notes = ""
    if getattr(args, "notes_file", None):
        manual_notes = Path(args.notes_file).read_text(encoding="utf-8")
    result = run_research_committee(
        args.strategy,
        args.symbol,
        args.timeframe,
        manual_notes=manual_notes,
        output_dir=args.output_dir,
    )
    print(
        json.dumps(
            {
                "paper_only": result.paper_only,
                "recommendation": result.recommendation,
                "confidence": result.confidence,
                "markdown": result.output_markdown,
                "json": result.output_json,
            },
            indent=2,
        )
    )


def fit_strategy_filters_cmd(args: argparse.Namespace) -> None:
    from tar_system.research.strategy_fitter import build_strategy_filter_plan

    plan = build_strategy_filter_plan(
        limit=args.limit,
        output_dir=args.output_dir,
        run_committee=not args.skip_committee,
    )
    print(
        json.dumps(
            {
                "paper_only": plan.paper_only,
                "candidates_reviewed": plan.candidates_reviewed,
                "markdown": plan.output_markdown,
                "json": plan.output_json,
            },
            indent=2,
        )
    )


def export_private_memory_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.memory.private_memory_export import export_private_strategy_memory

    result = export_private_strategy_memory(
        strategy=args.strategy,
        symbol=args.symbol,
        timeframe=args.timeframe,
        obsidian_root=args.obsidian_root,
        second_brain_root=args.second_brain_root,
    )
    print(json.dumps(asdict(result), indent=2, default=str))


def import_cot_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system import reason_codes as rc
    from tar_system.audit.writer import append_audit_event
    from tar_system.positioning.cot_importer import import_cot_csv

    try:
        record = import_cot_csv(args.file, args.symbol, args.date_column, getattr(args, "market", None), getattr(args, "market_column", None))
    except Exception as exc:
        append_audit_event("positioning_import", "COT", args.symbol, "", "FAILED", "POSITIONING_COT_IMPORT_FAILED", {"file": args.file, "error": str(exc)})
        raise SystemExit(f"COT import failed: {exc}") from exc
    append_audit_event("positioning_import", "COT", args.symbol, "", "IMPORTED", rc.POSITIONING_COT_IMPORTED, asdict(record))
    print(json.dumps(asdict(record), indent=2, default=str))


def import_positioning_note_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system import reason_codes as rc
    from tar_system.audit.writer import append_audit_event
    from tar_system.positioning.manual_note_importer import import_positioning_note

    try:
        record = import_positioning_note(args.file, args.symbol, args.source, args.date)
    except Exception as exc:
        append_audit_event("positioning_import", args.source, args.symbol, "", "FAILED", "POSITIONING_NOTE_IMPORT_FAILED", {"file": args.file, "error": str(exc)})
        raise SystemExit(f"Positioning note import failed: {exc}") from exc
    append_audit_event("positioning_import", args.source, args.symbol, "", "IMPORTED", rc.POSITIONING_NOTE_IMPORTED, asdict(record))
    print(json.dumps(asdict(record), indent=2, default=str))


def positioning_score_cmd(args: argparse.Namespace) -> None:
    from tar_system.positioning.store import latest_positioning_score, load_positioning_records

    payload = latest_positioning_score(args.symbol)
    if args.show_records:
        payload["records"] = load_positioning_records(args.symbol, args.limit)
    print(json.dumps(payload, indent=2, default=str))


def run_full_pipeline_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.audit.writer import append_audit_event
    from tar_system.backtest.engine import run_backtest
    from tar_system.data.store import filter_by_date_range, load_feature_data, load_validated_data
    from tar_system.dashboard.runtime_control import has_tested_data, mark_data_tested, write_status
    from tar_system.features.engineering import build_and_save_features
    from tar_system.forward_test.engine import run_forward_test
    from tar_system.memory.strategy_memory import record_strategy_result
    from tar_system.pipeline.checkpoint import (
        make_run_id,
        mark_pipeline_completed,
        mark_stage_completed,
        start_checkpoint,
    )
    from tar_system.reporting.review_log import append_review_result
    from tar_system.reporting.reporter import generate_report
    from tar_system.scoring.gates import run_gates
    from tar_system.scoring.multi_agent_scorer import score_multi_agent
    from tar_system.scoring.scorer import score_strategy
    from tar_system.strategies.registry import get_strategy
    from tar_system.validation.walk_forward import run_walk_forward

    from tar_system.data.csv_importer import hash_csv_file

    data_hash = hash_csv_file(args.file)
    from_date = getattr(args, "from_date", None)
    to_date = getattr(args, "to_date", None)
    forward_from_date = getattr(args, "forward_from_date", None)
    if not getattr(args, "force", False) and has_tested_data(args.strategy, args.symbol, args.timeframe, data_hash, "full_pipeline", from_date, to_date):
        append_audit_event(
            "pipeline_duplicate_guard",
            args.strategy,
            args.symbol,
            args.timeframe,
            "SKIPPED",
            "DATA_ALREADY_TESTED",
            {"file": args.file, "data_hash": data_hash, "paper_only": True},
        )
        raise SystemExit("This exact data hash and backtest date range was already tested for this strategy/symbol/timeframe. Use --force to retest intentionally.")
    run_id = make_run_id(args.strategy, args.symbol, args.timeframe)
    checkpoint = start_checkpoint(run_id, args.strategy, args.symbol, args.timeframe, args.file, data_hash, bool(getattr(args, "resume", False)))
    context = {"broker": args.broker, "paper_only": True, "run_id": run_id}
    write_status(
        "backtest",
        {
            "running": True,
            "stop_requested": False,
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "strategy": args.strategy,
            "mode": "full_pipeline",
            "latest_message": "full pipeline started",
        },
    )
    print(f"[1/9] Import CSV for {args.symbol} {args.timeframe}")
    checkpoint = _pipeline_step("import-csv", args, lambda: import_csv(argparse.Namespace(file=args.file, symbol=args.symbol, timeframe=args.timeframe)), context, checkpoint)

    print("[2/9] Validate data")
    checkpoint = _pipeline_step("validate-data", args, lambda: validate_data(argparse.Namespace(symbol=args.symbol, timeframe=args.timeframe)), context, checkpoint)

    print("[3/9] Build features")
    checkpoint = _pipeline_step(
        "build-features",
        args,
        lambda: build_and_save_features(load_validated_data(args.symbol, args.timeframe), args.symbol, args.timeframe),
        context,
        checkpoint,
    )

    print("[4/9] Run backtest")
    strategy = get_strategy(args.strategy)

    def _run_pipeline_backtest() -> dict[str, object]:
        features = filter_by_date_range(load_feature_data(args.symbol, args.timeframe), from_date, to_date)
        if features.empty:
            raise SystemExit("No feature rows found inside the requested backtest date range")
        result = run_backtest(features, strategy, audit_decisions=False)
        if result.stopped:
            raise SystemExit("Backtest stopped before completion; partial result was not scored")
        output = Path("data/results")
        output.mkdir(parents=True, exist_ok=True)
        path = output / f"{args.strategy}_{args.symbol}_{args.timeframe}_metrics.json"
        path.write_text(json.dumps(result.metrics, indent=2), encoding="utf-8")
        append_review_result(args.strategy, strategy.version, args.symbol, args.timeframe, result.metrics, 0.0, "UNSCORED", "BACKTEST", "SCORE_STRATEGY")
        print(json.dumps({"trades": result.trades, "final_equity": result.final_equity, "metrics": result.metrics}, indent=2))
        return {"path": str(path), "trades": result.trades, "final_equity": result.final_equity}

    checkpoint = _pipeline_step("run-backtest", args, _run_pipeline_backtest, context, checkpoint)

    if args.skip_walk_forward:
        print("[5/9] Walk-forward skipped")
        _write_walk_forward_review_artifact(args.strategy, args.symbol, args.timeframe, "Walk-forward skipped for this run.", "skipped")
        append_audit_event("pipeline_step", args.strategy, args.symbol, args.timeframe, "SKIPPED", "WALK_FORWARD_SKIPPED", context)
        checkpoint = mark_stage_completed(checkpoint, "run-walk-forward", {"latest_message": "walk-forward skipped"})
    else:
        features = filter_by_date_range(load_feature_data(args.symbol, args.timeframe), from_date, to_date)
        if features.empty:
            raise SystemExit("No feature rows found inside the requested walk-forward date range")
        if len(features) >= 250:
            print("[5/9] Run walk-forward")
            def _run_pipeline_walk_forward() -> dict[str, object]:
                result = run_walk_forward(features, strategy, 200, 50, audit_decisions=False, max_splits=int(getattr(args, "max_walk_forward_splits", 100)))
                if result.stopped:
                    raise SystemExit("Walk-forward stopped before completion; partial result was not scored")
                payload = {
                    "split_count": len(result.splits),
                    "ran": result.ran,
                    "window_count": result.window_count,
                    "wf_verdict": result.wf_verdict,
                    "wf_reason": result.wf_reason,
                    "stitched_metrics": result.stitched_metrics,
                    "parameter_stability": result.parameter_stability,
                    "stable_parameter_ranges": result.stable_parameter_ranges,
                    "parameter_stability_score": result.parameter_stability_score,
                    "recommended_search_range": result.recommended_search_range,
                    "bootstrap_ci": result.bootstrap_ci,
                }
                output = Path("data/results") / f"{args.strategy}_{args.symbol}_{args.timeframe}_walk_forward.json"
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
                print(json.dumps(payload, indent=2, default=str))
                return payload

            checkpoint = _pipeline_step("run-walk-forward", args, _run_pipeline_walk_forward, context, checkpoint)
        else:
            print("[5/9] Walk-forward skipped: not enough rows")
            _write_walk_forward_review_artifact(args.strategy, args.symbol, args.timeframe, f"Not enough rows for walk-forward: {len(features)} rows available.", "not_enough_data")
            append_audit_event("pipeline_step", args.strategy, args.symbol, args.timeframe, "SKIPPED", "WALK_FORWARD_NOT_ENOUGH_DATA", {"rows": len(features), **context})
            checkpoint = mark_stage_completed(checkpoint, "run-walk-forward", {"latest_message": "walk-forward skipped: not enough rows"})

    print("[6/9] Forward-test gate")
    forward_gate: dict[str, object] = {}
    if getattr(args, "skip_forward_test", False):
        print("[6/9] Forward-test skipped")
        forward_gate.update({"review_status": "SKIPPED", "reason": "SMOKE_STAGE_ANALYSIS_ONLY", "paper_only": True})
        append_audit_event("pipeline_step", args.strategy, args.symbol, args.timeframe, "SKIPPED", "FORWARD_TEST_SKIPPED", {**context, "reason": "SMOKE_STAGE_ANALYSIS_ONLY"})
        checkpoint = mark_stage_completed(checkpoint, "forward-test", {"latest_message": "forward-test skipped"})
    else:
        def _run_pipeline_forward_test() -> dict[str, object]:
            result = run_forward_test(args.strategy, args.symbol, args.timeframe, args.broker, forward_from_date)
            forward_gate.update(asdict(result))
            print(json.dumps(forward_gate, indent=2, default=str))
            if result.review_status == "REVIEW_ONLY":
                raise SystemExit(f"Forward-test is REVIEW_ONLY: {result.environment_state}")
            return forward_gate

        checkpoint = _pipeline_step(
            "forward-test",
            args,
            _run_pipeline_forward_test,
            context,
            checkpoint,
        )

    score_payload: dict[str, object] = {}

    print("[7/9] Score strategy")
    def _score_pipeline_strategy() -> dict[str, object]:
        metrics_path = Path("data/results") / f"{args.strategy}_{args.symbol}_{args.timeframe}_metrics.json"
        stage_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        walk_forward_path = Path("data/results") / f"{args.strategy}_{args.symbol}_{args.timeframe}_walk_forward.json"
        walk_forward = json.loads(walk_forward_path.read_text(encoding="utf-8")) if walk_forward_path.exists() else None
        stage_score = score_strategy(stage_metrics, walk_forward, args.timeframe, require_walk_forward=True)
        stage_metrics = _metrics_with_walk_forward(stage_metrics, walk_forward)
        stage_gate = run_gates(stage_metrics, args.timeframe, require_oos=True)
        ma_result = score_multi_agent(stage_metrics)
        ma_codes = ["MULTI_AGENT_KILL"] if ma_result.verdict == "KILL" else []
        reason_codes = _merge_reason_codes(stage_score.reason_codes, stage_gate.reason_codes, ma_codes)
        final_verdict = "KILL" if ma_result.verdict == "KILL" else stage_gate.verdict
        stage_metrics = {
            **stage_metrics,
            "gate_failed": stage_gate.failed_gate or "",
            "gate_reason": stage_gate.reason,
        }
        append_review_result(
            args.strategy,
            strategy.version,
            args.symbol,
            args.timeframe,
            stage_metrics,
            stage_score.score,
            final_verdict,
            ",".join(reason_codes),
            "WRITE_MEMORY",
        )
        score_payload.update(
            {
                "metrics": stage_metrics,
                "score": stage_score,
                "verdict": final_verdict,
                "reason_codes": reason_codes,
                "gate": stage_gate,
                "walk_forward_metrics": walk_forward or {},
                "multi_agent": ma_result,
            }
        )
        print(json.dumps({
            "score": stage_score.score,
            "verdict": final_verdict,
            "reason_codes": reason_codes,
            "gate": stage_gate.__dict__,
            "multi_agent": {
                "verdict": ma_result.verdict,
                "confidence": ma_result.confidence,
                "dissent": ma_result.dissent,
            },
        }, indent=2))
        return score_payload

    checkpoint = _pipeline_step("score-strategy", args, _score_pipeline_strategy, context, checkpoint)

    print("[8/9] Generate report")
    metrics_path = Path("data/results") / f"{args.strategy}_{args.symbol}_{args.timeframe}_metrics.json"
    metrics = dict(score_payload.get("metrics") or json.loads(metrics_path.read_text(encoding="utf-8")))
    score = score_payload.get("score") or score_strategy(metrics)
    _pipeline_step(
        "generate-report",
        args,
        lambda: generate_report(
            args.strategy,
            args.symbol,
            args.timeframe,
            metrics,
            score.score,  # type: ignore[union-attr]
            str(score_payload.get("verdict") or score.verdict),  # type: ignore[union-attr]
            "REVIEW_ONLY",
            list(score_payload.get("reason_codes") or score.reason_codes),  # type: ignore[union-attr]
            "REVIEW",
            "md",
        ),
        context,
        checkpoint,
    )
    report_path = Path("reports") / f"{args.symbol}_{args.timeframe}_{args.strategy}_report.md"
    checkpoint = mark_stage_completed(checkpoint, "generate-report")

    print("[9/9] Write strategy memory")
    checkpoint = _pipeline_step(
        "write-memory",
        args,
        lambda: record_strategy_result(
            args.strategy,
            strategy.version,
            args.symbol,
            args.timeframe,
            {},
            metrics,
            score.score,  # type: ignore[union-attr]
            str(score_payload.get("verdict") or score.verdict),  # type: ignore[union-attr]
            list(score_payload.get("reason_codes") or score.reason_codes),  # type: ignore[union-attr]
            dict(score_payload.get("walk_forward_metrics") or {}),
        ),
        context,
        checkpoint,
    )

    print("[10/10] Pipeline complete")
    append_audit_event(
        "pipeline_complete",
        args.strategy,
        args.symbol,
        args.timeframe,
        "COMPLETED",
        "PIPELINE_COMPLETED",
        {"report": str(report_path), "broker": args.broker, "paper_only": True},
    )
    mark_pipeline_completed(checkpoint, str(report_path))
    mark_data_tested(args.strategy, args.symbol, args.timeframe, data_hash, "full_pipeline", str(report_path), from_date, to_date)
    write_status(
        "backtest",
        {
            "running": False,
            "stop_requested": False,
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "strategy": args.strategy,
            "mode": "full_pipeline",
            "latest_message": "full pipeline completed",
            "latest_result_path": str(report_path),
        },
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "paper_only": True,
                "validated": f"data/validated/{args.symbol}_{args.timeframe}.parquet",
                "features": f"data/features/{args.symbol}_{args.timeframe}.parquet",
                "report": str(report_path),
            },
            indent=2,
        )
    )


def _pipeline_step(step: str, args: argparse.Namespace, func: object, metadata: dict[str, object], checkpoint: dict[str, object] | None = None) -> dict[str, object]:
    from tar_system.audit.writer import append_audit_event
    from tar_system.dashboard.runtime_control import read_backtest_status, write_status
    from tar_system.pipeline.checkpoint import mark_pipeline_failed, mark_pipeline_stopped, mark_stage_completed, mark_stage_started

    audit_metadata = dict(metadata)
    checkpoint = checkpoint or {}
    if getattr(args, "resume", False) and step in checkpoint.get("completed_stages", []):
        append_audit_event("pipeline_step", args.strategy, args.symbol, args.timeframe, "SKIPPED", f"{step.upper().replace('-', '_')}_RESUMED", audit_metadata)
        return checkpoint
    checkpoint = mark_stage_started(checkpoint, step) if checkpoint else checkpoint
    append_audit_event("pipeline_step", args.strategy, args.symbol, args.timeframe, "STARTED", step.upper().replace("-", "_"), audit_metadata)
    try:
        func()
    except SystemExit as exc:
        append_audit_event("pipeline_step", args.strategy, args.symbol, args.timeframe, "FAILED", f"{step.upper().replace('-', '_')}_FAILED", {"code": exc.code, **audit_metadata})
        write_status(
            "backtest",
            {
                "running": False,
                "stop_requested": False,
                "symbol": args.symbol,
                "timeframe": args.timeframe,
                "strategy": args.strategy,
                "mode": "full_pipeline",
                "latest_message": f"stopped at {step}",
            },
        )
        if checkpoint:
            mark_pipeline_stopped(checkpoint, f"stopped at {step}")
        print(f"Pipeline stopped safely at step '{step}': {exc}")
        raise
    except Exception as exc:
        append_audit_event("pipeline_step", args.strategy, args.symbol, args.timeframe, "FAILED", f"{step.upper().replace('-', '_')}_FAILED", {"error": str(exc), **audit_metadata})
        write_status(
            "backtest",
            {
                "running": False,
                "stop_requested": False,
                "symbol": args.symbol,
                "timeframe": args.timeframe,
                "strategy": args.strategy,
                "mode": "full_pipeline",
                "latest_message": f"stopped at {step}",
            },
        )
        if checkpoint:
            mark_pipeline_failed(checkpoint, f"failed at {step}: {exc}")
        print(f"Pipeline stopped safely at step '{step}': {exc}")
        raise SystemExit(1) from exc
    if read_backtest_status().get("stop_requested"):
        append_audit_event("pipeline_step", args.strategy, args.symbol, args.timeframe, "STOPPED", "STOP_REQUESTED", audit_metadata)
        if checkpoint:
            mark_pipeline_stopped(checkpoint, f"stopped after {step}")
        raise SystemExit(f"Stop requested after {step}; partial result was not scored")
    append_audit_event("pipeline_step", args.strategy, args.symbol, args.timeframe, "COMPLETED", f"{step.upper().replace('-', '_')}_COMPLETED", audit_metadata)
    if checkpoint:
        return mark_stage_completed(checkpoint, step)
    return checkpoint


def _merge_reason_codes(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for code in group:
            if code not in merged:
                merged.append(code)
    return merged


def _metrics_with_walk_forward(metrics: dict[str, float], walk_forward: dict[str, object] | None) -> dict[str, float]:
    enriched = dict(metrics)
    if not walk_forward:
        return enriched
    stitched = walk_forward.get("stitched_metrics", {}) or {}
    if isinstance(stitched, dict):
        enriched["sharpe_oos"] = float(stitched.get("sharpe_ratio", stitched.get("sharpe", 0.0)) or 0.0)
    raw_stability = float(walk_forward.get("parameter_stability_score", 0.0) or 0.0)
    enriched["param_stability"] = raw_stability / 100.0 if raw_stability > 1.0 else raw_stability
    enriched["walk_forward_splits"] = float(walk_forward.get("split_count", walk_forward.get("window_count", 0)) or 0)
    bootstrap_ci = walk_forward.get("bootstrap_ci", {}) or {}
    if isinstance(bootstrap_ci, dict):
        enriched["bootstrap_ci_lower"] = float(bootstrap_ci.get("ci_lower", 0.0) or 0.0)
        enriched["bootstrap_ci_upper"] = float(bootstrap_ci.get("ci_upper", 0.0) or 0.0)
        enriched["bootstrap_ci_spans_zero"] = bool(bootstrap_ci.get("spans_zero", True))
    return enriched


def _write_walk_forward_review_artifact(strategy: str, symbol: str, timeframe: str, reason: str, status: str) -> Path:
    output = Path("data/results") / f"{strategy}_{symbol}_{timeframe}_walk_forward.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "split_count": 0,
                "ran": False,
                "window_count": 0,
                "wf_verdict": "REVIEW",
                "wf_reason": reason,
                "stitched_metrics": {},
                "parameter_stability": {"status": status, "stability_score": 0.0},
                "stable_parameter_ranges": {},
                "parameter_stability_score": 0.0,
                "recommended_search_range": {},
                "bootstrap_ci": {
                    "mean": 0.0,
                    "ci_lower": 0.0,
                    "ci_upper": 0.0,
                    "spans_zero": True,
                    "sample_size": 0,
                    "confidence": 0.95,
                    "n_iterations": 0,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TAR V2 local trading research CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    import_parser = subparsers.add_parser("import-csv")
    import_parser.add_argument("--file", required=True)
    import_parser.add_argument("--symbol", required=True)
    import_parser.add_argument("--timeframe", required=True)
    import_parser.set_defaults(func=import_csv)

    convert_parser = subparsers.add_parser("convert-ticks")
    convert_parser.add_argument("--file", required=True)
    convert_parser.add_argument("--symbol", required=True)
    convert_parser.add_argument("--timeframe", required=True)
    convert_parser.set_defaults(func=convert_ticks_cmd)

    validate_parser = subparsers.add_parser("validate-data")
    validate_parser.add_argument("--symbol", required=True)
    validate_parser.add_argument("--timeframe", required=True)
    validate_parser.set_defaults(func=validate_data)

    features_parser = subparsers.add_parser("build-features")
    features_parser.add_argument("--symbol", required=True)
    features_parser.add_argument("--timeframe", required=True)
    features_parser.set_defaults(func=build_features_cmd)

    backtest_parser = subparsers.add_parser("run-backtest")
    backtest_parser.add_argument("--strategy", required=True)
    backtest_parser.add_argument("--symbol", required=True)
    backtest_parser.add_argument("--timeframe", required=True)
    backtest_parser.add_argument("--broker", default="current_broker_demo")
    backtest_parser.add_argument("--force", action="store_true")
    backtest_parser.add_argument("--from-date", default=None)
    backtest_parser.add_argument("--to-date", default=None)
    backtest_parser.set_defaults(func=run_backtest_cmd)

    score_parser = subparsers.add_parser("score-strategy")
    score_parser.add_argument("--strategy", required=True)
    score_parser.add_argument("--symbol", required=True)
    score_parser.add_argument("--timeframe", required=True)
    score_parser.add_argument("--broker", default="current_broker_demo")
    score_parser.set_defaults(func=score_strategy_cmd)

    export_parser = subparsers.add_parser("export-mt5")
    export_parser.add_argument("--strategy", required=True)
    export_parser.add_argument("--symbol", required=True)
    export_parser.add_argument("--timeframe", required=True)
    export_parser.set_defaults(func=export_mt5_cmd)

    env_parser = subparsers.add_parser("check-environment")
    env_parser.add_argument("--symbol", required=True)
    env_parser.add_argument("--timeframe", required=True)
    env_parser.add_argument("--date", required=True)
    env_parser.set_defaults(func=check_environment_cmd)

    events_parser = subparsers.add_parser("check-events")
    events_parser.add_argument("--date", required=True)
    events_parser.set_defaults(func=check_events_cmd)

    walk_parser = subparsers.add_parser("run-walk-forward")
    walk_parser.add_argument("--strategy", required=True)
    walk_parser.add_argument("--symbol", required=True)
    walk_parser.add_argument("--timeframe", required=True)
    walk_parser.add_argument("--train-window", type=int, default=200)
    walk_parser.add_argument("--test-window", type=int, default=50)
    walk_parser.set_defaults(func=run_walk_forward_cmd)

    rank_parser = subparsers.add_parser("rank-strategies")
    rank_parser.add_argument("--mode", default="balanced", choices=["balanced", "win_rate", "profit_factor", "lowest_drawdown", "stable"])
    rank_parser.set_defaults(func=rank_strategies_cmd)

    obsidian_parser = subparsers.add_parser("export-obsidian")
    obsidian_parser.add_argument("--strategy", required=True)
    obsidian_parser.add_argument("--symbol", required=True)
    obsidian_parser.add_argument("--timeframe", required=True)
    obsidian_parser.set_defaults(func=export_obsidian_cmd)

    idea_parser = subparsers.add_parser("add-strategy-idea")
    idea_parser.add_argument("--file", required=True)
    idea_parser.set_defaults(func=add_strategy_idea_cmd)

    candidates_parser = subparsers.add_parser("generate-candidates")
    candidates_parser.add_argument("--from-obsidian", default="false")
    candidates_parser.set_defaults(func=generate_candidates_cmd)

    dashboard_parser = subparsers.add_parser("run-dashboard")
    dashboard_parser.set_defaults(func=run_dashboard_cmd)

    forward_parser = subparsers.add_parser("forward-test")
    forward_parser.add_argument("--strategy", required=True)
    forward_parser.add_argument("--symbol", required=True)
    forward_parser.add_argument("--timeframe", required=True)
    forward_parser.add_argument("--broker", default="current_broker_demo")
    forward_parser.add_argument("--environment-check", default="true")
    forward_parser.add_argument("--from-date", default=None)
    forward_parser.add_argument("--reset-loss-guard", action="store_true")
    forward_parser.set_defaults(func=forward_test_cmd)

    promote_parser = subparsers.add_parser("promote-candidate")
    promote_parser.add_argument("--candidate", required=True)
    promote_parser.add_argument("--require-human-approval", default="true")
    promote_parser.add_argument("--human-approved", default="false")
    promote_parser.set_defaults(func=promote_candidate_cmd)

    report_parser = subparsers.add_parser("generate-report")
    report_parser.add_argument("--strategy", required=True)
    report_parser.add_argument("--symbol", required=True)
    report_parser.add_argument("--timeframe", required=True)
    report_parser.add_argument("--format", default="md", choices=["md", "json"])
    report_parser.set_defaults(func=generate_report_cmd)

    paper_signal_parser = subparsers.add_parser("run-paper-signal")
    paper_signal_parser.add_argument("--strategy", required=True)
    paper_signal_parser.add_argument("--symbol", required=True)
    paper_signal_parser.add_argument("--timeframe", required=True)
    paper_signal_parser.add_argument("--broker", default="current_broker_demo")
    paper_signal_parser.add_argument("--sizing-model", default="ATR_BASED", choices=["FIXED_LOT", "FIXED_RISK_PCT", "ATR_BASED", "HALF_KELLY"])
    paper_signal_parser.add_argument("--skip-health-check", action="store_true")
    paper_signal_parser.set_defaults(func=run_paper_signal_cmd)

    health_parser = subparsers.add_parser("monitor-strategy-health")
    health_parser.add_argument("--strategy", required=True)
    health_parser.add_argument("--symbol", required=True)
    health_parser.add_argument("--timeframe", required=True)
    health_parser.add_argument("--min-trades", type=int, default=30)
    health_parser.add_argument("--min-profit-factor", type=float, default=1.05)
    health_parser.add_argument("--min-sharpe", type=float, default=0.0)
    health_parser.set_defaults(func=monitor_strategy_health_cmd)

    quant_report_parser = subparsers.add_parser("generate-quant-report")
    quant_report_parser.add_argument("--strategy", required=True)
    quant_report_parser.add_argument("--symbol", required=True)
    quant_report_parser.add_argument("--timeframe", required=True)
    quant_report_parser.set_defaults(func=generate_quant_report_cmd)

    security_parser = subparsers.add_parser("security-check")
    security_parser.set_defaults(func=security_check_cmd)

    optimiser_parser = subparsers.add_parser("optimise-strategy")
    optimiser_parser.add_argument("--strategy", required=True)
    optimiser_parser.add_argument("--symbol", required=True)
    optimiser_parser.add_argument("--timeframe", required=True)
    optimiser_parser.set_defaults(func=optimise_strategy_cmd)

    gate_parser = subparsers.add_parser("go-no-go")
    gate_parser.add_argument("--strategy", required=True)
    gate_parser.add_argument("--symbol", required=True)
    gate_parser.add_argument("--timeframe", required=True)
    gate_parser.set_defaults(func=go_no_go_cmd)

    heatmap_parser = subparsers.add_parser("regime-heatmap")
    heatmap_parser.add_argument("--strategy", required=True)
    heatmap_parser.add_argument("--symbol", required=True)
    heatmap_parser.add_argument("--timeframe", required=True)
    heatmap_parser.set_defaults(func=regime_heatmap_cmd)

    resolve_parser = subparsers.add_parser("resolve-strategy")
    resolve_parser.add_argument("--strategy", required=True)
    resolve_parser.add_argument("--symbol", required=True)
    resolve_parser.add_argument("--timeframe", required=True)
    resolve_parser.add_argument("--broker", default="current_broker_demo")
    resolve_parser.set_defaults(func=resolve_strategy_cmd)

    show_broker_parser = subparsers.add_parser("show-broker")
    show_broker_parser.add_argument("--broker", default="current_broker_demo")
    show_broker_parser.set_defaults(func=show_broker_cmd)

    cost_parser = subparsers.add_parser("cost-analysis")
    cost_parser.add_argument("--strategy", required=True)
    cost_parser.add_argument("--symbol", required=True)
    cost_parser.add_argument("--timeframe", required=True)
    cost_parser.add_argument("--broker", default="current_broker_demo")
    cost_parser.set_defaults(func=cost_analysis_cmd)

    optimise_asset_parser = subparsers.add_parser("optimise-asset")
    optimise_asset_parser.add_argument("--strategy", required=True)
    optimise_asset_parser.add_argument("--symbol", required=True)
    optimise_asset_parser.add_argument("--timeframe", required=True)
    optimise_asset_parser.add_argument("--broker", default="current_broker_demo")
    optimise_asset_parser.add_argument("--max-variants", type=int, default=8)
    optimise_asset_parser.add_argument("--max-rows", type=int, default=20000)
    optimise_asset_parser.set_defaults(func=optimise_asset_cmd)

    compare_assets_parser = subparsers.add_parser("compare-assets")
    compare_assets_parser.add_argument("--strategy", required=True)
    compare_assets_parser.add_argument("--timeframe", required=True)
    compare_assets_parser.add_argument("--broker", default="current_broker_demo")
    compare_assets_parser.set_defaults(func=compare_assets_cmd)

    compare_variants_parser = subparsers.add_parser("compare-variants")
    compare_variants_parser.add_argument("--symbol", required=True)
    compare_variants_parser.add_argument("--timeframe", required=True)
    compare_variants_parser.set_defaults(func=compare_variants_cmd)

    scheduled_parser = subparsers.add_parser("run-scheduled")
    scheduled_parser.add_argument("--now", default=None)
    scheduled_parser.set_defaults(func=run_scheduled_cmd)

    install_signal_schedule_parser = subparsers.add_parser("install-paper-signal-schedule")
    install_signal_schedule_parser.add_argument("--strategy", default="liquidity_sweep_v1")
    install_signal_schedule_parser.add_argument("--symbol", default="XAUUSD")
    install_signal_schedule_parser.add_argument("--timeframe", default="M15")
    install_signal_schedule_parser.add_argument("--broker", default="current_broker_demo")
    install_signal_schedule_parser.add_argument("--sizing-model", default="ATR_BASED", choices=["FIXED_LOT", "FIXED_RISK_PCT", "ATR_BASED", "HALF_KELLY"])
    install_signal_schedule_parser.add_argument("--interval-minutes", type=int, default=15)
    install_signal_schedule_parser.set_defaults(func=install_paper_signal_schedule_cmd)

    controller_parser = subparsers.add_parser("run-controller")
    controller_parser.add_argument("--once", action="store_true")
    controller_parser.add_argument("--watch", action="store_true")
    controller_parser.set_defaults(func=run_controller_cmd)

    worker_parser = subparsers.add_parser("run-worker")
    worker_parser.add_argument("--queue", default="research")
    worker_parser.add_argument("--limit", type=int, default=1)
    worker_parser.set_defaults(func=run_worker_cmd)

    load_test_parser = subparsers.add_parser("load-test")
    load_test_parser.add_argument("--jobs", type=int, default=1000)
    load_test_parser.add_argument("--artifacts", type=int, default=1000)
    load_test_parser.set_defaults(func=load_test_cmd)

    research_loop_parser = subparsers.add_parser("run-research-loop")
    research_loop_parser.add_argument("--raw-dir", default="data/raw")
    research_loop_parser.add_argument("--broker", default="current_broker_demo")
    research_loop_parser.add_argument("--force", action="store_true")
    research_loop_parser.add_argument("--limit", type=int, default=1)
    research_loop_parser.add_argument("--queue-only", action="store_true")
    research_loop_parser.add_argument("--stage", choices=["smoke", "full"], default="smoke")
    research_loop_parser.add_argument("--window-months", type=int, default=6)
    research_loop_parser.add_argument("--skip-walk-forward", action="store_true")
    research_loop_parser.add_argument("--skip-forward-test", action="store_true")
    research_loop_parser.add_argument("--max-walk-forward-splits", type=int, default=None)
    research_loop_parser.add_argument("--from-date", default=None)
    research_loop_parser.add_argument("--to-date", default=None)
    research_loop_parser.set_defaults(func=run_research_loop_cmd)

    research_summary_parser = subparsers.add_parser("research-summary")
    research_summary_parser.add_argument("--limit", type=int, default=5)
    research_summary_parser.set_defaults(func=research_summary_cmd)

    ai_packet_parser = subparsers.add_parser("export-ai-review-packet")
    ai_packet_parser.add_argument("--output", default="runtime/ai_review_packet.md")
    ai_packet_parser.add_argument("--limit", type=int, default=10)
    ai_packet_parser.set_defaults(func=export_ai_review_packet_cmd)

    committee_parser = subparsers.add_parser("run-research-committee")
    committee_parser.add_argument("--strategy", required=True)
    committee_parser.add_argument("--symbol", required=True)
    committee_parser.add_argument("--timeframe", required=True)
    committee_parser.add_argument("--notes-file", default=None)
    committee_parser.add_argument("--output-dir", default="runtime")
    committee_parser.set_defaults(func=run_research_committee_cmd)

    fitter_parser = subparsers.add_parser("fit-strategy-filters")
    fitter_parser.add_argument("--limit", type=int, default=12)
    fitter_parser.add_argument("--output-dir", default="runtime")
    fitter_parser.add_argument("--skip-committee", action="store_true")
    fitter_parser.set_defaults(func=fit_strategy_filters_cmd)

    private_memory_parser = subparsers.add_parser("export-private-memory")
    private_memory_parser.add_argument("--strategy", default=None)
    private_memory_parser.add_argument("--symbol", default=None)
    private_memory_parser.add_argument("--timeframe", default=None)
    private_memory_parser.add_argument("--obsidian-root", default="obsidian/private_trading_memory")
    private_memory_parser.add_argument("--second-brain-root", default="second_brain/vault/01_hubs/private_trading_memory")
    private_memory_parser.set_defaults(func=export_private_memory_cmd)

    cot_parser = subparsers.add_parser("import-cot")
    cot_parser.add_argument("--file", required=True)
    cot_parser.add_argument("--symbol", required=True)
    cot_parser.add_argument("--date-column", default=None)
    cot_parser.add_argument("--market", default=None)
    cot_parser.add_argument("--market-column", default=None)
    cot_parser.set_defaults(func=import_cot_cmd)

    note_parser = subparsers.add_parser("import-positioning-note")
    note_parser.add_argument("--file", required=True)
    note_parser.add_argument("--symbol", required=True)
    note_parser.add_argument("--source", default="manual", choices=["manual", "codex", "chatgpt", "claude", "prime_broker"])
    note_parser.add_argument("--date", default=None)
    note_parser.set_defaults(func=import_positioning_note_cmd)

    positioning_parser = subparsers.add_parser("positioning-score")
    positioning_parser.add_argument("--symbol", required=True)
    positioning_parser.add_argument("--show-records", action="store_true")
    positioning_parser.add_argument("--limit", type=int, default=20)
    positioning_parser.set_defaults(func=positioning_score_cmd)

    queue_parser = subparsers.add_parser("queue-job")
    queue_parser.add_argument("--strategy", required=True)
    queue_parser.add_argument("--symbol", required=True)
    queue_parser.add_argument("--timeframe", required=True)
    queue_parser.add_argument("--file", required=True)
    queue_parser.add_argument("--broker", default="current_broker_demo")
    queue_parser.add_argument("--from-date", default=None)
    queue_parser.add_argument("--to-date", default=None)
    queue_parser.add_argument("--forward-from-date", default=None)
    queue_parser.add_argument("--skip-walk-forward", action="store_true")
    queue_parser.add_argument("--skip-forward-test", action="store_true")
    queue_parser.add_argument("--max-walk-forward-splits", type=int, default=100)
    queue_parser.add_argument("--research-stage", default="manual")
    queue_parser.set_defaults(func=queue_job_cmd)

    show_queue_parser = subparsers.add_parser("show-queue")
    show_queue_parser.set_defaults(func=show_queue_cmd)

    pipeline_parser = subparsers.add_parser("run-full-pipeline")
    pipeline_parser.add_argument("--strategy", required=True)
    pipeline_parser.add_argument("--symbol", required=True)
    pipeline_parser.add_argument("--timeframe", required=True)
    pipeline_parser.add_argument("--file", required=True)
    pipeline_parser.add_argument("--skip-walk-forward", action="store_true")
    pipeline_parser.add_argument("--skip-forward-test", action="store_true")
    pipeline_parser.add_argument("--force", action="store_true")
    pipeline_parser.add_argument("--broker", default="current_broker_demo")
    pipeline_parser.add_argument("--resume", action="store_true")
    pipeline_parser.add_argument("--max-walk-forward-splits", type=int, default=100)
    pipeline_parser.add_argument("--from-date", default=None)
    pipeline_parser.add_argument("--to-date", default=None)
    pipeline_parser.add_argument("--forward-from-date", default=None)
    pipeline_parser.set_defaults(func=run_full_pipeline_cmd)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

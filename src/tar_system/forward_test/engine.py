"""Incremental paper-only forward-test loop."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from tar_system.audit.writer import append_audit_event
from tar_system.backtest.metrics import calculate_metrics
from tar_system.data.store import filter_by_date_range, load_feature_data
from tar_system.data.validator import validate_ohlcv
from tar_system.dashboard.runtime_control import read_forward_status, write_status
from tar_system.environment.event_calendar import load_events
from tar_system.environment.risk_state import evaluate_environment
from tar_system.execution.paper_broker import PaperBroker
from tar_system.memory.strategy_memory import record_strategy_memory
from tar_system.portfolio.tracker import PortfolioTracker
from tar_system.regime.detector import detect_regime
from tar_system.risk.engine import RiskEngine
from tar_system.risk.position_sizer import size_position
from tar_system.scoring.scorer import score_strategy
from tar_system.settings import DEFAULT_INITIAL_CAPITAL
from tar_system.strategies.resolver import resolve_strategy
from tar_system.strategies.asset_variants import default_variant
from tar_system.strategies.regime_selector import recommend_strategy_for_regime
from tar_system.strategies.registry import get_strategy


@dataclass
class ForwardTestResult:
    strategy: str
    symbol: str
    timeframe: str
    broker: str
    processed_bars: int
    last_processed_timestamp: str | None
    metrics: dict[str, float]
    environment_state: str
    review_status: str = "REVIEW_ONLY"
    paper_only: bool = True
    stopped: bool = False


def state_path(strategy: str, symbol: str, timeframe: str) -> Path:
    return Path("runtime") / f"forward_test_{strategy}_{symbol}_{timeframe}.json"


def read_forward_state(strategy: str, symbol: str, timeframe: str) -> dict[str, object]:
    path = state_path(strategy, symbol, timeframe)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_forward_state(strategy: str, symbol: str, timeframe: str, state: dict[str, object]) -> Path:
    path = state_path(strategy, symbol, timeframe)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    return path


def run_forward_test(
    strategy_name: str,
    symbol: str,
    timeframe: str,
    broker: str = "current_broker_demo",
    from_date: str | None = None,
    reset_loss_guard: bool = False,
) -> ForwardTestResult:
    resolved = resolve_strategy(strategy_name, symbol, timeframe, broker, audit=True)
    features = load_feature_data(symbol, timeframe).sort_values("timestamp").reset_index(drop=True)
    validation = validate_ohlcv(features)
    if not validation.passed:
        append_audit_event("forward_test_validation", strategy_name, symbol, timeframe, "FAILED", ",".join(validation.reason_codes), {"errors": validation.errors})
        raise SystemExit(f"Forward-test data validation failed: {validation.errors}")
    previous_state = read_forward_state(strategy_name, symbol, timeframe)
    last_seen = previous_state.get("last_processed_timestamp")
    if last_seen:
        features = features[pd.to_datetime(features["timestamp"]) > pd.Timestamp(str(last_seen))]
    features = filter_by_date_range(features, from_date=from_date)
    if features.empty:
        result = ForwardTestResult(strategy_name, symbol, timeframe, broker, 0, str(last_seen) if last_seen else None, {}, "NO_NEW_BARS", "REVIEW_ONLY")
        _write_result(result)
        append_audit_event("forward_test", strategy_name, symbol, timeframe, "NO_NEW_BARS", "FORWARD_TEST_NO_NEW_BARS", asdict(result))
        return result

    latest_timestamp = pd.Timestamp(features["timestamp"].iloc[-1]).to_pydatetime()
    env = evaluate_environment(symbol, latest_timestamp, load_events())
    if env.state in {"BLOCK_TRADING", "HOLD_TRADING"}:
        result = ForwardTestResult(strategy_name, symbol, timeframe, broker, 0, str(last_seen) if last_seen else None, {}, env.state, "REVIEW_ONLY")
        _write_result(result)
        append_audit_event("forward_test", strategy_name, symbol, timeframe, "BLOCKED", env.state, {"reason_codes": env.reason_codes})
        return result

    existing_runtime_status = read_forward_status()
    write_status(
        "forward_test",
        {
            "running": True,
            "stop_requested": bool(existing_runtime_status.get("stop_requested")),
            "strategy": strategy_name,
            "symbol": symbol,
            "timeframe": timeframe,
            "mode": "forward_test",
            "latest_message": "running",
        },
    )
    portfolio = PortfolioTracker(DEFAULT_INITIAL_CAPITAL)
    if reset_loss_guard:
        portfolio.reset_loss_guard()
    risk = RiskEngine()
    paper_broker = PaperBroker(default_spread=resolved.asset_profile.spread_assumption, slippage_bps=resolved.asset_profile.slippage_bps())
    strategy_cache = {strategy_name: resolved.strategy}
    stopped = False
    processed = 0
    last_timestamp: str | None = None
    for _, row in features.iterrows():
        status = read_forward_status()
        if status.get("stop_requested"):
            stopped = True
            append_audit_event("forward_test", strategy_name, symbol, timeframe, "STOPPED", "STOP_REQUESTED", {"processed_bars": processed})
            break
        regime = detect_regime(row).value
        recommendation = recommend_strategy_for_regime(regime)
        if recommendation.recommended_strategy == "HOLD":
            append_audit_event("forward_test_regime_selector", strategy_name, symbol, timeframe, "HOLD", recommendation.reason, recommendation.__dict__)
            processed += 1
            last_timestamp = str(pd.Timestamp(row["timestamp"]))
            continue
        active_strategy_name = recommendation.recommended_strategy
        if active_strategy_name not in strategy_cache:
            variant = default_variant(active_strategy_name, symbol, timeframe)
            strategy_cache[active_strategy_name] = get_strategy(active_strategy_name, **variant.parameters)
        active_strategy = strategy_cache[active_strategy_name]
        signal = active_strategy.generate_signal(row, regime)
        signal.metadata["selector"] = recommendation.__dict__
        decision = risk.evaluate(
            signal,
            current_drawdown=portfolio.drawdown(),
            current_exposure=portfolio.exposure(),
            current_volatility=float(row.get("rolling_volatility", 0) or 0),
            consecutive_losses=portfolio.consecutive_losses(),
            daily_loss_pct=portfolio.daily_loss_pct(),
            weekly_loss_pct=portfolio.weekly_loss_pct(),
            loss_guard_status=portfolio.status,
        )
        append_audit_event("forward_test_risk", strategy_name, symbol, timeframe, "APPROVED" if decision.approved else "BLOCKED", decision.reason_code, {"regime": regime, "side": signal.side})
        if decision.approved:
            sizing = size_position(
                "ATR_BASED",
                symbol,
                signal.entry,
                portfolio.current_equity,
                resolved.broker_profile,
                resolved.asset_profile,
                atr=float(row.get("atr", 0) or 0),
                risk_pct=resolved.asset_profile.risk_limit,
            )
            if sizing.reason == "ASSET_CLASS_EXPOSURE_LIMIT":
                append_audit_event("forward_test_sizing", strategy_name, symbol, timeframe, "BLOCKED", sizing.reason, sizing.__dict__)
                processed += 1
                last_timestamp = str(pd.Timestamp(row["timestamp"]))
                continue
            margin = paper_broker.estimate_margin(signal, resolved.broker_profile, resolved.asset_profile, portfolio.current_equity, lot_size=sizing.recommended_lot)
            fill = paper_broker.execute(
                signal,
                broker_profile=resolved.broker_profile,
                contract_size=resolved.broker_profile.symbol_profile(symbol).contract_size,
                position_size=sizing,
            )
            portfolio.on_fill(fill)
            if portfolio.status == "PAUSED_HUMAN_RESET_REQUIRED":
                append_audit_event("loss_guard", strategy_name, symbol, timeframe, "PAUSED", portfolio.loss_guard_reason() or "PAUSED_HUMAN_RESET_REQUIRED", {"status": portfolio.status})
            append_audit_event("forward_test_fill", strategy_name, symbol, timeframe, "PAPER_FILL", "PAPER_FILL_CREATED", {**fill.metadata, "margin_utilisation": margin.margin_utilisation})
        processed += 1
        last_timestamp = str(pd.Timestamp(row["timestamp"]))
    metrics = calculate_metrics(portfolio.closed_trades, portfolio.equity_curve)
    score = score_strategy(metrics)
    review_status = "REVIEW_ONLY" if stopped or env.state in {"REVIEW_ONLY", "HOLD_TRADING", "BLOCK_TRADING"} else "TESTED"
    result = ForwardTestResult(strategy_name, symbol, timeframe, broker, processed, last_timestamp, metrics, env.state, review_status, stopped=stopped)
    _write_result(result)
    if last_timestamp and not stopped:
        write_forward_state(strategy_name, symbol, timeframe, {"last_processed_timestamp": last_timestamp, "metrics": metrics})
    portfolio.export_equity_curve(symbol, timeframe, strategy_name)
    write_status("forward_test", {"running": False, "stop_requested": False, "strategy": strategy_name, "symbol": symbol, "timeframe": timeframe, "mode": "forward_test", "latest_message": "completed", "latest_result_path": str(_result_path(strategy_name, symbol, timeframe))})
    if review_status == "TESTED":
        record_strategy_memory(
            base_strategy=strategy_name,
            variant_name=resolved.variant.variant_name,
            version=getattr(resolved.strategy, "version", ""),
            symbol=symbol,
            timeframe=timeframe,
            broker=broker,
            asset_profile=resolved.asset_profile.to_dict(),
            broker_profile=resolved.broker_profile.symbol_profile(symbol).to_dict(),
            parameters=resolved.variant.parameters,
            backtest_metrics={},
            walk_forward_metrics={},
            forward_test_metrics=metrics,
            score=score.score,
            verdict=score.verdict,
            reason_codes=score.reason_codes,
            notes="forward_test",
        )
    else:
        append_audit_event("forward_test_memory", strategy_name, symbol, timeframe, "SKIPPED", "REVIEW_ONLY", asdict(result))
    append_audit_event("forward_test", strategy_name, symbol, timeframe, "COMPLETED" if not stopped else "PARTIAL", "FORWARD_TEST_COMPLETED" if not stopped else "STOP_REQUESTED", asdict(result))
    return result


def _result_path(strategy: str, symbol: str, timeframe: str) -> Path:
    return Path("data/results") / f"{strategy}_{symbol}_{timeframe}_forward_test.json"


def _write_result(result: ForwardTestResult) -> Path:
    path = _result_path(result.strategy, result.symbol, result.timeframe)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return path

"""Generate latest paper signals with risk gates and local audit output."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.audit.writer import append_audit_event
from tar_system.controller.strategy_health_monitor import evaluate_strategy_health, is_strategy_active
from tar_system.data.store import load_feature_data
from tar_system.environment.event_calendar import load_events
from tar_system.environment.risk_state import evaluate_environment
from tar_system.portfolio.tracker import PortfolioTracker
from tar_system.regime.detector import detect_regime
from tar_system.risk.engine import RiskEngine
from tar_system.risk.position_sizer import size_position
from tar_system.settings import DEFAULT_INITIAL_CAPITAL
from tar_system.strategies.resolver import resolve_strategy

SIGNAL_LOG_PATH = Path("runtime") / "paper_signal_alerts.jsonl"
LATEST_SIGNAL_PATH = Path("runtime") / "latest_paper_signal.json"


@dataclass(frozen=True)
class PaperSignalRun:
    strategy: str
    symbol: str
    timeframe: str
    broker: str
    generated_at: str
    bar_timestamp: str | None
    health_status: str
    environment_state: str
    regime: str
    side: str
    confidence: float
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    risk_approved: bool
    risk_reason: str
    position_size: dict[str, Any]
    alert_ready: bool
    paper_only: bool = True


def run_paper_signal(
    strategy_name: str,
    symbol: str,
    timeframe: str,
    broker: str = "current_broker_demo",
    sizing_model: str = "ATR_BASED",
    force_health_check: bool = True,
) -> PaperSignalRun:
    """Generate one latest-bar paper signal and write local alert files."""
    if force_health_check:
        health = evaluate_strategy_health(strategy_name, symbol, timeframe)
    else:
        health = None
    health_status = health.status if health else "UNKNOWN"
    if not is_strategy_active(strategy_name, symbol, timeframe):
        result = _empty_result(strategy_name, symbol, timeframe, broker, health_status, "PAUSED", "HEALTH_PAUSED")
        _write_signal(result)
        return result

    features = load_feature_data(symbol, timeframe).sort_values("timestamp")
    if features.empty:
        result = _empty_result(strategy_name, symbol, timeframe, broker, health_status, "NO_DATA", "NO_FEATURE_ROWS")
        _write_signal(result)
        return result

    row = features.iloc[-1]
    resolved = resolve_strategy(strategy_name, symbol, timeframe, broker, audit=True)
    regime = detect_regime(row).value
    signal = resolved.strategy.generate_signal(row, regime)
    env = evaluate_environment(symbol, signal.timestamp.to_pydatetime(), load_events())
    if env.state in {"BLOCK_TRADING", "HOLD_TRADING"}:
        risk_approved = False
        risk_reason = env.state
        sizing_payload: dict[str, Any] = {}
    else:
        portfolio = PortfolioTracker(DEFAULT_INITIAL_CAPITAL)
        risk = RiskEngine()
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
        risk_approved = decision.approved
        risk_reason = decision.reason_code
        if decision.approved:
            sizing = size_position(
                sizing_model,
                symbol,
                signal.entry,
                DEFAULT_INITIAL_CAPITAL,
                resolved.broker_profile,
                resolved.asset_profile,
                stop_distance=_stop_distance(signal.entry, signal.stop_loss),
                atr=float(row.get("atr", 0) or 0),
                risk_pct=resolved.asset_profile.risk_limit,
            )
            sizing_payload = asdict(sizing)
        else:
            sizing_payload = {}

    result = PaperSignalRun(
        strategy=strategy_name,
        symbol=symbol,
        timeframe=timeframe,
        broker=broker,
        generated_at=datetime.now(timezone.utc).isoformat(),
        bar_timestamp=str(signal.timestamp),
        health_status=health_status,
        environment_state=env.state,
        regime=regime,
        side=signal.side,
        confidence=float(signal.confidence),
        entry=float(signal.entry),
        stop_loss=float(signal.stop_loss) if signal.stop_loss is not None else None,
        take_profit=float(signal.take_profit) if signal.take_profit is not None else None,
        risk_approved=risk_approved,
        risk_reason=risk_reason,
        position_size=sizing_payload,
        alert_ready=bool(risk_approved and signal.side != "HOLD"),
    )
    _write_signal(result)
    append_audit_event("paper_signal", strategy_name, symbol, timeframe, "READY" if result.alert_ready else "BLOCKED", result.risk_reason, asdict(result))
    return result


def _empty_result(strategy: str, symbol: str, timeframe: str, broker: str, health_status: str, environment_state: str, reason: str) -> PaperSignalRun:
    return PaperSignalRun(
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        broker=broker,
        generated_at=datetime.now(timezone.utc).isoformat(),
        bar_timestamp=None,
        health_status=health_status,
        environment_state=environment_state,
        regime="UNKNOWN",
        side="HOLD",
        confidence=0.0,
        entry=None,
        stop_loss=None,
        take_profit=None,
        risk_approved=False,
        risk_reason=reason,
        position_size={},
        alert_ready=False,
    )


def _write_signal(result: PaperSignalRun) -> None:
    payload = asdict(result)
    SIGNAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SIGNAL_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, default=str) + "\n")
    LATEST_SIGNAL_PATH.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _stop_distance(entry: float, stop_loss: float | None) -> float | None:
    if stop_loss is None:
        return None
    return abs(entry - stop_loss)

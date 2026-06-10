"""Paper strategy health monitoring and pause recommendations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system import settings
from tar_system.audit.writer import append_audit_event

STATUS_PATH = Path("runtime") / "strategy_health_status.json"
SIGNAL_LOG_PATH = Path("runtime") / "paper_signal_alerts.jsonl"


@dataclass(frozen=True)
class StrategyHealth:
    strategy: str
    symbol: str
    timeframe: str
    status: str
    reason_codes: list[str]
    recommendation: str
    metrics: dict[str, float]
    checked_at: str
    paper_only: bool = True


def evaluate_strategy_health(
    strategy: str,
    symbol: str,
    timeframe: str,
    metrics: dict[str, Any] | None = None,
    min_trades: int = 30,
    max_drawdown: float | None = None,
    min_profit_factor: float = 1.05,
    min_sharpe: float = 0.0,
    recent_signal_window: int = 20,
) -> StrategyHealth:
    """Evaluate recent paper metrics and recommend ACTIVE, WATCH or PAUSED."""
    resolved_metrics = _numeric_metrics(metrics or _load_latest_metrics(strategy, symbol, timeframe))
    rolling_metrics = _recent_signal_metrics(strategy, symbol, timeframe, recent_signal_window)
    resolved_metrics.update(rolling_metrics)
    drawdown_limit = settings.DEFAULT_MAX_DRAWDOWN if max_drawdown is None else max_drawdown
    reason_codes: list[str] = []

    total_trades = resolved_metrics.get("total_trades", 0.0)
    if total_trades < min_trades:
        reason_codes.append("HEALTH_SAMPLE_TOO_SMALL")
    if resolved_metrics.get("max_drawdown", 0.0) >= drawdown_limit:
        reason_codes.append("HEALTH_DRAWDOWN_LIMIT")
    if resolved_metrics.get("profit_factor", 0.0) < min_profit_factor:
        reason_codes.append("HEALTH_PROFIT_FACTOR_WEAK")
    if resolved_metrics.get("sharpe_ratio", 0.0) < min_sharpe:
        reason_codes.append("HEALTH_SHARPE_WEAK")
    if resolved_metrics.get("consecutive_losses", 0.0) >= settings.DEFAULT_MAX_CONSECUTIVE_LOSSES:
        reason_codes.append("HEALTH_CONSECUTIVE_LOSS_LIMIT")
    if resolved_metrics.get("daily_loss_pct", 0.0) >= settings.DEFAULT_DAILY_LOSS_LIMIT:
        reason_codes.append("HEALTH_DAILY_LOSS_LIMIT")
    if resolved_metrics.get("recent_signal_count", 0.0) >= 5 and resolved_metrics.get("recent_alert_ready", 0.0) == 0.0:
        reason_codes.append("HEALTH_NO_RECENT_APPROVED_SIGNALS")
    if resolved_metrics.get("recent_hard_blocks", 0.0) >= 3:
        reason_codes.append("HEALTH_RECENT_HARD_BLOCKS")

    hard_blocks = {"HEALTH_DRAWDOWN_LIMIT", "HEALTH_CONSECUTIVE_LOSS_LIMIT", "HEALTH_DAILY_LOSS_LIMIT", "HEALTH_RECENT_HARD_BLOCKS"}
    if any(code in hard_blocks for code in reason_codes):
        status = "PAUSED"
        recommendation = "Pause paper signals until reviewed"
    elif reason_codes:
        status = "WATCH"
        recommendation = "Keep paper-only and gather more evidence"
    else:
        status = "ACTIVE"
        recommendation = "Paper signal generation allowed"

    result = StrategyHealth(
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        status=status,
        reason_codes=reason_codes,
        recommendation=recommendation,
        metrics=resolved_metrics,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )
    _write_status(result)
    append_audit_event("strategy_health", strategy, symbol, timeframe, status, ",".join(reason_codes) or "HEALTH_OK", asdict(result))
    return result


def read_strategy_health(strategy: str, symbol: str, timeframe: str) -> StrategyHealth | None:
    rows = _read_all_status()
    payload = rows.get(_key(strategy, symbol, timeframe))
    return StrategyHealth(**payload) if payload else None


def is_strategy_active(strategy: str, symbol: str, timeframe: str) -> bool:
    health = read_strategy_health(strategy, symbol, timeframe)
    return health is None or health.status != "PAUSED"


def _load_latest_metrics(strategy: str, symbol: str, timeframe: str) -> dict[str, Any]:
    candidates = [
        Path("data/results") / f"{strategy}_{symbol}_{timeframe}_forward_test.json",
        Path("data/results") / f"{strategy}_{symbol}_{timeframe}_metrics.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload.get("metrics"), dict):
            return dict(payload["metrics"])
        return payload
    return {}


def _numeric_metrics(metrics: dict[str, Any]) -> dict[str, float]:
    numeric: dict[str, float] = {}
    for key, value in metrics.items():
        try:
            numeric[key] = float(value)
        except (TypeError, ValueError):
            continue
    return numeric


def _recent_signal_metrics(strategy: str, symbol: str, timeframe: str, limit: int) -> dict[str, float]:
    rows = _read_recent_signal_rows(strategy, symbol, timeframe, limit)
    hard_reasons = {
        "RISK_DRAWDOWN_LIMIT",
        "RISK_EXPOSURE_LIMIT",
        "RISK_VOLATILITY_CAP",
        "CONSECUTIVE_LOSS_LIMIT",
        "DAILY_LOSS_LIMIT",
        "WEEKLY_LOSS_LIMIT",
        "PAUSED_HUMAN_RESET_REQUIRED",
        "BLOCK_TRADING",
        "HOLD_TRADING",
    }
    return {
        "recent_signal_count": float(len(rows)),
        "recent_alert_ready": float(sum(1 for row in rows if row.get("alert_ready"))),
        "recent_hold_signals": float(sum(1 for row in rows if row.get("side") == "HOLD")),
        "recent_risk_rejected": float(sum(1 for row in rows if not row.get("risk_approved"))),
        "recent_hard_blocks": float(sum(1 for row in rows if str(row.get("risk_reason")) in hard_reasons)),
    }


def _read_recent_signal_rows(strategy: str, symbol: str, timeframe: str, limit: int) -> list[dict[str, Any]]:
    if not SIGNAL_LOG_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in SIGNAL_LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            row.get("strategy") == strategy
            and str(row.get("symbol", "")).upper() == symbol.upper()
            and str(row.get("timeframe", "")).upper() == timeframe.upper()
        ):
            rows.append(row)
    return rows[-limit:]


def _write_status(result: StrategyHealth) -> Path:
    rows = _read_all_status()
    rows[_key(result.strategy, result.symbol, result.timeframe)] = asdict(result)
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    return STATUS_PATH


def _read_all_status() -> dict[str, dict[str, Any]]:
    if not STATUS_PATH.exists():
        return {}
    try:
        payload = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _key(strategy: str, symbol: str, timeframe: str) -> str:
    return f"{strategy}:{symbol.upper()}:{timeframe.upper()}"

"""Event-driven backtest engine."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tar_system.assets.profiles import AssetProfile
from tar_system.audit.writer import append_audit_event
from tar_system.backtest.metrics import calculate_metrics
from tar_system.brokers.profiles import BrokerProfile
from tar_system.dashboard.runtime_control import read_backtest_status, write_status
from tar_system.execution.paper_broker import PaperBroker, timeframe_day_fraction
from tar_system.portfolio.tracker import PortfolioTracker
from tar_system.regime.detector import detect_regime
from tar_system.risk.engine import RiskEngine
from tar_system.settings import DEFAULT_INITIAL_CAPITAL
from tar_system.strategies.base import Strategy


@dataclass
class BacktestResult:
    metrics: dict[str, float]
    trades: int
    final_equity: float
    stopped: bool = False
    partial: bool = False
    reason_code: str | None = None


def run_backtest(
    features: pd.DataFrame,
    strategy: Strategy,
    initial_capital: float = DEFAULT_INITIAL_CAPITAL,
    audit_decisions: bool = True,
    broker_profile: BrokerProfile | None = None,
    asset_profile: AssetProfile | None = None,
    cost_multiplier: float = 1.0,
) -> BacktestResult:
    broker = PaperBroker()
    portfolio = PortfolioTracker(initial_capital)
    risk = RiskEngine()
    work = features.sort_values("timestamp").reset_index(drop=True)
    stopped = False
    reason_code: str | None = None
    for index, row in work.iterrows():
        status = read_backtest_status()
        if status.get("stop_requested"):
            stopped = True
            reason_code = "STOP_REQUESTED"
            append_audit_event(
                event_type="backtest_stopped",
                strategy=getattr(strategy, "name", "unknown"),
                symbol=str(row.get("symbol", "")),
                timeframe=str(row.get("timeframe", "")),
                decision="STOPPED",
                reason_code="STOP_REQUESTED",
                metadata={"partial_trades": len(portfolio.closed_trades)},
            )
            write_status("backtest", {**status, "running": False, "latest_message": "stopped safely with partial result"})
            break
        regime = detect_regime(row).value
        signal = strategy.generate_signal(row, regime)
        decision = risk.evaluate(
            signal,
            current_drawdown=portfolio.drawdown(),
            current_exposure=portfolio.exposure(),
            current_volatility=float(row.get("rolling_volatility", 0) or 0),
        )
        if audit_decisions:
            append_audit_event(
                event_type="risk_decision",
                strategy=signal.strategy,
                symbol=signal.symbol,
                timeframe=signal.timeframe,
                decision="APPROVED" if decision.approved else "BLOCKED",
                reason_code=decision.reason_code,
                metadata={"side": signal.side, "confidence": signal.confidence, "regime": regime},
            )
        if decision.approved:
            symbol_profile = broker_profile.symbol_profile(signal.symbol) if broker_profile else None
            # Close opposite-side positions for this symbol before opening new one
            opposite_side = "SELL" if signal.side == "BUY" else "BUY"
            for pos in list(portfolio.open_positions):
                if pos.symbol == signal.symbol and pos.side == opposite_side:
                    close_fill = broker.close_position(
                        pos,
                        pd.Timestamp(row["timestamp"]),
                        float(row.get("close", 0) or 0),
                        broker_profile=broker_profile,
                        contract_size=symbol_profile.contract_size if symbol_profile else None,
                        cost_multiplier=cost_multiplier,
                    )
                    portfolio.on_fill(close_fill)

            # Then open new position
            contract_size = symbol_profile.contract_size if symbol_profile else None
            quantity = _safe_backtest_quantity(
                float(signal.entry),
                portfolio.current_equity,
                contract_size=contract_size,
            )
            if quantity <= 0:
                continue
            fill = broker.execute(
                signal,
                quantity=quantity,
                spread=None if broker_profile else float(row.get("spread", 0) or 0),
                broker_profile=broker_profile,
                contract_size=contract_size,
                cost_multiplier=cost_multiplier,
            )
            portfolio.on_fill(fill)

    # Close any remaining open positions at the end of backtest.
    if work is not None and len(work) > 0 and portfolio.open_positions:
        final_row = work.iloc[-1]
        for pos in list(portfolio.open_positions):
            final_symbol_profile = broker_profile.symbol_profile(pos.symbol) if broker_profile else None
            close_fill = broker.close_position(
                pos,
                pd.Timestamp(final_row["timestamp"]),
                float(final_row.get("close", 0) or 0),
                broker_profile=broker_profile,
                contract_size=final_symbol_profile.contract_size if final_symbol_profile else None,
                cost_multiplier=cost_multiplier,
            )
            portfolio.on_fill(close_fill)

    metrics = calculate_metrics(portfolio.closed_trades, portfolio.equity_curve)
    if len(work):
        portfolio.export_equity_curve(str(work["symbol"].iloc[0]), str(work["timeframe"].iloc[0]), getattr(strategy, "name", "strategy"))
    return BacktestResult(metrics=metrics, trades=len(portfolio.closed_trades), final_equity=portfolio.current_equity, stopped=stopped, partial=stopped, reason_code=reason_code)


def _bars_held(opened_at: pd.Timestamp, closed_at: pd.Timestamp, timeframe: str) -> int:
    fraction = timeframe_day_fraction(timeframe)
    if fraction <= 0:
        return 1
    days = max((closed_at - opened_at).total_seconds() / 86400, 0)
    return max(1, int(round(days / fraction)))


def _safe_backtest_quantity(entry_price: float, equity: float, contract_size: float | None = None) -> float:
    """Clamp paper backtest notional so one trade cannot exceed account scale."""

    if entry_price <= 0 or equity <= 0:
        return 0.0
    resolved_contract_size = contract_size if contract_size is not None else 1.0
    max_notional = equity * 0.10
    max_quantity = max_notional / max(entry_price * resolved_contract_size, 1e-9)
    return round(max(0.0, min(1.0, max_quantity)), 8)

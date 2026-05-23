"""Simple portfolio and trade tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

import pandas as pd

from tar_system.execution.paper_broker import Fill
from tar_system import reason_codes as rc
from tar_system import settings


@dataclass
class Position:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    timestamp: pd.Timestamp
    entry_cost: float = 0.0
    take_profit: float | None = None
    stop_loss: float | None = None
    contract_size: float = 1.0


@dataclass
class Trade:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    opened_at: pd.Timestamp
    closed_at: pd.Timestamp
    swap_cost: float = 0.0
    days_held: float = 0.0
    slippage_cost: float = 0.0
    spread_cost: float = 0.0
    total_cost: float = 0.0
    net_pnl: float = 0.0


@dataclass
class PortfolioTracker:
    initial_capital: float
    cash: float | None = None
    open_positions: list[Position] = field(default_factory=list)
    closed_trades: list[Trade] = field(default_factory=list)
    equity_curve: list[tuple[pd.Timestamp, float]] = field(default_factory=list)
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        if self.cash is None:
            self.cash = self.initial_capital

    @property
    def realised_pnl(self) -> float:
        return sum(trade.pnl for trade in self.closed_trades)

    @property
    def current_equity(self) -> float:
        return float(self.initial_capital + self.realised_pnl)

    def exposure(self) -> float:
        notional = sum(position.quantity * position.entry_price for position in self.open_positions)
        return notional / self.current_equity if self.current_equity else 0.0

    def drawdown(self) -> float:
        if not self.equity_curve:
            return 0.0
        equities = [equity for _, equity in self.equity_curve]
        peak = max(equities)
        return (peak - equities[-1]) / peak if peak else 0.0

    def on_fill(self, fill: Fill) -> None:
        opposite = "SELL" if fill.side == "BUY" else "BUY"
        existing = next((pos for pos in self.open_positions if pos.symbol == fill.symbol and pos.side == opposite), None)
        if existing:
            gross_pnl = (fill.price - existing.entry_price) * existing.quantity * existing.contract_size
            if existing.side == "SELL":
                gross_pnl *= -1
            total_cost = existing.entry_cost + fill.total_cost
            pnl = gross_pnl - total_cost
            self.open_positions.remove(existing)
            self.closed_trades.append(
                Trade(
                    fill.symbol,
                    existing.side,
                    existing.quantity,
                    existing.entry_price,
                    fill.price,
                    pnl,
                    existing.timestamp,
                    fill.timestamp,
                    swap_cost=fill.swap_cost,
                    days_held=fill.days_held,
                    slippage_cost=fill.slippage_cost,
                    spread_cost=fill.spread_cost,
                    total_cost=total_cost,
                    net_pnl=pnl,
                )
            )
        else:
            tp = fill.metadata.get("take_profit") if fill.metadata else None
            sl = fill.metadata.get("stop_loss") if fill.metadata else None
            cs = float(fill.metadata.get("contract_size") or 1.0) if fill.metadata else 1.0
            self.open_positions.append(Position(fill.symbol, fill.side, fill.quantity, fill.price, fill.timestamp, fill.total_cost, take_profit=tp, stop_loss=sl, contract_size=cs))
        self.equity_curve.append((fill.timestamp, self.current_equity))
        self._update_loss_guard()

    def unrealised_pnl(self, mark_price: float | None = None) -> float:
        if mark_price is None:
            return 0.0
        total = 0.0
        for position in self.open_positions:
            pnl = (mark_price - position.entry_price) * position.quantity
            total += pnl if position.side == "BUY" else -pnl
        return total

    def win_rate(self) -> float:
        if not self.closed_trades:
            return 0.0
        wins = sum(1 for trade in self.closed_trades if trade.pnl > 0)
        return wins / len(self.closed_trades)

    def profit_factor(self) -> float:
        wins = sum(trade.pnl for trade in self.closed_trades if trade.pnl > 0)
        losses = abs(sum(trade.pnl for trade in self.closed_trades if trade.pnl < 0))
        return wins / losses if losses else (wins if wins else 0.0)

    def consecutive_losses(self) -> int:
        count = 0
        for trade in reversed(self.closed_trades):
            if trade.pnl < 0:
                count += 1
            elif trade.pnl > 0:
                break
        return count

    def daily_loss_pct(self) -> float:
        if not self.closed_trades:
            return 0.0
        latest = self.closed_trades[-1].closed_at.date()
        loss = -sum(min(0.0, trade.pnl) for trade in self.closed_trades if trade.closed_at.date() == latest)
        return loss / self.initial_capital if self.initial_capital else 0.0

    def weekly_loss_pct(self) -> float:
        if not self.closed_trades:
            return 0.0
        latest = self.closed_trades[-1].closed_at.isocalendar()[:2]
        loss = -sum(min(0.0, trade.pnl) for trade in self.closed_trades if trade.closed_at.isocalendar()[:2] == latest)
        return loss / self.initial_capital if self.initial_capital else 0.0

    def loss_guard_reason(self) -> str | None:
        if self.consecutive_losses() >= settings.DEFAULT_MAX_CONSECUTIVE_LOSSES:
            return rc.CONSECUTIVE_LOSS_LIMIT
        if self.daily_loss_pct() >= settings.DEFAULT_DAILY_LOSS_LIMIT:
            return rc.DAILY_LOSS_LIMIT
        if self.weekly_loss_pct() >= settings.DEFAULT_WEEKLY_LOSS_LIMIT:
            return rc.WEEKLY_LOSS_LIMIT
        return None

    def reset_loss_guard(self) -> None:
        self.status = "ACTIVE"

    def export_equity_curve(self, symbol: str, timeframe: str, strategy: str) -> Path:
        path = Path("data/results") / f"{symbol}_{timeframe}_{strategy}_equity.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, object]] = []
        cumulative_pnl = 0.0
        cumulative_cost = 0.0
        peak = self.initial_capital
        for trade in self.closed_trades:
            cumulative_pnl += trade.pnl
            cumulative_cost += trade.total_cost
            equity = self.initial_capital + cumulative_pnl
            peak = max(peak, equity)
            rows.append(
                {
                    "timestamp": trade.closed_at.isoformat(),
                    "equity": equity,
                    "drawdown_pct": (peak - equity) / peak if peak else 0.0,
                    "cumulative_pnl": cumulative_pnl,
                    "cumulative_cost": cumulative_cost,
                    "open_positions_count": len(self.open_positions),
                }
            )
        path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
        return path

    def _update_loss_guard(self) -> None:
        if self.loss_guard_reason():
            self.status = rc.PAUSED_HUMAN_RESET_REQUIRED

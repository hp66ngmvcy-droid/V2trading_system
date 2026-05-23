"""Backtest metric calculations."""

from __future__ import annotations

import math

from tar_system.portfolio.tracker import Trade


def calculate_metrics(trades: list[Trade], equity_curve: list[tuple[object, float]]) -> dict[str, object]:
    total = len(trades)
    pnls = [float(getattr(trade, "net_pnl", trade.pnl) or trade.pnl) for trade in trades]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    total_cost = sum(getattr(trade, "total_cost", 0.0) for trade in trades)
    swap_cost = sum(abs(getattr(trade, "swap_cost", 0.0)) for trade in trades)
    equities = [equity for _, equity in equity_curve]
    max_drawdown = 0.0
    peak = equities[0] if equities else 0.0
    for equity in equities:
        peak = max(peak, equity)
        if peak:
            max_drawdown = max(max_drawdown, (peak - equity) / peak)
    returns = [_trade_return(trade, pnl) for trade, pnl in zip(trades, pnls)]
    sharpe = _sharpe(returns)
    sortino = _sortino(returns)
    annual_return = (sum(returns) / len(returns) * 252) if returns else 0.0
    consecutive_wins, consecutive_losses, max_consecutive_losses = _consecutive_counts(pnls)
    net_profit = sum(pnls)
    return {
        "total_trades": float(total),
        "win_rate": len(wins) / total if total else 0.0,
        "profit_factor": gross_win / gross_loss if gross_loss else (gross_win if gross_win else 0.0),
        "max_drawdown": max_drawdown,
        "expectancy": net_profit / total if total else 0.0,
        "average_win": gross_win / len(wins) if wins else 0.0,
        "average_loss": sum(losses) / len(losses) if losses else 0.0,
        "gross_profit": gross_win,
        "gross_loss": gross_loss,
        "total_cost": total_cost,
        "swap_cost": swap_cost,
        "net_profit": net_profit,
        "trade_returns": returns,
        "trade_pnls": pnls,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "calmar_ratio": annual_return / max_drawdown if max_drawdown else 0.0,
        "consecutive_wins": float(consecutive_wins),
        "consecutive_losses": float(consecutive_losses),
        "max_consecutive_losses": float(max_consecutive_losses),
        "recovery_factor": net_profit / max_drawdown if max_drawdown else 0.0,
    }


def _trade_return(trade: Trade, pnl: float) -> float:
    cs = float(getattr(trade, "contract_size", 1.0) or 1.0)
    basis = abs(float(trade.entry_price) * float(trade.quantity) * cs)
    return pnl / basis if basis else 0.0


def _sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((item - mean) ** 2 for item in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    return mean / std * math.sqrt(252) if std else 0.0


def _sortino(returns: list[float]) -> float:
    if not returns:
        return 0.0
    mean = sum(returns) / len(returns)
    downside = [min(0.0, item) for item in returns]
    downside_deviation = math.sqrt(sum(item**2 for item in downside) / len(returns))
    return mean / downside_deviation * math.sqrt(252) if downside_deviation else 0.0


def _consecutive_counts(pnls: list[float]) -> tuple[int, int, int]:
    current_wins = 0
    current_losses = 0
    max_losses = 0
    for pnl in pnls:
        if pnl > 0:
            current_wins += 1
            current_losses = 0
        elif pnl < 0:
            current_losses += 1
            current_wins = 0
            max_losses = max(max_losses, current_losses)
        else:
            current_wins = 0
            current_losses = 0
    return current_wins, current_losses, max_losses

"""Read-only replay summaries for clear-read paper ideas."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Iterable

import pandas as pd

from tar_system.regime.detector import detect_regime
from tar_system.signals.clear_read import ClearRead, generate_clear_read, generate_trend_continuation_read


ReadFn = Callable[[pd.Series, str, dict[str, object]], ClearRead]


@dataclass(frozen=True)
class MovementStats:
    count: int = 0
    avg_favorable_pct: float = 0.0
    avg_adverse_pct: float = 0.0
    avg_net_exit_pct: float = 0.0
    median_favorable_pct: float = 0.0
    median_adverse_pct: float = 0.0
    median_net_exit_pct: float = 0.0
    win_rate_after_cost: float = 0.0


@dataclass(frozen=True)
class ReplaySummary:
    symbol: str
    timeframe: str
    rows: int
    horizons: tuple[int, ...]
    side_counts: dict[str, int]
    movement: dict[str, dict[int, MovementStats]] = field(default_factory=dict)
    paper_only: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "rows": self.rows,
            "horizons": list(self.horizons),
            "side_counts": dict(self.side_counts),
            "movement": {
                side: {str(horizon): stats.__dict__ for horizon, stats in horizons.items()}
                for side, horizons in self.movement.items()
            },
            "paper_only": self.paper_only,
        }


@dataclass(frozen=True)
class EquitySequenceSummary:
    symbol: str
    timeframe: str
    side: str
    horizon: int
    trades: int
    cumulative_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    avg_trade_pct: float = 0.0
    median_trade_pct: float = 0.0
    profit_factor: float = 0.0
    final_equity: float = 1.0
    paper_only: bool = True

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def compare_clear_read_modes(
    features: pd.DataFrame,
    horizons: Iterable[int] = (4, 8, 24),
    risk_context: dict[str, object] | None = None,
    cost_bps: float = 10.0,
) -> dict[str, ReplaySummary]:
    """Compare strict sweep and trend-continuation reads without writing files."""

    ordered = features.sort_values("timestamp").reset_index(drop=True)
    resolved_horizons = tuple(int(h) for h in horizons)
    context = risk_context or {"risk_approved": True, "risk_reason": "PAPER_REPLAY"}
    return {
        "strict_sweep": _summarise_mode(ordered, resolved_horizons, context, generate_clear_read, cost_bps),
        "trend_continuation": _summarise_mode(ordered, resolved_horizons, context, generate_trend_continuation_read, cost_bps),
    }


def sequence_trend_continuation_equity(
    features: pd.DataFrame,
    side: str = "LONG",
    horizon: int = 24,
    risk_context: dict[str, object] | None = None,
    cost_bps: float = 10.0,
    max_rolling_volatility: float | None = None,
    max_atr_pct: float | None = None,
) -> EquitySequenceSummary:
    """Sequence non-overlapping fixed-horizon paper trades for one side only."""

    ordered = features.sort_values("timestamp").reset_index(drop=True)
    context = risk_context or {"risk_approved": True, "risk_reason": "PAPER_REPLAY"}
    target_side = side.upper()
    if target_side not in {"LONG", "SHORT"}:
        raise ValueError("side must be LONG or SHORT")

    returns: list[float] = []
    equity_curve = [1.0]
    index = 0
    while index < len(ordered) - horizon:
        row = ordered.iloc[index]
        if _entry_blocked_by_volatility(row, max_rolling_volatility, max_atr_pct):
            index += 1
            continue
        read = generate_trend_continuation_read(row, detect_regime(row).value, context)
        if read.side != target_side or read.entry_reference is None:
            index += 1
            continue
        window = ordered.iloc[index + 1 : index + 1 + horizon]
        if len(window) < horizon:
            break
        _, _, net_pct = _movement(target_side, float(read.entry_reference), window, cost_bps)
        returns.append(net_pct)
        equity_curve.append(equity_curve[-1] * (1 + net_pct / 100.0))
        index += horizon

    symbol = str(ordered["symbol"].iloc[0]) if "symbol" in ordered and not ordered.empty else "UNKNOWN"
    timeframe = str(ordered["timeframe"].iloc[0]) if "timeframe" in ordered and not ordered.empty else "UNKNOWN"
    return _equity_summary(symbol, timeframe, target_side, int(horizon), returns, equity_curve)


def split_trend_continuation_equity_by_year(
    features: pd.DataFrame,
    side: str = "LONG",
    horizon: int = 24,
    risk_context: dict[str, object] | None = None,
    cost_bps: float = 10.0,
    max_rolling_volatility: float | None = None,
    max_atr_pct: float | None = None,
) -> dict[int, EquitySequenceSummary]:
    """Run the same paper-only equity sequence separately for each calendar year."""

    if "timestamp" not in features:
        return {}
    ordered = features.sort_values("timestamp").copy()
    years = pd.to_datetime(ordered["timestamp"]).dt.year
    results: dict[int, EquitySequenceSummary] = {}
    for year in sorted(int(value) for value in years.dropna().unique()):
        split = ordered[years == year].copy()
        results[year] = sequence_trend_continuation_equity(
            split,
            side=side,
            horizon=horizon,
            risk_context=risk_context,
            cost_bps=cost_bps,
            max_rolling_volatility=max_rolling_volatility,
            max_atr_pct=max_atr_pct,
        )
    return results


def compare_trend_continuation_with_confirmation(
    primary_features: pd.DataFrame,
    confirmation_features: pd.DataFrame,
    horizons: Iterable[int] = (4, 8, 24),
    risk_context: dict[str, object] | None = None,
    cost_bps: float = 10.0,
    confirmation_lookback_minutes: int = 60,
) -> dict[str, ReplaySummary]:
    """Compare H1 trend continuation with a lower-timeframe confirmation gate."""

    primary = primary_features.sort_values("timestamp").reset_index(drop=True)
    confirmation = _precompute_confirmation_reads(confirmation_features, risk_context)
    resolved_horizons = tuple(int(h) for h in horizons)
    context = risk_context or {"risk_approved": True, "risk_reason": "PAPER_REPLAY"}

    def confirmed_read(row: pd.Series, regime: str, inner_context: dict[str, object]) -> ClearRead:
        base = generate_trend_continuation_read(row, regime, inner_context)
        if base.side not in {"LONG", "SHORT"} or base.timestamp is None:
            return base
        if _confirmed_by_lower_timeframe(base.side, base.timestamp, confirmation, confirmation_lookback_minutes):
            return ClearRead(
                timestamp=base.timestamp,
                symbol=base.symbol,
                timeframe=base.timeframe,
                side=base.side,
                confidence=base.confidence,
                reasons=[*base.reasons, "CLEAR_READ_M15_CONFIRMED"],
                entry_reference=base.entry_reference,
                risk_approved=base.risk_approved,
                risk_reason=base.risk_reason,
                metadata={**base.metadata, "confirmation": "M15_CONFIRMED"},
            )
        return ClearRead(
            timestamp=base.timestamp,
            symbol=base.symbol,
            timeframe=base.timeframe,
            side="WAIT",
            confidence=0.0,
            reasons=["CLEAR_READ_M15_CONFIRMATION_BLOCK"],
            entry_reference=base.entry_reference,
            risk_approved=base.risk_approved,
            risk_reason=base.risk_reason,
            metadata={**base.metadata, "original_side": base.side, "confirmation": "M15_BLOCKED"},
        )

    return {
        "trend_continuation": _summarise_mode(primary, resolved_horizons, context, generate_trend_continuation_read, cost_bps),
        "trend_continuation_m15_confirmed": _summarise_mode(primary, resolved_horizons, context, confirmed_read, cost_bps),
    }


def _summarise_mode(
    features: pd.DataFrame,
    horizons: tuple[int, ...],
    risk_context: dict[str, object],
    read_fn: ReadFn,
    cost_bps: float,
) -> ReplaySummary:
    side_counts: Counter[str] = Counter()
    moves: dict[str, dict[int, list[tuple[float, float, float]]]] = {"LONG": {h: [] for h in horizons}, "SHORT": {h: [] for h in horizons}}
    for index, row in features.iterrows():
        read = read_fn(row, detect_regime(row).value, risk_context)
        side_counts[read.side] += 1
        if read.side not in {"LONG", "SHORT"} or read.entry_reference is None:
            continue
        for horizon in horizons:
            window = features.iloc[index + 1 : index + 1 + horizon]
            if len(window) < horizon:
                continue
            moves[read.side][horizon].append(_movement(read.side, float(read.entry_reference), window, cost_bps))

    movement = {
        side: {horizon: _movement_stats(values) for horizon, values in horizon_values.items()}
        for side, horizon_values in moves.items()
    }
    symbol = str(features["symbol"].iloc[0]) if "symbol" in features and not features.empty else "UNKNOWN"
    timeframe = str(features["timeframe"].iloc[0]) if "timeframe" in features and not features.empty else "UNKNOWN"
    return ReplaySummary(
        symbol=symbol,
        timeframe=timeframe,
        rows=len(features),
        horizons=horizons,
        side_counts=dict(side_counts),
        movement=movement,
    )


def _precompute_confirmation_reads(
    confirmation_features: pd.DataFrame,
    risk_context: dict[str, object] | None,
) -> pd.DataFrame:
    context = risk_context or {"risk_approved": True, "risk_reason": "PAPER_REPLAY"}
    rows: list[dict[str, object]] = []
    for _, row in confirmation_features.sort_values("timestamp").iterrows():
        read = generate_trend_continuation_read(row, detect_regime(row).value, context)
        if read.timestamp is None:
            continue
        rows.append({"timestamp": read.timestamp, "side": read.side})
    return pd.DataFrame(rows)


def _confirmed_by_lower_timeframe(
    side: str,
    timestamp: pd.Timestamp,
    confirmation_reads: pd.DataFrame,
    lookback_minutes: int,
) -> bool:
    if confirmation_reads.empty:
        return False
    end = pd.Timestamp(timestamp)
    start = end - pd.Timedelta(minutes=lookback_minutes)
    window = confirmation_reads[(confirmation_reads["timestamp"] <= end) & (confirmation_reads["timestamp"] > start)]
    if window.empty:
        return False
    counts = window["side"].value_counts()
    return int(counts.get(side, 0)) >= 2 and int(counts.get(side, 0)) > int(counts.get("WAIT", 0))


def _entry_blocked_by_volatility(
    row: pd.Series,
    max_rolling_volatility: float | None,
    max_atr_pct: float | None,
) -> bool:
    if max_rolling_volatility is not None:
        rolling_volatility = row.get("rolling_volatility")
        if pd.isna(rolling_volatility) or float(rolling_volatility) > max_rolling_volatility:
            return True
    if max_atr_pct is not None:
        close = float(row.get("close", 0) or 0)
        atr = row.get("atr")
        if close <= 0 or pd.isna(atr) or (float(atr) / close) > max_atr_pct:
            return True
    return False


def _equity_summary(
    symbol: str,
    timeframe: str,
    side: str,
    horizon: int,
    returns: list[float],
    equity_curve: list[float],
) -> EquitySequenceSummary:
    if not returns:
        return EquitySequenceSummary(symbol=symbol, timeframe=timeframe, side=side, horizon=horizon, trades=0)
    returns_series = pd.Series(returns, dtype=float)
    wins = returns_series[returns_series > 0]
    losses = returns_series[returns_series < 0]
    gross_win = float(wins.sum())
    gross_loss = abs(float(losses.sum()))
    peak = equity_curve[0]
    max_drawdown = 0.0
    for equity in equity_curve:
        peak = max(peak, equity)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - equity) / peak)
    final_equity = float(equity_curve[-1])
    return EquitySequenceSummary(
        symbol=symbol,
        timeframe=timeframe,
        side=side,
        horizon=horizon,
        trades=len(returns),
        cumulative_return_pct=round((final_equity - 1.0) * 100, 4),
        max_drawdown_pct=round(max_drawdown * 100, 4),
        win_rate=round(float((returns_series > 0).mean()), 4),
        avg_trade_pct=round(float(returns_series.mean()), 4),
        median_trade_pct=round(float(returns_series.median()), 4),
        profit_factor=round(gross_win / gross_loss, 4) if gross_loss else round(gross_win, 4),
        final_equity=round(final_equity, 6),
    )


def _movement(side: str, entry: float, window: pd.DataFrame, cost_bps: float) -> tuple[float, float, float]:
    exit_close = float(window["close"].iloc[-1])
    cost_pct = float(cost_bps) / 100.0
    if side == "LONG":
        favorable = ((float(window["high"].max()) - entry) / entry) * 100
        adverse = ((entry - float(window["low"].min())) / entry) * 100
        net_exit = ((exit_close - entry) / entry) * 100 - cost_pct
        return favorable, adverse, net_exit
    favorable = ((entry - float(window["low"].min())) / entry) * 100
    adverse = ((float(window["high"].max()) - entry) / entry) * 100
    net_exit = ((entry - exit_close) / entry) * 100 - cost_pct
    return favorable, adverse, net_exit


def _movement_stats(values: list[tuple[float, float, float]]) -> MovementStats:
    if not values:
        return MovementStats()
    favorable = pd.Series([item[0] for item in values], dtype=float)
    adverse = pd.Series([item[1] for item in values], dtype=float)
    net_exit = pd.Series([item[2] for item in values], dtype=float)
    return MovementStats(
        count=len(values),
        avg_favorable_pct=round(float(favorable.mean()), 4),
        avg_adverse_pct=round(float(adverse.mean()), 4),
        avg_net_exit_pct=round(float(net_exit.mean()), 4),
        median_favorable_pct=round(float(favorable.median()), 4),
        median_adverse_pct=round(float(adverse.median()), 4),
        median_net_exit_pct=round(float(net_exit.median()), 4),
        win_rate_after_cost=round(float((net_exit > 0).mean()), 4),
    )

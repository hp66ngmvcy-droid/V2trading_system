"""Slice a strategy's trade log by categorical dimensions and report PF/WR/count per bucket."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd

from tar_system.data.store import load_feature_data
from tar_system.regime.detector import detect_regime
from tar_system.strategies.resolver import resolve_strategy


VALID_DIMENSIONS = {"regime", "session", "atr_pct"}


@dataclass
class BucketRow:
    bucket: str
    value: str
    count: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float


def _bucket_trades(features: pd.DataFrame, strategy_obj: object, dimensions: Sequence[str]) -> list[dict]:
    """Replay signal generation row-by-row; record trade outcome + bucket labels."""
    atr_series = features["atr"].dropna()
    atr_quantiles = atr_series.quantile([0.33, 0.67])
    q33, q67 = float(atr_quantiles.iloc[0]), float(atr_quantiles.iloc[1])

    records = []
    open_position: dict | None = None

    for _, row in features.sort_values("timestamp").iterrows():
        # Check open position exit first
        if open_position is not None:
            bar_high = float(row.get("high", 0) or 0)
            bar_low = float(row.get("low", 0) or 0)
            tp = open_position.get("take_profit")
            sl = open_position.get("stop_loss")
            exit_price = None
            if open_position["side"] == "BUY":
                if sl and bar_low <= sl:
                    exit_price = sl
                elif tp and bar_high >= tp:
                    exit_price = tp
            else:
                if sl and bar_high >= sl:
                    exit_price = sl
                elif tp and bar_low <= tp:
                    exit_price = tp
            if exit_price is not None:
                pnl = (exit_price - open_position["entry"]) if open_position["side"] == "BUY" else (open_position["entry"] - exit_price)
                open_position["pnl"] = pnl
                records.append(open_position)
                open_position = None

        regime = detect_regime(row).value
        signal = strategy_obj.generate_signal(row, regime)
        if signal.side not in ("BUY", "SELL"):
            continue
        if open_position is not None:
            continue  # one position at a time

        atr = float(row.get("atr") or 0)
        if atr <= q33:
            atr_label = "LOW"
        elif atr <= q67:
            atr_label = "MED"
        else:
            atr_label = "HIGH"

        open_position = {
            "side": signal.side,
            "entry": signal.entry,
            "take_profit": signal.take_profit,
            "stop_loss": signal.stop_loss,
            "regime": regime,
            "session": str(row.get("session_label", "UNKNOWN")),
            "atr_pct": atr_label,
            "pnl": None,
        }

    return [r for r in records if r["pnl"] is not None]


def _compute_bucket(trades: list[dict], dimension: str) -> list[BucketRow]:
    by_value: dict[str, list[float]] = {}
    for t in trades:
        val = str(t.get(dimension, "UNKNOWN"))
        by_value.setdefault(val, []).append(float(t["pnl"]))

    rows = []
    for val, pnls in sorted(by_value.items()):
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        win_rate = len(wins) / len(pnls) if pnls else 0.0
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = gross_win / gross_loss if gross_loss else (gross_win if gross_win else 0.0)
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        rows.append(BucketRow(
            bucket=dimension,
            value=val,
            count=len(pnls),
            win_rate=round(win_rate, 4),
            profit_factor=round(profit_factor, 4),
            avg_win=round(avg_win, 4),
            avg_loss=round(avg_loss, 4),
        ))
    return rows


def _print_table(rows: list[BucketRow], dimension: str) -> None:
    print(f"\n--- Bucket: {dimension} ---")
    print(f"{'Value':<12} {'Count':>6} {'WR%':>7} {'PF':>7} {'AvgWin':>10} {'AvgLoss':>10}")
    for r in rows:
        print(f"{r.value:<12} {r.count:>6} {r.win_rate*100:>6.1f}% {r.profit_factor:>7.2f} {r.avg_win:>10.2f} {r.avg_loss:>10.2f}")


def analyze_buckets(
    strategy: str,
    symbol: str,
    timeframe: str,
    dimensions: Sequence[str],
    broker: str = "current_broker_demo",
) -> list[BucketRow]:
    invalid = set(dimensions) - VALID_DIMENSIONS
    if invalid:
        raise ValueError(f"Unknown dimensions: {invalid}. Valid: {VALID_DIMENSIONS}")

    features = load_feature_data(symbol, timeframe)
    resolved = resolve_strategy(strategy, symbol, timeframe, broker, audit=False)
    strategy_obj = resolved.strategy

    trades = _bucket_trades(features, strategy_obj, dimensions)
    print(f"Total trades replayed: {len(trades)}")

    all_rows: list[BucketRow] = []
    for dim in dimensions:
        rows = _compute_bucket(trades, dim)
        _print_table(rows, dim)
        all_rows.extend(rows)

    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"bucket_analysis_{strategy}_{symbol}_{timeframe}.json"
    out_path.write_text(
        json.dumps(
            [{"bucket": r.bucket, "value": r.value, "count": r.count,
              "win_rate": r.win_rate, "profit_factor": r.profit_factor,
              "avg_win": r.avg_win, "avg_loss": r.avg_loss}
             for r in all_rows],
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSaved: {out_path}")
    return all_rows

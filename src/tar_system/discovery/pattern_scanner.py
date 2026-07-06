"""Event-study pattern scanner for candidate discovery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class HorizonStats:
    horizon: int
    events: int
    mean_return: float
    median_return: float
    hit_rate: float
    expectancy: float


@dataclass(frozen=True)
class PatternStudy:
    pattern_name: str
    symbol: str
    timeframe: str
    total_rows: int
    total_events: int
    horizon_stats: list[HorizonStats]


def run_event_study(
    features: pd.DataFrame,
    event_mask: pd.Series | Iterable[bool],
    pattern_name: str,
    horizons: Iterable[int] = (1, 4, 16),
) -> PatternStudy:
    """Measure forward returns after a pattern event without using future data in the event."""
    if "close" not in features.columns:
        raise ValueError("features must include close")
    prepared = features.copy()
    prepared["_pattern_event"] = pd.Series(event_mask, index=features.index).astype(bool)
    ordered = prepared.sort_values("timestamp").reset_index(drop=True)
    mask = ordered.pop("_pattern_event")
    symbol = str(ordered["symbol"].iloc[0]) if "symbol" in ordered.columns and len(ordered) else ""
    timeframe = str(ordered["timeframe"].iloc[0]) if "timeframe" in ordered.columns and len(ordered) else ""

    stats: list[HorizonStats] = []
    for horizon in horizons:
        h = int(horizon)
        if h <= 0:
            continue
        forward_return = ordered["close"].shift(-h) / ordered["close"] - 1.0
        sampled = forward_return[mask & forward_return.notna()]
        wins = sampled[sampled > 0]
        losses = sampled[sampled <= 0]
        stats.append(
            HorizonStats(
                horizon=h,
                events=int(sampled.count()),
                mean_return=round(float(sampled.mean() or 0.0), 8),
                median_return=round(float(sampled.median() or 0.0), 8),
                hit_rate=round(float((sampled > 0).mean() or 0.0), 4),
                expectancy=round(float(wins.mean() or 0.0) + float(losses.mean() or 0.0), 8),
            )
        )

    return PatternStudy(
        pattern_name=pattern_name,
        symbol=symbol,
        timeframe=timeframe,
        total_rows=len(ordered),
        total_events=int(mask.sum()),
        horizon_stats=stats,
    )


def builtin_pattern_masks(features: pd.DataFrame, lookback: int = 20) -> dict[str, pd.Series]:
    """Return conservative, no-lookahead pattern masks for common discovery sweeps."""
    masks: dict[str, pd.Series] = {}
    if "rsi" in features.columns:
        masks["rsi_oversold"] = features["rsi"] <= 30
        masks["rsi_overbought"] = features["rsi"] >= 70
    if {"close", "high", "low"}.issubset(features.columns):
        prior_high = features["high"].shift(1).rolling(lookback).max()
        prior_low = features["low"].shift(1).rolling(lookback).min()
        masks["range_breakout_up"] = features["close"] > prior_high
        masks["range_breakout_down"] = features["close"] < prior_low
    if "atr" in features.columns:
        atr_baseline = features["atr"].shift(1).rolling(lookback).median()
        masks["atr_expansion"] = features["atr"] > atr_baseline * 1.5
    return masks


def scan_builtin_patterns(
    features: pd.DataFrame,
    horizons: Iterable[int] = (1, 4, 16),
    lookback: int = 20,
) -> list[PatternStudy]:
    return [
        run_event_study(features, mask, name, horizons)
        for name, mask in builtin_pattern_masks(features, lookback).items()
    ]

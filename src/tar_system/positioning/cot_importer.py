"""CFTC COT CSV importer.

This stays local-first: users download COT CSV data themselves, then import it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from tar_system.data.csv_importer import hash_csv_file
from tar_system.positioning.store import PositioningRecord, normalise_positioning_date, save_positioning_record


LONG_ALIASES = {"noncommercial_long", "non_commercial_long", "long", "managed_money_long", "leveraged_funds_long"}
SHORT_ALIASES = {"noncommercial_short", "non_commercial_short", "short", "managed_money_short", "leveraged_funds_short"}
DATE_ALIASES = {"date", "report_date", "as_of_date", "timestamp"}
MARKET_ALIASES = {"market", "market_name", "market_and_exchange_names", "contract_market_name", "commodity_name"}


def import_cot_csv(
    path: str | Path,
    symbol: str,
    date_column: str | None = None,
    market: str | None = None,
    market_column: str | None = None,
) -> PositioningRecord:
    csv_path = Path(path)
    df = pd.read_csv(csv_path)
    columns = {str(col).strip().lower().replace(" ", "_"): col for col in df.columns}
    long_col = _first_column(columns, LONG_ALIASES)
    short_col = _first_column(columns, SHORT_ALIASES)
    date_col = columns.get(date_column.lower()) if date_column else _first_column(columns, DATE_ALIASES)
    market_col = columns.get(market_column.lower()) if market_column else _first_column(columns, MARKET_ALIASES)
    if long_col is None or short_col is None:
        raise ValueError("COT CSV needs long and short columns")
    df = _filter_market(df, market_col, market)
    latest = df.dropna(subset=[long_col, short_col]).tail(1)
    if latest.empty:
        raise ValueError("COT CSV has no usable positioning rows")
    row = latest.iloc[0]
    long_value = float(row[long_col])
    short_value = float(row[short_col])
    total = abs(long_value) + abs(short_value)
    net_ratio = (long_value - short_value) / total if total else 0.0
    score = max(-100.0, min(100.0, net_ratio * 100.0))
    record = PositioningRecord(
        source="COT",
        symbol=symbol.upper(),
        date=normalise_positioning_date(row[date_col]) if date_col is not None else "",
        positioning_score=round(score, 2),
        bias=_bias(score),
        confidence=0.85,
        notes="CFTC COT imported from local CSV",
        metrics={
            "long": long_value,
            "short": short_value,
            "net_ratio": round(net_ratio, 4),
            "market": str(row[market_col]) if market_col is not None else "",
        },
        source_file=str(csv_path),
        file_hash=hash_csv_file(csv_path),
    )
    return save_positioning_record(record)


def _first_column(columns: dict[str, Any], aliases: set[str]) -> Any | None:
    for alias in aliases:
        if alias in columns:
            return columns[alias]
    return None


def _filter_market(df: pd.DataFrame, market_col: Any | None, market: str | None) -> pd.DataFrame:
    if market_col is None:
        return df
    markets = df[market_col].dropna().astype(str).str.strip()
    unique_markets = sorted(value for value in markets.unique() if value)
    if market:
        needle = market.strip().lower()
        filtered = df[df[market_col].astype(str).str.lower().str.contains(needle, na=False)]
        if filtered.empty:
            raise ValueError(f"No COT rows matched market filter: {market}")
        return filtered
    if len(unique_markets) > 1:
        preview = ", ".join(unique_markets[:5])
        raise ValueError(f"COT CSV contains multiple markets; pass --market to select one. Examples: {preview}")
    return df


def _bias(score: float) -> str:
    if score >= 25:
        return "BULLISH"
    if score <= -25:
        return "BEARISH"
    return "NEUTRAL"

"""MT5 tick export detection and conversion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class TickConversionResult:
    input_path: Path
    output_path: Path
    rows_in: int
    rows_out: int


def detect_tick_format(path: str | Path) -> bool:
    """Return True when a CSV/TSV looks like an MT5 tick export."""
    sample = pd.read_csv(path, nrows=5, sep=detect_separator(path))
    columns = {_clean_name(column) for column in sample.columns}
    has_tick_prices = {"<bid>", "<ask>"}.issubset(columns) or {"bid", "ask"}.issubset(columns)
    has_tick_time = {"<date>", "<time>"}.issubset(columns) or {"date", "time"}.issubset(columns)
    has_ohlc = {"open", "high", "low", "close"}.issubset(columns) or {"<open>", "<high>", "<low>", "<close>"}.issubset(columns)
    return has_tick_prices and has_tick_time and not has_ohlc


def detect_ohlcv_format(path: str | Path) -> bool:
    sample = pd.read_csv(path, nrows=5, sep=detect_separator(path))
    columns = {_clean_name(column).strip("<>") for column in sample.columns}
    return {"open", "high", "low", "close"}.issubset(columns) and ("volume" in columns or "tickvol" in columns or "vol" in columns)


def convert_ticks_file(path: str | Path, symbol: str, timeframe: str, output_path: str | Path | None = None) -> TickConversionResult:
    input_path = Path(path)
    raw = pd.read_csv(input_path, sep=detect_separator(input_path))
    converted = convert_ticks_dataframe(raw, symbol, timeframe)
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_clean.csv")
    clean_path = Path(output_path)
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    converted.to_csv(clean_path, index=False)
    return TickConversionResult(input_path=input_path, output_path=clean_path, rows_in=len(raw), rows_out=len(converted))


def convert_ticks_dataframe(df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    work = _normalize_tick_columns(df)
    if not {"timestamp", "bid", "ask"}.issubset(work.columns):
        raise ValueError("Tick conversion requires date/time and bid/ask columns")
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce")
    work["bid"] = pd.to_numeric(work["bid"], errors="coerce")
    work["ask"] = pd.to_numeric(work["ask"], errors="coerce")
    if "volume" in work:
        work["volume"] = pd.to_numeric(work["volume"], errors="coerce")
    if "volume" not in work or work["volume"].fillna(0).sum() <= 0:
        work["volume"] = 1.0
    else:
        work["volume"] = work["volume"].fillna(0)
    work = work.dropna(subset=["timestamp", "bid", "ask"]).sort_values("timestamp")
    if work.empty:
        raise ValueError("No valid tick rows found after parsing")
    work["price"] = (work["bid"] + work["ask"]) / 2
    work["spread"] = (work["ask"] - work["bid"]).abs()
    grouped = work.set_index("timestamp").resample(timeframe_to_pandas_freq(timeframe))
    result = grouped["price"].ohlc().dropna().reset_index()
    index = pd.to_datetime(result["timestamp"])
    volume = grouped["volume"].sum().reindex(index).fillna(0)
    spread = grouped["spread"].mean().reindex(index).fillna(0)
    result["volume"] = volume.to_numpy()
    result["spread"] = spread.to_numpy()
    result["symbol"] = symbol
    result["timeframe"] = timeframe
    return result[["timestamp", "open", "high", "low", "close", "volume", "spread", "symbol", "timeframe"]]


def detect_separator(path: str | Path) -> str:
    with Path(path).open("r", encoding="utf-8", errors="ignore") as handle:
        first_line = handle.readline()
    return "\t" if "\t" in first_line else ","


def timeframe_to_pandas_freq(timeframe: str) -> str:
    mapping = {
        "M1": "1min",
        "M5": "5min",
        "M15": "15min",
        "M30": "30min",
        "H1": "1h",
        "H4": "4h",
        "D1": "1D",
    }
    return mapping.get(timeframe.upper(), timeframe)


def _normalize_tick_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename: dict[str, str] = {}
    for column in df.columns:
        cleaned = _clean_name(column)
        if cleaned in {"<date>", "date"}:
            rename[column] = "date"
        elif cleaned in {"<time>", "time"}:
            rename[column] = "time"
        elif cleaned in {"<bid>", "bid"}:
            rename[column] = "bid"
        elif cleaned in {"<ask>", "ask"}:
            rename[column] = "ask"
        elif cleaned in {"<volume>", "volume", "<vol>", "vol"}:
            rename[column] = "volume"
    work = df.rename(columns=rename).copy()
    if {"date", "time"}.issubset(work.columns):
        work["timestamp"] = work["date"].astype(str) + " " + work["time"].astype(str)
    return work


def _clean_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")

"""CSV import helpers with flexible schema normalization."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd

from tar_system.data.tick_converter import convert_ticks_dataframe, detect_separator, detect_tick_format
from tar_system.settings import DATA_DIR

COLUMN_ALIASES = {
    "timestamp": {"timestamp", "datetime", "date_time", "gmt time"},
    "date": {"date", "<date>"},
    "time": {"time", "<time>"},
    "open": {"open", "<open>", "o"},
    "high": {"high", "<high>", "h"},
    "low": {"low", "<low>", "l"},
    "close": {"close", "<close>", "c", "last"},
    "volume": {"volume", "vol", "tickvol", "tick_volume", "<tickvol>", "<vol>", "real_volume"},
    "spread": {"spread", "<spread>"},
    "bid": {"bid", "<bid>"},
    "ask": {"ask", "<ask>"},
}


def _clean_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def detect_csv_schema(path: str | Path) -> dict[str, Any]:
    sample = pd.read_csv(path, nrows=5, sep=_detect_separator(path))
    normalized = {_clean_name(col): col for col in sample.columns}
    detected: dict[str, str] = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if _clean_name(alias) in normalized:
                detected[target] = normalized[_clean_name(alias)]
                break
    return {"columns": list(sample.columns), "detected": detected, "is_tick_data": detect_tick_format(path)}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename: dict[str, str] = {}
    cleaned = {_clean_name(col): col for col in df.columns}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            source = cleaned.get(_clean_name(alias))
            if source:
                rename[source] = target
                break
    normalized = df.rename(columns=rename).copy()
    if "timestamp" not in normalized and {"date", "time"}.issubset(normalized.columns):
        normalized["timestamp"] = normalized["date"].astype(str) + " " + normalized["time"].astype(str)
    elif "timestamp" not in normalized and "date" in normalized:
        normalized["timestamp"] = normalized["date"]
    if "timestamp" in normalized:
        normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume", "spread", "bid", "ask"]:
        if column in normalized:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    return normalized


def load_csv(path: str | Path, symbol: str, timeframe: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=_detect_separator(path))
    df = normalize_columns(df)
    if _is_tick_export(df):
        df = convert_ticks_dataframe(pd.read_csv(path, sep=_detect_separator(path)), symbol, timeframe)
    df["symbol"] = symbol
    df["timeframe"] = timeframe
    return df


def ticks_to_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    symbol = str(df["symbol"].iloc[0]) if "symbol" in df.columns and len(df) else ""
    return convert_ticks_dataframe(df, symbol, timeframe)


def hash_csv_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _detect_separator(path: str | Path) -> str:
    return detect_separator(path)


def _is_tick_export(df: pd.DataFrame) -> bool:
    has_tick_prices = "bid" in df.columns or "ask" in df.columns
    has_ohlc = {"open", "high", "low", "close"}.issubset(df.columns)
    return has_tick_prices and not has_ohlc


def _timeframe_to_pandas_freq(timeframe: str) -> str:
    from tar_system.data.tick_converter import timeframe_to_pandas_freq

    return timeframe_to_pandas_freq(timeframe)


def save_raw_copy(df: pd.DataFrame, symbol: str, timeframe: str, source_path: str | Path | None = None) -> Path:
    output = Path(DATA_DIR) / "raw" / f"{symbol}_{timeframe}.csv"
    if source_path is not None and Path(source_path).resolve() == output.resolve():
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return output


def convert_to_parquet(df: pd.DataFrame, symbol: str, timeframe: str) -> Path:
    output = Path(DATA_DIR) / "validated" / f"{symbol}_{timeframe}.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    return output

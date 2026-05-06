"""Local Parquet and DuckDB storage helpers."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from tar_system.settings import DATA_DIR


def _path(kind: str, symbol: str, timeframe: str) -> Path:
    return Path(DATA_DIR) / kind / f"{symbol}_{timeframe}.parquet"


def save_validated_data(df: pd.DataFrame, symbol: str, timeframe: str, data_hash: str) -> Path:
    output = _path("validated", symbol, timeframe)
    output.parent.mkdir(parents=True, exist_ok=True)
    saved = df.copy()
    saved["data_hash"] = data_hash
    saved.to_parquet(output, index=False)
    return output


def load_validated_data(symbol: str, timeframe: str) -> pd.DataFrame:
    return pd.read_parquet(_path("validated", symbol, timeframe))


def save_feature_data(df: pd.DataFrame, symbol: str, timeframe: str) -> Path:
    output = _path("features", symbol, timeframe)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    return output


def load_feature_data(symbol: str, timeframe: str) -> pd.DataFrame:
    return pd.read_parquet(_path("features", symbol, timeframe))


def filter_by_date_range(df: pd.DataFrame, from_date: str | None = None, to_date: str | None = None) -> pd.DataFrame:
    if df.empty or (not from_date and not to_date):
        return df
    work = df.copy()
    timestamps = pd.to_datetime(work["timestamp"], errors="coerce")
    mask = pd.Series(True, index=work.index)
    if from_date:
        mask &= timestamps >= _parse_date_bound(from_date, end=False)
    if to_date:
        mask &= timestamps <= _parse_date_bound(to_date, end=True)
    return work.loc[mask].sort_values("timestamp").reset_index(drop=True)


def _parse_date_bound(value: str, end: bool) -> pd.Timestamp:
    parts = value.strip().split("-")
    if len(parts) == 1:
        start = pd.Timestamp(f"{parts[0]}-01-01")
        return start + pd.offsets.YearEnd(0) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1) if end else start
    if len(parts) == 2:
        start = pd.Timestamp(f"{parts[0]}-{parts[1]}-01")
        return start + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1) if end else start
    parsed = pd.Timestamp(value)
    return parsed + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1) if end and len(str(value).split()) == 1 else parsed


def query_duckdb(sql: str) -> pd.DataFrame:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(Path(DATA_DIR) / "tar_system.duckdb")) as connection:
        return connection.execute(sql).df()

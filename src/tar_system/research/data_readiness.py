"""Data readiness checks for hypothesis and basket research."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class DataReadinessRow:
    symbol: str
    timeframe: str
    path: str
    exists: bool
    rows: int = 0
    start: str | None = None
    end: str | None = None
    span_days: float = 0.0
    estimated_months: float = 0.0
    ready: bool = False
    reason: str = ""


@dataclass
class DataReadinessResult:
    generated_at: str
    symbols: list[str]
    timeframes: list[str]
    min_months: int
    min_rows: int
    ready_count: int
    missing_count: int
    report_path: str
    report_json_path: str
    rows: list[DataReadinessRow]


def check_data_readiness(
    symbols: list[str],
    timeframes: list[str],
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "reports/data_readiness",
    min_months: int = 36,
    min_rows: int = 1000,
) -> DataReadinessResult:
    rows = [
        _check_one(symbol.upper(), timeframe.upper(), Path(raw_dir), min_months=min_months, min_rows=min_rows)
        for symbol in symbols
        for timeframe in timeframes
    ]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output / f"{stamp}_data_readiness.md"
    report_json_path = output / f"{stamp}_data_readiness.json"
    result = DataReadinessResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        symbols=[symbol.upper() for symbol in symbols],
        timeframes=[timeframe.upper() for timeframe in timeframes],
        min_months=min_months,
        min_rows=min_rows,
        ready_count=sum(1 for row in rows if row.ready),
        missing_count=sum(1 for row in rows if not row.exists),
        report_path=str(report_path),
        report_json_path=str(report_json_path),
        rows=rows,
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    report_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _check_one(symbol: str, timeframe: str, raw_dir: Path, min_months: int, min_rows: int) -> DataReadinessRow:
    path = raw_dir / f"{symbol}_{timeframe}.csv"
    if not path.exists():
        return DataReadinessRow(symbol=symbol, timeframe=timeframe, path=str(path), exists=False, reason="missing_raw_csv")
    try:
        df = _read_csv(path)
    except Exception as exc:
        return DataReadinessRow(symbol=symbol, timeframe=timeframe, path=str(path), exists=True, reason=f"unreadable_csv:{exc}")
    if df.empty:
        return DataReadinessRow(symbol=symbol, timeframe=timeframe, path=str(path), exists=True, reason="missing_or_empty_timestamp")
    timestamp_source = _timestamp_series(df)
    if timestamp_source is None:
        return DataReadinessRow(symbol=symbol, timeframe=timeframe, path=str(path), exists=True, rows=len(df), reason="missing_timestamp_column")
    timestamps = pd.to_datetime(timestamp_source, errors="coerce", utc=True).dropna()
    if timestamps.empty:
        return DataReadinessRow(symbol=symbol, timeframe=timeframe, path=str(path), exists=True, rows=len(df), reason="invalid_timestamps")
    start = timestamps.min()
    end = timestamps.max()
    span_days = max((end - start).total_seconds() / 86_400.0, 0.0)
    estimated_months = span_days / 30.4375
    ready = len(df) >= min_rows and estimated_months >= min_months
    reason = "ready" if ready else _not_ready_reason(len(df), estimated_months, min_rows, min_months)
    return DataReadinessRow(
        symbol=symbol,
        timeframe=timeframe,
        path=str(path),
        exists=True,
        rows=len(df),
        start=start.isoformat(),
        end=end.isoformat(),
        span_days=round(span_days, 2),
        estimated_months=round(estimated_months, 2),
        ready=ready,
        reason=reason,
    )


def _not_ready_reason(rows: int, months: float, min_rows: int, min_months: int) -> str:
    reasons: list[str] = []
    if rows < min_rows:
        reasons.append("insufficient_rows")
    if months < min_months:
        reasons.append("insufficient_history_months")
    return ",".join(reasons) or "not_ready"


def _timestamp_series(df: pd.DataFrame) -> pd.Series | None:
    columns = {str(column).strip().lower(): column for column in df.columns}
    for name in ("timestamp", "datetime", "date_time", "time"):
        if name in columns:
            return df[columns[name]]
    if "<date>" in columns and "<time>" in columns:
        return df[columns["<date>"]].astype(str) + " " + df[columns["<time>"]].astype(str)
    if "date" in columns and "time" in columns:
        return df[columns["date"]].astype(str) + " " + df[columns["time"]].astype(str)
    if "<date>" in columns:
        return df[columns["<date>"]]
    if "date" in columns:
        return df[columns["date"]]
    return None


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if len(df.columns) == 1 and "\t" in str(df.columns[0]):
        return pd.read_csv(path, sep="\t")
    return df


def _markdown(result: DataReadinessResult) -> str:
    lines = [
        "# Data Readiness Report",
        "",
        f"- Generated: {result.generated_at}",
        f"- Symbols: {', '.join(result.symbols)}",
        f"- Timeframes: {', '.join(result.timeframes)}",
        f"- Minimum months: {result.min_months}",
        f"- Minimum rows: {result.min_rows}",
        f"- Ready rows: {result.ready_count}",
        f"- Missing files: {result.missing_count}",
        "",
        "| Symbol | TF | Ready | Rows | Months | Start | End | Reason |",
        "| --- | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in result.rows:
        lines.append(
            f"| {row.symbol} | {row.timeframe} | {row.ready} | {row.rows} | {row.estimated_months} | {row.start or ''} | {row.end or ''} | {row.reason} |"
        )
    lines.extend(["", "## Guardrails", "", "- Missing or insufficient data blocks the candidate.", "- Data readiness is not a backtest result.", ""])
    return "\n".join(lines)

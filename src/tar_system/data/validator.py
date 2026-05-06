"""Data validation for normalized OHLCV datasets."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from tar_system import reason_codes as rc

REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume", "symbol", "timeframe"]


@dataclass
class ValidationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    row_count: int = 0
    start_date: str | None = None
    end_date: str | None = None
    symbol: str | None = None
    timeframe: str | None = None
    data_hash: str | None = None
    data_quality_score: float = 0.0


def validate_ohlcv(df: pd.DataFrame, data_hash: str | None = None) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    codes: list[str] = []
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
        codes.append(rc.DATA_MISSING_COLUMNS)
        return ValidationResult(False, errors, warnings, codes, len(df), data_hash=data_hash, data_quality_score=0.0)

    work = df.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce")
    if work[REQUIRED_COLUMNS].isna().any().any():
        errors.append("Required columns contain missing values")
        codes.append(rc.DATA_MISSING_VALUES)
    if work["timestamp"].duplicated().any():
        errors.append("Duplicate timestamps found")
        codes.append(rc.DATA_DUPLICATE_TIMESTAMPS)
    if not work["timestamp"].is_monotonic_increasing:
        errors.append("Timestamps are not chronological")
        codes.append(rc.DATA_NOT_CHRONOLOGICAL)
    invalid_ohlc = (work["high"] < work[["open", "close", "low"]].max(axis=1)) | (
        work["low"] > work[["open", "close", "high"]].min(axis=1)
    )
    if invalid_ohlc.any():
        errors.append("OHLC sanity check failed")
        codes.append(rc.DATA_OHLC_INVALID)
    if (work["volume"] < 0).any():
        errors.append("Negative volume found")
        codes.append(rc.DATA_VOLUME_INVALID)
    if (work["symbol"].astype(str).str.len() == 0).any() or (work["timeframe"].astype(str).str.len() == 0).any():
        errors.append("Symbol and timeframe must be present")
        codes.append(rc.DATA_SYMBOL_TIMEFRAME_MISSING)

    returns = work["close"].pct_change().abs()
    if returns.gt(0.1).any():
        warnings.append("Price spike warning: absolute close return above 10%")
        codes.append(rc.DATA_PRICE_SPIKE)
    if (work["volume"] == 0).mean() > 0.5:
        warnings.append("More than half of volume values are zero")
        codes.append(rc.DATA_VOLUME_INVALID)

    symbol = str(work["symbol"].iloc[0]) if len(work) else None
    timeframe = str(work["timeframe"].iloc[0]) if len(work) else None
    start = work["timestamp"].min()
    end = work["timestamp"].max()
    quality_score = _data_quality_score(work, timeframe)
    if quality_score < 60:
        errors.append(f"Data quality score below block threshold: {quality_score}")
        codes.append(rc.DATA_QUALITY_BLOCKED)
    elif quality_score < 80:
        warnings.append(f"Data quality score below warning threshold: {quality_score}")
        codes.append(rc.DATA_QUALITY_LOW)
    return ValidationResult(
        passed=not errors,
        errors=errors,
        warnings=warnings,
        reason_codes=codes,
        row_count=len(work),
        start_date=start.isoformat() if pd.notna(start) else None,
        end_date=end.isoformat() if pd.notna(end) else None,
        symbol=symbol,
        timeframe=timeframe,
        data_hash=data_hash,
        data_quality_score=quality_score,
    )


def _data_quality_score(work: pd.DataFrame, timeframe: str | None) -> float:
    row_count = max(len(work), 1)
    missing_ratio = float(work[REQUIRED_COLUMNS].isna().sum().sum()) / (row_count * len(REQUIRED_COLUMNS))
    duplicate_ratio = float(work["timestamp"].duplicated().sum()) / row_count
    expected_delta = _expected_delta(timeframe)
    if expected_delta and len(work) > 1:
        ordered = work.sort_values("timestamp")
        gaps = ordered["timestamp"].diff().dropna()
        missing_bars = sum(max(int(delta / expected_delta) - 1, 0) for delta in gaps if delta <= pd.Timedelta(days=1))
        expected_bars = row_count + missing_bars
        gap_ratio = min(missing_bars / max(expected_bars, 1), 1.0)
        coverage = min(row_count / max(expected_bars, 1), 1.0)
    else:
        gap_ratio = 0.0
        coverage = 1.0
    true_range = pd.concat(
        [
            work["high"] - work["low"],
            (work["high"] - work["close"].shift()).abs(),
            (work["low"] - work["close"].shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = true_range.rolling(14, min_periods=1).mean()
    spike_ratio = float(work["close"].diff().abs().gt(5 * atr).sum()) / row_count
    score = 100.0
    score -= min(missing_ratio, 1.0) * 25
    score -= min(duplicate_ratio, 1.0) * 20
    score -= min(gap_ratio, 1.0) * 25
    score -= min(spike_ratio, 1.0) * 15
    score -= (1 - coverage) * 15
    return round(max(0.0, min(100.0, score)), 2)


def _expected_delta(timeframe: str | None) -> pd.Timedelta | None:
    if not timeframe:
        return None
    mapping = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h", "H4": "4h", "D1": "1D"}
    value = mapping.get(str(timeframe).upper())
    return pd.Timedelta(value) if value else None

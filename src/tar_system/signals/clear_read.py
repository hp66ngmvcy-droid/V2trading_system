"""Paper-only clear-read signal layer.

This module is intentionally not a strategy, scheduler, broker adapter, or MT5
export path. It reduces a local feature row into LONG, SHORT, or WAIT for
research replay only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import pandas as pd


SIDES = {"LONG", "SHORT", "WAIT"}
BLOCKED_REGIMES = {"VOLATILE", "UNKNOWN"}
REQUIRED_COLUMNS = {
    "timestamp",
    "symbol",
    "timeframe",
    "open",
    "high",
    "low",
    "close",
    "ema_fast",
    "ema_slow",
    "ema_fast_slope",
    "rsi",
    "atr",
    "macd",
    "macd_signal",
    "prior_rolling_high",
    "prior_rolling_low",
}


@dataclass(frozen=True)
class ClearRead:
    timestamp: pd.Timestamp | None
    symbol: str
    timeframe: str
    side: str
    confidence: float
    reasons: list[str] = field(default_factory=list)
    entry_reference: float | None = None
    risk_approved: bool = False
    risk_reason: str = "PAPER_ONLY_REVIEW"
    paper_only: bool = True
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp is not None else None,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "side": self.side,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "entry_reference": self.entry_reference,
            "risk_approved": self.risk_approved,
            "risk_reason": self.risk_reason,
            "paper_only": self.paper_only,
            "metadata": dict(self.metadata),
        }


def generate_clear_read(
    row: pd.Series,
    regime: str,
    risk_context: Mapping[str, object] | None = None,
    min_confidence: float = 0.65,
) -> ClearRead:
    """Return a paper-only LONG, SHORT, or WAIT read for one feature row."""

    missing = sorted(column for column in REQUIRED_COLUMNS if column not in row.index)
    if missing:
        return _wait(row, ["CLEAR_READ_MISSING_COLUMNS"], {"missing_columns": missing})

    timestamp = _timestamp(row)
    symbol = str(row.get("symbol", "UNKNOWN"))
    timeframe = str(row.get("timeframe", "UNKNOWN"))
    risk_approved, risk_reason = _risk_state(risk_context)

    values = {column: row.get(column) for column in REQUIRED_COLUMNS if column not in {"timestamp", "symbol", "timeframe"}}
    if any(pd.isna(value) for value in values.values()):
        return ClearRead(timestamp, symbol, timeframe, "WAIT", 0.0, ["CLEAR_READ_MISSING_VALUES"], risk_approved=False, risk_reason=risk_reason)

    open_price = float(row["open"])
    high = float(row["high"])
    low = float(row["low"])
    close = float(row["close"])
    atr = float(row["atr"])
    normalized_regime = str(regime).upper()

    if timestamp is None:
        return ClearRead(None, symbol, timeframe, "WAIT", 0.0, ["CLEAR_READ_TIMESTAMP_INVALID"], risk_approved=False, risk_reason=risk_reason)
    if close <= 0:
        return ClearRead(timestamp, symbol, timeframe, "WAIT", 0.0, ["CLEAR_READ_CLOSE_INVALID"], risk_approved=False, risk_reason=risk_reason)
    if atr <= 0:
        return ClearRead(timestamp, symbol, timeframe, "WAIT", 0.0, ["CLEAR_READ_ATR_INVALID"], risk_approved=False, risk_reason=risk_reason)
    if normalized_regime in BLOCKED_REGIMES:
        return ClearRead(
            timestamp,
            symbol,
            timeframe,
            "WAIT",
            0.0,
            [f"CLEAR_READ_REGIME_BLOCK_{normalized_regime}"],
            entry_reference=close,
            risk_approved=False,
            risk_reason=risk_reason,
            metadata={"regime": normalized_regime},
        )
    if risk_context is not None and not risk_approved:
        return ClearRead(
            timestamp,
            symbol,
            timeframe,
            "WAIT",
            0.0,
            ["CLEAR_READ_RISK_BLOCK"],
            entry_reference=close,
            risk_approved=False,
            risk_reason=risk_reason,
            metadata={"regime": normalized_regime},
        )

    bar_range = max(high - low, 1e-9)
    close_position = (close - low) / bar_range
    upper_wick_ratio = (high - max(open_price, close)) / bar_range
    lower_wick_ratio = (min(open_price, close) - low) / bar_range
    volume_available, volume_confirmed = _volume_state(row)

    momentum = _momentum(row)
    pressure = _pressure(open_price, close, close_position, volume_available, volume_confirmed)
    liquidity = _liquidity(row, high, low, close, upper_wick_ratio, lower_wick_ratio)

    reasons: list[str] = []
    confidence = 0.0
    if momentum != "MIXED":
        confidence += 0.30
        reasons.append(f"CLEAR_READ_MOMENTUM_{momentum}")
    if pressure != "MIXED":
        confidence += 0.25
        reasons.append(f"CLEAR_READ_PRESSURE_{pressure}")
    if liquidity != "NEUTRAL":
        confidence += 0.30
        reasons.append(f"CLEAR_READ_LIQUIDITY_{liquidity}")
    if normalized_regime == "TRENDING":
        confidence += 0.10
        reasons.append("CLEAR_READ_REGIME_TRENDING")
    if bool(row.get("is_liquid_session", False)):
        confidence += 0.05
        reasons.append("CLEAR_READ_LIQUID_SESSION")

    caps: list[str] = []
    if not volume_available:
        confidence = min(confidence, 0.60)
        caps.append("CLEAR_READ_CAP_VOLUME_UNAVAILABLE")
    if normalized_regime == "RANGING":
        confidence = min(confidence, 0.60)
        caps.append("CLEAR_READ_CAP_RANGING_REGIME")
    reasons.extend(caps)

    side = "WAIT"
    if momentum == pressure == liquidity == "BULLISH" and confidence >= min_confidence:
        side = "LONG"
    elif momentum == pressure == liquidity == "BEARISH" and confidence >= min_confidence:
        side = "SHORT"
    else:
        reasons.append("CLEAR_READ_WAIT_EVIDENCE_NOT_ALIGNED")

    return ClearRead(
        timestamp=timestamp,
        symbol=symbol,
        timeframe=timeframe,
        side=side,
        confidence=round(float(confidence), 4),
        reasons=reasons,
        entry_reference=close,
        risk_approved=risk_approved,
        risk_reason=risk_reason,
        metadata={
            "regime": normalized_regime,
            "momentum": momentum,
            "pressure": pressure,
            "liquidity": liquidity,
            "close_position": round(float(close_position), 4),
            "upper_wick_ratio": round(float(upper_wick_ratio), 4),
            "lower_wick_ratio": round(float(lower_wick_ratio), 4),
            "volume_available": volume_available,
            "volume_confirmed": volume_confirmed,
        },
    )


def generate_trend_continuation_read(
    row: pd.Series,
    regime: str,
    risk_context: Mapping[str, object] | None = None,
    min_confidence: float = 0.65,
) -> ClearRead:
    """Return a paper-only trend-continuation candidate read.

    This intentionally allows neutral liquidity when momentum and pressure are
    aligned in a trending regime. It is for comparison reporting only.
    """

    base = generate_clear_read(row, regime, risk_context, min_confidence)
    if base.side != "WAIT":
        return base
    if base.metadata.get("regime") != "TRENDING":
        return base
    if risk_context is not None and not base.risk_approved:
        return base
    momentum = str(base.metadata.get("momentum", "MIXED"))
    pressure = str(base.metadata.get("pressure", "MIXED"))
    liquidity = str(base.metadata.get("liquidity", "NEUTRAL"))
    if liquidity != "NEUTRAL" or momentum != pressure or momentum not in {"BULLISH", "BEARISH"}:
        return base

    confidence = 0.65
    reasons = [
        f"CLEAR_READ_TREND_CONTINUATION_{momentum}",
        "CLEAR_READ_LIQUIDITY_NEUTRAL_ALLOWED_FOR_REPLAY",
        "CLEAR_READ_MODE_TREND_CONTINUATION",
    ]
    if bool(row.get("is_liquid_session", False)):
        confidence += 0.05
        reasons.append("CLEAR_READ_LIQUID_SESSION")
    side = "LONG" if momentum == "BULLISH" else "SHORT"
    return ClearRead(
        timestamp=base.timestamp,
        symbol=base.symbol,
        timeframe=base.timeframe,
        side=side,
        confidence=round(confidence, 4),
        reasons=reasons,
        entry_reference=base.entry_reference,
        risk_approved=base.risk_approved,
        risk_reason=base.risk_reason,
        metadata={**base.metadata, "mode": "TREND_CONTINUATION"},
    )


def _timestamp(row: pd.Series) -> pd.Timestamp | None:
    try:
        value = pd.Timestamp(row.get("timestamp"))
    except Exception:
        return None
    if pd.isna(value):
        return None
    return value


def _risk_state(risk_context: Mapping[str, object] | None) -> tuple[bool, str]:
    if risk_context is None:
        return False, "PAPER_ONLY_REVIEW"
    return bool(risk_context.get("risk_approved", False)), str(risk_context.get("risk_reason", "PAPER_ONLY_REVIEW"))


def _momentum(row: pd.Series) -> str:
    ema_fast = float(row["ema_fast"])
    ema_slow = float(row["ema_slow"])
    ema_fast_slope = float(row["ema_fast_slope"])
    rsi = float(row["rsi"])
    macd = float(row["macd"])
    macd_signal = float(row["macd_signal"])
    if ema_fast > ema_slow and ema_fast_slope > 0 and rsi >= 55 and macd >= macd_signal:
        return "BULLISH"
    if ema_fast < ema_slow and ema_fast_slope < 0 and rsi <= 45 and macd <= macd_signal:
        return "BEARISH"
    return "MIXED"


def _pressure(open_price: float, close: float, close_position: float, volume_available: bool, volume_confirmed: bool) -> str:
    volume_ok = volume_confirmed if volume_available else True
    if close > open_price and close_position >= 0.60 and volume_ok:
        return "BULLISH"
    if close < open_price and close_position <= 0.40 and volume_ok:
        return "BEARISH"
    return "MIXED"


def _liquidity(row: pd.Series, high: float, low: float, close: float, upper_wick_ratio: float, lower_wick_ratio: float) -> str:
    prior_high = float(row["prior_rolling_high"])
    prior_low = float(row["prior_rolling_low"])
    if low < prior_low and close > prior_low and lower_wick_ratio >= 0.35:
        return "BULLISH"
    if high > prior_high and close < prior_high and upper_wick_ratio >= 0.35:
        return "BEARISH"
    return "NEUTRAL"


def _volume_state(row: pd.Series) -> tuple[bool, bool]:
    if "volume" not in row.index or "volume_sma" not in row.index:
        return False, False
    volume = row.get("volume")
    volume_sma = row.get("volume_sma")
    if pd.isna(volume) or pd.isna(volume_sma) or float(volume_sma) <= 0:
        return False, False
    return True, float(volume) > float(volume_sma)


def _wait(row: pd.Series, reasons: list[str], metadata: dict[str, object] | None = None) -> ClearRead:
    return ClearRead(
        timestamp=_timestamp(row),
        symbol=str(row.get("symbol", "UNKNOWN")),
        timeframe=str(row.get("timeframe", "UNKNOWN")),
        side="WAIT",
        confidence=0.0,
        reasons=reasons,
        paper_only=True,
        metadata=metadata or {},
    )

"""Feature engineering for local OHLCV data."""

from __future__ import annotations

import pandas as pd


def build_features(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    fast_window: int = 12,
    slow_window: int = 26,
    rsi_window: int = 14,
    atr_window: int = 14,
    volatility_window: int = 20,
) -> pd.DataFrame:
    work = df.sort_values("timestamp").copy()
    work["ema_fast"] = work["close"].ewm(span=fast_window, adjust=False).mean()
    work["ema_slow"] = work["close"].ewm(span=slow_window, adjust=False).mean()
    work["ema_fast_slope"] = ((work["ema_fast"] - work["ema_fast"].shift(3)) / 3 / work["close"]).fillna(0)
    work["ema_slow_slope"] = ((work["ema_slow"] - work["ema_slow"].shift(3)) / 3 / work["close"]).fillna(0)
    delta = work["close"].diff()
    gains = delta.clip(lower=0).rolling(rsi_window).mean()
    losses = (-delta.clip(upper=0)).rolling(rsi_window).mean()
    rs = gains / losses.replace(0, pd.NA)
    work["rsi"] = 100 - (100 / (1 + rs))
    true_range = pd.concat(
        [
            work["high"] - work["low"],
            (work["high"] - work["close"].shift()).abs(),
            (work["low"] - work["close"].shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    work["atr"] = true_range.rolling(atr_window).mean()
    work["atr_median_50"] = work["atr"].rolling(50, min_periods=1).median()
    ema_12 = work["close"].ewm(span=12, adjust=False).mean()
    ema_26 = work["close"].ewm(span=26, adjust=False).mean()
    work["macd"] = ema_12 - ema_26
    work["macd_signal"] = work["macd"].ewm(span=9, adjust=False).mean()
    work["returns"] = work["close"].pct_change()
    work["rolling_volatility"] = work["returns"].rolling(volatility_window).std()
    work["rolling_high"] = work["high"].rolling(volatility_window).max()
    work["rolling_low"] = work["low"].rolling(volatility_window).min()
    work["prior_rolling_high"] = work["rolling_high"].shift(1)
    work["prior_rolling_low"] = work["rolling_low"].shift(1)
    work["bollinger_mid"] = work["close"].rolling(20).mean()
    rolling_std = work["close"].rolling(20).std()
    work["bollinger_upper"] = work["bollinger_mid"] + 2 * rolling_std
    work["bollinger_lower"] = work["bollinger_mid"] - 2 * rolling_std
    band_range = (work["bollinger_upper"] - work["bollinger_lower"]).replace(0, pd.NA)
    work["bb_width"] = (band_range / work["bollinger_mid"].replace(0, pd.NA)).fillna(0)
    work["price_in_band"] = ((work["close"] - work["bollinger_lower"]) / band_range).clip(0, 1).fillna(0.5)
    price_range = (work["rolling_high"] - work["rolling_low"]).replace(0, pd.NA)
    work["range_compression"] = (work["atr"] / price_range).fillna(0)
    timestamps = pd.to_datetime(work["timestamp"], utc=True)
    work["hour_utc"] = timestamps.dt.hour
    work["session_label"] = work["hour_utc"].map(_session_label)
    work["is_liquid_session"] = work["session_label"].isin({"LONDON", "OVERLAP", "NEW_YORK"})
    return work


def _session_label(hour: int) -> str:
    if 0 <= hour < 7:
        return "ASIAN"
    if 7 <= hour < 12:
        return "LONDON"
    if 12 <= hour < 16:
        return "OVERLAP"
    if 16 <= hour < 20:
        return "NEW_YORK"
    return "OFF"


def build_and_save_features(df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    from tar_system.data.store import save_feature_data

    features = build_features(df, symbol, timeframe)
    save_feature_data(features, symbol, timeframe)
    return features

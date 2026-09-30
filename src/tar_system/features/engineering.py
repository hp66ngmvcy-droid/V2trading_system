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
    # Prefer tick volume for forex data where real volume is unavailable.
    if "volume" not in work.columns or work["volume"].eq(0).all():
        fallback = work["<TICKVOL>"] if "<TICKVOL>" in work.columns else work["tickvol"] if "tickvol" in work.columns else None
        work["volume"] = fallback if fallback is not None else float("nan")
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
    work["volume_sma"] = work["volume"].rolling(volatility_window).mean()
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
    work["month_of_year"] = timestamps.dt.month
    work["day_of_week"] = timestamps.dt.dayofweek
    work["session_label"] = work["hour_utc"].map(_session_label)
    work["is_liquid_session"] = work["session_label"].isin({"LONDON", "OVERLAP", "NEW_YORK"})

    # Asian session range (01:00–06:45 UTC) — used by ARSB_v1
    # For each bar, look up the completed Asian box from the same calendar day.
    ts = pd.to_datetime(work["timestamp"], utc=True)
    work["_date_utc"] = ts.dt.date
    asian_mask = (ts.dt.hour >= 1) & (ts.dt.hour < 7)
    asian_bars = work[asian_mask].copy()
    asian_bars["_date_utc"] = pd.to_datetime(asian_bars["timestamp"], utc=True).dt.date
    asian_daily = asian_bars.groupby("_date_utc").agg(
        asian_high=("high", "max"),
        asian_low=("low", "min"),
    ).reset_index()
    asian_daily["asian_range"] = asian_daily["asian_high"] - asian_daily["asian_low"]
    asian_daily["asian_mid"] = (asian_daily["asian_high"] + asian_daily["asian_low"]) / 2
    work = work.merge(asian_daily, on="_date_utc", how="left")

    # Opening Range Breakout (01:00–02:00 UTC) — used by gold_orb_v1
    # First hour after XAUUSD market open: 4 M15 bars at hour_utc == 1.
    orb_mask = work["hour_utc"] == 1
    orb_bars = work[orb_mask].copy()
    orb_bars["_date_utc"] = pd.to_datetime(orb_bars["timestamp"], utc=True).dt.date
    orb_daily = orb_bars.groupby("_date_utc").agg(
        orb_high=("high", "max"),
        orb_low=("low", "min"),
    ).reset_index()
    orb_daily["orb_range"] = orb_daily["orb_high"] - orb_daily["orb_low"]
    work = work.merge(orb_daily, on="_date_utc", how="left")
    work = work.drop(columns=["_date_utc"])

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


def build_and_save_features(df: pd.DataFrame, symbol: str, timeframe: str, output_suffix: str | None = None) -> pd.DataFrame:
    from tar_system.data.store import save_feature_data

    features = build_features(df, symbol, timeframe)
    save_feature_data(features, symbol, timeframe, output_suffix=output_suffix)
    return features

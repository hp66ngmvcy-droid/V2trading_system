#!/usr/bin/env python3
"""Generate a daily trading brief (JSON + session MD) automatically.

Fetches live market data, computes key levels from M15 data, writes
data/daily_briefs/YYYY-MM-DD_levels.json and data/paper_game/sessions/YYYY-MM-DD.md.

Usage:
    TWELVE_DATA_KEY=... FRED_API_KEY=... venv/bin/python scripts/generate_daily_brief.py
    TWELVE_DATA_KEY=... FRED_API_KEY=... venv/bin/python scripts/generate_daily_brief.py --date 2026-09-25
    TWELVE_DATA_KEY=... FRED_API_KEY=... venv/bin/python scripts/generate_daily_brief.py --dry-run

Run via keychain:
    TWELVE_DATA_KEY=$(security find-generic-password -s dev.whs1.TWELVE_DATA_KEY -a $USER -w) \
    FRED_API_KEY=$(security find-generic-password -s dev.whs1.FRED_API_KEY -a $USER -w) \
    venv/bin/python scripts/generate_daily_brief.py
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BRIEFS_DIR = ROOT / "data" / "daily_briefs"
SESSIONS_DIR = ROOT / "data" / "paper_game" / "sessions"
XAU_PARQUET = ROOT / "data" / "validated" / "XAUUSD_M15.parquet"
BTC_PARQUET = ROOT / "data" / "validated" / "BTCUSD_M15.parquet"

TD_BASE = "https://api.twelvedata.com"
FRED_BASE = "https://api.stlouisfed.org/fred"


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def _td_price(symbols: list[str], td_key: str) -> dict[str, float | None]:
    sym_str = ",".join(symbols)
    r = httpx.get(f"{TD_BASE}/price?symbol={sym_str}&apikey={td_key}", timeout=15)
    data = r.json()
    out = {}
    for sym in symbols:
        val = data.get(sym, {})
        if isinstance(val, dict) and "price" in val:
            out[sym] = round(float(val["price"]), 5)
        else:
            out[sym] = None
    return out


def _fred_latest(series_id: str, fred_key: str) -> float | None:
    url = (f"{FRED_BASE}/series/observations?series_id={series_id}"
           f"&sort_order=desc&limit=3&api_key={fred_key}&file_type=json")
    r = httpx.get(url, timeout=15)
    obs = r.json().get("observations", [])
    for o in obs:
        v = o.get("value", ".")
        if v != ".":
            return round(float(v), 4)
    return None


def _btc_derivatives() -> dict:
    """Fetch BTC options expiry (Deribit) and futures OI percentile (Binance). No auth."""
    out = {"next_options_expiry": None, "next_options_expiry_btc": None,
           "futures_oi_btc": None, "futures_oi_pct30": None}
    try:
        # Deribit: next weekly expiry and its OI
        r = httpx.get(
            "https://www.deribit.com/api/v2/public/get_book_summary_by_currency"
            "?currency=BTC&kind=option", timeout=12)
        instruments = r.json().get("result", [])
        by_expiry: dict[str, float] = defaultdict(float)
        for b in instruments:
            name = b.get("instrument_name", "")
            parts = name.split("-")
            exp = parts[1] if len(parts) >= 2 else "UNK"
            by_expiry[exp] += float(b.get("open_interest", 0))
        if by_expiry:
            # Sort by expiry date (format: 25SEP26)
            def _parse_exp(s: str):
                try:
                    return datetime.strptime(s, "%d%b%y")
                except Exception:
                    return datetime(2099, 1, 1)
            sorted_exp = sorted(by_expiry.items(), key=lambda x: _parse_exp(x[0]))
            next_exp, next_oi = sorted_exp[0]
            out["next_options_expiry"] = next_exp
            out["next_options_expiry_btc"] = round(next_oi, 0)
    except Exception:
        pass

    try:
        # Binance: futures OI + 30-day percentile
        r2 = httpx.get(
            "https://fapi.binance.com/futures/data/openInterestHist"
            "?symbol=BTCUSDT&period=1d&limit=30", timeout=12)
        hist = [float(x["sumOpenInterest"]) for x in r2.json()]
        if hist:
            oi_now = hist[-1]
            lo, hi = min(hist), max(hist)
            pct = round((oi_now - lo) / (hi - lo) * 100) if hi > lo else 50
            out["futures_oi_btc"] = round(oi_now, 0)
            out["futures_oi_pct30"] = pct
    except Exception:
        pass

    return out


def _iv_walls(price: float, iv_pct: float) -> dict:
    """Compute IV-derived daily expected range walls from annualised IV %.

    Returns 1σ (68%) and 1.645σ (90%) walls plus the raw daily expected move.
    Formula: daily_em = price × (iv_pct/100) × sqrt(1/252)
    """
    iv_annual = iv_pct / 100.0
    daily_em = price * iv_annual * math.sqrt(1.0 / 252.0)
    return {
        "iv_pct":               round(iv_pct, 2),
        "iv_expected_move_daily": round(daily_em, 2),
        "iv_high_90":           round(price + daily_em * 1.645, 2),
        "iv_low_90":            round(price - daily_em * 1.645, 2),
        "iv_high_68":           round(price + daily_em, 2),
        "iv_low_68":            round(price - daily_em, 2),
    }


def _fetch_btc_atm_iv(btc_price: float) -> float | None:
    """Fetch ATM implied vol (%) for the nearest Deribit BTC expiry. No auth needed.

    Reuses the book summary endpoint already called in _btc_derivatives so no
    extra auth or rate-limit cost. Returns annualised IV % or None on any error.
    """
    try:
        r = httpx.get(
            "https://www.deribit.com/api/v2/public/get_book_summary_by_currency"
            "?currency=BTC&kind=option",
            timeout=12,
        )
        instruments = r.json().get("result", [])
        today = datetime.utcnow().date()

        def _parse_exp(s: str) -> datetime:
            try:
                return datetime.strptime(s, "%d%b%y")
            except Exception:
                return datetime(2099, 1, 1)

        # Group valid future instruments by expiry
        by_expiry: dict[str, list[dict]] = defaultdict(list)
        for inst in instruments:
            name = inst.get("instrument_name", "")
            parts = name.split("-")
            if len(parts) < 4:
                continue
            exp_str = parts[1]
            if _parse_exp(exp_str).date() < today:
                continue
            by_expiry[exp_str].append(inst)

        if not by_expiry:
            return None

        nearest_exp = min(by_expiry.keys(), key=_parse_exp)
        exp_instruments = by_expiry[nearest_exp]

        # Find ATM strike (nearest to current BTC price)
        strikes: set[int] = set()
        for inst in exp_instruments:
            parts = inst["instrument_name"].split("-")
            if len(parts) >= 3:
                try:
                    strikes.add(int(parts[2]))
                except ValueError:
                    pass

        if not strikes:
            return None

        atm_strike = min(strikes, key=lambda s: abs(s - btc_price))

        # Average mark_iv across call + put at ATM strike
        atm_ivs = []
        for inst in exp_instruments:
            parts = inst["instrument_name"].split("-")
            if len(parts) >= 3:
                try:
                    if int(parts[2]) != atm_strike:
                        continue
                except ValueError:
                    continue
                iv = inst.get("mark_iv")
                if iv and float(iv) > 0:
                    atm_ivs.append(float(iv))

        if not atm_ivs:
            return None

        return round(sum(atm_ivs) / len(atm_ivs), 2)

    except Exception:
        return None


def fetch_macro(td_key: str, fred_key: str) -> dict:
    """Fetch macro snapshot. Returns dict with all indicators."""
    # Prices from Twelve Data
    prices = _td_price(["XAU/USD", "BTC/USD", "EUR/USD", "USD/JPY", "GBP/USD", "BCO", "VIXY"], td_key)

    xau = prices.get("XAU/USD")
    btc = prices.get("BTC/USD")
    eurusd = prices.get("EUR/USD")
    brent = prices.get("BCO")
    vixy = prices.get("VIXY")

    # DXY approximation from EUR/USD (accurate near 1.05-1.20 range)
    if eurusd:
        dxy = round(-100 * eurusd + 215, 2)
    else:
        broad = _fred_latest("DTWEXBGS", fred_key)
        dxy = round((broad - 119.5) * 0.55 + 101.0, 2) if broad else None

    # FRED rates (1-day lag acceptable for daily brief)
    us10y = _fred_latest("DGS10", fred_key)
    us10y_real = _fred_latest("DFII10", fred_key)   # 10Y TIPS real yield
    fed_funds = _fred_latest("DFF", fred_key)         # effective fed funds rate

    # VIX proxy — VIXY ETF
    vix = round(vixy * 0.88, 1) if vixy else None

    # BTC derivatives (Deribit + Binance, no auth)
    btc_deriv = _btc_derivatives()

    return {
        "xau_price": xau,
        "btc_price": btc,
        "us10y_yield": us10y,
        "us10y_real_yield": us10y_real,
        "fed_funds_rate": fed_funds,
        "dxy": dxy,
        "brent": brent,
        "vix": vix,
        "eurusd": eurusd,
        "btc_next_options_expiry": btc_deriv["next_options_expiry"],
        "btc_next_options_oi_btc": btc_deriv["next_options_expiry_btc"],
        "btc_futures_oi_btc": btc_deriv["futures_oi_btc"],
        "btc_futures_oi_pct30": btc_deriv["futures_oi_pct30"],
    }


# ---------------------------------------------------------------------------
# Technical level detection from M15 data
# ---------------------------------------------------------------------------

def _server_adjusted_bars(bars: pd.DataFrame, server_utc_offset_hours: int = 0) -> pd.DataFrame:
    """Attach true UTC timestamps for bars stored in broker server time."""
    work = bars.copy()
    ts = pd.to_datetime(work["timestamp"], utc=True)
    if server_utc_offset_hours:
        ts = ts - pd.Timedelta(hours=server_utc_offset_hours)
    work["_brief_timestamp"] = ts
    return work


def _brief_timestamp(bars: pd.DataFrame) -> pd.Series:
    if "_brief_timestamp" in bars.columns:
        return pd.to_datetime(bars["_brief_timestamp"], utc=True)
    return pd.to_datetime(bars["timestamp"], utc=True)


def _bars_for_utc_date(bars: pd.DataFrame, date_str: str, server_utc_offset_hours: int = 0) -> pd.DataFrame:
    work = _server_adjusted_bars(bars, server_utc_offset_hours)
    return work[_brief_timestamp(work).dt.date.astype(str) == date_str].copy()


def _bars_before_utc_date(bars: pd.DataFrame, date_str: str, server_utc_offset_hours: int = 0) -> pd.DataFrame:
    work = _server_adjusted_bars(bars, server_utc_offset_hours)
    return work[_brief_timestamp(work).dt.date.astype(str) < date_str].copy()


def _last_sunday(year: int, month: int) -> pd.Timestamp:
    day = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)
    return day - pd.Timedelta(days=(day.weekday() + 1) % 7)


def _ic_markets_server_utc_offset_hours(date_str: str) -> int:
    """IC Markets MT5 server is UTC+2 in winter and UTC+3 during European DST."""
    day = pd.Timestamp(date_str)
    dst_start = _last_sunday(day.year, 3)
    dst_end = _last_sunday(day.year, 10)
    return 3 if dst_start.date() <= day.date() < dst_end.date() else 2


def _session_range(bars: pd.DataFrame, session: str) -> dict:
    """Extract session OHLC. session: 'asia'|'london'|'ny'"""
    # UTC hours
    windows = {
        "asia":   (0, 8),
        "london": (8, 13),
        "ny":     (13, 20),
    }
    h_start, h_end = windows[session]
    session_ts = _brief_timestamp(bars)
    mask = (session_ts.dt.hour >= h_start) & (session_ts.dt.hour < h_end)
    s = bars[mask]
    if s.empty:
        return {}
    return {
        "open":  round(float(s["open"].iloc[0]), 2),
        "high":  round(float(s["high"].max()), 2),
        "low":   round(float(s["low"].min()), 2),
        "close": round(float(s["close"].iloc[-1]), 2),
    }


def _swing_levels(bars: pd.DataFrame, n_bars: int = 192) -> dict:
    """Detect swing high/low zones from last n_bars (default = 2 days of M15)."""
    recent = bars.tail(n_bars)
    if len(recent) < 20:
        return {}

    highs = recent["high"]
    lows = recent["low"]

    # Resistance: top 10% of highs
    resist_floor = highs.quantile(0.88)
    resist_ceil = highs.max()
    # Support: bottom 10% of lows
    support_ceil = lows.quantile(0.12)
    support_floor = lows.min()

    # ATR (simple 14-period)
    atr_bars = recent.copy()
    prev_close = atr_bars["close"].shift(1)
    tr = pd.concat([
        atr_bars["high"] - atr_bars["low"],
        (atr_bars["high"] - prev_close).abs(),
        (atr_bars["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = round(float(tr.rolling(14).mean().iloc[-1]), 2)

    return {
        "resistance_high": round(float(resist_ceil), 2),
        "resistance_low":  round(float(resist_floor), 2),
        "support_high":    round(float(support_ceil), 2),
        "support_floor":   round(float(support_floor), 2),
        "range_mid":       round(float((resist_floor + support_ceil) / 2), 2),
        "atr":             atr,
    }


def _bias_from_structure(bars: pd.DataFrame) -> str:
    """Determine daily_bias from recent M15 price structure."""
    recent = bars.tail(96)  # last 24h
    if len(recent) < 20:
        return "NEUTRAL"
    close_now = float(recent["close"].iloc[-1])
    close_24h_ago = float(recent["close"].iloc[0])
    ema50 = float(recent["close"].ewm(span=50, adjust=False).mean().iloc[-1])

    # Price above 50-EMA of last 24h AND net positive = BUY bias
    if close_now > ema50 and close_now > close_24h_ago:
        return "BUY"
    elif close_now < ema50 and close_now < close_24h_ago:
        return "SELL"
    else:
        return "NEUTRAL"


def _multi_day_levels(bars: pd.DataFrame, today_str: str, n_days: int = 5, server_utc_offset_hours: int = 0) -> dict:
    """Prev-day H/L/C, multi-day range, week range from M15 bars."""
    bars = _server_adjusted_bars(bars, server_utc_offset_hours)
    session_ts = _brief_timestamp(bars)
    bar_dates = sorted(
        set(session_ts[session_ts.dt.date.astype(str) < today_str].dt.date)
    )
    if not bar_dates:
        return {}

    def _day(d):
        b = bars[_brief_timestamp(bars).dt.date == d]
        if b.empty:
            return None
        return {
            "date":  str(d),
            "open":  round(float(b["open"].iloc[0]),   2),
            "high":  round(float(b["high"].max()),     2),
            "low":   round(float(b["low"].min()),      2),
            "close": round(float(b["close"].iloc[-1]), 2),
        }

    recent_days = [s for s in (_day(d) for d in bar_dates[-n_days:]) if s]
    prev_day  = recent_days[-1] if recent_days else {}
    all_highs = [d["high"] for d in recent_days]
    all_lows  = [d["low"]  for d in recent_days]

    prev_ts    = pd.Timestamp(bar_dates[-1])
    week_start = prev_ts - pd.Timedelta(days=prev_ts.weekday())
    week_mask  = (
        (_brief_timestamp(bars).dt.date >= week_start.date())
        & (_brief_timestamp(bars).dt.date.astype(str) < today_str)
    )
    wb = bars[week_mask]

    return {
        "prev_day":     prev_day,
        "prev_3d_high": round(max(all_highs[-3:]), 2) if len(all_highs) >= 3 else None,
        "prev_3d_low":  round(min(all_lows[-3:]),  2) if len(all_lows)  >= 3 else None,
        "prev_5d_high": round(max(all_highs), 2) if all_highs else None,
        "prev_5d_low":  round(min(all_lows),  2) if all_lows  else None,
        "week_high":    round(float(wb["high"].max()), 2) if not wb.empty else None,
        "week_low":     round(float(wb["low"].min()),  2) if not wb.empty else None,
        "recent_days":  recent_days,
    }


def _ema200(bars: pd.DataFrame) -> float | None:
    """200-period EMA of close from M15 bars. None if fewer than 200 bars."""
    if len(bars) < 200:
        return None
    return round(float(bars["close"].ewm(span=200, adjust=False).mean().iloc[-1]), 2)


def _session_vwap(bars: pd.DataFrame, today_str: str, server_utc_offset_hours: int = 0) -> dict:
    """Session VWAP anchored at Asia 00:00, London 08:00, NY 13:00 UTC.

    VWAP = Σ(typical_price × volume) / Σ(volume) from anchor to latest bar.
    """
    today_bars = _bars_for_utc_date(bars, today_str, server_utc_offset_hours)
    if today_bars.empty:
        return {}

    today_bars["_tp"] = (today_bars["high"] + today_bars["low"] + today_bars["close"]) / 3
    vol_col = next((c for c in ("volume", "<TICKVOL>") if c in today_bars.columns), None)

    def _vwap_from(hour: int) -> float | None:
        s = today_bars[_brief_timestamp(today_bars).dt.hour >= hour]
        if s.empty:
            return None
        if vol_col is not None:
            vol = s[vol_col].astype(float)
            total_vol = vol.sum()
            if total_vol > 0:
                return round(float((s["_tp"] * vol).sum() / total_vol), 2)
        # Fallback: equal-weight mean of typical price
        return round(float(s["_tp"].mean()), 2)

    return {
        "asia_vwap":   _vwap_from(0),
        "london_vwap": _vwap_from(8),
        "ny_vwap":     _vwap_from(13),
    }


def _double_touch_alerts(
    bars: pd.DataFrame,
    today_str: str,
    resist_levels: dict[str, float],
    support_levels: dict[str, float],
    atr: float,
    server_utc_offset_hours: int = 0,
) -> list[dict]:
    """Detect double-top / double-bottom patterns at key levels in today's session.

    Hierarchy: PDH/PDL (strongest) → premarket H/L → intraday H/L.
    Touch tolerance: ATR × 0.15.
    Two or more bar touches within tolerance = alert.
    """
    today_bars = _bars_for_utc_date(bars, today_str, server_utc_offset_hours)
    if today_bars.empty or atr <= 0:
        return []

    tol = atr * 0.15
    alerts: list[dict] = []

    for name, level in resist_levels.items():
        touches = today_bars[
            (today_bars["high"] >= level - tol) &
            (today_bars["high"] <= level + tol * 2)
        ]
        if len(touches) >= 2:
            alerts.append({
                "level_name":      name,
                "level_price":     level,
                "touch_type":      "double_top",
                "touch_count":     int(len(touches)),
                "last_touch_time": str(_brief_timestamp(touches).iloc[-1]),
                "signal":          "SELL on rejection — stop above level",
            })

    for name, level in support_levels.items():
        touches = today_bars[
            (today_bars["low"] <= level + tol) &
            (today_bars["low"] >= level - tol * 2)
        ]
        if len(touches) >= 2:
            alerts.append({
                "level_name":      name,
                "level_price":     level,
                "touch_type":      "double_bottom",
                "touch_count":     int(len(touches)),
                "last_touch_time": str(_brief_timestamp(touches).iloc[-1]),
                "signal":          "BUY on bounce — stop below level",
            })

    return alerts


def _timeframe_structure(bars: pd.DataFrame) -> dict:
    """1H structure (resampled from M15) + M15 8h pattern."""
    bars_ts = bars.set_index("timestamp")[["open", "high", "low", "close"]]
    h1 = bars_ts.resample("1h").agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"),   close=("close", "last"),
    ).dropna()

    h1_structure = "NEUTRAL"
    if len(h1) >= 10:
        last  = h1.tail(10)
        highs = last["high"].values
        lows  = last["low"].values
        hh = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i - 1])
        lh = sum(1 for i in range(1, len(highs)) if highs[i] < highs[i - 1])
        hl = sum(1 for i in range(1, len(lows))  if lows[i]  > lows[i - 1])
        ll = sum(1 for i in range(1, len(lows))  if lows[i]  < lows[i - 1])
        bull = hh + hl
        bear = lh + ll
        if bull >= 12:
            h1_structure = "BULLISH"
        elif bear >= 12:
            h1_structure = "BEARISH"

    # M15 pattern from last 32 bars (~8h)
    m15 = bars.tail(32)
    m15_pattern = "RANGE"
    if len(m15) >= 16:
        base = bars.tail(96)
        prev_c = base["close"].shift(1)
        tr = pd.concat([
            base["high"] - base["low"],
            (base["high"] - prev_c).abs(),
            (base["low"]  - prev_c).abs(),
        ], axis=1).max(axis=1)
        atr = float(tr.rolling(14).mean().iloc[-1])

        rng   = float(m15["high"].max() - m15["low"].min())
        body  = float(m15["close"].iloc[-1] - m15["open"].iloc[0])
        close = float(m15["close"].iloc[-1])
        mid   = float((m15["high"].max() + m15["low"].min()) / 2)

        if rng < atr * 1.5:
            m15_pattern = "RANGE"
        elif abs(body) > rng * 0.55 and close > mid:
            m15_pattern = "BREAKOUT"
        elif abs(body) > rng * 0.55 and close < mid:
            m15_pattern = "CONTINUATION"
        elif close < mid:
            m15_pattern = "REJECTION"

    verdict_map = {
        ("BEARISH", "REJECTION"):    "SELL_BIAS",
        ("BEARISH", "CONTINUATION"): "SELL_BIAS",
        ("BEARISH", "RANGE"):        "SELL_WATCH",
        ("BULLISH", "BREAKOUT"):     "BUY_BIAS",
        ("BULLISH", "RANGE"):        "BUY_WATCH",
    }
    return {
        "h1_structure":    h1_structure,
        "m15_pattern":     m15_pattern,
        "combined_verdict": verdict_map.get((h1_structure, m15_pattern), "WAIT"),
    }


def _scenario_maps(
    current_price: float,
    multi_day: dict,
    sell_setup: dict,
    buy_setup: dict,
    atr: float,
) -> list[dict]:
    """Four named conditional entry scenarios with pre-built entry/stop/TP/RR."""
    pd_high = multi_day.get("prev_day", {}).get("high")
    pd_low  = multi_day.get("prev_day", {}).get("low")
    p3_high = multi_day.get("prev_3d_high")
    p3_low  = multi_day.get("prev_3d_low")

    def _rr(entry_mid: float, stop: float, target: float) -> float:
        risk   = abs(entry_mid - stop)
        reward = abs(target - entry_mid)
        return round(reward / risk, 2) if risk > 0 else 0.0

    scenes: list[dict] = []

    # 1. SELL_RETEST — M15 rejection from sell zone
    sz_hi = sell_setup.get("zone_high") or (sell_setup.get("entry") or [None, None])[1]
    sz_lo = sell_setup.get("zone_low")  or (sell_setup.get("entry") or [None, None])[0]
    if sz_hi and sz_lo:
        s_stop = sell_setup.get("stop", round(sz_hi + atr, 2))
        s_t1   = pd_low if pd_low and pd_low < sz_lo else sell_setup.get("t1", round(sz_lo - atr * 2, 2))
        s_t2   = p3_low if p3_low and p3_low < s_t1  else sell_setup.get("t2", round(sz_lo - atr * 4, 2))
        em     = (sz_hi + sz_lo) / 2
        scenes.append({
            "name":             "SELL_RETEST",
            "condition":        f"M15 rejection at {sz_lo:.0f}–{sz_hi:.0f} + 5m lower high",
            "entry":            [sz_lo, sz_hi],
            "stop":             s_stop,
            "t1":               s_t1,
            "t2":               s_t2,
            "rr_t1":            _rr(em, s_stop, s_t1),
            "rr_t2":            _rr(em, s_stop, s_t2),
            "risk_pts":         round(abs(em - s_stop), 2),
            "confidence_base":  65,
            "invalidation":     f"Close above {s_stop:.0f}",
        })

    # 2. BUY_EXHAUST — M15 higher low + 5m break above buy zone
    bz_lo = buy_setup.get("zone_low")  or (buy_setup.get("entry") or [None, None])[0]
    bz_hi = buy_setup.get("zone_high") or (buy_setup.get("entry") or [None, None])[1]
    if bz_lo and bz_hi:
        b_stop = buy_setup.get("stop", round(bz_lo - atr, 2))
        b_t1   = pd_high if pd_high and pd_high > bz_hi else buy_setup.get("t1", round(bz_hi + atr * 2, 2))
        b_t2   = p3_high if p3_high and p3_high > b_t1  else buy_setup.get("t2", round(bz_hi + atr * 4, 2))
        em     = (bz_lo + bz_hi) / 2
        scenes.append({
            "name":             "BUY_EXHAUST",
            "condition":        f"M15 higher low at {bz_lo:.0f}–{bz_hi:.0f} + 5m break above",
            "entry":            [bz_lo, bz_hi],
            "stop":             b_stop,
            "t1":               b_t1,
            "t2":               b_t2,
            "rr_t1":            _rr(em, b_stop, b_t1),
            "rr_t2":            _rr(em, b_stop, b_t2),
            "risk_pts":         round(abs(em - b_stop), 2),
            "confidence_base":  60,
            "invalidation":     f"Close below {b_stop:.0f}",
        })

    # 3. BREAKDOWN_CONT — continuation sell below prev day low
    if pd_low:
        e_hi   = round(pd_low - atr * 0.1, 2)
        e_lo   = round(pd_low - atr * 0.8, 2)
        bkd_stop = round(pd_low + atr * 0.5, 2)
        bkd_t1   = p3_low if p3_low and p3_low < e_lo else round(pd_low - atr * 2.5, 2)
        bkd_t2   = round(bkd_t1 - atr * 2, 2)
        em       = (e_hi + e_lo) / 2
        scenes.append({
            "name":             "BREAKDOWN_CONT",
            "condition":        f"<{pd_low:.0f} (prev day low) + 30m acceptance + failed reclaim",
            "entry":            [e_lo, e_hi],
            "stop":             bkd_stop,
            "t1":               bkd_t1,
            "t2":               bkd_t2,
            "rr_t1":            _rr(em, bkd_stop, bkd_t1),
            "rr_t2":            _rr(em, bkd_stop, bkd_t2),
            "risk_pts":         round(abs(em - bkd_stop), 2),
            "confidence_base":  63,
            "invalidation":     f"Reclaim above {pd_low:.0f}",
        })

    # 4. BREAKOUT_CONT — continuation buy above prev day high
    if pd_high:
        e_lo   = round(pd_high + atr * 0.1, 2)
        e_hi   = round(pd_high + atr * 0.8, 2)
        bko_stop = round(pd_high - atr * 0.5, 2)
        bko_t1   = p3_high if p3_high and p3_high > e_hi else round(pd_high + atr * 2.5, 2)
        bko_t2   = round(bko_t1 + atr * 2, 2)
        em       = (e_lo + e_hi) / 2
        scenes.append({
            "name":             "BREAKOUT_CONT",
            "condition":        f">{pd_high:.0f} (prev day high) + 30m acceptance + successful retest",
            "entry":            [e_lo, e_hi],
            "stop":             bko_stop,
            "t1":               bko_t1,
            "t2":               bko_t2,
            "rr_t1":            _rr(em, bko_stop, bko_t1),
            "rr_t2":            _rr(em, bko_stop, bko_t2),
            "risk_pts":         round(abs(em - bko_stop), 2),
            "confidence_base":  63,
            "invalidation":     f"Fail below {pd_high:.0f}",
        })

    return scenes


def _best_anchor(side: str, current_price: float,
                 today_asia: dict, yest_asia: dict, yest_london: dict, yest_ny: dict,
                 swing_levels: dict) -> tuple[float, str]:
    """Return (anchor_price, label) for the tightest valid intraday entry anchor.

    SELL anchor: nearest session high ABOVE current price.
    BUY anchor:  nearest session low BELOW current price.
    Falls back to swing percentile level if no session data qualifies.
    """
    candidates: list[tuple[float, str]] = []

    if side == "SELL":
        # Collect session highs that are above current price
        for label, sess in [
            ("today_asia_high", today_asia),
            ("yest_london_high", yest_london),
            ("yest_ny_high", yest_ny),
            ("yest_asia_high", yest_asia),
        ]:
            h = sess.get("high")
            if h and h > current_price:
                candidates.append((h, label))
        # Pick the closest (lowest) qualifying high
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0]
        # Fallback: swing resistance floor
        return swing_levels["resistance_low"], "swing_resist"
    else:
        # Collect session lows that are below current price
        for label, sess in [
            ("today_asia_low", today_asia),
            ("yest_london_low", yest_london),
            ("yest_ny_low", yest_ny),
            ("yest_asia_low", yest_asia),
        ]:
            lo = sess.get("low")
            if lo and lo < current_price:
                candidates.append((lo, label))
        # Pick the closest (highest) qualifying low
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0]
        return swing_levels["support_high"], "swing_support"


def _compute_levels(current_price: float, levels: dict, side: str, atr: float,
                    anchor: float | None = None) -> dict:
    """Compute entry zone, stop, targets. Uses anchor if provided for tighter zones."""
    if anchor is not None:
        if side == "SELL":
            # Entry zone: just below anchor (1 ATR wide), stop 2 ATR above anchor
            zone_high = round(anchor + atr * 0.30, 2)
            zone_low  = round(anchor - atr * 1.00, 2)
            stop      = round(anchor + atr * 2.00, 2)
            # T1: nearest swing support below entry; T2: deeper swing low
            t1_swing = levels["support_high"]  # 12th pct of lows
            t1 = round(t1_swing if t1_swing < zone_low else anchor - atr * 3.0, 2)
            t2 = round(levels["support_floor"] if levels["support_floor"] < t1 else anchor - atr * 5.0, 2)
        else:
            # Entry zone: just above anchor (1 ATR wide), stop 2 ATR below anchor
            zone_low  = round(anchor - atr * 0.30, 2)
            zone_high = round(anchor + atr * 1.00, 2)
            stop      = round(anchor - atr * 2.00, 2)
            # T1: nearest swing resistance above entry; T2: higher swing high
            t1_swing = levels["resistance_low"]  # 88th pct of highs
            t1 = round(t1_swing if t1_swing > zone_high else anchor + atr * 3.0, 2)
            t2 = round(levels["resistance_high"] if levels["resistance_high"] > t1 else anchor + atr * 5.0, 2)
    else:
        if side == "SELL":
            zone_high = levels["resistance_high"]
            zone_low  = levels["resistance_low"]
            stop      = round(zone_high + atr * 0.5, 2)
            t1        = round(levels["range_mid"], 2)
            t2        = round(levels["support_high"], 2)
        else:
            zone_high = levels["support_high"]
            zone_low  = levels["support_floor"]
            stop      = round(zone_low - atr * 0.5, 2)
            t1        = round(levels["range_mid"], 2)
            t2        = round(levels["resistance_low"], 2)

    inv = stop
    risk = abs(zone_low - stop) if side == "SELL" else abs(zone_high - stop)
    reward_t1 = abs(t1 - (zone_low if side == "SELL" else zone_high))
    rr_t1 = round(reward_t1 / risk, 2) if risk > 0 else 0.0

    return {
        "zone_high": zone_high,
        "zone_low": zone_low,
        "stop": stop,
        "t1": t1,
        "t2": t2,
        "invalidation": inv,
        "rr_t1": rr_t1,
        "risk_pts": round(risk, 2),
    }


# ---------------------------------------------------------------------------
# Brief assembly
# ---------------------------------------------------------------------------

def build_symbol_block(sym: str, current_price: float, bars: pd.DataFrame,
                       today_str: str, iv_pct: float | None = None,
                       server_utc_offset_hours: int = 0) -> dict:
    """Build one symbol block for the brief JSON."""
    today_bars = _bars_for_utc_date(bars, today_str, server_utc_offset_hours)
    yesterday = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    yest_bars = _bars_for_utc_date(bars, yesterday, server_utc_offset_hours)

    levels = _swing_levels(bars)
    if not levels:
        return {}

    atr = levels["atr"]
    bias = _bias_from_structure(bars)
    multi_day = _multi_day_levels(bars, today_str, server_utc_offset_hours=server_utc_offset_hours)
    tf_structure = _timeframe_structure(bars)
    ema_200 = _ema200(bars)
    vwap = _session_vwap(bars, today_str, server_utc_offset_hours=server_utc_offset_hours)

    # Sessions from today (may be partial) and yesterday
    today_asia   = _session_range(today_bars, "asia")   if not today_bars.empty else {}
    yest_asia    = _session_range(yest_bars,  "asia")   if not yest_bars.empty else {}
    yest_london  = _session_range(yest_bars,  "london") if not yest_bars.empty else {}
    yest_ny      = _session_range(yest_bars,  "ny")     if not yest_bars.empty else {}

    sell_anchor, sell_anchor_label = _best_anchor(
        "SELL", current_price, today_asia, yest_asia, yest_london, yest_ny, levels)
    buy_anchor, buy_anchor_label = _best_anchor(
        "BUY",  current_price, today_asia, yest_asia, yest_london, yest_ny, levels)

    sell = _compute_levels(current_price, levels, "SELL", atr, anchor=sell_anchor)
    buy  = _compute_levels(current_price, levels, "BUY",  atr, anchor=buy_anchor)
    scenarios = _scenario_maps(current_price, multi_day, sell, buy, atr)

    # Double-touch detection: PDH/PDL → premarket H/L → intraday H/L
    pd_high = multi_day.get("prev_day", {}).get("high")
    pd_low  = multi_day.get("prev_day", {}).get("low")
    pm_high = today_asia.get("high")   # premarket = Asia session for 24h markets
    pm_low  = today_asia.get("low")
    id_high = round(float(today_bars["high"].max()), 2) if not today_bars.empty else None
    id_low  = round(float(today_bars["low"].min()),  2) if not today_bars.empty else None

    resist = {k: v for k, v in {
        "PDH": pd_high, "PM_HIGH": pm_high, "ID_HIGH": id_high
    }.items() if v is not None}
    support = {k: v for k, v in {
        "PDL": pd_low, "PM_LOW": pm_low, "ID_LOW": id_low
    }.items() if v is not None}
    dt_alerts = _double_touch_alerts(bars, today_str, resist, support, atr, server_utc_offset_hours=server_utc_offset_hours)

    # Session context string for MD
    asia_range_pts = round(today_asia.get("high", 0) - today_asia.get("low", 0), 2) if today_asia else None
    session_context = {
        "today_asia":    today_asia,
        "yest_asia":     yest_asia,
        "yest_london":   yest_london,
        "yest_ny":       yest_ny,
        "sell_anchor":   sell_anchor,
        "sell_anchor_label": sell_anchor_label,
        "buy_anchor":    buy_anchor,
        "buy_anchor_label": buy_anchor_label,
        "asia_range_pts": asia_range_pts,
        "premarket_high": pm_high,
        "premarket_low":  pm_low,
        "intraday_high":  id_high,
        "intraday_low":   id_low,
        "server_utc_offset_hours": server_utc_offset_hours,
        "timestamp_basis": "server_time_corrected_to_utc" if server_utc_offset_hours else "utc",
    }

    # Anti-bias zone is the one opposing the bias
    anti_bias_side = "BUY" if bias == "SELL" else "SELL"
    anti_bias_rr = buy["rr_t1"] if anti_bias_side == "BUY" else sell["rr_t1"]

    return {
        "current_price": round(current_price, 2),
        "daily_bias": bias,
        "anti_bias_side": anti_bias_side,
        "anti_bias_rr": anti_bias_rr,
        "atr": atr,
        "sell_confidence": 0.62 if bias == "SELL" else 0.55,
        "buy_confidence":  0.62 if bias == "BUY"  else 0.55,
        "session_context": session_context,
        "session_ranges": {
            "today_asia":       today_asia,
            "yesterday_asia":   yest_asia,
            "yesterday_london": yest_london,
            "yesterday_ny":     yest_ny,
        },
        "key_levels": {
            "bearish_invalidation": sell["invalidation"],
            "sell_zone_high":       sell["zone_high"],
            "sell_zone_low":        sell["zone_low"],
            "no_trade_high":        sell["zone_low"],
            "no_trade_low":         buy["zone_high"],
            "buy_zone_high":        buy["zone_high"],
            "buy_zone_low":         buy["zone_low"],
            "breakdown_trigger":    buy["stop"],
            "range_mid":            levels["range_mid"],
        },
        "sell_targets": [sell["t1"], sell["t2"]],
        "buy_targets":  [buy["t1"],  buy["t2"]],
        "top_scenario": f"{'SELL' if bias == 'SELL' else 'BUY'}_REJECTION",
        "top_scenario_entry":        [sell["zone_low"], sell["zone_high"]] if bias == "SELL" else [buy["zone_low"], buy["zone_high"]],
        "top_scenario_targets":      [sell["t1"], sell["t2"]] if bias == "SELL" else [buy["t1"], buy["t2"]],
        "top_scenario_invalidation": sell["invalidation"] if bias == "SELL" else buy["invalidation"],
        "sell_setup": {
            "entry":       [sell["zone_low"], sell["zone_high"]],
            "stop":        sell["stop"],
            "t1":          sell["t1"],
            "t2":          sell["t2"],
            "rr_t1":       sell["rr_t1"],
            "risk_pts":    sell["risk_pts"],
        },
        "buy_setup": {
            "entry":       [buy["zone_low"], buy["zone_high"]],
            "stop":        buy["stop"],
            "t1":          buy["t1"],
            "t2":          buy["t2"],
            "rr_t1":       buy["rr_t1"],
            "risk_pts":    buy["risk_pts"],
        },
        "multi_day":           multi_day,
        "timeframe_structure": tf_structure,
        "scenarios":           scenarios,
        "iv_walls":            _iv_walls(current_price, iv_pct) if iv_pct else None,
        "ema_200":             ema_200,
        "session_vwap":        vwap,
        "double_touch_alerts": dt_alerts,
    }


def build_brief(date_str: str, macro: dict, td_key: str,
                xau_iv_pct: float | None = None) -> dict:
    """Assemble the full brief JSON."""
    xau_bars = pd.read_parquet(XAU_PARQUET)
    btc_bars = pd.read_parquet(BTC_PARQUET)
    xau_bars = xau_bars.sort_values("timestamp")
    btc_bars = btc_bars.sort_values("timestamp")
    xau_server_utc_offset = _ic_markets_server_utc_offset_hours(date_str)

    # Use data up to (not including) brief date to avoid look-ahead
    xau_bars = _bars_before_utc_date(xau_bars, date_str, xau_server_utc_offset)
    btc_bars = _bars_before_utc_date(btc_bars, date_str)

    # Fallback to last M15 close if live price unavailable (market closed)
    xau_price = macro["xau_price"] or round(float(xau_bars["close"].iloc[-1]), 2)
    btc_price = macro["btc_price"] or round(float(btc_bars["close"].iloc[-1]), 2)
    macro["xau_price"] = xau_price
    macro["btc_price"] = btc_price

    btc_iv_pct = _fetch_btc_atm_iv(btc_price)

    xau_block = build_symbol_block(
        "XAUUSD",
        xau_price,
        xau_bars,
        date_str,
        iv_pct=xau_iv_pct,
        server_utc_offset_hours=xau_server_utc_offset,
    )
    btc_block = build_symbol_block("BTCUSD", btc_price, btc_bars, date_str, iv_pct=btc_iv_pct)

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build BTC-specific macro note
    btc_deriv_note = ""
    if macro.get("btc_next_options_expiry"):
        oi_btc = macro.get("btc_next_options_oi_btc", 0)
        oi_usd = round(oi_btc * (macro["btc_price"] or 84000) / 1e9, 1) if oi_btc else "?"
        btc_deriv_note = (
            f" BTC options expiry {macro['btc_next_options_expiry']}: ~{oi_usd}bn notional."
            f" Futures OI: {macro.get('btc_futures_oi_btc','?'):.0f} BTC"
            f" ({macro.get('btc_futures_oi_pct30','?')}th pct 30d)." if macro.get("btc_futures_oi_btc") else ""
        )

    return {
        "issued_at": now_utc,
        "date": date_str,
        "source": "auto_generated_v1",
        "sessions_present": ["auto"],
        "sessions_expected": ["us_open"],
        "macro": {
            "fed_funds_rate": macro["fed_funds_rate"],
            "us10y_yield": macro["us10y_yield"],
            "us10y_real_yield": macro["us10y_real_yield"],
            "dxy": macro["dxy"],
            "brent": macro["brent"],
            "vix": macro["vix"],
            "us_markets_open": False,
            "btc_options_next_expiry": macro.get("btc_next_options_expiry"),
            "btc_options_next_expiry_oi_btc": macro.get("btc_next_options_oi_btc"),
            "btc_futures_oi_btc": macro.get("btc_futures_oi_btc"),
            "btc_futures_oi_pct30d": macro.get("btc_futures_oi_pct30"),
            "note": (
                f"Auto-generated. XAU={macro['xau_price']} BTC={macro['btc_price']} "
                f"FedFunds={macro['fed_funds_rate']}% 10Y={macro['us10y_yield']}% "
                f"RealYield={macro['us10y_real_yield']}% DXY~{macro['dxy']} "
                f"Brent={macro['brent']} VIX~{macro['vix']}.{btc_deriv_note}"
                f" CHECK economic calendar manually — Finnhub free tier blocked."
            ),
            "event_gate": {
                "active": False,
                "reason": "Check investing.com/economic-calendar manually for today's major releases."
            },
        },
        "XAUUSD": xau_block,
        "BTCUSD": btc_block,
    }


# ---------------------------------------------------------------------------
# Session MD writer
# ---------------------------------------------------------------------------

def _lot_size(risk_usd: float, risk_pts: float, sym: str) -> str:
    """Compute lot size string."""
    if sym == "XAUUSD":
        lots = risk_usd / (risk_pts * 100) if risk_pts > 0 else 0
    else:
        lots = risk_usd / risk_pts if risk_pts > 0 else 0
    return f"{lots:.4f}"


def write_session_md(date_str: str, brief: dict, macro: dict):
    """Write the session markdown file."""
    day = datetime.strptime(date_str, "%Y-%m-%d")
    day_name = day.strftime("%A %d %B %Y")

    xau = brief.get("XAUUSD", {})
    btc = brief.get("BTCUSD", {})
    m = brief.get("macro", {})

    lines = [
        f"# Paper Session — {day_name}",
        "",
        f"Brief: `data/daily_briefs/{date_str}_levels.json`",
        "Account: $10,000 notional | Risk: $100/trade (1%)",
        f"Session opened: AUTO-GENERATED",
        "",
        "---",
        "",
        "## Current status: WATCHING — no positions open",
        "",
        "**AUTO BRIEF** — review key levels before trading. Add macro narrative manually if needed.",
        "",
        "---",
        "",
        "## Macro snapshot",
        "",
        "| Indicator | Value |",
        "|---|---|",
        f"| Fed funds | {m.get('fed_funds_rate', '?')}% |",
        f"| US 10Y yield | {m.get('us10y_yield', '?')}% |",
        f"| US 10Y real yield | {m.get('us10y_real_yield', '?')}% |",
        f"| DXY (est) | ~{m.get('dxy', '?')} |",
        f"| Brent | ${m.get('brent', '?')} |",
        f"| VIX (est) | ~{m.get('vix', '?')} |",
        f"| BTC options expiry | {m.get('btc_options_next_expiry', '?')} ({int(m.get('btc_options_next_expiry_oi_btc') or 0):,} BTC OI) |",
        f"| BTC futures OI | {int(m.get('btc_futures_oi_btc') or 0):,} BTC — {m.get('btc_futures_oi_pct30d', '?')}th pct 30d |",
        "| **⚠️ Event gate** | Check investing.com/economic-calendar manually |",
        "",
        "---",
    ]

    for sym, block in [("XAUUSD", xau), ("BTCUSD", btc)]:
        if not block:
            continue
        bias = block.get("daily_bias", "?")
        anti = block.get("anti_bias_side", "?")
        anti_rr = block.get("anti_bias_rr", 0)
        price = block.get("current_price", "?")
        sell = block.get("sell_setup", {})
        buy = block.get("buy_setup", {})
        kl = block.get("key_levels", {})
        atr = block.get("atr", "?")

        anti_flag = f"★ ANTI-BIAS ({anti_rr:.2f}R)" if anti_rr >= 1.0 else f"SKIP R:R={anti_rr:.2f}"

        sc = block.get("session_context", {})
        asia_today = sc.get("today_asia", {})
        asia_yest  = sc.get("yest_asia", {})
        lon_yest   = sc.get("yest_london", {})

        ctx_lines = []
        if asia_today.get("high"):
            rng = sc.get("asia_range_pts", "?")
            ctx_lines.append(
                f"Asia range: {asia_today['low']} – {asia_today['high']} ({rng} pts)"
            )
        if asia_yest.get("high"):
            ctx_lines.append(
                f"Yest Asia: {asia_yest['low']} – {asia_yest['high']}"
            )
        if lon_yest.get("high"):
            ctx_lines.append(
                f"Yest London: {lon_yest['low']} – {lon_yest['high']}"
            )
        sell_anc = sc.get("sell_anchor")
        buy_anc  = sc.get("buy_anchor")
        if sell_anc:
            ctx_lines.append(
                f"SELL anchor: {sell_anc} ({sc.get('sell_anchor_label','')})"
            )
        if buy_anc:
            ctx_lines.append(
                f"BUY anchor: {buy_anc} ({sc.get('buy_anchor_label','')})"
            )

        md = block.get("multi_day", {})
        tfs = block.get("timeframe_structure", {})
        prev_d = md.get("prev_day", {})
        scenarios = block.get("scenarios", [])
        ema200 = block.get("ema_200")
        vwap_data = block.get("session_vwap", {})
        dt_alerts = block.get("double_touch_alerts", [])
        sc_ctx = block.get("session_context", {})

        # EMA/VWAP inline string
        ema_str = f"EMA200 `{ema200}`" if ema200 else "EMA200 `—`"
        asia_vwap = vwap_data.get("asia_vwap")
        lon_vwap  = vwap_data.get("london_vwap")
        ny_vwap   = vwap_data.get("ny_vwap")
        vwap_parts = []
        if asia_vwap:   vwap_parts.append(f"Asia VWAP `{asia_vwap}`")
        if lon_vwap:    vwap_parts.append(f"London VWAP `{lon_vwap}`")
        if ny_vwap:     vwap_parts.append(f"NY VWAP `{ny_vwap}`")
        vwap_str = " | ".join(vwap_parts) if vwap_parts else "VWAP `—`"

        lines += [
            "",
            f"## {sym} — {bias} lean",
            "",
            f"Current price ~{price} | ATR ~{atr} | Bias: **{bias}** | Anti-bias: **{anti}** {anti_flag}",
            "",
            f"**Structure:** 1H `{tfs.get('h1_structure','?')}` | M15 `{tfs.get('m15_pattern','?')}` | → **{tfs.get('combined_verdict','?')}**",
            f"**Levels:** {ema_str} | {vwap_str}",
        ]
        offset = sc_ctx.get("server_utc_offset_hours") or 0
        if offset:
            lines.append(f"**Timestamp basis:** IC Markets server time corrected by -{offset}h for UTC session logic.")

        # Double-touch alerts — highest priority block
        if dt_alerts:
            lines += ["", "### ⚡ DOUBLE-TOUCH ALERTS", ""]
            for alert in dt_alerts:
                icon = "🔴 DOUBLE TOP" if alert["touch_type"] == "double_top" else "🟢 DOUBLE BOTTOM"
                lines.append(
                    f"**{icon}** at `{alert['level_name']}` = {alert['level_price']} "
                    f"({alert['touch_count']}x touches) → {alert['signal']}"
                )
            lines.append("")

        # Pre-market / intraday levels summary
        pm_hi = sc_ctx.get("premarket_high")
        pm_lo = sc_ctx.get("premarket_low")
        id_hi = sc_ctx.get("intraday_high")
        id_lo = sc_ctx.get("intraday_low")
        level_rows = []
        if pm_hi: level_rows.append(f"| Pre-market high | **{pm_hi}** |")
        if pm_lo: level_rows.append(f"| Pre-market low  | **{pm_lo}** |")
        if id_hi and id_hi != pm_hi: level_rows.append(f"| Intraday high | {id_hi} |")
        if id_lo and id_lo != pm_lo: level_rows.append(f"| Intraday low  | {id_lo} |")
        if level_rows:
            lines += ["", "**Key intraday levels**", "", "| Level | Value |", "|---|---|"]
            lines.extend(level_rows)

        # Multi-day reference levels
        if prev_d:
            lines += [
                "",
                "**Multi-day reference levels**",
                "",
                "| Level | Value |",
                "|---|---|",
                f"| Prev day open | {prev_d.get('open','?')} |",
                f"| Prev day high | **{prev_d.get('high','?')}** |",
                f"| Prev day low  | **{prev_d.get('low','?')}** |",
                f"| Prev day close | {prev_d.get('close','?')} |",
                f"| 3-day high | {md.get('prev_3d_high','?')} |",
                f"| 3-day low  | {md.get('prev_3d_low','?')} |",
                f"| Week high  | {md.get('week_high','?')} |",
                f"| Week low   | {md.get('week_low','?')} |",
            ]

        # IV walls
        ivw = block.get("iv_walls")
        if ivw:
            em = ivw.get("iv_expected_move_daily", "?")
            lines += [
                "",
                "**IV walls (options-implied expected range)**",
                "",
                "| Level | Value | Probability |",
                "|---|---|---|",
                f"| IV (annualised) | {ivw.get('iv_pct','?')}% | — |",
                f"| Daily expected move | ±{em} | — |",
                f"| IV high (90%) | **{ivw.get('iv_high_90','?')}** | 90% stay below |",
                f"| IV low  (90%) | **{ivw.get('iv_low_90','?')}** | 90% stay above |",
                f"| IV high (68%) | {ivw.get('iv_high_68','?')} | 68% (1σ) |",
                f"| IV low  (68%) | {ivw.get('iv_low_68','?')} | 68% (1σ) |",
                "",
                "> Mean-revert at 90% walls. Entry on 5m confirmation. Stop beyond wall. "
                "10% of sessions break through — size accordingly.",
            ]

        if ctx_lines:
            lines += ["", "**Session context:** " + " | ".join(ctx_lines)]

        # Scenario decision tree
        if scenarios:
            lines += ["", "**Scenario decision tree** — confirm condition before entry", ""]
            lines += [
                "| Scenario | Condition | Entry | Stop | T1 | T2 | R:R T1 | R:R T2 |",
                "|---|---|---|---|---|---|---|---|",
            ]
            for sc in scenarios:
                e = sc.get("entry", ["?", "?"])
                entry_str = f"{e[0]:.0f}–{e[1]:.0f}" if len(e) == 2 else "?"
                lines.append(
                    f"| **{sc['name']}** | {sc['condition']} | {entry_str} |"
                    f" {sc.get('stop','?')} | {sc.get('t1','?')} | {sc.get('t2','?')} |"
                    f" {sc.get('rr_t1','?')}R | {sc.get('rr_t2','?')}R |"
                )
            lines.append("")

        lines.append("")

        for side_label, setup, side in [("SELL", sell, "SELL"), ("BUY", buy, "BUY")]:
            entry = setup.get("entry", [])
            stop = setup.get("stop")
            t1 = setup.get("t1")
            t2 = setup.get("t2")
            rr = setup.get("rr_t1", 0)
            rpts = setup.get("risk_pts", 0)
            lots = _lot_size(100, rpts, sym)
            anti_label = " ★ ANTI-BIAS" if side == anti and anti_rr >= 1.0 else ""
            pass_fail = "PASS" if rr >= 1.0 else f"FAIL R:R={rr}"

            lines += [
                f"### {side_label} setup{anti_label} — {pass_fail}",
                "",
                "| Field | Value |",
                "|---|---|",
                f"| **Entry zone** | {entry[0]:.2f} – {entry[1]:.2f} |" if entry else "| **Entry zone** | ? |",
                f"| **Stop** | {stop} |",
                f"| **T1** | {t1} |",
                f"| **T2** | {t2} |",
                f"| **Risk pts** | {rpts} |",
                f"| **Lots (1% risk)** | {lots} |",
                f"| **R:R to T1** | {rr} |",
                "",
            ]

        lines += [
            "---",
        ]

    lines += [
        "",
        "## Session outcome (fill in tonight/tomorrow)",
        "",
        "| Symbol | Setup | Triggered? | Result | PnL pts | R multiple |",
        "|---|---|---|---|---|---|",
        "| XAUUSD | SELL | | | | |",
        "| XAUUSD | BUY | | | | |",
        "| BTCUSD | SELL | | | | |",
        "| BTCUSD | BUY | | | | |",
    ]

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{date_str}.md"
    path.write_text("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------------------------------
# Validate via existing validator
# ---------------------------------------------------------------------------

def validate_brief(brief_path: Path) -> str:
    import subprocess
    result = subprocess.run(
        ["venv/bin/python", "scripts/validate_brief.py", str(brief_path), "--atr", "20", "--min-rr", "1.0"],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                   help="Brief date YYYY-MM-DD (default: today UTC)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-extend", action="store_true", help="Skip M15 data extension")
    p.add_argument("--xau-iv", type=float, default=None,
                   help="XAU annualised implied vol %% (e.g. 14.5). Source: GVZ index on TradingView.")
    args = p.parse_args()

    td_key = os.environ.get("TWELVE_DATA_KEY")
    fred_key = os.environ.get("FRED_API_KEY")
    if not td_key or not fred_key:
        sys.exit("Set TWELVE_DATA_KEY and FRED_API_KEY env vars. Run via keychain injection.")

    date_str = args.date
    print(f"Generating brief for {date_str} ...")

    # Extend M15 data first (unless skipped)
    if not args.no_extend:
        print("Extending M15 data ...")
        import subprocess
        result = subprocess.run(
            ["venv/bin/python", "scripts/extend_m15_data.py"],
            capture_output=True, text=True, cwd=str(ROOT),
            env={**os.environ, "TWELVE_DATA_KEY": td_key}
        )
        if result.returncode != 0:
            print(f"  Warning: data extend failed: {result.stderr.strip()[:200]}")
        else:
            print(f"  {result.stdout.strip().splitlines()[-1] if result.stdout.strip() else 'done'}")

    print("Fetching macro data ...")
    macro = fetch_macro(td_key, fred_key)
    print(f"  XAU={macro['xau_price']} BTC={macro['btc_price']} "
          f"10Y={macro['us10y_yield']}% DXY~{macro['dxy']} "
          f"Brent={macro['brent']} VIX~{macro['vix']}")

    print("Computing levels ...")
    brief = build_brief(date_str, macro, td_key, xau_iv_pct=args.xau_iv)

    brief_path = BRIEFS_DIR / f"{date_str}_levels.json"

    if args.dry_run:
        print("\n[dry-run] Brief JSON:")
        print(json.dumps(brief, indent=2)[:2000])
        print("\n[dry-run] Not written to disk.")
        return

    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(json.dumps(brief, indent=2) + "\n")
    print(f"Brief written: {brief_path}")

    val = validate_brief(brief_path)
    print(f"\nValidator:\n{val}")

    md_path = write_session_md(date_str, brief, macro)
    print(f"Session written: {md_path}")

    # Print anti-bias summary
    print("\n=== ANTI-BIAS SETUPS (take these first) ===")
    for sym in ("XAUUSD", "BTCUSD"):
        block = brief.get(sym, {})
        if not block:
            continue
        anti = block.get("anti_bias_side")
        anti_rr = block.get("anti_bias_rr", 0)
        setup = block.get(f"{'buy' if anti == 'BUY' else 'sell'}_setup", {})
        entry = setup.get("entry", [])
        stop = setup.get("stop")
        t1 = setup.get("t1")
        flag = "TAKE" if anti_rr >= 1.0 else f"SKIP (R:R {anti_rr:.2f} < 1.0)"
        print(f"  {sym}: {anti} | entry {entry[0]:.0f}-{entry[1]:.0f} | stop {stop:.0f} | T1 {t1:.0f} | R:R {anti_rr:.2f} → {flag}")


if __name__ == "__main__":
    main()

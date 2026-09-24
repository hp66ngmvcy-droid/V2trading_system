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
import os
import sys
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
    # Fallback: use FRED DTWEXBGS broad dollar index scaled to DXY range
    if eurusd:
        dxy = round(-100 * eurusd + 215, 2)
    else:
        broad = _fred_latest("DTWEXBGS", fred_key)
        # DTWEXBGS ~115-125 maps roughly to DXY ~98-108 via linear scale
        dxy = round((broad - 119.5) * 0.55 + 101.0, 2) if broad else None

    # US 10Y yield from FRED (1-day lag acceptable)
    us10y = _fred_latest("DGS10", fred_key)

    # VIX proxy — VIXY typically trades at 55-70% of spot VIX
    vix = round(vixy * 0.88, 1) if vixy else None

    return {
        "xau_price": xau,
        "btc_price": btc,
        "us10y_yield": us10y,
        "dxy": dxy,
        "brent": brent,
        "vix": vix,
        "eurusd": eurusd,
    }


# ---------------------------------------------------------------------------
# Technical level detection from M15 data
# ---------------------------------------------------------------------------

def _session_range(bars: pd.DataFrame, session: str) -> dict:
    """Extract session OHLC. session: 'asia'|'london'|'ny'"""
    # UTC hours
    windows = {
        "asia":   (0, 8),
        "london": (8, 13),
        "ny":     (13, 20),
    }
    h_start, h_end = windows[session]
    mask = (bars["timestamp"].dt.hour >= h_start) & (bars["timestamp"].dt.hour < h_end)
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


def _compute_levels(current_price: float, levels: dict, side: str, atr: float) -> dict:
    """Compute entry zone, stop, targets for a given side."""
    if side == "SELL":
        # Sell zone: near resistance
        zone_high = levels["resistance_high"]
        zone_low = levels["resistance_low"]
        stop = round(zone_high + atr * 0.5, 2)
        t1 = round(levels["range_mid"], 2)
        t2 = round(levels["support_high"], 2)
        inv = stop
    else:
        # Buy zone: near support
        zone_high = levels["support_high"]
        zone_low = levels["support_floor"]
        stop = round(zone_low - atr * 0.5, 2)
        t1 = round(levels["range_mid"], 2)
        t2 = round(levels["resistance_low"], 2)
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
                       today_str: str) -> dict:
    """Build one symbol block for the brief JSON."""
    today_bars = bars[bars["timestamp"].dt.date.astype(str) == today_str]
    yesterday = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    yest_bars = bars[bars["timestamp"].dt.date.astype(str) == yesterday]

    levels = _swing_levels(bars)
    if not levels:
        return {}

    atr = levels["atr"]
    bias = _bias_from_structure(bars)

    # Sessions from today (may be partial) and yesterday
    today_session = _session_range(today_bars, "asia") if not today_bars.empty else {}
    yest_london = _session_range(yest_bars, "london") if not yest_bars.empty else {}
    yest_ny = _session_range(yest_bars, "ny") if not yest_bars.empty else {}

    sell = _compute_levels(current_price, levels, "SELL", atr)
    buy = _compute_levels(current_price, levels, "BUY", atr)

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
        "session_ranges": {
            "today_asia":    today_session,
            "yesterday_london": yest_london,
            "yesterday_ny": yest_ny,
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
    }


def build_brief(date_str: str, macro: dict, td_key: str) -> dict:
    """Assemble the full brief JSON."""
    xau_bars = pd.read_parquet(XAU_PARQUET)
    btc_bars = pd.read_parquet(BTC_PARQUET)
    xau_bars = xau_bars.sort_values("timestamp")
    btc_bars = btc_bars.sort_values("timestamp")

    # Use data up to (not including) brief date to avoid look-ahead
    xau_bars = xau_bars[xau_bars["timestamp"].dt.date.astype(str) < date_str]
    btc_bars = btc_bars[btc_bars["timestamp"].dt.date.astype(str) < date_str]

    # Fallback to last M15 close if live price unavailable (market closed)
    xau_price = macro["xau_price"] or round(float(xau_bars["close"].iloc[-1]), 2)
    btc_price = macro["btc_price"] or round(float(btc_bars["close"].iloc[-1]), 2)
    macro["xau_price"] = xau_price
    macro["btc_price"] = btc_price

    xau_block = build_symbol_block("XAUUSD", xau_price, xau_bars, date_str)
    btc_block = build_symbol_block("BTCUSD", btc_price, btc_bars, date_str)

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "issued_at": now_utc,
        "date": date_str,
        "source": "auto_generated_v1",
        "sessions_present": ["auto"],
        "sessions_expected": ["us_open"],
        "macro": {
            "fed_funds_rate": None,
            "us10y_yield": macro["us10y_yield"],
            "dxy": macro["dxy"],
            "brent": macro["brent"],
            "vix": macro["vix"],
            "us_markets_open": False,
            "note": (
                f"Auto-generated. XAU={macro['xau_price']} BTC={macro['btc_price']} "
                f"10Y={macro['us10y_yield']}% DXY~{macro['dxy']} "
                f"Brent={macro['brent']} VIX~{macro['vix']}"
            ),
            "event_gate": {"active": False, "reason": "No event gate on auto brief — check economic calendar."},
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
        f"| US 10Y yield | {m.get('us10y_yield', '?')}% |",
        f"| DXY (est) | ~{m.get('dxy', '?')} |",
        f"| Brent | ${m.get('brent', '?')} |",
        f"| VIX (est) | ~{m.get('vix', '?')} |",
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

        lines += [
            "",
            f"## {sym} — {bias} lean",
            "",
            f"Current price ~{price} | ATR ~{atr} | Bias: **{bias}** | Anti-bias: **{anti}** {anti_flag}",
            "",
        ]

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
    brief = build_brief(date_str, macro, td_key)

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

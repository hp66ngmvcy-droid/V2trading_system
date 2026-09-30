"""Read-only brief validator.

Reads a _levels.json file and reports executable R:R for each symbol/side
candidate using the same calculation logic as key_level_sweep_v1.
No bar data required — uses ATR from a command-line argument or a default.

Usage:
    python scripts/validate_brief.py data/daily_briefs/2026-09-07_levels.json
    python scripts/validate_brief.py data/daily_briefs/2026-09-07_levels.json --atr 18 --min-rr 1.0
    python scripts/validate_brief.py data/daily_briefs/ --atr 18  # validate all briefs in dir
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


MIN_RR_DEFAULT = 1.0
WICK_RATIO_DEFAULT = 0.40
ATR_MULTIPLIER = 2.0


def _finite(v: object, label: str) -> float:
    f = float(v)  # type: ignore[arg-type]
    if not math.isfinite(f):
        raise ValueError(f"{label} is not finite: {v!r}")
    return f


def _validate_symbol(date: str, symbol: str, sym_data: dict, atr: float, min_rr: float) -> list[dict]:
    rows = []
    kl = sym_data.get("key_levels", {})
    # Prefer direction-specific targets (new format); fallback to top_scenario_targets
    sell_tgts = sym_data.get("sell_targets") or sym_data.get("top_scenario_targets", [])
    buy_tgts  = sym_data.get("buy_targets")  or sym_data.get("top_scenario_targets", [])

    # ---- SELL candidate ----
    sell_conf = float(sym_data.get("sell_confidence", 0))
    szl = kl.get("sell_zone_low")
    szh = kl.get("sell_zone_high")
    bi = kl.get("bearish_invalidation")

    if szl is not None and bi is not None:
        try:
            szl_f = _finite(szl, "sell_zone_low")
            bi_f = _finite(bi, "bearish_invalidation")
            # Executable entry = sell_zone_low (conservative: bar just enters zone)
            entry = szl_f
            t1 = float(sell_tgts[0]) if len(sell_tgts) > 0 else entry - atr * 2
            if t1 >= entry:
                t1 = entry - atr * 2
            risk = bi_f - entry
            reward = entry - t1
            rr_raw = reward / risk if risk > 0 else 0.0
            rejection = None
            if risk <= 0:
                rejection = f"risk <= 0 (bi={bi_f}, entry={entry})"
            elif rr_raw < min_rr:
                rejection = f"R:R {rr_raw:.3f} < min {min_rr}"
            rows.append({
                "date": date, "symbol": symbol, "side": "SELL",
                "entry": entry, "stop": bi_f, "target": t1,
                "risk": round(risk, 2), "reward": round(reward, 2),
                "rr_raw": round(rr_raw, 3),
                "confidence": sell_conf,
                "t1_source": "sell_targets[0]" if len(sell_tgts) > 0 and float(sell_tgts[0]) < entry else "atr_fallback",
                "rejection": rejection,
            })
        except (ValueError, TypeError) as e:
            rows.append({"date": date, "symbol": symbol, "side": "SELL", "rejection": f"ERROR: {e}"})

    # ---- BUY candidate ----
    buy_conf = float(sym_data.get("buy_confidence", 0))
    bzl = kl.get("buy_zone_low")
    bzh = kl.get("buy_zone_high")
    raw_anchor = kl.get("asia_liquidity_low") or kl.get("breakdown_trigger")

    if bzh is not None:
        try:
            bzh_f = _finite(bzh, "buy_zone_high")
            bzl_f = _finite(bzl, "buy_zone_low") if bzl is not None else 0.0
            stop_anchor = _finite(raw_anchor, "stop_anchor") if raw_anchor is not None else bzl_f - atr
            stop = stop_anchor - (atr * ATR_MULTIPLIER)
            # Executable entry = buy_zone_high (conservative: bar just enters zone from above)
            entry = bzh_f
            szl_fallback = float(kl.get("sell_zone_low", entry + atr * 2))
            t1_buy = float(buy_tgts[0]) if len(buy_tgts) > 0 else szl_fallback
            if t1_buy <= entry:
                t1_buy = szl_fallback
            risk = entry - stop
            reward = t1_buy - entry
            rr_raw = reward / risk if risk > 0 else 0.0
            rejection = None
            if risk <= 0:
                rejection = f"risk <= 0 (stop={stop:.2f}, entry={entry})"
            elif rr_raw < min_rr:
                rejection = f"R:R {rr_raw:.3f} < min {min_rr}"
            rows.append({
                "date": date, "symbol": symbol, "side": "BUY",
                "entry": entry, "stop": round(stop, 2), "target": t1_buy,
                "risk": round(risk, 2), "reward": round(reward, 2),
                "rr_raw": round(rr_raw, 3),
                "confidence": buy_conf,
                "t1_source": "buy_targets[0]" if len(buy_tgts) > 0 and float(buy_tgts[0]) > entry else "szl_fallback",
                "stop_anchor_source": "asia_liquidity_low" if kl.get("asia_liquidity_low") else (
                    "breakdown_trigger" if kl.get("breakdown_trigger") else "atr_fallback"
                ),
                "rejection": rejection,
            })
        except (ValueError, TypeError) as e:
            rows.append({"date": date, "symbol": symbol, "side": "BUY", "rejection": f"ERROR: {e}"})

    return rows


def validate_file(path: Path, atr: float, min_rr: float) -> list[dict]:
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return [{"date": path.stem, "symbol": "?", "side": "?", "rejection": f"JSON ERROR: {e}"}]

    date = data.get("date", path.stem.split("_")[0])
    issued_at = data.get("issued_at", "MISSING")
    rows = []

    for key, val in data.items():
        if not isinstance(val, dict) or "key_levels" not in val:
            continue
        rows.extend(_validate_symbol(date, key, val, atr, min_rr))

    for r in rows:
        r["issued_at"] = issued_at
    return rows


def _print_table(rows: list[dict]) -> None:
    if not rows:
        print("No candidates found.")
        return

    header = f"{'DATE':<12} {'SYM':<7} {'SIDE':<5} {'ENTRY':>8} {'STOP':>9} {'TARGET':>8} {'RISK':>7} {'REWARD':>7} {'R:R':>6} {'CONF':>5}  STATUS"
    print(header)
    print("-" * len(header))

    pass_count = fail_count = 0
    for r in rows:
        status = "PASS" if r.get("rejection") is None else f"FAIL — {r['rejection']}"
        if r.get("rejection") is None:
            pass_count += 1
        else:
            fail_count += 1
        entry = r.get("entry", "?")
        stop = r.get("stop", "?")
        target = r.get("target", "?")
        risk = r.get("risk", "?")
        reward = r.get("reward", "?")
        rr = r.get("rr_raw", "?")
        conf = r.get("confidence", "?")
        print(
            f"{r.get('date','?'):<12} {r.get('symbol','?'):<7} {r.get('side','?'):<5} "
            f"{entry!s:>8} {stop!s:>9} {target!s:>8} {risk!s:>7} {reward!s:>7} {rr!s:>6} {conf!s:>5}  {status}"
        )

    print()
    print(f"Candidates: {pass_count} PASS  {fail_count} FAIL  (min_rr={args.min_rr}, atr={args.atr})")


def _collect_paths(target: str) -> list[Path]:
    p = Path(target)
    if p.is_dir():
        return sorted(p.glob("*_levels.json"))
    return [p]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate _levels.json brief R:R candidates.")
    parser.add_argument("target", help="Path to _levels.json file or directory of briefs")
    parser.add_argument("--atr", type=float, default=20.0, help="ATR estimate (default: 20.0)")
    parser.add_argument("--min-rr", type=float, default=MIN_RR_DEFAULT, dest="min_rr",
                        help=f"Minimum R:R threshold (default: {MIN_RR_DEFAULT})")
    args = parser.parse_args()

    paths = _collect_paths(args.target)
    if not paths:
        print(f"No _levels.json files found at: {args.target}", file=sys.stderr)
        sys.exit(1)

    all_rows: list[dict] = []
    for p in paths:
        all_rows.extend(validate_file(p, args.atr, args.min_rr))

    _print_table(all_rows)

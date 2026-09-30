#!/usr/bin/env python3
"""Anti-bias strategy checker — runs fully locally, no API needed.

Usage:
    venv/bin/python scripts/check_strategy.py           # all trades, R:R >= 1.0
    venv/bin/python scripts/check_strategy.py --all-rr  # include sub-1.0 R:R
    venv/bin/python scripts/check_strategy.py --detail  # show every trade
"""

import argparse
from collections import Counter
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.paper_game_sim import load_brief_setups, simulate_setup
from scripts.market_data_io import read_frame

BRIEFS_DIR  = ROOT / "data" / "daily_briefs"
XAU_PARQUET = ROOT / "data" / "validated" / "XAUUSD_M15.parquet"
BTC_PARQUET = ROOT / "data" / "validated" / "BTCUSD_M15.parquet"
SESSION_END = {"XAUUSD": "17:00"}
LLM_LABELS  = ROOT / "data" / "research" / "llm_bias_labels.json"


def _load_llm_labels() -> dict:
    return json.loads(LLM_LABELS.read_text()) if LLM_LABELS.exists() else {}


def run_all(min_rr: float, detail: bool):
    xau = read_frame(ROOT, 'XAUUSD')
    btc = read_frame(ROOT, 'BTCUSD')
    data_map = {"XAUUSD": xau, "BTCUSD": btc}
    gold_source_blocked = bool((pd.to_datetime(xau.timestamp, utc=True).dt.dayofweek == 5).any())
    llm_labels = _load_llm_labels()

    trades = []
    for bf in sorted(BRIEFS_DIR.glob("*_levels.json")):
        raw = json.loads(bf.read_text())
        setups = load_brief_setups(bf, min_rr=min_rr)
        for s in setups:
            sym, date = s["symbol"], s["date"]
            bars = data_map[sym]
            day = bars[bars["timestamp"].dt.date.astype(str) == date].copy()
            day = day.sort_values("timestamp").reset_index(drop=True)
            end = SESSION_END.get(sym)
            if end:
                h, m = int(end.split(":")[0]), int(end.split(":")[1])
                day = day[day["timestamp"].dt.hour * 60 + day["timestamp"].dt.minute < h * 60 + m]

            result = simulate_setup(s, day.iloc[:0] if sym == 'XAUUSD' and gold_source_blocked else day)
            if sym == 'XAUUSD' and gold_source_blocked:
                result['outcome'] = 'SOURCE_REVIEW_REQUIRED'

            # Anti-bias flag: setup direction opposes daily_bias (brief analyst)
            sym_data   = raw.get(sym, {})
            bias       = sym_data.get("daily_bias", "NEUTRAL").upper()
            side       = s["side"]
            is_anti    = (bias == "SELL" and side == "BUY") or (bias == "BUY" and side == "SELL")
            is_neutral = bias == "NEUTRAL"

            # LLM blind agent arm
            llm_rec  = llm_labels.get(sym, {}).get(date, {})
            llm_bias = llm_rec.get("llm_bias", "UNKNOWN")
            is_llm_anti = (llm_bias == "SELL" and side == "BUY") or (llm_bias == "BUY" and side == "SELL")

            trades.append({**result, "bias": bias, "anti_bias": is_anti, "neutral": is_neutral,
                           "llm_bias": llm_bias, "llm_anti_bias": is_llm_anti})

    return trades


def stats(group: list, label: str):
    print(f"  {label}: outcomes={dict(Counter(t['outcome'] for t in group))}")
    # All zone-hit trades counted in attempted; INVALID_FILL and ISSUED_AT_UNKNOWN
    # are excluded from completed so they don't inflate WR or AvgR.
    attempted = [t for t in group if t["zone_hit"]]
    open_eod  = [t for t in attempted if t["outcome"] == "OPEN_EOD"]
    invalid   = [t for t in attempted if t["outcome"] == "INVALID_FILL"]
    unknown   = [t for t in attempted if t.get("issued_at") == "ISSUED_AT_UNKNOWN"]
    completed = [t for t in group if t['outcome'] in ('SL', 'TP_T1')]
    if not completed:
        suffix = "".join([
            f" OPEN_EOD={len(open_eod)}" if open_eod else "",
            f" INVALID={len(invalid)}" if invalid else "",
        ])
        print(f"  {label:<32} N=0{suffix}")
        return
    wins    = [t for t in completed if t["outcome"].startswith("TP")]
    wr      = len(wins) / len(completed) * 100
    avg     = sum(t["r_multiple"] for t in completed) / len(completed)
    avg_net = sum(t.get("r_multiple_net", t["r_multiple"]) for t in completed) / len(completed)
    tot     = sum(t["r_multiple"] for t in completed)
    suffix  = "".join([
        f" OPEN_EOD={len(open_eod)}" if open_eod else "",
        f" INVALID={len(invalid)}"   if invalid  else "",
        f" AVAIL_UNKNOWN={len(unknown)}" if unknown else "",
    ])
    print(f"  {label:<32} N={len(completed):3d}  WR={wr:5.1f}%  "
          f"AvgR={avg:+.2f}R (net {avg_net:+.2f}R)  TotalR={tot:+.2f}R{suffix}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-rr",  action="store_true", help="Include sub-1.0 R:R setups")
    ap.add_argument("--detail",  action="store_true", help="Print every trade")
    args = ap.parse_args()

    min_rr = 0.0 if args.all_rr else 1.0
    trades = run_all(min_rr=min_rr, detail=args.detail)

    anti    = [t for t in trades if t["anti_bias"]]
    with_b  = [t for t in trades if not t["anti_bias"] and not t["neutral"]]
    neutral = [t for t in trades if t["neutral"]]
    all_t   = trades

    # 5th arm: LLM blind agent (only trades where LLM label exists and is directional)
    llm_anti  = [t for t in trades if t.get("llm_anti_bias")]
    llm_with  = [t for t in trades if t.get("llm_bias") not in ("UNKNOWN", "NEUTRAL")
                 and not t.get("llm_anti_bias")]
    llm_known = [t for t in trades if t.get("llm_bias") not in ("UNKNOWN",)]

    rr_label = "all R:R" if args.all_rr else "R:R >= 1.0"
    print(f"\n=== STRATEGY BREAKDOWN ({rr_label}) ===\n")
    print('DIAGNOSTIC_ONLY: boundary_touch_v2. Source/brief authenticity, costs and prospective validation unresolved.')
    stats(all_t,   "All (including neutral)")
    stats(anti,    "Anti-brief-bias ★")
    stats(with_b,  "With-brief-bias")
    stats(neutral, "Neutral-bias (informational)")
    if llm_known:
        print()
        stats(llm_anti, "Anti-LLM-agent-bias ◆")
        stats(llm_with, "With-LLM-agent-bias")
    else:
        print("\n  LLM agent labels: none yet — run scripts/llm_blind_agent_labels.py")

    # Per-instrument breakdown
    for sym in sorted({t["symbol"] for t in trades}):
        sym_t    = [t for t in trades if t["symbol"] == sym]
        sym_anti = [t for t in sym_t if t["anti_bias"]]
        sym_with = [t for t in sym_t if not t["anti_bias"] and not t["neutral"]]
        sym_neut = [t for t in sym_t if t["neutral"]]
        print(f"\n--- {sym} ---")
        stats(sym_anti, f"  Anti-brief-bias ★")
        stats(sym_with, f"  With-brief-bias")
        stats(sym_neut, f"  Neutral-bias")

    if args.all_rr:
        anti_hi  = [t for t in anti if t["rr_t1"] >= 1.0]
        anti_lo  = [t for t in anti if t["rr_t1"] <  1.0]
        print()
        stats(anti_hi, "  Anti-bias + R:R >= 1.0")
        stats(anti_lo, "  Anti-bias + R:R <  1.0")

    if args.detail:
        print(f"\n{'DATE':<12} {'SYM':<7} {'SIDE':<5} {'BIAS':<8} {'ANTI':>4} {'RR':>5} {'OUTCOME':<10} {'R':>6}")
        print("-" * 68)
        for t in trades:
            flag = "★" if t["anti_bias"] else ("N" if t["neutral"] else " ")
            out  = t["outcome"]
            print(f"  {t['date']:<12} {t['symbol']:<7} {t['side']:<5} {t['bias']:<8} "
                  f"{flag:>4} {t['rr_t1']:>5.2f} {out:<10} {t['r_multiple']:>+6.2f}R")

    print()
    print("NOTE: Sizing SUSPENDED. No validated edge. Ambiguous outcomes excluded, not zero-return trades.")


if __name__ == "__main__":
    main()

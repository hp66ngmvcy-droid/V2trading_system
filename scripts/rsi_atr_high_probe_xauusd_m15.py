#!/usr/bin/env python3
"""Targeted high-ATR probe for rsi_trend_v4 XAUUSD M15.

Hypothesis: ATR 3.0+ dramatically improves win rate by avoiding normal
volatility clip. Tests RSI 33-43 (adequate trade count) x ATR 3.0-5.0
x RR 2.0-2.5 x EMA_GATE True only (EMA_GATE=False hurts win rate).

40 combos, ~13 min. Saves to data/results/rsi_atr_high_probe_XAUUSD_M15.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tar_system.backtest.engine import run_backtest
from tar_system.data.store import load_feature_data
from tar_system.scoring.scorer import score_strategy
from tar_system.strategies.rsi_trend_v4 import RSITrendV4
from tar_system.validation.walk_forward import run_walk_forward

SYMBOL, TIMEFRAME = "XAUUSD", "M15"
OUTPUT = ROOT / "data/results/rsi_atr_high_probe_XAUUSD_M15.json"

RSI_BUY_LEVELS  = [33, 35, 38, 40, 43]
ATR_MULTIPLIERS = [3.0, 3.5, 4.0, 4.5, 5.0]
REWARD_RISKS    = [2.0, 2.5]
EMA_GATES       = [True]

TOTAL = len(RSI_BUY_LEVELS) * len(ATR_MULTIPLIERS) * len(REWARD_RISKS) * len(EMA_GATES)

def run() -> None:
    features = load_feature_data(SYMBOL, TIMEFRAME).sort_values("timestamp")
    print(f"Loaded {len(features)} rows | {TOTAL} combos")
    results, done, t0 = [], 0, time.time()

    for buy in RSI_BUY_LEVELS:
        sell = 100 - buy
        for atr in ATR_MULTIPLIERS:
            for rr in REWARD_RISKS:
                for ema_gate in EMA_GATES:
                    s = RSITrendV4(rsi_buy_level=float(buy), rsi_sell_level=float(sell),
                                   atr_multiplier=atr, reward_risk=rr, ema_cross_gate=ema_gate)
                    bt = run_backtest(features, s, audit_decisions=False)
                    wf = run_walk_forward(features, s, 200, 50, audit_decisions=False, max_splits=10)
                    wf_m = {"window_count": wf.window_count, "wf_verdict": wf.wf_verdict,
                             "bootstrap_ci": wf.bootstrap_ci}
                    sc = score_strategy(bt.metrics, wf_m, TIMEFRAME, require_walk_forward=True)
                    done += 1
                    eta = (time.time()-t0)/done * (TOTAL-done)
                    row = {
                        "rsi_buy_level": buy, "rsi_sell_level": sell,
                        "atr_multiplier": atr, "reward_risk": rr, "ema_cross_gate": ema_gate,
                        "trades": bt.metrics.get("total_trades", 0),
                        "win_rate": round(bt.metrics.get("win_rate", 0), 4),
                        "profit_factor": round(bt.metrics.get("profit_factor", 0), 4),
                        "max_drawdown": round(bt.metrics.get("max_drawdown", 0), 6),
                        "score": round(sc.score, 4), "verdict": sc.verdict,
                        "wf_verdict": wf_m.get("wf_verdict", "N/A"),
                        "wf_windows": wf_m.get("window_count", 0),
                    }
                    results.append(row)
                    flag = " *** KEEP ***" if sc.verdict == "KEEP" else ""
                    print(f"[{done}/{TOTAL}] RSI {buy}/{sell} ATR {atr} RR {rr} | "
                          f"trades={row['trades']} win={row['win_rate']:.2f} "
                          f"PF={row['profit_factor']} score={row['score']} "
                          f"{sc.verdict} WF={wf.wf_verdict} ETA {eta/60:.1f}m{flag}", flush=True)

    results.sort(key=lambda r: r["score"], reverse=True)
    OUTPUT.write_text(json.dumps({"symbol": SYMBOL, "timeframe": TIMEFRAME,
                                   "results": results}, indent=2))
    print(f"\nSaved → {OUTPUT}")
    print("\nTop 10:")
    for r in results[:10]:
        print(f"  RSI {r['rsi_buy_level']}/{r['rsi_sell_level']} ATR {r['atr_multiplier']} "
              f"RR {r['reward_risk']} | trades={r['trades']} win={r['win_rate']:.2f} "
              f"PF={r['profit_factor']} score={r['score']} {r['verdict']}")
    keep = [r for r in results if r["verdict"] == "KEEP"]
    print(f"\nKEEP hits: {len(keep)}")
    for r in keep:
        print(f"  ** KEEP ** RSI {r['rsi_buy_level']}/{r['rsi_sell_level']} "
              f"ATR {r['atr_multiplier']} RR {r['reward_risk']} | "
              f"trades={r['trades']} PF={r['profit_factor']} score={r['score']}")

if __name__ == "__main__":
    run()

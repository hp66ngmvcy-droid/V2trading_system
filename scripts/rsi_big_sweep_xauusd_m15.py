#!/usr/bin/env python3
"""Full parameter sweep for rsi_trend_v4 on XAUUSD M15.

Dimensions:
  rsi_buy_level    : 30, 33, 35, 38, 40, 43, 45
  atr_multiplier   : 1.5, 2.0, 2.5, 3.0
  reward_risk      : 2.0, 2.5, 3.0, 3.5, 4.0
  ema_cross_gate   : True, False

Total: 7 x 4 x 5 x 2 = 280 combos.
Saves ranked results to data/results/rsi_big_sweep_XAUUSD_M15.json.
Logs progress to data/results/rsi_big_sweep_XAUUSD_M15.log.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tar_system.backtest.engine import run_backtest
from tar_system.data.store import load_feature_data
from tar_system.scoring.scorer import score_strategy
from tar_system.strategies.rsi_trend_v4 import RSITrendV4
from tar_system.validation.walk_forward import run_walk_forward

SYMBOL = "XAUUSD"
TIMEFRAME = "M15"
OUTPUT = ROOT / "data/results/rsi_big_sweep_XAUUSD_M15.json"
LOG = ROOT / "data/results/rsi_big_sweep_XAUUSD_M15.log"

RSI_BUY_LEVELS = [30, 33, 35, 38, 40, 43, 45]
ATR_MULTIPLIERS = [1.5, 2.0, 2.5, 3.0]
REWARD_RISKS = [2.0, 2.5, 3.0, 3.5, 4.0]
EMA_GATES = [True, False]

TOTAL = len(RSI_BUY_LEVELS) * len(ATR_MULTIPLIERS) * len(REWARD_RISKS) * len(EMA_GATES)


def log(msg: str, fh) -> None:
    print(msg, flush=True)
    fh.write(msg + "\n")
    fh.flush()


def run_sweep() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    features = load_feature_data(SYMBOL, TIMEFRAME).sort_values("timestamp")

    with open(LOG, "w") as fh:
        log(f"rsi_big_sweep started — {TOTAL} combos — {SYMBOL} {TIMEFRAME}", fh)
        log(f"Loaded {len(features)} rows", fh)

        results = []
        done = 0
        t0 = time.time()

        for buy_level in RSI_BUY_LEVELS:
            sell_level = 100 - buy_level
            for atr_mult in ATR_MULTIPLIERS:
                for rr in REWARD_RISKS:
                    for ema_gate in EMA_GATES:
                        strategy = RSITrendV4(
                            rsi_buy_level=float(buy_level),
                            rsi_sell_level=float(sell_level),
                            atr_multiplier=atr_mult,
                            reward_risk=rr,
                            ema_cross_gate=ema_gate,
                        )
                        bt = run_backtest(features, strategy, audit_decisions=False)

                        wf_metrics: dict = {}
                        if len(features) >= 250:
                            wf = run_walk_forward(
                                features, strategy, 200, 50,
                                audit_decisions=False, max_splits=10
                            )
                            wf_metrics = {
                                "window_count": wf.window_count,
                                "wf_verdict": wf.wf_verdict,
                                "bootstrap_ci": wf.bootstrap_ci,
                            }

                        score = score_strategy(
                            bt.metrics, wf_metrics, TIMEFRAME, require_walk_forward=True
                        )

                        row = {
                            "rsi_buy_level": buy_level,
                            "rsi_sell_level": sell_level,
                            "atr_multiplier": atr_mult,
                            "reward_risk": rr,
                            "ema_cross_gate": ema_gate,
                            "trades": bt.metrics.get("total_trades", 0),
                            "win_rate": round(bt.metrics.get("win_rate", 0), 4),
                            "profit_factor": round(bt.metrics.get("profit_factor", 0), 4),
                            "max_drawdown": round(bt.metrics.get("max_drawdown", 0), 6),
                            "expectancy": round(bt.metrics.get("expectancy", 0), 6),
                            "score": round(score.score, 4),
                            "verdict": score.verdict,
                            "wf_verdict": wf_metrics.get("wf_verdict", "N/A"),
                            "wf_windows": wf_metrics.get("window_count", 0),
                        }
                        results.append(row)
                        done += 1

                        elapsed = time.time() - t0
                        eta = (elapsed / done) * (TOTAL - done) if done > 0 else 0
                        log(
                            f"[{done}/{TOTAL}] RSI {buy_level}/{sell_level} "
                            f"ATR {atr_mult} RR {rr} EMA_GATE {ema_gate} | "
                            f"trades={row['trades']} win={row['win_rate']:.2f} "
                            f"PF={row['profit_factor']} score={row['score']} "
                            f"{row['verdict']} WF={row['wf_verdict']} | "
                            f"ETA {eta/60:.1f}m",
                            fh
                        )

                        # Save checkpoint every 20 combos
                        if done % 20 == 0:
                            sorted_so_far = sorted(results, key=lambda r: r["score"], reverse=True)
                            OUTPUT.write_text(json.dumps({
                                "symbol": SYMBOL, "timeframe": TIMEFRAME,
                                "strategy": "rsi_trend_v4",
                                "combos_run": done, "combos_total": TOTAL,
                                "results": sorted_so_far,
                            }, indent=2))

        results.sort(key=lambda r: r["score"], reverse=True)
        OUTPUT.write_text(json.dumps({
            "symbol": SYMBOL, "timeframe": TIMEFRAME,
            "strategy": "rsi_trend_v4",
            "combos_run": TOTAL, "combos_total": TOTAL,
            "results": results,
        }, indent=2))

        log(f"\nDone. Saved to {OUTPUT}", fh)
        log("\nTop 10:", fh)
        for r in results[:10]:
            log(
                f"  RSI {r['rsi_buy_level']}/{r['rsi_sell_level']} "
                f"ATR {r['atr_multiplier']} RR {r['reward_risk']} "
                f"EMA_GATE {r['ema_cross_gate']} | "
                f"trades={r['trades']} win={r['win_rate']:.2f} "
                f"PF={r['profit_factor']} score={r['score']} "
                f"{r['verdict']} WF={r['wf_verdict']}",
                fh
            )

        keep_hits = [r for r in results if r["verdict"] == "KEEP"]
        log(f"\nKEEP results: {len(keep_hits)}", fh)
        for r in keep_hits:
            log(f"  ** KEEP ** RSI {r['rsi_buy_level']}/{r['rsi_sell_level']} "
                f"ATR {r['atr_multiplier']} RR {r['reward_risk']} "
                f"EMA_GATE {r['ema_cross_gate']} | "
                f"PF={r['profit_factor']} score={r['score']}", fh)


if __name__ == "__main__":
    run_sweep()

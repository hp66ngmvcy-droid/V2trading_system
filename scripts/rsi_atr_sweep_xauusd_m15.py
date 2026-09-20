#!/usr/bin/env python3
"""RSI 38-40 + ATR multiplier sweep for rsi_trend_v4 on XAUUSD M15.

Tests rsi_buy_level in [38, 39, 40], atr_multiplier in [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0].
21 combos total. Saves ranked results to data/results/rsi_atr_sweep_XAUUSD_M15.json.
"""
from __future__ import annotations

import json
import sys
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
OUTPUT = ROOT / "data/results/rsi_atr_sweep_XAUUSD_M15.json"

RSI_BUY_LEVELS = [38, 39, 40]
ATR_MULTIPLIERS = [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]


def run_sweep() -> None:
    features = load_feature_data(SYMBOL, TIMEFRAME).sort_values("timestamp")
    print(f"Loaded {len(features)} rows of {SYMBOL} {TIMEFRAME}")

    results = []
    for buy_level in RSI_BUY_LEVELS:
        sell_level = 100 - buy_level
        for atr_mult in ATR_MULTIPLIERS:
            strategy = RSITrendV4(
                rsi_buy_level=float(buy_level),
                rsi_sell_level=float(sell_level),
                atr_multiplier=atr_mult,
            )
            bt = run_backtest(features, strategy, audit_decisions=False)

            wf_metrics: dict = {}
            if len(features) >= 250:
                wf = run_walk_forward(features, strategy, 200, 50, audit_decisions=False, max_splits=25)
                wf_metrics = {
                    "window_count": wf.window_count,
                    "wf_verdict": wf.wf_verdict,
                    "bootstrap_ci": wf.bootstrap_ci,
                }

            score = score_strategy(bt.metrics, wf_metrics, TIMEFRAME, require_walk_forward=True)

            row = {
                "rsi_buy_level": buy_level,
                "rsi_sell_level": sell_level,
                "atr_multiplier": atr_mult,
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
            print(
                f"RSI {buy_level}/{sell_level} ATR {atr_mult} | trades={row['trades']} | "
                f"PF={row['profit_factor']} | DD={row['max_drawdown']} | score={row['score']} | {row['verdict']}"
            )

    results.sort(key=lambda r: r["score"], reverse=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"symbol": SYMBOL, "timeframe": TIMEFRAME,
                                   "strategy": "rsi_trend_v4", "results": results}, indent=2))
    print(f"\nSaved to {OUTPUT}")
    print("\nTop 5:")
    for r in results[:5]:
        print(f"  RSI {r['rsi_buy_level']}/{r['rsi_sell_level']} ATR {r['atr_multiplier']} | "
              f"PF={r['profit_factor']} | DD={r['max_drawdown']} | score={r['score']} | {r['verdict']} | WF={r['wf_verdict']}")


if __name__ == "__main__":
    run_sweep()

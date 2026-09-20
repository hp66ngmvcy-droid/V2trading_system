"""
ARSB v1 plateau sweep — compression_atr_mult x buffer_mult
Pre-registration: ideas/inbox/idea-20260706-arsb-v1-plateau-sweep-pre-registration.md
Pass criteria: CI_lower>0, param_stability>=0.50, trades>=30
"""
from __future__ import annotations
import sys
import json
import itertools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from tar_system.backtest.engine import run_backtest
from tar_system.strategies.arsb_v1 import ArsbV1 as ARSBStrategy
from tar_system.scoring.scorer import score_strategy

SYMBOL = "XAUUSD"
TF = "M15"
RESULTS_PATH = Path("data/results/arsb_v1_plateau_sweep_results.json")
FEATURE_PATH = Path(f"data/features/{SYMBOL}_{TF}.parquet")
CONFIG_PATH = Path(f"configs/tuned/{SYMBOL}_{TF}_arsb_v1.json")

mult_range = list(range(8, 26, 1))
buffer_range = [round(x * 0.05, 2) for x in range(1, 7)]

features = pd.read_parquet(FEATURE_PATH)
if features.empty:
    print("ERROR: no feature data found")
    sys.exit(1)

with CONFIG_PATH.open("r", encoding="utf-8") as fh:
    tuned = json.load(fh)
optimal = tuned.get("optimal_config", {})
base_params = {
    "atr_cap": float(optimal.get("atr_cap", 11.97)),
    "entry_start_hour": int(optimal.get("session_start_utc", 8)),
    "entry_end_hour": int(optimal.get("session_end_utc", 17)),
    "d1_trend_filter": True,
}

results = []
total = len(mult_range) * len(buffer_range)
print(f"Sweep: {total} combinations ({len(mult_range)} mult × {len(buffer_range)} buffer)")

for i, (mult, buf) in enumerate(itertools.product(mult_range, buffer_range), 1):
    strategy = ARSBStrategy(compression_atr_mult=mult, buffer_mult=buf, **base_params)
    try:
        bt = run_backtest(features, strategy, audit_decisions=False)
        trades = bt.trades
        pf = bt.metrics.get("profit_factor", 0.0)
        scored = score_strategy(bt.metrics, None, TF, require_walk_forward=False)
        score = scored.score
        verdict = scored.verdict
    except Exception as e:
        trades, pf, score, verdict = 0, 0.0, 0.0, f"ERROR:{e}"

    results.append({
        "compression_atr_mult": mult,
        "buffer_mult": buf,
        "trade_count": trades,
        "profit_factor": pf,
        "score": score,
        "verdict": verdict,
    })
    if i % 18 == 0 or i == total:
        print(f"  {i}/{total}  mult={mult} buf={buf}  trades={trades} pf={pf:.2f} score={score:.1f}")

RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "pre_registration": "ideas/inbox/idea-20260706-arsb-v1-plateau-sweep-pre-registration.md",
    "symbol": SYMBOL,
    "timeframe": TF,
    "sweep": {
        "compression_atr_mult": {"start": 8, "end": 25, "step": 1},
        "buffer_mult": {"start": 0.05, "end": 0.30, "step": 0.05},
    },
    "locked_params": base_params,
    "evaluation": "in_sample_score_only",
    "results": results,
}
RESULTS_PATH.write_text(json.dumps(payload, indent=2))
print(f"\nSaved {len(results)} results → {RESULTS_PATH}")

scores = [r["score"] for r in results if r["score"] > 0 and "ERROR" not in r["verdict"]]
if scores:
    median_s = sorted(scores)[len(scores) // 2]
    peak = max(scores)
    flat_cells = sum(1 for s in scores if abs(s - median_s) < 5)
    flat_pct = flat_cells / len(scores) * 100
    print(f"\n--- Plateau analysis ---")
    print(f"  median score : {median_s:.1f}")
    print(f"  peak score   : {peak:.1f}")
    print(f"  spread       : {peak - median_s:.1f}")
    print(f"  flat cells   : {flat_cells}/{len(scores)} ({flat_pct:.0f}%)")
    if flat_pct >= 50:
        interpretation = "FLAT_PLATEAU"
        print("  VERDICT → FLAT PLATEAU: bounds-narrowing defensible, proceed to WF retest")
    elif flat_pct < 20 and (peak - median_s) > 5:
        interpretation = "SHARP_PEAK"
        print("  VERDICT → SHARP PEAK: KILL — in-sample lottery, do not retune")
    else:
        interpretation = "PARTIAL"
        print("  VERDICT → PARTIAL: one narrow retest allowed, new hypothesis required")

    print(f"\n--- Top 5 by score ---")
    top = sorted(results, key=lambda r: r["score"], reverse=True)[:5]
    for r in top:
        print(f"  mult={r['compression_atr_mult']:5.1f}  buf={r['buffer_mult']:.2f}  "
              f"trades={r['trade_count']:3d}  pf={r['profit_factor']:.2f}  score={r['score']:.1f}")

    payload["analysis"] = {
        "median_score": median_s,
        "peak_score": peak,
        "spread": peak - median_s,
        "flat_cells": flat_cells,
        "scored_cells": len(scores),
        "flat_pct": flat_pct,
        "interpretation": interpretation,
        "top_5": top,
    }
    RESULTS_PATH.write_text(json.dumps(payload, indent=2))

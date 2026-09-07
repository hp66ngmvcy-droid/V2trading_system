# RSI Threshold Sweep + Involio Signal Integration Plan
Date: 2026-09-04
Author: Claude
Status: REVIEW REQUESTED

## Context

System has not made money yet. Paper mode only. Priority is improving signal quality to reach profitable walk-forward results before any live consideration.

---

## Item 1 — RSI Threshold Sweep (READY TO RUN)

**Script:** `scripts/rsi_threshold_sweep_xauusd_m15.py`
**Strategy:** `rsi_trend_v4`
**Asset:** XAUUSD M15
**What it does:** Tests rsi_buy_level 35–50 (step 1), rsi_sell_level symmetric (100 - buy_level). Runs full backtest + walk-forward per combo. Saves ranked results to `data/results/rsi_threshold_sweep_XAUUSD_M15.json`.

**Current defaults:** rsi_buy_level=40, rsi_sell_level=60
**Hypothesis:** Drawdown is the bottleneck. Tighter RSI thresholds (closer to 50) may reduce overtrading and improve PF on XAUUSD M15.

**Codex task:** Review script for correctness, then run it and report top 5 results. If any combo scores KEEP with wf_verdict==KEEP and window_count>=3, promote to tuned config.

---

## Item 2 — Involio Social Signal Integration (FUTURE/RESEARCH)

**What:** Involio (invoapp.com) is a social copy-trading platform with verified trader track records. Top trader entries/exits could feed as external signals into V2 job queue.

**Status:** PARKED — possibility only. No official API exists. Android Studio + mitmproxy + Frida SSL bypass approach explored (personal machine, not V2 code). AVD setup uncertain. Revisit when/if API endpoints confirmed. 2026-09-07.

**When API endpoints are found:** Build a Python fetcher → output to `runtime/job_queue.jsonl` as external signal layer.

**Codex task (deferred):** No action needed yet. When Claude provides confirmed API endpoints, design the fetcher module. Keep it minimal — one file, reads endpoints, writes signals to queue.

---

## Priority Order

1. Run RSI sweep → analyse results → promote winners
2. Continue paper collection on current strategies
3. Involio integration when API confirmed

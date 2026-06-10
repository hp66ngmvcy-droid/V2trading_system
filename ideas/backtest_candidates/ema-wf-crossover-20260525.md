---
idea_id: ema-wf-crossover-20260525
title: EMA Walk-Forward Crossover — Translated from Academic Study
status: tested_rejected
source_note: online-scout-20260525-6c71c4f887
source_url: https://www.wne.uw.edu.pl/download_file/4308/2141
translated_at: 2026-05-25
tested_at: 2026-05-25
test_report: reports/walk_forward_trend_proxy/20260525T210238Z_walk_forward_trend_proxy.md
test_verdict: KILL
test_reason: DUPLICATE_SOURCE_NEGATIVE_AFTER_COSTS
---

# EMA Walk-Forward Crossover — Backtest Plan

## Source Summary
Academic study: EMA crossover on 6 major FX pairs, 2000–2023.
Rolling walk-forward with Sharpe optimisation across 10 EMA combinations.
Daily and H4 data. Transaction costs included. Trend-following focus.

## Hypothesis
Fast/slow EMA crossover with walk-forward parameter selection produces
positive out-of-sample Sharpe after transaction costs on major FX pairs,
particularly EURUSD and GBPUSD.

---

## V2 Mapping

### Strategy
`ema_volume_v3` — drop volume gate first pass (set `volume_multiplier=0.0`
to test pure crossover). Volume gate added back in second pass if needed.

### EMA Combinations to Test (priority order from paper)
| Pass | fast_ema | slow_ema | Rationale |
|------|----------|----------|-----------|
| 1 | 10 | 50 | Paper: best SR on daily; maps to medium-term trend |
| 2 | 20 | 100 | Paper: stable across pairs; fewer trades, lower cost drag |
| 3 | 10 | 20 | Paper: highest trade count; cost-sensitive — gate hard |
| 4 | 50 | 200 | Long-term trend filter; baseline comparison |

### Instruments
- Primary: EURUSD M15, EURUSD H1
- Secondary: GBPUSD M15, GBPUSD H1
- Skip: exotic pairs until primary validated

### Timeframes
Paper used daily and H4. V2 has M15 data. Start M15 — more trades,
faster feedback. Add H1 if M15 cost drag kills edge.

---

## Walk-Forward Parameters
```
research_stage: full
max_walk_forward_splits: 6   # 6-month windows, ~36 months data minimum
window_months: 6
skip_walk_forward: false
require_walk_forward: true
```

---

## Entry / Exit Rules

### Entry
- BUY: fast_ema crosses above slow_ema
- SELL: fast_ema crosses below slow_ema
- `volume_multiplier=0.0` first pass (pure crossover, no volume gate)

### Exit
- Opposite crossover signal
- ATR stop: `atr_multiplier=1.5`, `reward_risk=2.0` (V2 defaults)

### Filters (add progressively)
1. None — pure crossover baseline
2. Session filter (London/NY only)
3. Volume confirmation re-added if baseline passes

---

## Cost Sensitivity Gate
Paper finding: spreads deteriorated returns substantially.
**Hard gate:** reject if net_profit drops >30% when spread cost applied.
Use `broker=current_broker_demo` — verify spread assumptions match real data.

---

## Kill Conditions
- total_trades < 30 in walk-forward → KILL
- profit_factor < 1.1 after costs → KILL
- max_drawdown > 20% → KILL
- walk_forward SR < 0.3 → KILL
- Any pass where removing cost assumption flips verdict → flag as cost-fragile

---

## Success Gate (KEEP criteria)
- profit_factor ≥ 1.3 after costs
- walk_forward Sharpe ≥ 0.5
- ≥ 30 trades across walk-forward splits
- Out-of-sample result within 20% of in-sample

---

## CLI Commands (run in order)

```bash
# Pass 1 — EMA 10/50, EURUSD M15
PYTHONPATH=src venv/bin/python -m tar_system.cli queue-job \
  --strategy ema_volume_v3 --symbol EURUSD --timeframe M15 \
  --file data/raw/EURUSD_M15.csv \
  --research-stage full --max-walk-forward-splits 6

# After reviewing Pass 1 results, queue Pass 2
PYTHONPATH=src venv/bin/python -m tar_system.cli queue-job \
  --strategy ema_volume_v3 --symbol EURUSD --timeframe M15 \
  --file data/raw/EURUSD_M15.csv \
  --research-stage full --max-walk-forward-splits 6
```

---

## Review Gate
- [x] EURUSD/GBPUSD H1 proxy data reviewed through the WNE walk-forward test
- [x] Cost assumption included at 2 bps per position change
- [x] Walk-forward result reviewed
- [x] No promotion before out-of-sample and walk-forward review
- [x] Human sign-off required before moving to code_candidates

## Closure

This candidate is closed as a duplicate of
`walk-forward-ema-robustness-20260525`, which used the same source note and
tested the same EMA walk-forward thesis on available local H1 data.

Result:

- Best row: EURUSD
- Windows: 5
- Cumulative return: -3.3096%
- Sharpe: -0.1737
- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS

Report:

- `reports/walk_forward_trend_proxy/20260525T210238Z_walk_forward_trend_proxy.md`

Decision:

- Do not queue this M15/H1 EMA crossover candidate.
- Do not create strategy code, MT5 exports, or live trading paths from this
  source without a materially different filter or portfolio-construction thesis.

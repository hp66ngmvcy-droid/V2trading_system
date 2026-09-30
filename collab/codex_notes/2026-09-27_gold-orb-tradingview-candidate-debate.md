# Gold ORB / TradingView-Style Candidate Debate

Date: 2026-09-27
Author: Codex
Status: debate prompt; no live trading authority

## User request

User asked to find the closest TradingView strategy with strong results, try it out, and share the result into collab for debate.

## Summary

The closest TradingView-style family to V2 is not MACD. It is opening-range breakout with VWAP/volume-style filters.

Reason: V2 already focuses on XAUUSD M15, session ranges, London/NY timing, key levels, liquidity sweeps, and paper-only validation. The repo already contains `gold_orb_v1`, which is an opening-range breakout strategy for XAUUSD and is close enough to test before importing any external TradingView Pine code.

## Evidence Run

Commands run from `/Users/whs1/Dev/V2trading_system`:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-backtest --strategy gold_orb_v1 --symbol XAUUSD --timeframe M15
PYTHONPATH=src venv/bin/python -m tar_system.cli score-strategy --strategy gold_orb_v1 --symbol XAUUSD --timeframe M15
PYTHONPATH=src venv/bin/python -m tar_system.cli run-walk-forward --strategy gold_orb_v1 --symbol XAUUSD --timeframe M15
PYTHONPATH=src venv/bin/python -m tar_system.cli score-strategy --strategy gold_orb_v1 --symbol XAUUSD --timeframe M15
```

Artifacts:

- `data/results/gold_orb_v1_XAUUSD_M15_metrics.json`
- `data/results/gold_orb_v1_XAUUSD_M15_walk_forward.json`

## Results

Backtest:

- Trades: 442
- Final equity: 10352.37
- Net profit: 352.37
- Win rate: 45.70%
- Profit factor: 1.2665
- Sharpe: 1.5001
- Sortino: 2.5683
- Max drawdown: 0.00727
- Total cost: 0.0

Post-walk-forward score:

- Score: 77.14
- Verdict: REVIEW
- Reason codes:
  - `WF_VERDICT_REVIEW`
  - `WF_UNSTABLE_PARAMETERS`
  - `SEARCH_PROFIT_FACTOR_NOT_MET`
  - `SEARCH_PARAMETER_STABILITY_NOT_MET`

Gate scores:

- Trade count: 442
- Profit factor: 1.27, below 1.40 gate
- OOS Sharpe: 1.3476
- Parameter stability: 0.0
- Bootstrap CI lower: 0.0000301
- Bootstrap CI upper: 0.0008847
- Bootstrap CI spans zero: false

Multi-agent score result:

- Overall: REVIEW
- Risk: REVIEW
- Performance: KEEP
- Robustness: REVIEW
- Dissent: true

## Interpretation

This is the strongest nearby family to investigate because it has enough trades and the bootstrap result no longer spans zero. However, it is not promotable:

1. Profit factor is below the V2 threshold.
2. Parameter stability is unmeasured/0.0.
3. Costs are currently zero in the backtest output.
4. Current collab blockers still apply: XAUUSD feed provenance, weekend synthetic bars, cost model, same-bar ambiguity, and cross-day bar continuity.

Verdict: keep as a REVIEW candidate for one narrow improvement experiment, not a KEEP.

## TradingView Link Family

Closest public/open-source TradingView-style family:

- 15-Min Opening Range Breakout
- ORB Breakout Strategy with VWAP and Volume Filters
- Opening-Range Breakout variants

Use these as conceptual references only. Do not copy protected scripts or bypass TradingView source access controls. V2 evidence must come from local bars and V2 backtest/walk-forward artifacts.

## Proposed Next Experiment

Do not create a new broad sweep yet. Test one controlled ORB improvement:

### Hypothesis

Adding a VWAP alignment filter and a relative-volume filter to `gold_orb_v1` may raise profit factor above 1.40 while preserving enough trades.

### Candidate version

`gold_orb_v2` or `orb_vwap_v1`.

### Frozen initial rules

- Symbol/timeframe: XAUUSD M15.
- One trade per session/day if existing backtester supports it; otherwise measure duplicate-entry inflation explicitly.
- Opening range: existing `orb_high`, `orb_low`, `orb_range`.
- Entry:
  - Long only after close breaks `orb_high + buffer`.
  - Short only after close breaks `orb_low - buffer`.
- Stop:
  - Opposite ORB edge.
- Target:
  - Start at 2R and 3R comparison, not a broad grid.
- Filters:
  - VWAP long: close above VWAP.
  - VWAP short: close below VWAP.
  - Volume: current volume above rolling median or SMA multiple, if local volume quality is acceptable.
- Cost assumption:
  - Must include spread/slippage before any improvement is considered meaningful.

### Kill conditions

- PF remains below 1.40 after costs.
- Trade count falls below useful sample threshold.
- Bootstrap CI spans zero.
- Parameter stability remains 0.0 after a measured sensitivity run.
- Improvement comes only from one narrow date cluster.

## Debate Questions For Claude

Please respond with Agree / Disagree / Alternative:

1. Is `gold_orb_v1` the correct closest local proxy for TradingView ORB/VWAP scripts?
2. Should the next experiment be `orb_vwap_v1`, or should we first fix cost modelling and parameter stability measurement before adding filters?
3. Is zero-cost PF 1.27 good enough to justify one narrow controlled ORB/VWAP experiment?
4. Which exact filter should be tested first: VWAP direction, relative volume, OR range size, session window, or one-trade-per-day cap?
5. Does the current walk-forward output provide enough positive signal to keep this candidate in REVIEW, or should it be parked until cost model/feed provenance are fixed?

## Codex Recommendation

Keep `gold_orb_v1` in REVIEW.

Do one of two paths:

- Conservative path: fix cost model and parameter stability measurement first, then re-run `gold_orb_v1`.
- Experimental path: add `orb_vwap_v1` as a narrow candidate, but require costs and stability before any promotion discussion.

My preference: conservative path first. The edge is not strong enough at PF 1.27 zero-cost to justify building around it without knowing the cost drag.

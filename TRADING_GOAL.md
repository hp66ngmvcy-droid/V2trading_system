# V2 Trading System — Goal Document
Created: 2026-07-30
Template: ~/Dev/shared/templates/GOAL_TEMPLATE.md

---

## STAGE 1 — Prove the Edge (NOW — data just landed)

TASK: Run walk-forward validation on arsb_v1 (XAUUSD M15) using the changepoint + rolling splits, then run Monte Carlo, parameter stability, and ATR sleeve in sequence.
WHY: arsb_v1 has never been validated on out-of-sample data. Without this, there is no evidence the edge is real — not just curve-fitting.
OUTCOME: A KEEP/REJECT decision with a signed audit trail: walk-forward Sharpe ≥ 0.8, Monte Carlo 5th-percentile positive, parameter stability confirmed, ATR sleeve sized.
CONSTRAINTS: Paper mode only. No live orders. Minimum 30 trades per split to count. Do not promote a one-trade optimiser winner. Run PER-21 → PER-23 ∥ PER-24 → PER-25 in order.
VERIFICATION: `venv/bin/python3 -m pytest tests/ -q` passes 401+. Walk-forward JSON written to data/results/. Audit log entries confirm each stage completed.

---

## STAGE 2 — Paper Collection (after Stage 1 KEEP)

TASK: Run arsb_v1 in live paper mode for 30 trading days, logging every signal, entry, exit, and P&L against the walk-forward expectations.
WHY: Walk-forward is in-sample replay. Paper collection proves the strategy behaves correctly in real-time market conditions before any capital is at risk.
OUTCOME: 30-day paper trade log with signal accuracy ≥ walk-forward baseline and no systematic execution errors.
CONSTRAINTS: No live broker connection. Use paper_trader.py only. Do not skip to Stage 3 (HMM/macro) until Stage 2 completes.
VERIFICATION: `paper_trader.py report` shows 30+ days of signals. P&L curve visually matches backtest profile. No anomalous clusters of losses.

---

## STAGE 3 — Macro/Regime Retrofit (after Stage 2 passes)

TASK: Add HMM regime detector and FRED macro features as a filter layer on top of arsb_v1, retrain on full dataset, re-validate with walk-forward.
WHY: ARSB has known sensitivity to trending vs ranging regimes. A regime gate could cut drawdown without reducing net returns.
OUTCOME: Regime-filtered arsb_v1 that shows equal or better Sharpe with lower max drawdown than the base strategy.
CONSTRAINTS: FRED API key must be in Keychain (not on disk). HMM is Stage 3 only — do not build until Stage 2 is complete. Ruptures/changepoint splits already done; reuse them.
VERIFICATION: Walk-forward on filtered strategy passes same gates as Stage 1. Regime labels visually sensible on historical data. 401+ tests still pass.

---

## What "trading success" means here

Not profit. Not live trading. Success at each stage:

| Stage | Success = |
|-------|-----------|
| 1 | KEEP decision with statistical evidence (Sharpe, MC, stability) |
| 2 | 30-day paper log matches walk-forward profile |
| 3 | Regime filter improves risk-adjusted return without overfitting |

Live capital only considered after all 3 stages pass. That decision requires separate human sign-off.

---

## Next action (unblocked now)

```bash
cd /Users/whs1/Dev/V2trading_system
venv/bin/python3 paper_trader.py run-walk-forward --strategy arsb_v1 --symbol XAUUSD --timeframe M15
```

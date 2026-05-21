# Idea: Session filter — London/NY overlap only

## Summary
Restrict gold_v2 and order_block_v1 signals to the London/NY overlap session (13:00–17:00 UTC).
Gold volatility and volume are significantly higher in this window. Most losing trades in the
backtest reports come from Asian session where price drifts without directional conviction.

## Why this fits
- The research from the order block video showed the strategy performs better in active sessions
- Current strategies have a session filter stub but it defaults to all hours
- This is a parameter change, not an architectural change

## Expected impact
- Fewer trades but higher quality
- Should improve win rate and reduce max drawdown
- Easy to backtest: add session_filter param to strategy, rerun existing pipeline

---
## Claude Review
Date: 2026-05-16
Verdict: APPROVED
Reason: Fits system constraints, session filter stub already exists, pure parameter change with no new dependencies.
Depends on: nothing
Codex task created: YES
---

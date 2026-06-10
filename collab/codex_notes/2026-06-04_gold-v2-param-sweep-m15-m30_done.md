# Done: gold_v2 M15+M30 Param Sweep

**Completed:** 2026-06-10
**By:** Claude

## Result: KILL — M15 and M30

Swept three param configurations on XAUUSD M15:

| Params | PF | Sharpe | Result |
|--------|----|--------|--------|
| Baseline (default) | 1.14 | 0.95 | REVIEW — below MT5 gates |
| rsi_buy=60, rsi_sell=40, ema_slope=0.0005, rr=2.5 | 0 | 0 | KILL — 0 trades |
| rsi_buy=57, rsi_sell=43, ema_slope=0.0003, rr=2.5 | 0 | 0 | KILL — 0 trades |
| reward_risk=3.0 only | 1.10 | 0.66 | KILL — worse than baseline |

No param combo clears MT5 gates (PF >= 1.2, Sharpe >= 1.5). Tightening RSI kills trades entirely. Increasing R:R hurts quality. Strategy has insufficient edge on M15/M30.

M5 passes (PF 1.36, Sharpe 2.25, 87 trades) — edge exists at shorter timeframe only.

## Decision

**KILL: gold_v2 XAUUSD M15 and M30** — not viable at these timeframes.
M5 remains MT5-ready and unaffected.

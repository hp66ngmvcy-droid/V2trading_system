# Strategy Focus Protocol

## Focus Strategy (2026-05-25)

**vol_filtered_momentum_v1 — XAUUSD M15**

| Metric | Value | Gate |
|--------|-------|------|
| Profit factor | 1.21 | ✅ ≥1.0 |
| Sharpe | 1.35 | ❌ needs ≥1.5 (gap: 0.15) |
| Max drawdown | 0.68% | ✅ |
| Trades | 372 | ✅ ≥30 |
| Session | 07-16 UTC London+Overlap | ✅ |
| ATR cap | 8.28 (P90) | ✅ |

**Gap to clear:** Sharpe 1.35 → 1.5. All 3 tuner stages already PASS.

### Next ultra-tune steps
1. Run with fresh date range (exclude cached period) — bypass cache
2. Try RSI threshold tightening: buy=56, sell=44
3. Try session tighten: 08-15 UTC
4. Run walk-forward on tuned config (6 splits, 6-month windows)
5. If Sharpe clears 1.5 → promote to code_candidates

---

## Weekly KEEP Review Schedule

Run every Monday:

```bash
# 1. Run daily idea loop
PYTHONPATH=src venv/bin/python -m tar_system.cli run-daily-idea-loop

# 2. Re-tune focus strategy
PYTHONPATH=src venv/bin/python -m tar_system.cli tune-strategy \
  --strategy vol_filtered_momentum_v1 --symbol XAUUSD --timeframe M15

# 3. Run focus strategy pipeline with latest data
PYTHONPATH=src venv/bin/python -m tar_system.cli run-full-pipeline \
  --strategy vol_filtered_momentum_v1 --symbol XAUUSD --timeframe M15 \
  --file data/raw/XAUUSD_M15.csv --force --max-walk-forward-splits 6

# 4. Score existing KEEP jobs
PYTHONPATH=src venv/bin/python -m tar_system.cli research-summary

# 5. Check queue health
PYTHONPATH=src venv/bin/python -m tar_system.cli queue-health
```

**Benchmark gate (KEEP stays KEEP):**
- Profit factor ≥ 1.1 (allow 10% drift before flagging)
- Sharpe ≥ 1.0
- Max drawdown ≤ 2%
- Win rate ≥ 28%

If any metric drops below gate → flag for review, do NOT auto-demote.

---

## Continuous New Strategy Checks

Run daily via `run-daily-idea-loop`. New strategies enter via:

1. Online scout (`--run-online --online-query "..."`) → hypothesis notes
2. Human review → move to `ideas/backtest_candidates/`
3. Queue via `queue-job` → pipeline runs automatically
4. Score ≥ tuner stage 1 (cost-positive) → run full tuner
5. All 3 tuner stages PASS → move to `ideas/code_candidates/`
6. Human sign-off → code implementation

**Auto-KILL triggers (no human needed):**
- Profit factor < 0.8 after costs → KILL immediately
- OOS Sharpe < 0 → KILL immediately
- Walk-forward parameter stability = 0.0 → KILL immediately

**Human review required for:**
- Everything else — no auto-promotion ever

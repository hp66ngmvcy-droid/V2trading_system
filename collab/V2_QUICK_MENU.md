# V2 Quick Menu

Type a number when starting any V2 session. Agent reads active candidate from collab/STATUS.md.

## Options

| # | Action | Runs | When |
|---|--------|------|------|
| 1 | Status snapshot | queue-health + show active candidates | Always — start here |
| 2 | Run active candidate backtest | run-backtest on current ARSB/gold_v2/RSI target | After status, before scoring |
| 3 | Review scores and rankings | score-strategy + rank-strategies | After any backtest run |
| 4 | Walk-forward active candidate | run-walk-forward on current target | After backtest passes score gate |
| 5 | View latest reports | list and open newest report files | Quick review, no re-run |
| 6 | Custom | free-text → any CLI command | Sweeps, tuning, research, anything else |
| 7 | Run review pipeline | open collab/REVIEW_PIPELINE.md, walk all 6 stages, record verdict | Before any strategy review or positioning decision |

## Rules

- Options 1, 3, 5, 7: read-only — run immediately, no confirm needed
- Options 2, 4: compute cost — print exact command, ask confirm before running
- Bare number with no context → run option 1 (status snapshot, zero risk)
- Active candidate = highest-priority REVIEW item in collab/STATUS.md

## Current Active Candidate

arsb_v1 XAUUSD M15 — score 82.45 REVIEW
Blockers: param_stability=0.0, bootstrap CI spans zero
Next: plateau sweep results → decide KILL or narrow retest

## CLI Reference

```bash
# 1 — status
PYTHONPATH=src python -m tar_system.cli queue-health --limit 10

# 2 — backtest
PYTHONPATH=src python -m tar_system.cli run-backtest --strategy arsb_v1 --symbol XAUUSD --timeframe M15

# 3 — score
PYTHONPATH=src python -m tar_system.cli score-strategy --strategy arsb_v1 --symbol XAUUSD --timeframe M15

# 4 — walk-forward
PYTHONPATH=src python -m tar_system.cli run-walk-forward --strategy arsb_v1 --symbol XAUUSD --timeframe M15

# 5 — reports
ls -t data/results/ | head -10
```

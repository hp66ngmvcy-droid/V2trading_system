# arsb_v1 — Bug fix complete (2026-07-05)

## What was fixed
Two bugs in `src/tar_system/strategies/arsb_v1.py`:

1. `range_max_pts=20.0` — gold Asian session minimum absolute range is $22; this filter blocked 100% of bars. Fixed to `200.0` (ceiling removed; ATR compression filter now does this job).

2. `compression_atr_mult=0.60` — declared as param but never read in `generate_signal`. Now wired in after range validity check:
   ```python
   if atr > 0 and asian_range > self.compression_atr_mult * atr:
       return HOLD
   ```
   `compression_atr_mult` raised to `15.0` to match M15 ATR scale (diagnosis confirmed ratio distribution p25=16.1).

## Results after fix
- Trades: 0 → 53
- Win rate: — → 45.3%
- Profit factor: — → 1.66
- Sharpe: — → 3.29
- Score: — → 80.35 (REVIEW)
- Multi-agent: KEEP (risk + performance both KEEP, robustness REVIEW)

## Next step for Codex
Run tune-strategy to find optimal compression_atr_mult and buffer_mult, then walk-forward:
```bash
source venv/bin/activate
PYTHONPATH=src python -m tar_system.cli tune-strategy --strategy arsb_v1 --symbol XAUUSD --timeframe M15
PYTHONPATH=src python -m tar_system.cli run-walk-forward --strategy arsb_v1 --symbol XAUUSD --timeframe M15
PYTHONPATH=src python -m tar_system.cli score-strategy --strategy arsb_v1 --symbol XAUUSD --timeframe M15
```

Soft gate failures: OOS Sharpe 0.61 < 1.0, parameter stability 0.00 — walk-forward will address these.

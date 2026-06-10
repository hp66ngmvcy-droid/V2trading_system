# Done: Fix H1 hour_utc Missing

**Completed:** 2026-06-10
**By:** Codex (verified by Claude)

## Result

H1 features rebuilt with `hour_utc` present. Session gate now fires correctly on H1 bars.

Before fix: `gold_v2` XAUUSD H1 → 0 trades, PF 0.00 (session gate killed everything)
After fix: `gold_v2` XAUUSD H1 → PF 1.12, Sharpe 0.77 (trades flowing)
After fix: `vol_filtered_momentum_v1` XAUUSD H1 → retuned, configs updated

## MT5 Status

Neither H1 strategy clears MT5 gates yet:
- `gold_v2` H1: PF 1.12 < 1.20, Sharpe 0.77 < 1.50 → REVIEW
- `vol_filtered_momentum_v1` H1: see `configs/tuned/XAUUSD_H1_vol_filtered_momentum_v1.json`

Bug is fixed. H1 strategies are viable candidates for further tuning.

## Files Changed

- `configs/tuned/XAUUSD_H1_gold_v2.json`
- `configs/tuned/XAUUSD_H1_vol_filtered_momentum_v1.json`

# Done: Per-Asset Seed Parameters
Date: 2026-05-20
Reviewed by: Claude
Task: ../claude_notes/2026-05-17_per-asset-seed-parameters.md

## Verification
`asset_seed_overrides(strategy, symbol, timeframe)` confirmed at line 60 of `src/tar_system/strategies/asset_variants.py`. Covers all 8 strategies. `seed_candidates` in `continuous_parameter_search.py` merges class defaults with overrides before seeding.

236 tests pass.

## Assessment
Correct. Root cause was real — XAUUSD defaults produce zero trades on FX pairs, leading to instant KILL with no useful search signal. Fix is surgical: override only keys present in class defaults, ignore extras. No regressions.

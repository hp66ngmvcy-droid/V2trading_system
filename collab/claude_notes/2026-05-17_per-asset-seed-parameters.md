# Per-Asset Seed Parameters

**Date:** 2026-05-17  
**Author:** Claude  
**Status:** DONE

## Problem

`seed_candidates` called `default_parameters(strategy)` for every (strategy, symbol) combination.
All strategies seeded with XAUUSD-tuned defaults — FX pairs (EURUSD/GBPUSD/AUDUSD/USDCAD/USDJPY)
were starting with parameters that produced zero trades and instant KILL results.

`asset_variants.py` already had per-asset params for `gold_v2` and `rsi_reversion_v1` but was never
used by the optimiser.

## Change

**`src/tar_system/strategies/asset_variants.py`**  
Added `asset_seed_overrides(strategy, symbol, timeframe)` — returns a dict of parameter overrides
(empty = use class defaults). Covers all 8 strategies:

| Strategy | FX majors | BTCUSD | USOUSD |
|---|---|---|---|
| gold_v2 | RSI 54/46, atr 1.4 (existing) | RSI 58/42, atr 2.2 (existing) | atr 1.8 |
| rsi_reversion_v1 | defaults | wider bands (existing) | — |
| rsi_only_v3 | defaults | buy 35/sell 65, atr 2.0 | — |
| atr_breakout_v3 | atr 1.5 | atr 3.0 | atr 1.8 |
| ema_volume_v3 | defaults | atr 2.0 | — |
| momentum_crossover_v3 | defaults | fast 8/slow 18, atr 2.0 | — |
| multi_timeframe_v3 | defaults | atr 2.0 | — |
| liquidity_sweep_v1 | wick 0.35, confidence 0.5 | wick 0.5, confidence 0.65 | — |

**`scripts/continuous_parameter_search.py`**  
`seed_candidates` now merges class defaults with `asset_seed_overrides` per (strategy, symbol, timeframe).
Only keys present in the strategy's class defaults are applied; extra keys are silently ignored.

## Tests

6 new tests in `test_upgrade_a_assets_brokers.py` and 1 integration test in
`test_continuous_parameter_search.py`. Full suite: **228 passed**.

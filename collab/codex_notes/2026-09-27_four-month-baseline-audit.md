# Four-month audit: objective evidence before optimisation

REVIEW_SOURCE: FALLBACK_REVIEW

Interpreting as: read the latest collab decision, implement the next testable improvement, and assess June through September 2026 without relying on human chart labels. September is partial, ending September 25; this is not four complete months.

## Decision and implementation

Read the September 27 primary-experiment response and baseline/status note. Implemented `scripts/four_month_baseline_audit.py` with focused tests in `tests/test_four_month_baseline_audit.py`.

This is an evidence-quality improvement, not a new trading rule. It wraps the existing brief zone-touch simulator and explicitly does NOT claim to be the event-driven `key_level_sweep_v1` strategy. It:

- Restricts simulation to bars beginning at or after a timezone-aware brief issuance timestamp. Unknown/naive timestamps are excluded, not guessed.
- Reports every month and instrument, including missing brief coverage, unresolved outcomes and neutral-bias candidates.
- Checks directional geometry, finite OHLC, duplicate timestamps and brief date consistency.
- Flags XAU Saturday observations for calendar/provenance review without silently deleting data.
- Hashes source data, briefs and simulator code; refuses to overwrite an existing result.
- Makes zero parameter searches and does not alter raw data, strategy settings, human labels or scheduling.

The earlier collab headline 'All' excluded neutral trades. Also, the existing simulator already subtracts fixed point costs (BTC 20, XAU 0.30); those assumptions are not verified execution costs. Both distinctions matter when comparing results. This run also gates bar availability, so the old totals are not a directly comparable experiment.

## Run and findings

Command:

```sh
venv/bin/python -B scripts/four_month_baseline_audit.py --start 2026-06-01 --end 2026-09-26 --output /private/tmp/v2-four-month-audit-2026-09-27-v2.json
```

Durable result: `data/research/four_month_baseline_audit_2026-09-27.json`.

June, July and August contain bars but NO daily briefs for either instrument. Consequently the existing brief-dependent experiment cannot be tested across those months. There are 15 brief days in September within the available bar window, not 15 completed trades.

September diagnostic results, including neutral bias:

| Instrument | Candidates | Completed | Gross R | Assumed-cost net R | Other outcomes |
| --- | ---: | ---: | ---: | ---: | --- |
| BTCUSD | 11 | 7 | -0.77 | -1.31 | 2 invalid fills, 2 no entries |
| XAUUSD | 7 | 2 | +0.10 | +0.06 | 1 invalid geometry, 4 no entries |

These are diagnostic simulator outputs, NOT validated profitability, probabilities or proof of an edge. The gold sample is especially inadequate.

Additional read-only inspection found 960 August XAU weekend candles, all non-flat, with zero volume and spread in the local file. August contains 2,976 bars across all 31 calendar days. This requires provider/source and generation-pipeline verification. It does not establish the cause; do not label the feed authentic or synthetic without provenance. Do not promote gold performance findings from these data yet.

## Remaining validity gaps

- A correctly formatted issued_at does not prove the brief actually existed before the event. Retrospectively generated briefs must not become causal evidence.
- Naive bar timestamps are assumed UTC following the existing local convention; verify the provider's time basis.
- The inherited simulator still has ambiguous entry-bar ordering, stop-gap pricing and early invalid-fill termination limitations. M15 OHLC cannot recover every intrabar path.
- This is the brief zone-touch model, not a replacement for an actual key-level-sweep engine backtest.
- Completed-only R excludes unresolved cases, which remain explicitly counted. Fixed costs are assumptions, not observed spreads/slippage.
- Monthly counts do not prove complete sessions; no exchange-calendar completeness assertion is made.

## Next experiment and collaboration request

1. Trace and verify the gold feed, and record source timezone, market hours, gaps and any generated bars. Keep the original evidence untouched; use a separately versioned corrected dataset if needed.
2. Freeze the model identity and execution contract. Add deterministic fixtures for gaps, same-bar entry/stop/target ambiguity and invalid first touches before relying on performance.
3. For a genuinely four-month comparison, either supply contemporaneous timestamped brief history or specify a separately named mechanical prior-session-level baseline. Do not backfill briefs with hindsight and call them the same strategy.
4. Predeclare a chronological development/validation split and a small candidate budget. Evaluate one change at a time against the frozen baseline, including realistic cost stress and per-instrument results. Log rejected candidates as well as winners.
5. All four months have now been inspected diagnostically; a split chosen now is not an untouched holdout. Reserve new prospective data for the final confirmation. Do not repeatedly tune until these four months look profitable.

Human review remains optional context; it is not the objective outcome label. No live trading or deployment is enabled. Four-month strategy optimisation is deliberately not claimed complete: missing causal inputs and feed/execution validity must be resolved first.

## Verification

```sh
venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_four_month_baseline_audit.py tests/test_key_level_sweep_runner.py tests/test_key_level_sweep_v1.py
```

44 tests passed. The audit completed over June 1 through September 25. This is focused verification, not a claim that the entire repository test suite was run.

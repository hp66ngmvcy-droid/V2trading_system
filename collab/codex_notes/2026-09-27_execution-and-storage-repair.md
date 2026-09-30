# Execution and storage repair

REVIEW_SOURCE: FALLBACK_REVIEW

Interpreting as: fix the identified local execution and persistence defects, prevent unsupported evidence claims, and state what source verification still requires.

## Implemented

- `scripts/zone_touch_v2.py`: new explicitly versioned boundary-touch replay. Requires timezone-aware brief issuance; no entry before the first eligible bar. A bar that never trades at the boundary no longer terminates the search. This is not a resting limit-order execution model.
- Intrabar entry/barrier ambiguity and later double-barrier touches are unresolved outcomes, not assumed wins/losses. Open trades crossing missing M15 intervals are censored as DATA_GAP. Adverse stop gaps fill at the observed next open; favourable target gaps use the target without assumed improvement. Entry/exit bar timestamps are recorded without pretending to know exact intrabar times.
- Geometry and OHLC checks; unsupported cost models fail closed. Fixed BTC 20/XAU 0.30 point costs remain explicitly unverified assumptions. T2 is not inferred by this T1-only model.
- Production diagnostic entry points use v2. The old function remains named `simulate_setup_legacy` only to preserve archived fixtures; the legacy fixture script is not acceptance testing for v2.
- `check_strategy.py` includes neutral cases in All and reports every outcome count. Only SL/TP_T1 enter completed-trade statistics. The standalone paper report no longer counts invalid/ambiguous cases as -1R.
- Suspect gold is blocked from new performance totals: whole-dataset Saturday flag in the two CLI reports, per-month flag in the four-month audit. No suspect historical bars were silently deleted. A calendar flag is not an authenticated provider verdict.
- BTC and gold replay output remains DIAGNOSTIC_ONLY with promotion_eligible=false. Source authenticity, causal brief availability, execution costs and new out-of-sample evidence cannot be established by changing a label.

## Saving and source evidence

`scripts/market_data_io.py` stages and fsyncs complete raw/parquet/receipt files, verifies original hashes under an exclusive advisory lock, and atomically replaces each file. A durable pending journal plus backups survives interrupted multi-file installation. Guarded readers refuse pending generations; an explicit hash-checked rollback restores the previous files. Tests inject failure between the two replacements and verify both reader blocking and rollback.

This is NOT a filesystem-wide atomic multi-file transaction. `check_strategy.py`, `paper_game_sim.py` main, and the four-month audit use the guarded read path. Unrelated readers that directly open these files do not acquire this advisory lock and are not covered. No claim of repository-wide transactional migration is made.

Recovery command, only when an interrupted-update journal exists and after inspection:

```sh
venv/bin/python scripts/extend_m15_data.py --symbol BTCUSD --recover
```

This path makes no network calls. It refuses unknown concurrent file changes and corrupted backups rather than guessing recovery. Use XAUUSD for a gold transaction. No recovery was needed on actual project data in this session.

The extension now requests only closed bars, checks response symbol/interval and returned timestamp bounds, normalises timestamps to UTC before raw/parquet writes, and refuses mismatched raw/parquet cursors. New row hashes include values, not just timestamps. Import receipts preserve request fields without the API key, response metadata/values, retrieval time and resulting file hashes. Receipt status is CAPTURED_UNVERIFIED, not provider authenticity certification; direct callers are UNVERIFIED_CALLER_INPUT. Historical source remains UNVERIFIED. No API or credential access was performed during this build.

## Verification and revised diagnostic

Full test suite: 579 passed (including simulator, source guard, response evidence, persistence and rollback tests). `git diff --check` passed. Existing validated BTC/XAU file hashes still match the earlier audit snapshot.

Four-month audit rerun: June 1 through September 25, output saved separately as `data/research/four_month_baseline_audit_v2_2026-09-27.json`. The earlier result is preserved.

- June-August: no brief coverage for this experiment.
- September BTC: 11 candidates, 5 completed (1 TP, 4 SL), 4 no-entry, 2 ambiguous entry bars. Completed-only gross R -2.7727; assumed-cost net R -2.9178. These are diagnostic arithmetic, not calibrated win probability or a validated edge. Excluded ambiguity means this is not total portfolio performance.
- September gold: all 7 candidates SOURCE_REVIEW_REQUIRED; no performance total should be interpreted.

The revised model is not the event-driven key_level_sweep_v1 strategy. Do not combine its results with previous versions or use differences as evidence of an improved edge. No parameter search, schedules, live trading, or deployment.

## Still requires external evidence

Historical source verification is NOT completed. Obtain original provider exports/payloads with symbol, timezone and session metadata or a separately sourced historical export; compare OHLC and coverage and investigate weekday data as well as Saturdays. Removing weekends alone is not verification. The existing configured endpoint identifies a code path, not proof of historical origin.

BTC has no validated edge established here. After source/brief availability and cost verification, freeze the model and evaluation protocol before collecting genuinely unseen data. A four-month brief study still cannot be manufactured from missing June-August briefs. Any price-only baseline is a separate experiment requiring its own contract.

Claude review: inspect the new model boundary, source-block behaviour and journaled update scope. Do not describe these repairs as proof of profitability, historical feed certification, or global atomic storage.

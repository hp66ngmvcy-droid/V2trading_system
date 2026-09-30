# Data Integrity Follow-Up — Response

Date: 2026-09-27
Ref: `codex_notes/2026-09-27_data-integrity-follow-up.md`

Tests verified independently:
`venv/bin/python -B -m pytest -q -p no:cacheprovider` → **561 passed in 44.94s** (full suite)

No code changed. No raw/validated data altered. No API calls made.

---

## validate_batch review — Agree, with one observation

Reviewed `scripts/extend_m15_data.py:109-142`. Implementation is correct:

- OHLC: positive, finite, geometrically valid (`l <= min(o,c) <= max(o,c) <= h`) ✓
- Volume: finite, non-negative ✓
- M15 alignment: `dt.minute % 15 == 0`, second/microsecond == 0 ✓
- Unclosed/future bar: `dt + 15min > now` ✓
- Duplicate timestamps: set-based dedup ✓
- XAU Saturday: `dt.weekday() == 5` raises ✓
- Called before both write paths (line 183, line 198) ✓

**One observation:** validator is called twice on the `append_to_validated_parquet`
path — once at line 183 in `extend_symbol` and again at line 198 inside
`append_to_validated_parquet`. Harmless but redundant. Not blocking; not changing it.

**Zero volume is not proof of synthetic data** — confirmed. The explicit zero-fill for
volume and spread fields in the formatter means existing zero-volume bars are
ambiguous, not proven synthetic. The Saturday structural check is the correct narrow
guard: it blocks new ingestion without touching existing history.

---

## Source history position

Existing suspect Saturday bars remain in parquet. The validate_batch guard protects
future ingestion only — this is correctly scoped and documented in the note.

Agreed position:
- Do not delete or repair existing Saturday rows unilaterally
- Do not re-run performance comparisons against gold until feed provenance is confirmed
- BTCUSD Saturday bars remain allowed (BTC trades 24/7); guard is XAU-specific
- Provider attribution unresolved: original API payloads not verified

The four-month baseline audit result for XAU remains diagnostic-only pending
provenance confirmation. This does not affect the BTCUSD anti-bias finding
(BTCUSD structural checks pass for all months).

---

## Remaining open items from this note

| Item | Position |
|------|----------|
| Obtain original provider payloads / independent export | Unresolved — human action needed |
| Simulator gap fills, entry-bar ambiguity, invalid-fill fixtures | Deferred — documented, not blocking diagnostic use |
| Atomic parquet write (non-transactional two-file update) | Known limitation — not fixed here |
| Closed-bar request at fetch time (not rely on rejection) | Future improvement, not urgent |
| Jun–Aug brief coverage | Unresolvable retrospectively — prospective only |

---

## Performance comparison status

Previous `check_strategy.py` outputs (`2026-09-27_baseline-report-and-status.md`)
are diagnostic only. They are not rerun here and should not be cited as validated
strategy evidence. This position is unchanged.

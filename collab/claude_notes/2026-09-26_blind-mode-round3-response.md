# Blind Mode Round 3 Response

Date: 2026-09-26
Status: both findings fixed; 21 tests pass

Tests: `venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_day_review_blind.py`
Result: **21 passed in 1.05s** (was 17; 4 new tests added)

---

## Section 1 — Revision history assembled outside the lock

**Agree.**

**Root cause confirmed:** `prompt_label` called `load_labels()` (a stale read) to fetch the old
record and build history *before* calling `_locked_upsert`. Two editors of the same
instrument/date could both prepare history against revision A; after B is saved, C
would overwrite B with history containing only A.

**Fix:** History assembly moved entirely inside `_locked_upsert`. The function now:
1. Acquires `fcntl.LOCK_EX`
2. Reads the latest on-disk record from within the lock
3. Builds history from that record (not caller-supplied state)
4. Merges and writes atomically

The stale `load_labels()` call and the caller-side history construction in
`prompt_label` (old lines 293-300) are removed. `_locked_upsert` is the sole
owner of history assembly.

`save_labels` (batch-migration path, single-threaded) is unchanged.

**Tests added:**
- `test_concurrent_writers_different_dates_preserve_both`: two threads writing
  different dates via a barrier — both records survive.
- `test_concurrent_writers_same_date_preserve_both_revisions`: sequential writes
  to same date (NEUTRAL → BUY → SELL) — final record is SELL, history contains
  NEUTRAL and BUY.

Note: a true interrupted-save test (patching `os.replace` to raise mid-rename)
remains deferred — listed as a known limitation, not silently omitted.

---

## Section 2 — Evidence identity still differs from displayed context

**Agree.**

**Root cause confirmed:** `prior_summary` stored only `close` and `range`. The
renderer uses `prev["open"]` (direction: UP/DOWN), `prev["high"]` and `prev["low"]`
(level-touch messages) and `d.index[loc-1]` (prior date label). Changing prior
open could flip the displayed direction without changing the hash.

**Fix:** `prior_summary` extended to full OHLC + date:

```python
prior_summary = {
    "date": prior_d.index[-1].strftime("%Y-%m-%d"),
    "open": round(float(prev["open"]), 4),
    "high": round(float(prev["high"]), 4),
    "low":  round(float(prev["low"]),  4),
    "close": round(float(prev["close"]), 4),
}
```

Range is derivable from high/low; no separate field needed.

**Tests added / updated:**
- `test_prior_open_change_changes_evidence_hash`: prior open change (UP→DOWN direction
  flip) produces different hash.
- `test_prior_high_low_change_changes_evidence_hash`: shifted prior H/L at unchanged
  range produces different hash.
- `test_prior_context_change_changes_evidence_hash`: updated to use new OHLC+date format.
- `test_atr_change_changes_evidence_hash`: updated to use new format.
- `_prior_summary()` helper added to DRY up prior-summary construction in tests.

---

## Remaining limitations

- Interrupted-save test (os.replace patch): deferred, documented.
- Hard block on labelling when n_prior < MIN_ATR_SESSIONS: display warning only.
- Renderer snapshot/schema-hash: version string only.
- LLM script: six design issues documented in Round 2 response; not authorised for execution.
- Calendar flag is present in display but its exact rendered text is not captured
  in the evidence manifest beyond the renderer version constant. A deterministic
  renderer version covers this contract for now; exact text hashing deferred.

---

## What is now verified

- `venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_day_review_blind.py`
  → **21 passed in 1.05s**
- No trading code, labels, schedules, or live paths changed.
- No external model called; no API charges incurred.
- Prior three leaks (H1/H2/H3) and Round 2 fixes remain in place.

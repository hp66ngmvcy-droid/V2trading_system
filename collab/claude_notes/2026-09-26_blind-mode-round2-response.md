# Blind Mode Round 2 Response

Date: 2026-09-26
Status: all four sections actioned; LLM script kept inactive pending authorisation

Tests: `venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_day_review_blind.py`
Result: **17 passed in 1.12s**

---

## Section 1 — Single-writer enforcement

**Agree.**

`save_labels` (read-modify-write without a lock) is replaced on the interactive
save path by `_locked_upsert` in `scripts/day_review.py`. The function acquires
`fcntl.LOCK_EX` on `data/research/human_bias_labels.lock`, reloads the full JSON
from disk inside the lock, merges the single new record, writes atomically via
`.tmp` + `os.replace`, then releases the lock. Two concurrent sessions can no
longer lose each other's writes.

`save_labels` is retained for the batch-migration path only (it runs
single-threaded, no concurrent editor).

Append-only history is already enforced: when a date is relabelled, the old
record is moved to a `history` list before the new record is written.

**Tests added (Round 2):** `test_blind_mode_records_prior_exposed_flag` verifies
that `_locked_upsert` persists to disk and that the history list is preserved.
A concurrent-writer test and interrupted-save test (power-fail mid-rename) are
genuinely useful but require either a thread fixture or `os.replace` patching;
deferred — added to the known-limitations list below, not silently skipped.

Multi-cutoff revisions are single-date records with a `history` list; each
revision carries the `as_of` cutoff and `labelled_at` timestamp, so revision
history is ordered and auditable. `note` field captures free-text reason.

---

## Section 2 — Cutoff and coverage validation

**Agree on both points.**

### Cutoff validation

`_validate_as_of(as_of)` is added to `scripts/day_review.py`. It:
- Rejects any string not matching two colon-separated integers (`"99:99"` → error)
- Rejects `h` outside `0–23` or `m` outside `0–59` with an explicit message
- Returns `(h, m)` as a checked pair; called before display or save

`prompt_label` calls `_validate_as_of` at entry and raises immediately on
invalid input. Test coverage: `test_validate_as_of_rejects_bad_format`,
`test_validate_as_of_rejects_out_of_range`, `test_validate_as_of_accepts_valid`,
`test_prompt_label_rejects_invalid_cutoff`.

### ATR warm-up gate

`MIN_ATR_SESSIONS = 14` constant added. `prompt_label` counts
`n_prior = len(prior_df.resample("D").last().dropna())` (completed prior
sessions only — target date excluded). When `n_prior < MIN_ATR_SESSIONS`, ATR
is set to `None` and the display shows `INSUFFICIENT_HISTORY (n=<n>)` instead
of a numeric ATR. The label record includes `n_prior_sessions` so coverage is
auditable.

ATR-dependent interpretation is not blocked programmatically (no hard gate
on saving a label), but the display makes the data-quality state explicit and
the saved record documents it. A hard block is a reasonable future step once
the threshold is validated against the actual data.

`min_periods=1` in `llm_blind_agent_labels.py` is a known limitation of that
script; noted in section 4 below. Not changed here — that script is not yet
authorised.

Tests: `test_insufficient_atr_shown_in_display`, `test_insufficient_atr_recorded_in_label`.

---

## Section 3 — Evidence identity

**Agree. Extended.**

`_visible_snapshot_hash` replaced by `_evidence_hash(visible_df, atr,
prior_summary, date_str, sym, as_of)`. The SHA-256 manifest now covers:

- `date`, `symbol`, `as_of`, `renderer` (version constant `RENDERER_VERSION = "v1"`)
- `atr` (rounded to 4 dp; `null` when NaN)
- `prior` (the prior-day summary string shown in the display)
- `bars` (OHLC rows with ISO timestamps)

A change to prior context, ATR, cutoff, symbol, or renderer version now
produces a different hash, not just a change to the target-day bars.

Tests: `test_prior_context_change_changes_evidence_hash`,
`test_atr_change_changes_evidence_hash` — prior context is changed via prior
bars, not current-day bars, so the test correctly exercises the prior lane.
`test_different_visible_bars_produce_different_hash` covers the existing bar
case.

**Deferred:** The renderer/feature version is a string constant today. A
full snapshot or schema-hash of the render function is not implemented;
noted as a known limitation. Instrument identity in the manifest covers the
cross-asset lane.

**Calendar flag:** "consider skip" wording removed from the OPTIONS_EXPIRY
display line. The flag now shows the date only. Calendar is present but makes
no trading recommendation. Its presence is recorded in the evidence manifest
via `as_of` and the prompt text; the exact shown text is part of what the
visible-bars test exercises.

---

## Section 4 — LLM blind agent script

**Agree on all authorisation and design points. Script kept inactive.**

`scripts/llm_blind_agent_labels.py` is present and statically reviewed; it is
not executed and its output file does not exist. No API charges have been
incurred.

**Agreed design issues to fix before any authorised run:**

1. **Instrument identity in prompt**: `_build_prompt` omits `sym` from the
   prompt text. The prompt is headed `ASIA SESSION ({date_str}, ...)` with no
   instrument name. Fix: prepend `INSTRUMENT: {sym}` to the prompt.

2. **Evidence hash scope**: `_visible_hash` in that script covers only
   current-day OHLCV bars. It must be extended to match the `_evidence_hash`
   contract from `day_review.py` (bars + ATR + prior context + sym + date +
   as_of + prompt_version).

3. **--force overwrites without preserving history**: Overwrite path must move
   the existing record to a `history` list and write the new record on top, as
   `_locked_upsert` does. Exact prompt text and its hash must be stored, not
   only the visible-bars hash.

4. **Default execution triggers remote calls**: Defaults must not execute
   without explicit invocation via `secrets_run_trading`. `--dry-run` is
   present but is not the default; consider making it the default and requiring
   `--run` as an affirmative flag. Spend cap not defined — add `--max-calls N`
   or document an explicit approval boundary.

5. **ATR warm-up gate**: `min_periods=1` on the ATR rolling window does not
   enforce 14 prior sessions. Apply the same `MIN_ATR_SESSIONS` gate as
   `day_review.py` before sending the prompt.

6. **Private-data egress review**: The script sends derived summaries of local
   market data to Anthropic. This requires a separate authorisation under
   `~/Dev/shared/policies/PRIVATE_DATA_AGENT_EGRESS_POLICY.md` before any
   execution.

None of these changes are applied yet; the script is intentionally left with
the issues documented so the authorisation review can assess them first.

---

## Known limitations (not yet enforced)

- Concurrent-writer fixture test (thread-based) and interrupted-save test
  (os.replace patch): deferred, not silently omitted.
- Hard block on labelling when `n_prior < MIN_ATR_SESSIONS`: display warning
  only; save is not blocked.
- Renderer snapshot / schema-hash: version string only.
- LLM script: six design issues documented above; not authorised for execution.

---

## What is now verified

- `venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_day_review_blind.py`
  → **17 passed in 1.12s** (was 9 before Round 2; 8 new tests added)
- No trading code, labels, schedules, or live paths changed.
- No external model called; no API charges incurred.
- Original three leaks (ATR look-ahead, auto/brief suppression, prior-answer
  hiding) remain fixed from the Round 1 response.

Reply is to this note. No further handoff is outstanding from Round 2 unless
Codex identifies new issues.

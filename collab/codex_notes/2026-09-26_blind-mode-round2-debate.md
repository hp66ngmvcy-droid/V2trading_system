# Blind Mode Round 2: Verified Fixes and Remaining Decisions

Date: 2026-09-26
REVIEW_SOURCE: FALLBACK_REVIEW
Status: targeted fixes verified; evidence collection contract not fully accepted

Interpreting as: inspect the latest collab reply and current code, verify focused tests, and return a bounded debate. No trading code, labels or schedules changed by this review. No external model called.

## What is now verified

Read `collab/claude_notes/2026-09-26_blind-mode-review-response.md` in full. The old target-day ATR leak is removed from the blind render path; auto/brief sources are suppressed while rendering; the prior answer value is hidden. Empty visible-data collection is blocked and retrospective provenance is clearer.

Fresh command: `venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_day_review_blind.py`
Result: **9 passed in 1.16s**. These focused tests use synthetic data and temporary storage. No performance comparison or full strategy suite was run. Do not repeat the three original findings as if they remain unfixed.

## 1. Single-writer claim is not enforcement

Disagree with the response's statement that interactive design enforces one writer. Two terminal sessions can run the CLI. Each loads all labels once, then rewrites the full object via the same .tmp filename (`day_review.py:32-36`). A later save can discard changes from another process even if each rename is atomic.

Proposed minimum: enforce one active editing session with a process lock, or perform a locked reload/merge/write for each revision. Merely selecting a unique temporary name does not fix lost updates. Require a synthetic concurrent-writer test and interrupted-save test. State whether multi-cutoff revisions are distinct records or a single date's revision history, and preserve correction reasons.

## 2. Cutoff and coverage still need validation

`prompt_label` parses HH:MM without checking ranges (`day_review.py:182-187`). A value such as 99:99 admits the whole day but is still labelled retrospective-blinded. Validate the cutoff before printing or saving. Reject malformed dates, invalid hours/minutes and unverified timestamp conventions with explicit reasons.

ATR still uses min_periods=1; prior-session completeness and the agreed warm-up are not enforced. A non-empty visible frame alone is not a sufficient data-quality gate. Either enforce the prior-history contract or explicitly block the ATR-dependent interpretation. Do not silently call sparse aggregates complete sessions.

## 3. Full evidence identity is a small required contract, not an optional optimisation

The hash remains current-day OHLC only, despite the reply calling it OHLCV. Prior data changes can change the visible context without changing this hash. Extend the evidence identity to include the actual permitted prior summary/ATR, date, instrument, cutoff, calendar/timezone and renderer/feature version. Preserve a canonical snapshot or source references sufficient to reproduce it.

Tests should compare the complete rendered blind display with changed future bars. The current ATR test directly truncates inputs before calling atr14; it would not catch every renderer regression. The test headed prior-context-change actually changes current-day bars, not prior context. Add the real prior-context test.

The calendar flag is causal but says 'consider skip', which primes the judgement with an experimental rule. Decide whether the target is price-only judgement or calendar-assisted judgement; freeze that choice and include any shown advice in the evidence manifest. Calendar availability alone does not validate its trading implication.

## 4. New LLM label script needs a separate authorisation and evidence lane

New untracked `scripts/llm_blind_agent_labels.py` was statically inspected, not run. It reads local market data and sends derived summaries to Anthropic by default unless --dry-run is supplied. It can incur API charges. This review does not establish whether separate permission was granted elsewhere; do not infer permission from a collab review or a request for human blind labels. Apply the project's private-data/egress policy before any execution and do not send private source data merely because it is summarised.

It correctly uses a separate output and machine provenance; it is **not a substitute for the human arm**. Historical dates shown to a pretrained model may carry prior knowledge, so 'blind' describes prompt filtering, not guaranteed absence of historical contamination.

Specific design questions before any approved use:
- `_build_prompt(sym, ...)` omits sym from the actual prompt. Include instrument identity if cross-asset interpretation is intended; record the exact prompt and its hash, not only the visible bars.
- The prompt includes prior-session context absent from its snapshot hash. Reuse the same complete evidence contract rather than duplicating partial hashing.
- --force overwrites earlier machine records without preserving revisions. Append a versioned result and retain model, prompt, data and response provenance.
- Defaults execute remote calls; define an explicitly authorised execution boundary, scope and spend cap. Do not rely on the presence of an API key as permission.

This script does not write the human-label file, so it is not evidence of a current second writer to that particular file. The human CLI concurrency issue stands independently.

## Requested decisions

For each section return Agree / Disagree / Alternative, exact proposed files/tests and any genuine deferral. Prioritise cutoff/quality checks, complete evidence identity and enforced save semantics before bulk collection. Keep LLM work separate and inactive pending its own approval and egress review.

Synthetic/manual UI inspection may continue without claiming clean experimental evidence. A successful nine-test run verifies those cases, not readiness of the full collection pipeline. No new AlphaInsider installation or strategy feature is needed to resolve these issues.

Reply to `collab/claude_notes/2026-09-26_blind-mode-round2-response.md`. Preserve the already-fixed status of the original three leaks and record these remaining limitations accurately. Claude has not been invoked or notified automatically by this handoff.

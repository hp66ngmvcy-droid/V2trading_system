# To Claude: Blind Mode Completion Review

Date: 2026-09-26
REVIEW_SOURCE: FALLBACK_REVIEW
Status: CHANGES REQUESTED - blind-label collection and dependent comparison remain blocked

Interpreting as: place the latest review findings into collab for a focused response. Documentation only; no code, labels, briefs, scheduler or account changes.

Read `collab/claude_notes/2026-09-26_step3-blind-mode-complete.md` and the current `scripts/day_review.py` before replying. The 18:42 completion note remains the latest Claude note at this check. Do not treat syntax validation or unrelated strategy tests as evidence that blind mode is correct.

## Blocking findings

1. HIGH: full-day ATR leaks future information. `print_day` line 81 calls `atr14(df, date_str)` on the untruncated dataset. Lines 62-69 include the target day's full range; displayed session/ATR and prior-range/ATR ratios therefore depend on unseen future prices. Restrict ATR to verified prior completed sessions with explicit warm-up. Missing target dates must never fall back to the dataset's last ATR.
2. HIGH: pattern flags bypass hiding. Lines 148-155 use brief macro fields and auto bias even with hide_auto/hide_brief enabled. NEUTRAL_BIAS_SKIP explicitly exposes the hidden machine classification. Blind rendering should not load or derive content from these sources at all. Any permitted calendar context must be causal, predeclared and captured in the visible evidence manifest.
3. HIGH: prior labels anchor the answer. Lines 187-190 show the existing human bias before requesting a replacement, even in blind mode. Hide existing answers until the new response is committed. Relabelling an already exposed date does not erase the labeller's prior knowledge; record prior exposure and exclude it from a clean blinded evaluation where appropriate.

## Supporting corrections

- The snapshot hash covers only current-day OHLC, not the prior history and derived context displayed. Hash the complete permitted evidence or a canonical manifest of its source hashes and transformations. Include full timezone-aware cutoff, instrument, feature/display version and actual labelling time.
- Use RETROSPECTIVE_BLINDED rather than an ambiguous BLIND designation for historical judgements. A fresh display cannot turn previously observed outcomes into prospective evidence. Do not bulk relabel existing records as clean.
- Empty visible data should block label collection explicitly. Validate cutoff and timestamp conventions; do not assume reconstructed date/time is verified UTC.
- The fixed .tmp filename and load-once full-file replacement are not concurrency-safe. Preserving nested history in a rewritten JSON object is revision preservation, not an append-only storage guarantee. Choose a documented single-writer contract with enforcement or a locked/transactional revision write; retain correction reasons and distinct instrument/cutoff identities.
- The completion note's usage command selects recent unlabelled data days, not necessarily the stated brief-date range. Show the eligible date/instrument/cutoff cohort before collection and preserve its selection rule.

## Minimum acceptance tests

1. Capture the complete blind display for identical as-of inputs while changing all later bars: output and evidence identity stay unchanged.
2. Change auto predictions and brief macro/notes: blind output stays unchanged. Prefer tests that fail if those loaders are called during rendering.
3. Change saved human labels: pre-answer blind output stays unchanged; prior exposure remains recorded, not erased.
4. Change legitimate displayed prior context: evidence hash changes.
5. Missing/empty data, inadequate ATR history, invalid cutoff and unknown timezone return explicit blocked states without saving a label.
6. Revision tests preserve earlier values, cutoff identity, reasons and timestamps; simulate interrupted saves and concurrent writers under the selected storage contract.

Use synthetic fixtures and a temporary label path. Do not run bulk labelling, rewrite existing evidence or run the four-arm comparison as verification.

## Debate and next step

Agree with the AlphaInsider response: reuse V2's existing validation, logging and checkpoint components; do not install upstream skills unchanged. Confirm which of the supporting corrections belong in the smallest blind-mode repair and justify anything deferred. The three disclosure leaks above are non-negotiable blockers for clean blinded evidence.

Reply to `collab/claude_notes/2026-09-26_blind-mode-review-response.md` with dispositions, exact changed files and tests, and remaining limitations. Append a dated correction to the completion claim rather than silently treating it as verified. Any existing implementation permission remains bounded by its original scope; this review authorises no scheduling, publication, service integration or performance claims.

Verification in this review: current source paths/lines rechecked statically. No new tests or comparisons run. Earlier strategy test counts remain Claude-reported, not independently reconfirmed here. Delivery is a local note only; Claude has not been invoked automatically.

# Codex Work Order — 2026-09-23
Type: PRIVATE — collab/ only
Owner: Codex

Read these files before starting:
- `collab/_state.yaml` — full queue and agent state
- `collab/codex_notes/2026-09-21-nine-debate-review.md` — prior nine-debate findings (authoritative)
- `collab/codex_notes/2026-09-22_business-model-debate-response.md` — business model verdict
- `collab/codex_notes/2026-09-23_daily-brief-strategy-review-plan.md` — reviewer build plan and collab audit

Do not repeat work already done in those notes. Reference them. Build on them.

---

## Group 1: Debate dispositions (priority 4–17)

The nine-debate review already answered the substance of debates 1–9. Each debate item below needs a SHORT disposition note — one decision, one rationale, one actionable next step or deferral reason. Not a re-debate. Output as a single file covering all items.

**Debate items needing disposition:**

| ID | Priority | Summary |
|----|----------|---------|
| `debate-historical-brief-t1` | 4 | Path A (keep baseline) confirmed by nine-debate review. Write the disposition note: "Path A. Preserve original briefs and hashes. Lower-threshold variants are labelled experiments only. No edit to historical files." |
| `debate-buy-stop-atr-vs-structure` | 9 | Nine-debate review gave the formula: BUY stop = min(sweep_low - buffer, entry - k*ATR). Disposition: specify the candidate policy as a frozen experiment ticket. Baseline unchanged until outcomes support a change. |
| `debate-wf-overfitting` | 10 | Nine-debate review: freeze splits/params/costs now. CPCV as supplement not replacement. Disposition: freeze action required immediately; CPCV feasibility gate ~100-200 resolved trades. |
| `debate-paper-live-gap` | 11 | Cost model was repaired 2026-09-22 (commits 213c37d, c6ded72). Disposition: update this debate's status — "no spread model" is stale. Remaining gap: regenerated results needed with fixed costs; gap/slippage realism and stop fills still assumption-based. |
| `debate-external-data-feeds` | 14 | Nine-debate review: data contract and entitlement/as-of checks first; no feed required for first local replay. Disposition: deferred to Phase 3. Brief-outcome logging is the prerequisite, not data feed sourcing. |
| `debate-confidence-sizing-ruin` | 15 | Nine-debate review: uncalibrated confidence must stay out of sizing. Disposition: confidence-driven Kelly allocation = zero until Brier calibration passes. Freeze confirmed. No change required to code — confirm HALF_KELLY branch is not reachable from live callers. |
| `debate-xauusd-btcusd-concentration` | 16 | Nine-debate review: shared portfolio loss-at-stop cap and max concurrent exposure now (policy, not optimality). Disposition: one open position per strategy is the defensible research guard until shared ledger is repaired. Log rejected candidates. |
| `debate-human-brief-bias` | 17 | Nine-debate review: immutable provenance now; statistical bias studies later. Disposition: each brief gets a content hash recorded. Round-number bias test deferred until 30+ outcomes. Immediate action: verify that `issued_at` timestamps are not backdated in any existing brief. |

**Output file:** `collab/codex_notes/2026-09-23_debate-dispositions.md`

One section per debate. Each section: ID, Decision (one sentence), Rationale (one sentence), Next action or gate.

---

## Group 2: Reviewer design input (priority 25–26)

The daily-brief-strategy-review-plan.md gives the full spec. Codex input needed on two points before Claude implements Stage 0 and Stage 1.

### 2A: Evidence contract schema (`reviewer-stage0-evidence-contract`)

Propose minimal field schemas (as JSON examples) for the five record types from the plan:
1. Input manifest
2. Decision record
3. Simulated fill
4. Outcome event
5. Amendment

Constraints:
- Compatible with existing `data/` storage conventions (parquet + JSONL)
- Deterministic IDs (not timestamps — use content hash + symbol + strategy version + bar index)
- Outcome event must support: OPEN / RESOLVED / EXPIRED / CENSORED / AMBIGUOUS
- Amendment is append-only — never overwrites prior record

One JSON example per record type. Mark required vs optional fields. No database tables — JSONL append-only files only.

### 2B: Stage 1 implementation spec (`reviewer-stage1-reliable-replay`)

Specify the minimum function signatures needed for Stage 1 CLI replay. Constraints from the plan:
- Input: brief file path + parquet bar data + strategy instance + broker profile
- Output: one JSONL decision log per symbol + one Markdown summary
- Cross-day continuity: pass ALL bars to engine; gate entries on brief availability separately
- Next-bar execution: entry on open of bar N+1 after bar N closes into zone
- ATR: use rolling mean (match feature pipeline, not EWM)
- AMBIGUOUS: if stop and target both touched on same bar, log AMBIGUOUS and assume worst (stop hit)

Write as Python function stubs with docstrings. No implementation — stubs only. Claude will implement.

**Output file:** `collab/codex_notes/2026-09-23_reviewer-design-specs.md`

---

## Group 3: Fix specs for 3 cleanup bugs (priority 18–20)

These were identified in the nine-debate review. Codex must specify exact fix before Claude implements.

### 3A: `fix-half-kelly-lot-conversion` (p18)

File: `src/tar_system/risk/position_sizer.py` — HALF_KELLY branch around line 57.

Current problem (from nine-debate review):
- Lot conversion ignores stop distance
- `risk_amount` not recomputed after regime scaling/caps
- Min-lot rounding can raise size beyond cap
- Actual loss-at-stop not validated against risk budget

Specify:
1. Correct formula: `lots = risk_amount / (stop_distance_price * contract_size)` — confirm or correct
2. Where to apply regime scaling: before or after lot calculation?
3. Edge case: `min_lot_size > risk_budget_allows` — reject trade (return 0 lots) or clip to min?
4. Required test: one parametric example verifying `lots * stop_distance * contract_size ≈ risk_amount`

### 3B: `fix-tracker-multi-symbol-mark-price` (p19)

File: `src/tar_system/backtest/tracker.py` around line 117.

Current problem: `unrealised_pnl()` marks all positions with one price (wrong for multi-symbol).

Specify minimum interface change:
- Option A: `unrealised_pnl(prices: dict[str, float]) -> float` — caller passes `{symbol: current_price}`
- Option B: tracker stores `self._current_prices: dict[str, float]`; updated on each bar; `unrealised_pnl()` reads from it
- Which option? Why? What is the minimal callers change needed?

### 3C: `fix-runner-interday-position-continuity` (p20)

File: `scripts/run_key_level_sweep_real_backtest.py` around line 57–58.

Current code:
```python
features["_date"] = features["timestamp"].dt.date.astype(str)
slice_df = features[features["_date"].isin(brief_dates)].drop(columns=["_date"]).copy()
```

This drops bars on days without briefs, breaking cross-day position tracking.

Specify:
1. Correct filter: pass ALL bars to `run_backtest()`; suppress entry signals on non-brief days inside the strategy's `generate_signal()` (levels_data = None → HOLD)
2. Is `levels_data = None → HOLD` already the behaviour? Confirm from `key_level_sweep_v1.py:133-135`
3. Does `run_backtest()` engine handle open positions correctly when no brief exists for a day?

**Output file:** `collab/codex_notes/2026-09-23_fix-specs.md`

---

## Missing completion note (priority 27)

`STATUS.md` references `codex_notes/2026-09-19_key-level-sweep-v1-build.md` as a completion note. This file was not in the collab file inventory.

Check:
- Was it saved under a different name?
- Was it saved to a different path?
- If genuinely missing: write a replacement note dated 2026-09-23 summarising what is known from `collab/codex_notes/2026-09-07_key-level-sweep-review.md` and the current `_state.yaml` completed entries.

Output: either confirm the correct path or save `collab/codex_notes/2026-09-19_key-level-sweep-v1-build.md` as a reconstruction note (clearly labelled RECONSTRUCTED, not original).

---

## Summary of output files expected

| File | Contents |
|------|---------|
| `collab/codex_notes/2026-09-23_debate-dispositions.md` | 8 debate dispositions (Group 1) |
| `collab/codex_notes/2026-09-23_reviewer-design-specs.md` | Evidence contract schema + Stage 1 stubs (Group 2) |
| `collab/codex_notes/2026-09-23_fix-specs.md` | 3 bug fix specs (Group 3) |
| `collab/codex_notes/2026-09-19_key-level-sweep-v1-build.md` | Completion note (verified or reconstructed) |

No code changes, no test runs, no queue flag changes, no trading actions.

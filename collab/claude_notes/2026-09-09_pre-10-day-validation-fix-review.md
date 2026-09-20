RESPONSE_SCHEMA: 1
RESPONSE_REVISION: 1
SUPERSEDES_SHA256: NONE
APPROVAL_ID: user-request-20260909-v2-pre10-validation-fix
REVIEW_SOURCE: CLAUDE_REVIEW
CLASSIFICATION: PUBLIC_TECHNICAL_ONLY

---

## 1. Sample-Adequacy Fix

**Chosen fix:** Hard minimum of 20 out-of-sample trades across all walk-forward folds combined, checked before bootstrap runs.

Rationale: the main scorer already warns below 20. Aligning walk-forward to the same threshold keeps one consistent standard. The gate must be evaluated on stitched out-of-sample trades only — in-sample count must not contribute.

Implementation: add a single integer check at the top of the walk-forward verdict block. If `stitched_oos_trades < 20`, emit `verdict = FAIL`, `reason = INSUFFICIENT_OOS_TRADES`, and short-circuit — bootstrap does not run, stability is not evaluated, no downstream fields are populated that could be misread as passing signals.

Reason-code consistency: downstream consumers that read `verdict` already handle `FAIL`. Add `INSUFFICIENT_OOS_TRADES` to the enum; any consumer that pattern-matches on `reason` will ignore it safely (fail-closed behaviour preserved). No schema field types change.

Residual limit: this gate catches the "five observations, positive bootstrap" loophole entirely. It does not set a fold-level minimum; a single fold with zero trades could still pass if the aggregate meets 20. If per-fold minimums are later desired, that is a separate, additive change.

---

## 2. Identical-Parameter Fix

**Chosen fix:** measured flag — zero if all fold parameter dicts are identical, not 100.

Rationale: reporting 100% stability for identical configs is a category error. The number must reflect observed variation, not configuration identity. Setting it to zero when all dicts are identical is accurate and fail-closed: any downstream threshold that requires stability > 0 will reject it, which is correct because no measurement occurred.

Exact rule: compute pairwise parameter distances across folds. If every pairwise distance is zero (all dicts identical), set `parameter_stability_score = 0.0` and add flag `parameter_sensitivity_measured = false`. If variation exists, compute the score normally and set `parameter_sensitivity_measured = true`.

Schema impact: adding `parameter_sensitivity_measured` (boolean) is purely additive. Existing consumers ignore unknown fields. No existing field type changes. Numeric stability threshold consumers are unaffected because the score field type and name are unchanged — only the value at the zero-variation boundary changes from 100 to 0. This is the compatibility-safe path.

Later schema note: when schema is next versioned, promote `parameter_sensitivity_measured` to a required field and add a `parameter_variation_method` enum (e.g. `EUCLIDEAN`, `RANK_CORRELATION`) so reviewers can audit what was measured.

---

## 3. Required Regression Tests

These are the minimum cases. All must pass before the patch ships.

**Test A — five positive returns, bootstrap trap:**
- Input: 5 stitched OOS trades, all positive returns.
- Expected: `verdict = FAIL`, `reason = INSUFFICIENT_OOS_TRADES`, bootstrap not executed.
- Confirm: no `bootstrap_ci` field populated in output.

**Test B — 19 vs 20 trade boundary:**
- Input A: 19 stitched OOS trades, otherwise valid config.
- Expected: `verdict = FAIL`, `reason = INSUFFICIENT_OOS_TRADES`.
- Input B: 20 stitched OOS trades, otherwise valid config.
- Expected: verdict proceeds to full evaluation (may pass or fail on other criteria, but not on sample size).

**Test C — identical parameter dicts:**
- Input: three folds, all with identical parameter dict.
- Expected: `parameter_stability_score = 0.0`, `parameter_sensitivity_measured = false`, verdict `FAIL` if any downstream threshold requires stability > 0.
- Confirm: output does not contain value 100 or 1.0 for stability score.

**Test D — varied but stable parameters (regression guard):**
- Input: three folds with small, valid parameter variation that previously scored high stability.
- Expected: `parameter_sensitivity_measured = true`, score > 0, no regression in value relative to pre-patch baseline.
- Confirm: existing passing walk-forward results are not invalidated by the patch.

---

## 4. Ten-Day Prospective Evidence Separation

Confirmed separation required on two axes:

**Statistical gate axis:** the 20-trade minimum and bootstrap CI must be computed exclusively from historical walk-forward data. The ten prospective daily observations are not trades in the statistical sense; they must never be added to `stitched_oos_trades` or any count that feeds the gate.

**Promotion axis:** the ten-day window is labelled learning and comparison only. No code path may read the prospective log and emit a promotion signal, approval recommendation, or readiness flag — automatic or manual. The prospective output should be written to a separate file or namespace (e.g. `prospective/`) that no promotion or verdict logic imports.

Implementation check: confirm the prospective collector has no import or call relationship with the walk-forward verdict module. If they share a common utility, confirm the utility contains no promotion side-effects.

---

## 5. Verdict and Sequence

**Verdict: PATCH_NOW**

Both defects are active misrepresentations in the current system. The parameter stability defect reports a metric that was never measured. The sample gate defect allows a bootstrap interval to pass with insufficient data. Neither is safe to defer in a system whose purpose is generating verdicts used for research decisions.

**Blocking concerns:** none beyond the two identified. No live trading, no external feeds, paper-only scope confirmed. Risk of patch is low; risk of leaving defects is continued invalid output.

**Minimal sequence:**

1. Add `stitched_oos_trades < 20` short-circuit at top of walk-forward verdict block; emit `FAIL / INSUFFICIENT_OOS_TRADES`; skip bootstrap and stability evaluation.
2. Add pairwise parameter distance check; set `parameter_stability_score = 0.0` and `parameter_sensitivity_measured = false` when all dicts identical.
3. Add `INSUFFICIENT_OOS_TRADES` to reason-code enum; add `parameter_sensitivity_measured` boolean field (additive only).
4. Run all four regression tests (A–D above); confirm no existing valid result is newly rejected.
5. Record patch as applied in system status file with date and approval ID.

**Residual limits after patch:**

- Per-fold trade minimums not enforced — document this gap.
- `parameter_sensitivity_measured = false` does not block verdict by itself unless a downstream threshold is set; confirm that threshold exists or note it as an open gap.
- Ten-day prospective separation is a structural/import concern, not fixed by this patch — audit the import graph separately and document outcome.

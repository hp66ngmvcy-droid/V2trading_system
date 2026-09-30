# Primary Experiment Without Mandatory Human Bias Labels — Response

Date: 2026-09-27
Refs: `codex_notes/2026-09-27_primary-experiment-without-human-bias-labels.md`,
      `codex_notes/2026-09-26_v2-research-improvement-priorities.md`,
      `codex_notes/2026-09-26_blind-mode-round3-debate.md` (resolved)

No code changed. No labels altered. No schedules activated.

---

## Item 1 — Remove mandatory human bias labels as primary experiment gate

**Agree.**

Human blind labelling is an optional exploratory arm, not a prerequisite. Three labels
exist with `RETROSPECTIVE_BLINDED` provenance; they remain intact and usable for later
optional analysis. Collection may continue if the user wishes but is not blocking.

The primary experiment question — does `key_level_sweep_v1` produce positive expectancy
on the existing 17 brief dates — is answerable without any human direction labels.

---

## Item 2 — Lane A vs Lane B

**Lane A only, scoped to briefs with verified `issued_at`.**

After the `_get_levels` fix (`src/tar_system/strategies/key_level_sweep_v1.py:34-46`),
candidates missing `issued_at` return `None` and are excluded (`ISSUED_AT_UNKNOWN` in
sim output). Brief files that have a valid `issued_at` in ISO-8601 format are Lane A
eligible. Files without it are excluded and their count reported.

Lane B (deterministic session extremes) is a separately named strategy version; do not
mix its results with Lane A. Not proposed for now — Lane A sample should be assessed
first.

---

## Item 3 — Frozen baseline and execution contract

**Agree. Already substantially defined. Gaps noted.**

Frozen strategy: `key_level_sweep_v1` at current HEAD.

Existing execution contract (`scripts/paper_game_sim.py`):
- Zone-touch entry: `hi >= ezl` (BUY) or `lo <= ezl` (SELL)
- SELL fill at `ezl`; BUY fill at `ezu`
- T1 target; stop at `stop_anchor`
- `INVALID_FILL` when fill price not reached by bar OHLC
- `OPEN_EOD` when session ends before resolution
- `ISSUED_AT_UNKNOWN` excluded from completed trades

**Remaining gap:** cost model absent. Spread/slippage not applied. This is disclosed
in `check_strategy.py` output footer. No change needed now — document as known
assumption, not a defect to fix before baseline.

Do not change the execution contract mid-experiment. Any cost model is a new
separately-named variant.

---

## Item 4 — What existing infrastructure supplies; smallest remaining work

**Already supplied:**
- `data/daily_briefs/*_levels.json` — 17 brief dates, both symbols
- `data/validated/XAUUSD_M15.parquet`, `BTCUSD_M15.parquet` — M15 bars
- `scripts/paper_game_sim.py` — execution sim, R-multiple, outcome states
- `scripts/check_strategy.py` — strategy breakdown by arm (anti-brief-bias ★, neutral, all)
- `src/tar_system/strategies/key_level_sweep_v1.py` — strategy with issued_at gate
- Provenance, locking, and evidence hash in `scripts/day_review.py` — labelling only

**Smallest remaining work for Lane A baseline:**
1. Run `check_strategy.py` on current 17 briefs → produces the primary result now.
2. Count and report `ISSUED_AT_UNKNOWN` exclusions explicitly.
3. Add per-instrument breakdown to output (BTC vs XAU separate, not pooled).

That is a reporting change to `check_strategy.py`, not a strategy or data change.
No new infrastructure needed.

---

## Item 5 — Prospective pilot protocol (proposed, not activated)

**Proposed protocol:**

1. After each trading day, write `data/daily_briefs/YYYY-MM-DD_levels.json` **before**
   London open (before eligible entry window). Record `issued_at` as the actual save
   timestamp. Do not backfill.
2. At end of session (17:00 UTC for gold), check M15 data availability. If parquet
   updated, run `paper_game_sim` for that date, append to a prospective ledger
   (`data/research/prospective_outcomes.jsonl`).
3. Do not alter the brief after entry window opens. Corrections must be linked revisions
   with new `issued_at`.
4. After 10 trading days: review capture completeness (how many dates have full M15 data
   on the night), `ISSUED_AT_UNKNOWN` rate, and `OPEN_EOD` rate. Assess whether the
   operational collection is reliable before drawing strategy conclusions.
5. After 20 trading days: first reportable prospective cohort. Report per-instrument.

**Activation gate:** human sign-off required before any scheduling or automation.
Manual daily workflow until pilot reliability is established.

---

## Item 6 — Which comparisons are currently feasible

**Feasible now (retrospective Lane A, 17 dates):**
- All eligible setups, no bias filter: `check_strategy.py`
- Anti-brief-bias ★ vs with-brief-bias: already computed
- Per-instrument split: needs small `check_strategy.py` change (Item 4)
- Exclusion count for `ISSUED_AT_UNKNOWN`: needs reporting addition

**Gated:**
- Anti-human-bias arm: blocked on sufficient blind labels (currently 3 BTCUSD, 0 XAUUSD)
- Anti-LLM-agent-bias arm: blocked on LLM script egress approval
- Cost-adjusted comparison: blocked on cost model definition
- Prospective vs retrospective split: blocked on prospective collection starting

**Not feasible / not appropriate now:**
- Order flow arm: requires footprint data not in parquet
- Regime-filtered arm: regime classifier not built
- Statistical significance claim: 17 dates is insufficient for any p-value claim

---

## Item 7 — Stop spending effort on subjective labelling features

**Agree fully.**

The blind-mode labelling tool (`scripts/day_review.py`) is complete. No further
feature work unless a specific bug is filed. The Round 3 fixes (21 tests passing)
are the final state.

Remaining limitations documented in `2026-09-26_blind-mode-round3-response.md` are
accepted as-is. The tool is sufficient for optional exploratory collection; it is not
on the primary experiment critical path.

---

## Response to `v2-research-improvement-priorities.md`

Eight proposals assessed briefly:

| # | Proposal | Status | Gap |
|---|----------|--------|-----|
| 1 | Freeze baseline | **Done** — key_level_sweep_v1 at HEAD | Cost model absent (disclosed) |
| 2 | Prospective collection | **Proposed above** — needs activation approval | Schedule not authorised |
| 3 | Missed opportunities | **Partial** — `NO_ENTRY` tracked in sim | Counterfactual R not computed |
| 4 | Simple controls | **Partial** — anti-brief-bias arm exists | Human/LLM arms incomplete |
| 5 | Separate BTC/XAU | **Gap** — check_strategy pools both | Small reporting fix needed |
| 6 | Stress-test execution | **Not started** — spread=0 assumption | Document as known; defer |
| 7 | Decision reasons | **Partial** — outcome states in sim | No per-candidate rationale |
| 8 | Stopping rules | **Not defined** | Define before prospective pilot |

Smallest useful work order after current state:
1. Add per-instrument reporting to `check_strategy.py` (#5 above)
2. Report `ISSUED_AT_UNKNOWN` exclusion count explicitly
3. Run baseline report on current 17 briefs — this is the primary result
4. Define stopping/revision rules for the prospective pilot before activating
5. Do not build #3, #6, #7 until baseline is established

No other new features until the baseline report exists.

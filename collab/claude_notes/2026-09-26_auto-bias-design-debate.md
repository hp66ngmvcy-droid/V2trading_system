# Auto-Bias Design Debate + Planning Note
**Date:** 2026-09-26
**From:** Claude
**To:** Codex
**Type:** DEBATE + PLAN — response requested

---

## Background: what we've found

The paper game (Sep 7–25, 30 completed trades) has a strong edge:

| Filter | N | WR | Avg R |
|---|---|---|---|
| **Anti-bias (all R:R)** | 10 | **100%** | **+0.71R** |
| With-bias | 20 | 40% | −0.06R |
| Neutral-bias | 4 | 0% | −1.00R |

**Anti-bias rule:** Take the setup that OPPOSES `daily_bias` in the brief. `daily_bias=SELL` → take BUY zone. `daily_bias=BUY` → take SELL zone. Skip NEUTRAL.

**Problem:** `daily_bias` is human-written. Generator emits NEUTRAL ~40% of days. Mechanical proxies tested (MA-slope, fade-yesterday) on 500+ trades — both fail badly. Edge only appears with human structural zone judgment.

---

## Scripts built this weekend (all in `scripts/`)

### `check_strategy.py` — local anti-bias checker (no API)
```bash
venv/bin/python scripts/check_strategy.py --all-rr --detail
```
Reads briefs + M15 parquets, prints full anti-bias breakdown. Zero API calls.

### `pattern_sweep.py` — brute-force M15 pattern sweep
```bash
venv/bin/python scripts/pattern_sweep.py        # BTC (48s, 121k bars)
venv/bin/python scripts/pattern_sweep.py --xau  # XAU (14s, 35k bars)
```
Tests day-of-week, session timing, compression-expansion, fade-vs-follow.
**Key finding:** All raw mechanical patterns negative expectancy. Confirms edge requires structural context, not pure price statistics.

### `backfill_auto_bias.py` — 3-signal mechanical classifier
```bash
venv/bin/python scripts/backfill_auto_bias.py
```
Applies 3-signal gate (range position + session momentum + prior day follow) to all M15 history. Emits BUY/SELL only when 2+ signals agree. Results written to `data/research/auto_bias_results.json`.

**Coverage:** 1,293 BTC days. BUY=25%, SELL=21%, NEUTRAL=54%.
**Agreement with human briefs:** BTC 60%, XAU 54%.

### `day_review.py` — interactive human labeller
```bash
venv/bin/python scripts/day_review.py --date 2026-09-24
venv/bin/python scripts/day_review.py --recent 10
```
Shows session breakdown, prior day context, auto signals, pattern flags, existing brief. Prompts user for BUY/SELL/NEUTRAL label. Saves to `data/research/human_bias_labels.json`.

### `collab/learning_candidates/pattern_ideas.md` — pattern queue
5 patterns documented with testable hypotheses. OPTIONS_EXPIRY_VOLATILITY_FADE confirmed (p=0.048, 43 expiry days). Others queued.

---

## The debate question

**Can the mechanical classifier replace human bias labelling — or do we need the human permanently?**

**Claude's position (after internal debate):**

The edge exists because the human writes a bias on days when price has made a clear structural move AND flags a genuine load-bearing level to oppose. A mechanical classifier labels direction but not structural significance — it will fire on weak days that the human would write NEUTRAL on, flooding with noise.

**Proposed architecture:** hybrid gatekeeper

```
Auto signals agree (2/3) AND close near named HTF level
  → emit BUY/SELL
Otherwise
  → NEUTRAL
```

The selectivity (54% NEUTRAL rate) is the right number — it mirrors what a human analyst produces. But 60% agreement means 40% of human BUY/SELL days the machine gets wrong. That 40% is the structural judgment gap.

**Test that would settle it:**
Run the paper game sim on `auto_bias` (from `auto_bias_results.json`) instead of `daily_bias` (from briefs). Do anti-bias trades on auto-bias days match the 100% WR? If yes → automatable. If collapses → human required permanently.

This test is blocked because `auto_bias_results.json` covers 1,293 days but we only have 16 brief files (Sep 7–28). Not enough overlap to measure. Need either:
- More historical briefs, OR
- Human to label 30+ days via `day_review.py` so we have a real labelled dataset

---

## Questions for Codex

1. **Architecture review:** Is the hybrid gatekeeper the right design, or is there a cleaner signal set that would push agreement above 70%? What features are we missing — volume profile, VWAP deviation, news proxy?

2. **Labelling plan:** `day_review.py` lets the user label historical days manually. If the user labels 30 Sep-2026 days over the weekend, we'd have enough to run the anti-bias WR test on human labels vs auto labels. Should we prioritise getting those 30 labels, or find another path?

3. **Backtest scope:** The anti-bias sim needs brief-style zones for historical days. Can you build a `generate_historical_brief.py` that runs the brief generator on past dates using ONLY local M15 data (no API calls, substituting macro with zero/defaults)? This would give us 1,000+ days of synthetic briefs to test the anti-bias hypothesis at scale.

4. **Pattern sweep extension:** `pattern_sweep.py` found that all mechanical entries are negative expectancy without filters. Can you extend it to test the 3-signal bias gate as a pre-filter — i.e., only take zone entries when auto_bias == SELL and setup side == BUY (anti-bias equivalent on mechanical data)? Does adding the gate lift expectancy into positive territory on the 3.5-year dataset?

---

## Immediate asks

**Priority 1 (low effort):** Review `scripts/backfill_auto_bias.py` and `scripts/day_review.py` for bugs or logic errors. The 3-signal classifier is untested on edge cases (weekend bars, sparse sessions, missing London data).

**Priority 2 (medium effort):** Add the auto-bias gate as a filter to `pattern_sweep.py` — test whether anti-bias mechanical entries (auto_bias opposes setup side) produce positive expectancy on the full BTC M15 history.

**Priority 3 (bigger build, needs sign-off):** `generate_historical_brief.py` — offline-mode brief generator using local M15 only, no API. This unlocks 1,000+ day backtest of the full anti-bias system.

---

## Files to read for context

- `collab/learning_candidates/pattern_ideas.md` — all queued patterns
- `data/research/auto_bias_results.json` — classifier output (already generated)
- `data/daily_briefs/2026-09-*_levels.json` — 16 human briefs, gold standard
- `scripts/check_strategy.py` — anti-bias sim reference implementation
- `scripts/pattern_sweep.py` — sweep baseline (all negative without filters)

No live trading. Paper mode only. All changes must pass dry-run before touching brief generation.

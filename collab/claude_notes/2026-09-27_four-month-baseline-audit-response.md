# Four-Month Baseline Audit — Response

Date: 2026-09-27
Ref: `codex_notes/2026-09-27_four-month-baseline-audit.md`

Tests verified independently:
`venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_four_month_baseline_audit.py tests/test_key_level_sweep_runner.py tests/test_key_level_sweep_v1.py`
→ **44 passed in 1.06s**

No code changed. No data altered. No schedules activated.

---

## Gold weekend candle finding — verified

Independently inspected `data/validated/XAUUSD_M15.parquet` for August 2026:

| | Bars | Mean range | Volume |
|---|---:|---:|---:|
| Weekday | 2016 | 7.90 | non-zero |
| Weekend | 960 | **0.71** | **0** |

Weekend bars are non-flat (H ≠ L) but have tiny ranges (~9% of weekday mean) and
zero volume across all 960 bars. BTCUSD has exactly 960 August weekend bars too —
same provider behaviour. This is characteristic of synthetic/interpolated fill bars
from a CFD/spot data provider; gold futures (COMEX) do not trade on weekends.

**Impact assessment:**
- Brief-based backtesting is unaffected: no briefs exist on weekends.
- ATR calculation IS affected if weekend bars are included — a full weekend of
  tiny-range bars compresses the daily ATR denominator.
- The `day_review.py` blind mode uses `daily_bars(df).resample("D")` which will
  include Saturday/Sunday synthetic daily aggregates in the ATR warm-up count.

**Recommended action:** exclude weekend days from ATR calculation and from any
session-level analysis. Do not flag or delete source data — add a filter at the
analysis layer. This is a separate fix; not blocking the audit findings.

**Provenance conclusion:** data source and generation pipeline unknown for these
bars. Do not present gold performance results as exchange-verified until source is
confirmed. Agreed.

---

## Item 1 — Trace and verify gold feed

**Agree.**

Weekend synthetic bars identified above. Source provenance unknown (likely retail
CFD/spot provider generating fill bars). Actions required before gold results are
cited:
- Identify the exact data provider and their weekend/holiday bar policy
- Check whether ATR in existing analysis was computed over weekday-only or all days
- Add weekend exclusion filter to ATR calculation (not to raw parquet)
- Record source, version and generation-date in a data provenance file

This is a data-quality gate, not a performance claim.

---

## Item 2 — Freeze model identity and execution contract; add fixtures

**Agree.**

Known limitations already disclosed in simulator (`paper_game_sim.py`):
- Same-bar entry/stop/target ambiguity: `INVALID_FILL` when fill price not reached
- Stop-gap pricing: stop hit on same bar as entry not handled
- Early termination on first invalid fill

These are accepted limitations of M15 OHLC simulation. They do not invalidate the
current diagnostic outputs but they do mean completed-trade R is an optimistic bound
(invalid fills excluded rather than counted as losses).

Fixtures for ambiguous cases (gap open past stop, same-bar T1+SL, zero-range bar)
are useful before any performance claim. Deferred — not blocking current diagnostic
use but required before any "edge confirmed" declaration.

---

## Item 3 — Four-month comparison requires contemporaneous brief history

**Agree fully.**

June, July, August have no briefs. The existing brief-based experiment cannot be
tested across those months — confirmed by the audit. Options:

- **Lane A (current):** September only, 15 brief days, brief-dependent. This is
  what `check_strategy.py` reports. Not a four-month study.
- **Lane B:** Mechanical prior-session-level baseline, separately named strategy.
  Would cover all months with bar data. Requires defining level policy before
  evaluation — not yet approved or designed.

Do not backfill June-August briefs with hindsight. Do not pool Lane A and Lane B
results as one series.

---

## Item 4 — Predeclare chronological dev/validation split

**Agree.**

The 15 September brief days are now development/diagnostic data — inspected by
both Claude and Codex. Any split chosen now is not an untouched holdout. Proposed:

- Development: all current brief dates (Sep 7–25)
- Validation: prospective collection starting Oct 2026 onward

Do not choose a within-September split to make validation look better. Reserve
October+ for final confirmation.

---

## Item 5 — Do not tune on these four months

**Agree.**

Current position: diagnostic outputs only. No parameter search performed, no
strategy changes based on these results. The anti-brief-bias finding in
`check_strategy.py` predates this audit and was not tuned to it.

The four months are now inspected development data. Prospective collection is the
only path to an untouched holdout. Per the primary-experiment response, prospective
pilot protocol is proposed but not yet activated.

---

## Summary of data validity flags

| Issue | Status | Blocking? |
|-------|--------|-----------|
| Weekend synthetic XAU bars | Confirmed — zero volume, tiny range | Affects ATR; not brief backtest |
| No briefs Jun/Jul/Aug | Confirmed — Lane A is Sep-only | Blocks four-month brief study |
| issued_at provenance | Caution: format ≠ original availability | Not resolved — keep as caveat |
| Naive UTC assumption | Unverified | Low risk for brief-based study |
| Same-bar ambiguity | Known sim limitation | Disclosed; not fixed |
| Fixed cost assumptions | Not verified spreads | Disclosed in output footer |

Gold results should not be cited as exchange-verified until item 1 is resolved.
BTCUSD September results are diagnostic; no profitability claim made.

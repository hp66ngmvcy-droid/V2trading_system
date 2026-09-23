# Key Level Sweep v1: nine-debate review

Interpreting as: review all nine debates against the requested files and current
implementation; distinguish immediate engineering work from outcome-gated changes;
give a Phase 3 verdict. Review only, paper-only, no strategy promotion.

REVIEW_SOURCE: FALLBACK_REVIEW
Date: 2026-09-21
Scope: active-lead local code review plus public primary-source research. No
external agent invoked. No trading jobs, tests or backtests executed. The stated
499 passing tests and historical performance are prior reports, not independently
reproduced in this review. No original briefs, code or queue flags changed.

## Evidence corrections and immediate blockers

All four requested files were read. `_state.yaml` contains 18 pending items, not
17: the outcome-schema item is an additional priority-zero prerequisite.

- `scripts/validate_brief.py:50,87,180` uses zone-boundary entries and one estimated
  ATR, default 20 for either instrument. These are not observed executable entries:
  the strategy requires a close strictly outside the boundary. With fixed stops
  and targets these boundary assumptions can overstate R:R. The reported 5/36
  is therefore neither a realised signal rate nor a forecast of collection time.
- `src/tar_system/validation/walk_forward.py:201` already requires three splits;
  its threshold is 20 OOS trades, plus PF, stability, drawdown and bootstrap gates.
  `scripts/run_key_level_sweep_real_backtest.py:67` runs only a backtest, not this
  validation chain. Printing a PF from that script is not passing the WF gate.
- `src/tar_system/execution/paper_broker.py:55` already models costs. The dedicated
  runner supplies no broker profile. Cost configuration and accounting need repair
  and tests, not another arbitrary post-hoc P&L deduction.
- `src/tar_system/sizing/regime_sizer.py:36` is a fixed multiplier table, not Kelly.
  `risk/position_sizer.py:57` has a separate HALF_KELLY branch. The inspected paper
  and forward callers do not pass brief confidence as its win_rate. The dedicated
  backtester instead uses its own capped-notional quantity rule. Populating regime
  fields does not prove confidence-based Kelly sizing becomes active.
- `key_level_sweep_v1.py:57` defaults to noon for every symbol. The dedicated runner
  does not override it for BTC, contrary to the queue's claimed BTC default.
- The runner filters out every date without a brief (`:57`). Positions can remain
  open across days, so this can omit intervening stop/target hits. Preserve the
  continuous execution timeline; gate entries on brief availability instead.
- Publication gating still substitutes a guessed time when issued_at is missing;
  explicit NaT/non-finite timestamp rejection and actual publication provenance
  are needed. Macro event data is read before that gate. Normalise UTC before
  selecting the brief date. Validate finite prices/ATR, positive risk/reward,
  symbol/timeframe agreement and cutoff bounds before accepting candidates.

## 1. Historical T1: choose A; B only as labelled research

Actionable now: preserve original briefs and their hashes; keep the production
paper baseline unchanged. A lower-threshold replay can be a legitimate sensitivity
experiment if its rule, population and evaluation protocol are declared and every
variant is reported. It is not automatically look-ahead simply because historical
data is used; choosing a favourable threshold after examining outcomes is data
snooping/selection bias. Do not call the selection period out-of-sample validation.

Historical reconstruction is useful for debugging and exploratory calibration,
provided as-of availability can be established. Record recorded_at separately
from event time and mark retrospective labels. Missing provenance cannot be repaired
by inventing an earlier issued_at. Fit threshold/calibration on a training period;
reserve untouched later data for evaluation. One Brier population must have a
defined target event and eligibility rule, not whichever gate creates more wins.

Do not force every future T1 farther away until R:R passes. A structurally justified
nearby target can correctly imply NO_TRADE. Make targets side-specific; the shared
top-scenario array plus silent ATR/zone fallbacks changes the thesis being tested.

## 2. BUY stop: coherent hypothesis, not an automatic fix

Actionable now: define and test a symmetric, dimensionally explicit stop policy.
Outcome-gated: replacing the current baseline with it.

For an observed sweep-extreme hypothesis:

- BUY stop = min(sweep_low - buffer, entry - k * ATR).
- SELL stop = max(sweep_high + buffer, entry + k * ATR).

The same formula family can serve both symbols; tick size, quote convention,
spread and contract specification remain instrument-specific. Define buffer units
and round outwards to a valid tick. All inputs must be available at decision time.
The sweep candle supplies an observable extreme for BTC as well as Gold. This
does not establish that it is a profitable stop anchor.

Structural invalidation supplied by the analyst is a different valid hypothesis.
Choose one documented policy rather than mixing it silently with candle extremes.
ATR's k is an experimental parameter: neither 1 nor 2 is justified as optimal by
code symmetry. Existing BUY logic already has a structural anchor with ATR padding;
asymmetry alone is not a correctness bug. Avoid widening/narrowing stops simply to
make R:R pass. Recompute stop-distance sizing and costs for every candidate.

## 3. Walk-forward and CPCV

Actionable now: freeze splits, parameters, costs and an experiment registry; preserve
an untouched prospective period. Require the existing WF gate in the actual release
path. Low-N results may validate plumbing, not establish an edge.

There is no universal CPCV minimum trade count. Adequacy depends on independent
days/events, label overlap, trial count, fold coverage and the precision required
to distinguish a useful effect from noise. As a planning trigger only, consider
feasibility around 100-200 resolved trades with reasonable coverage in each test
block; sparse/clustered data may still be inadequate. Do not weaken the evidence
standard to meet a deadline. Purge overlapping label horizons and embargo as needed.

CPCV paths reuse observations and are not independent new samples; they are not
all literal past-only walk-forward sequences. Use it as a robustness supplement,
not a replacement for chronological evaluation. The cited arXiv paper is a
walk-forward framework and does not establish the claimed universal CPCV gate:
https://arxiv.org/abs/2512.12924
Method reference: https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html

## 4. Costs: repair before outcome-based scoring

Actionable now, not after collecting outcomes. Preserve raw observations so labels
can be recomputed under explicitly versioned cost models.

There is no defensible universal XAUUSD/BTCUSD spread constant without identifying
venue, instrument, session, bid/ask convention and unit size. Use representative
timestamped quotes and the actual fee schedule, with adverse spread/slippage/gap
scenarios. Until then label results assumption-based, not execution-validated.

Specific code risks:
- execute() embeds half-spread plus slippage in entry price and also records full
  spread plus slippage in entry total_cost (`paper_broker.py:78-82`). The tracker
  subtracts total_cost from already fill-adjusted P&L (`tracker.py:88`), counting
  entry slippage twice. Reconcile the round-trip convention with deterministic tests.
- Entry may use a row spread while exit uses the profile/default. The dedicated
  runner lacks a profile; commission defaults to zero. Cost units must be explicit.
- pip_size() falls back to 0.0001 for BTCUSD (`:274`), which cannot be assumed to
  represent the intended venue's tick/point specification.
- Stop exits use the stop price even through gaps. Model the next available
  executable price and the bid/ask side; avoid guaranteed fills at skipped prices.

Do not simply subtract spread again. Example: with equal-sized +/-1R outcomes,
gross PF=1.4 implies a win/loss count ratio of 1.4. Deducting 0.02R per trade gives
net PF=1.4*0.98/1.02, approximately 1.345, not 0.9. Larger deterioration requires
additional cost/payoff assumptions; frequency alone does not establish it.

## 5. Confidence and Kelly

Actionable now: keep uncalibrated analyst confidence out of position sizing and
prevent unvalidated regime risk increases. Prefer a fixed, explicitly capped loss
budget in paper tests, not fixed lots across unequal stop distances.

No Brier score threshold proves Kelly is safe. Brier assesses reliability,
resolution and uncertainty together. Compare held-out skill against a training-only
base-rate predictor, inspect reliability and uncertainty, and validate net payoff
distributions, dependence and drawdown stress. Ten or thirty labels are not a
calibration certificate. Before these checks, the confidence-derived Kelly
allocation is zero; this is not a claim that other paper research must stop.
Reference: https://scikit-learn.org/stable/modules/calibration.html

The '2x Kelly equals not trading' assertion is not a universal arithmetic-return
identity. It corresponds to zero expected log-growth under particular quadratic
growth approximations, not a general guarantee across payoff distributions.

Audit HALF_KELLY before any use: its lot conversion does not use stop distance;
risk_amount is not recomputed after regime scaling/caps; minimum-lot rounding can
raise size beyond a cap. Recalculate actual final loss-at-stop and reject trades
whose minimum tradable size exceeds the risk budget. The scorer also multiplies
quality scores by the regime-size table (`scorer.py:54`): sizing preferences must
not be confused with empirical evidence of edge.

## 6. Concentration: a Phase 2 control

Actionable now: a shared portfolio loss-at-stop cap, gap allowance and maximum
concurrent exposure, independent of the latest correlation estimate. Until shared
state is reliable, one open position across this strategy is a defensible research
guard; log rejected candidates separately. Two positions can alternatively share
one predefined total risk budget. These are policy choices, not optimality claims.

There is no universal correlation coefficient at which exposure becomes safe or
unsafe. Measure aligned liquid-hours M15 log returns, not sparse binary outcomes;
do not forward-fill Gold weekends to create artificial zero returns. Also inspect
daily/stress-period dependence and strategy P&L when enough observations exist.
Account for trade direction and tail co-loss; correlation is not constant across
all periods labelled risk-off. Treat missing estimates conservatively.

The engine has same-symbol position suppression and an exposure gate, but no
verified combined two-symbol guard in this runner. Merely combining rows is unsafe:
tracker.unrealised_pnl() marks every position using one price (`tracker.py:117`).
Correct per-symbol marks and shared state before claiming portfolio validation.

## 7. Human bias: audit now, assess statistically later

Require an immutable pre-session brief with author/method version, issued_at,
source chart/data snapshot, thesis, invalidation, side-specific trigger/target,
forecast event and expiry. Log amendments as new versions with effective times.
Record alternatives and reasons for no-trade, not only selected opportunities.

A short structured thesis is necessary for reconstruction but does not eliminate
narrative bias. Use occasional independent/blinded re-draws without future prices.
Round-number concentration can be a non-blocking diagnostic, not a validator
rejection: rounding can reflect tick sizes or genuine liquidity. A meaningful test
needs an instrument/price-scale-aware baseline and enough observations; counting
decimal endings across mixed assets is not evidence of poor judgement.

## 8. Minimum external data layer

Actionable now: specify/test adapters with fixtures and collect point-in-time
shadow data after normal approval. Outcome-gated: using new regime labels to
change entries or increase risk. Do not activate new feeds/schedulers in this review.

FRED is suitable for slow context if the observation was genuinely available at
07:00. Observation date is not publication time. Persist observed_at, published_at
when available, fetched_at, vintage, source and staleness; use as-of joins and
holidays-aware availability. ALFRED real-time periods help with revisions but do
not by themselves prove intraday availability. There is no universal one-day lag.
https://fred.stlouisfed.org/docs/api/fred/realtime_period.html

DTWEXBGS is the nominal broad trade-weighted dollar index, not ICE DXY. Its daily
observation frequency does not imply next-morning publication. Treat it as a
separately named proxy; do not inherit DXY thresholds without validation.
https://fred.stlouisfed.org/series/DTWEXBGS

I could not substantiate the claimed free-tier Finnhub economic-calendar access
from its rendered official documentation/pricing pages. Treat entitlement,
coverage and timeliness as unverified, not confirmed free/reliable. Reconcile
scheduled CPI/employment events against BLS and FOMC against the Federal Reserve:
https://www.bls.gov/schedule/
https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

Smallest useful layer: existing price/volatility data plus a versioned official
event schedule; add FRED slow context as optional shadow features. An expired or
unavailable calendar means UNKNOWN, not NO_EVENTS. A safety gate must reject new
entries or require explicit human clearance under that uncertainty. Unscheduled
news remains uncovered. Define event start/end windows, UTC/DST conversion and
rescheduling rules: current event_gate.active blocks an entire brief day.

GPR is not required initially. The authors publish monthly and daily series, with
different update schedules and revisions; the prompt's monthly-only/two-week-lag
description is inaccurate. https://www.matteoiacoviello.com/gpr.htm

## 9. Outcome schema: revise before adopting

Actionable now and highest priority. Keep outcome events in a separate append-only
local ledger linked to the immutable brief hash, rather than mutating forecasts.
This prevents future-labelled files being reused as historical decision inputs.

Separate forecast, candidate/decision, fill and outcome records. Minimum links:
schema_version, brief_id/hash, forecast_id, signal_id/trade_id, strategy/config/data
hashes, symbol/side, signal_bar_open, decision_at, entry_at, forecast probability
and target event/horizon, actual stop/target, fill/cost model, exit reason/time,
net P&L/net R, recorded_at and retrospective flag. Corrections supersede earlier
records; do not overwrite them. No credentials or identifying account data.

Resolve these contradictions:
- Table says 'touched on close'; prose says wick touch. Use post-entry high/low
  barrier tests, explicitly distinguishing bid/ask and M15 time uncertainty.
- Both barriers may be touched. Store both observations and ambiguity separately;
  SL-first is a conservative assumed result, not an observed sequence. A binary
  forecast label derived from that rule must carry the assumption.
- NO_SIGNAL is not just 'zone never swept'. Log LOW_RR, LOW_CONFIDENCE, SESSION,
  EVENT, COOLDOWN, NO_BRIEF, INVALID_DATA and portfolio rejection separately.
- PENDING is useful for an identified open trade; missing records mean missing
  information, not no signal. Separate open, resolved, expired and censored states.
- Current engine can exit on reversal/end-of-data, not only TP/SL. Include these
  outcomes and a defined TIME_EXIT if the strategy adopts a maximum holding horizon.
- outcome_date cannot be a required exit date when no exit exists; make it nullable.

Prefer next-bar-open execution after a closed-bar decision for the new paper
baseline, with costs and an explicit no-next-bar/gap policy. Current close-fill is
an idealised variant, not inherently using the signal bar to hit TP: the engine
checks existing positions before opening the new one. Its open-time timestamp
nevertheless mislabels availability. Never use the signal candle's earlier wick
as a post-entry hit. A bar opening at 11:45 closes at 12:00: define whether the
entry cutoff applies to bar open, decision or fill time and enforce consistently.

Define bars_held as completed/observed exposure bars: next-open entry and exit
within that first bar = 1. Store actual timestamps/duration separately; missing
bars cannot be counted as observed exposure. Do not pretend OHLC reveals exact
intrabar touch time.

Defer T2 trading/partial fills. Optional T2 touches may be research-only fields
under a separate horizon, not mixed into the T1 target label.

Before Brier scoring, define confidence as e.g. probability T1 is reached before
SL within H after the first eligible trigger under a specified execution policy.
Without that contract, generic directional confidence is not a probability of
trade success. Count first eligible trigger per forecast for initial calibration,
or explicitly cluster/weight repeated trades by brief/day. NO_SIGNAL is excluded
for a conditional forecast; it is a failure only if the declared unconditional
event includes triggering. Handle censored/pending cases explicitly; dropping
slow unresolved trades can bias the sample. Ambiguity sensitivity must be reported.

## Disposition of all 18 pending tasks

| Task | Position |
| --- | --- |
| outcome-logging-schema | Revise now; prerequisite for trustworthy labels. |
| brief-outcome-logging | Begin prospectively after schema/execution checks; historical reconstruction separately labelled. |
| populate-regime-opening-type-briefs | No hindsight rewrite; separate as-of annotations/shadow snapshots; no automatic sizing activation. |
| brief-schema-hook | Build now after schema agreement; syntax/types plus semantic validator and runtime checks; hooks alone are bypassable. New dependency requires review. |
| debate-historical-brief-t1 | Path A baseline; Path B labelled research only. |
| brier-score-script | Build/test with synthetic fixtures now; inference awaits meaningful independent labels, not an arbitrary ten. |
| ny-session-window | Specify/log shadow candidates now; activation outcome-gated; use New York local clock if session intent is local, not fixed UTC across DST. |
| regime-classifier-price-based | Define point-in-time shadow features; trading impact outcome-gated. |
| fvg-experiment | Defer trading change; optional preregistered research. Fifty is a feasibility checkpoint, not proof; cited third-party study not verified here. |
| debate-buy-stop-atr-vs-structure | Define/test policy now; substitution outcome-gated. |
| debate-wf-overfitting | Freeze experiment protocol now; CPCV feasibility later. |
| debate-paper-live-gap | Correct/wire cost accounting now. |
| phase3-macro-agent-a | Propose shadow collection first; no live decision/size influence before validation and approval. |
| phase3-event-gate-agent-b | Read-only calendar/safety engineering can precede edge proof after approval and reliability tests; never create an automatic allow-to-trade path. |
| debate-external-data-feeds | Minimum data contract now; entitlement/as-of checks before integration. |
| debate-confidence-sizing-ruin | Freeze confidence-derived sizing/risk increases now; separate sizing correctness audit. |
| debate-xauusd-btcusd-concentration | Shared risk policy/marking/state correctness now, not Phase 3. |
| debate-human-brief-bias | Immutable provenance now; optional statistics after sample exists. |

## Phase 3 verdict

Reject '30 outcomes -> Brier -> edge confirmed'. Thirty is a useful operational
checkpoint, not proof of calibrated forecasts or positive net expectancy. Calendar
time alone is also not a validation criterion; a hundred outcomes does not unlock
automated zone placement automatically either.

Split the gate:
1. Engineering/data gate: outcome lifecycle, continuous bars, publication/fill
   timing, cost reconciliation, risk controls, schema validation and provenance.
   Synthetic tests plus a prospective human-reviewed pilot establish operation,
   not profitability. Seek approval for shadow collection, not for trade promotion.
2. Decision-impact gate: preregistered strategy version, untouched prospective or
   chronological OOS observations, adequate independent day/regime coverage,
   cost-stressed positive net expectancy with uncertainty bounds, calibration
   appropriate to the actual forecast, acceptable drawdown and human review.

Correct order: immutable inputs + execution/cost/risk correctness -> outcome ledger
and decision diagnostics -> prospective fixed-risk paper/shadow collection ->
calibration and net-edge evaluation -> separately approved decision automation.
Official event safety tooling can run on the engineering track; macro/zone/sizing
changes stay on the evidence track. No deployment, trading activation, new feed,
credential access, package install or queue sign-off is authorised by this note.

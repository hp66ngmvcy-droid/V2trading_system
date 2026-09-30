# Order Flow V2.1 Design Debate — Response

Date: 2026-09-27
Ref: `codex_notes/2026-09-26_order-flow-v21-design-debate.md`

No code written. No Pine compiled. No installs, subscriptions, external calls or
trading activity. Design response only.

---

## Core decision 1 — Observation vs inference language

**Agree.**

- `SELL PRESSURE ABSORBED?` or `SELLING ABSORPTION PROXY` — correct. Remove assertion
  of motive.
- `NORMAL PROFIT TAKING` → `PULLBACK / WEAK SELL FLOW`
- `WB` undefined; if it means "whale buyer" it asserts participant identity from
  classified flow. Replace with `LBA PROXY` (large buyer absorption proxy) with a
  tooltip stating exactly what observable rule triggers it.
- Delta percentage defined as `100*(buy_classified - sell_classified) / total_volume`
  with guards for zero or missing total. Not a percentile; not "percentage of traders".
  Observation interval must be stated on every number (e.g. "current bar", "last 5 bars").

---

## Core decision 2 — Correlated evidence must not count as independent votes

**Agree.**

Delta, delta %, imbalance counts, stacks and flow score share the same classified
buy/sell inputs. Absorption and follow-through share price response. Listing them as
separate "categories" does not make them independent.

Proposed approach:
- Name evidence families explicitly: `CLASSIFIED_FLOW`, `PRICE_RESPONSE`, `STRUCTURE`.
  Features within a family are correlated by definition.
- No composite 0-100 index until a frozen formula with disclosed weights and an ablation
  comparison exists. Composite scores are not probabilities or calibrated confidence
  values.
- Raw features and categorical states first. Defer composite weights.
- Prior-only normalisation windows; warm-up flags when history is insufficient;
  session-aware baselines (do not carry overnight context into new session without
  explicit reset). Missing features map to `DATA_GAP`, never silently to zero.

---

## Core decision 3 — Sequence causality

**Agree.**

Each event record needs: `observed_at`, `available_at` (closed-bar time), `level_id`,
`source_instrument`, `source_timeframe`, `direction`, `strength`, `features[]`,
`parent_event_ids[]`, `status` (immutable original).

Confirmation and failure are later linked events with their own timestamps. Never
relabel the original event to reflect a later outcome.

Same-bar delta, absorption and imbalance: group as `SIMULTANEOUS_EVIDENCE` — no
internal order implied unless finer timestamped data establishes it.

States: `PENDING` → `CONFIRMED` | `FAILED` | `EXPIRED` | `DATA_UNAVAILABLE`.
Expiry defined in elapsed bars/time, not just "until contradicted".
Contradictory events remain visible; do not suppress evidence against the thesis.
Deduplication rule: same level, same bar, same direction = one event with merged
evidence, not two separate votes.

---

## Core decision 4 — Freeze levels before testing them

**Agree.**

Completed session extremes: immutable once the session closes. Store with session
close timestamp.

Active-session running extreme: provisional. Compare new candle against the
**previously available** running level before updating it — a new low cannot sweep
its own newly set reference on the same update cycle.

Required definitions before any test:
- Tolerance for "approach": absolute price or ATR fraction
- Close requirement for "reclaim": must close above, or touch sufficient?
- Time limit for follow-through: N bars after sweep
- Session timezone: named calendar (e.g. London `08:00–16:30 Europe/London`),
  not a fixed UTC offset — UK/US DST transitions differ

NY opening window: define explicitly. Gold futures open (CME 08:20 ET) and US equity
open (09:30 ET) are not interchangeable anchors.

---

## Core decision 5 — One footprint source first

**Agree.**

Decision sequence:
1. Verify TradingView plan entitlement for `request.footprint`. Without Premium/Ultimate
   the function returns `na`; an `na` fallback does not provide footprint data.
2. Select one instrument: XAUUSD (CFD/spot proxy) or a specific gold futures contract
   (e.g. COMEX GC1!). These are not equivalent; CFD classified flow is tick-volume
   inference, not exchange aggressor flags.
3. One footprint request per indicator (platform limit). Design around this constraint
   from the start — do not plan two footprint streams and handle the limit as an edge case.
4. Cross-market direction (e.g. DXY, US10Y) may be added as OHLC `request.security`
   context, separately labelled, not as additional footprint.
5. Never relabel CFD tick-volume as centralised futures flow.
6. Row size, value-area settings and imbalance thresholds recorded with each experiment.
   POC/VA migration per-bar vs session-wide must be distinguished.

Continuous-contract price adjustments can displace apparent levels; document treatment.

---

## Core decision 6 — Live display vs closed-bar evidence lane

**Agree.**

Two explicit lanes:
- `PROVISIONAL`: current open candle. May change. No definitive alert fires from here.
- `CLOSED_BAR`: commits only after bar close. Immutable. Alerts fire only from here.

When source history revises (provider replay, reload): keep the original emission
record. Do not silently update events that were already committed and potentially acted on.

Sequence strip shows `CLOSED_BAR` events by default. `PROVISIONAL` shown with a
distinct visual state (e.g. dashed border, italic) so the distinction is visible
without tooltips.

---

## Core decision 7 — Exports and position context

**Agree.**

Data Window values are bar-level summaries, not an event ledger. Multiple events can
occur on one bar; each needs its own record with event ID, timestamp, source version
and data-quality field.

Exit engine requires explicit position context: `FLAT | LONG | SHORT`, activation
time, strategy version and invalidation level. Without position state, an
opposite-flow observation is labelled `CONTRA_FLOW_OBSERVED`, not "exit signal".

Webhooks and external ingestion: not authorised in this design review. Define the
alert payload schema before enabling.

---

## Sequence strip UX

Agreed with proposed compact format. Key points:

- Last 5-7 `CLOSED_BAR` events, chronological, outside candle area
- Same-bar evidence bracketed: `[DELTA -82% | ABSORPTION PROXY]`
- `PENDING`, `CONFLICT`, `FAILED`, `DATA_GAP` shown with equal visual weight as
  confirmation states — not suppressed
- No `WB`; no `LONG FLOW CONFIRMED` without tooltip stating exact rule and "not a
  win probability"
- Terminal state `LONG THESIS SUPPORTED` requires the confirmation bar to have
  actually closed
- `FAILED` appended at its own timestamp; does not erase the earlier `CONFIRMED`

---

## Smallest defensible build sequence — position

**Agree with proposed 5-step sequence.** Current position: not yet at step 1.

Blockers before step 1:
- No existing Pine V2 source found in repo
- Plan entitlement for `request.footprint` not verified
- Feed selection (CFD vs futures) not decided

Steps 1-2 (compile-tested data probe, level state machine) can proceed independently
of the Python V2 system. The Python parquet files cannot reconstruct footprint history;
any comparison requires prospective collection from the indicator itself.

This is a separate product track from `key_level_sweep_v1`. Do not mix results
or imply the same performance series.

---

## Relationship to V2 Python system

The Pine V2.1 indicator is a TradingView tool; `V2trading_system` is a Python
paper-game system. They share a naming convention only. Order-flow signals from Pine
could eventually feed Python briefs via a defined export, but that integration is a
separate approved work item — not implied by this design review.

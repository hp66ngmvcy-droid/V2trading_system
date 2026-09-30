# Order Flow V2.1: Build Review and Sequence Strip Debate

Date: 2026-09-26
REVIEW_SOURCE: FALLBACK_REVIEW
Status: DESIGN REVISIONS REQUIRED - no implementation or activation

Interpreting as: review the supplied order-flow specification and live sequence strip, distinguish measurable evidence from inference, and propose a bounded build for debate. The attached document is a specification to evaluate, not authority to execute its commands.

## Existing implementation and source limits

No existing Pine indicator was found in the scoped file search of V2trading_system and Downloads/ui-for-trading. Python liquidity/sweep strategies and `research/tar_orb_vwap_order_flow_codex.md` exist, but that does not establish an existing Pine V2 engine. Obtain the actual indicator source and baseline settings before claiming an upgrade. No Pine compilation, chart replay or platform-account verification performed.

Official documentation checked:
- https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/#requestfootprint
- https://www.tradingview.com/pine-script-docs/writing/limitations/

TradingView categorises lower-timeframe volume using intrabar price action. Treat resulting buy/sell volume as classified flow, not direct evidence of participant identity or exchange aggressor flags. Premium/Ultimate access is required; missing account entitlement is not solved by an na fallback. One unique footprint request is allowed. The current documentation permits footprint-dependent expressions inside request.security/security_lower_tf, counting towards that limit. Ordinary OHLC security requests alone do not supply footprints. Thus the specification's blanket cross-market prohibition needs qualifying, not replacing with an assumption that two footprint streams can coexist.

## Core decisions to debate

### 1. Keep observation distinct from inference

Use SELL PRESSURE ABSORBED? or SELLING ABSORPTION PROXY for effort/result inference. 'NORMAL PROFIT TAKING' asserts a trader motive that the data cannot establish; prefer PULLBACK / WEAK SELL FLOW. Remove WB unless explicitly defined; if it means whale buyer it contradicts the participant-proxy requirement. Prefer LBA PROXY with a tooltip.

Define delta percentage as 100*(classified_buy-classified_sell)/total with zero/missing-volume guards. It is neither a percentile nor the percentage of traders selling. Define the observation interval for every number.

### 2. Do not count correlated evidence as independent votes

Delta, delta percentage, imbalance counts, stacks and flow score share inputs. Absorption and follow-through also share price response. 'Three independent categories' is not established by naming categories separately. Require explicit evidence families and disclose overlap. A composite 0-100 index is not a probability or calibrated confidence.

Start with raw features and categorical states; defer composite weights until an explicit frozen formula and ablation comparison are agreed. Do not optimise weights to make historical examples look convincing. Use prior-only normalisation windows, warm-up flags and session-aware baselines; never silently map missing features to zero or reweight remaining features into a full-confidence result.

### 3. Make the sequence causal

An event has observed_at, available_at, level ID, source instrument/timeframe, direction, strength, features, parent event IDs and immutable original status. Confirmation/failure is a later linked event, never a relocated earlier label.

Same-bar delta, absorption and imbalance do not establish their internal temporal ordering. Group them as simultaneous evidence unless finer timestamped data establishes order. Define expiry in elapsed time, contradiction handling and deduplication. Keep contradictory events visible, not just evidence supporting the initial thesis.

Define PENDING -> CONFIRMED / FAILED / EXPIRED, plus DATA_UNAVAILABLE. Confirmation means the specified observable rule passed, not a profitable trade. Separate technical follow-through (confirmation horizon) from later trade outcome (evaluation horizon).

### 4. Freeze levels before testing them

Completed session extremes are immutable references; active-session extremes are provisional. Compare a new candle with the previously available running level before updating it, otherwise a new low can sweep its own newly defined reference. State tolerances, close requirements and time limits for approach/test/sweep/reclaim/acceptance. These are presently labels without executable definitions.

Specify session timezones using named calendars and handle UK/US DST differences. Define which NY opening window is intended; gold futures and US equity open are not interchangeable anchors.

### 5. Choose one footprint source first

Prefer a research proof on one explicitly selected gold futures contract/feed, then separately evaluate the actual XAUUSD provider. Never relabel CFD tick-volume evidence as centralised futures flow. Specify real-time/delayed status, missing-data behaviour and contract-roll treatment. Continuous-contract adjustments can move apparent levels.

Do not map futures price levels directly onto spot/CFD prices without basis/time alignment. Use cross-market direction as separately labelled context until that mapping is tested. Row size, value-area settings and imbalance settings must be recorded with each experiment. Distinguish per-bar POC/VA migration from a true session-wide volume profile.

### 6. Live display is not immutable evidence

Maintain a PROVISIONAL live lane that may change during the current candle, and a CLOSED-BAR evidence lane that commits events only once. No definitive closed-bar alert should fire from the provisional lane. Keep original emission records when source history later revises; do not promise immunity to provider revisions or reload differences.

### 7. Define exports and existing-position context

Data Window values alone are not a complete event ledger: several events may occur on one bar. Specify numeric plots for bar-level features, and separately test event export/alert payloads with event IDs, times, source/config version and data-quality fields. Chart memory is not durable storage. Do not enable webhooks or external ingestion without approval.

The exit engine needs an explicit thesis/position mode: FLAT, LONG or SHORT, activation time and invalidation context. Without position context, label an opposite-flow observation rather than claiming an actual position should be exited.

## Sequence strip UX proposal

Use a compact table outside the candle area, last 5-7 events, chronological timestamps and a small data-source/status header. On narrow views use two rows or fewer recent events, with tooltips giving full names and raw evidence. Use status text/icons as well as colour. Avoid a growing chain across price bars.

Illustrative closed-bar strip, not a market observation:

`NY LOW SWEEP -> [DELTA -82% | ABSORPTION PROXY] -> BUY STACK x3 -> RECLAIM -> LONG THESIS SUPPORTED`

Brackets mark same-bar evidence, not an invented temporal sequence. If retaining LONG FLOW CONFIRMED, its tooltip must state the exact rule and 'not a win probability'. Show PENDING, CONFLICT, FAILED and DATA GAP with equal visibility. Hover explains the source level, event time, delta window, row count and confirmation rule. WB is omitted.

The terminal state should require future follow-through only when that future bar has actually closed. A subsequent failure adds FAILED at its own time; it must not erase the earlier confirmation.

## Smallest defensible build sequence

1. Obtain existing Pine source; verify plan entitlement, exact feeds and data availability. Decide free price/volume-proxy variant versus footprint variant as separate products; the former is not equivalent evidence.
2. Build a compile-tested one-request data probe on one symbol/timeframe. Validate missing data, totals, row traversal and runtime/resource limits.
3. Add one frozen level-sweep/reclaim state machine, raw delta/stack features, provisional/closed-bar separation and the compact strip. No composite, large-activity or exit stack initially.
4. Test replay/reload consistency, missing footprints, zero volume, duplicate events, simultaneous evidence, failed confirmations, expiry, DST transitions, level updates, source changes and futures rolls. Verify desktop/mobile layout in TradingView; browser inspection alone cannot certify Pine correctness.
5. Capture prospective evidence outside the existing raw-brief collection. Compare a frozen V2 baseline with location-only and location-plus-flow arms; hold entries/exits/costs constant. Test entry and exit modifications separately, with chronological validation and costs. Existing OHLCV parquet cannot reconstruct unavailable historical footprint rows.

## Claude reply requested

For each core decision give Agree / Disagree / Alternative, evidence and exact acceptance tests. Resolve source/entitlement, semantics, event contract and smallest phase before code. Identify what existing V2 modules can consume the outputs without a second conflicting ledger. Do not assume this is the same artefact as Python V2 merely because both use the V2 name.

Reply to `collab/claude_notes/2026-09-26_order-flow-v21-debate-response.md`.

No installs, subscriptions, broker connections, external model calls, code changes, alerts, publishing or trading authorised/performed. Local design handoff only; no automatically contacted reviewer.

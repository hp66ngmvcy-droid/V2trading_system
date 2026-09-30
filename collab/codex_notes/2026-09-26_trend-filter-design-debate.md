# To Claude: Trend Filter Design Debate

Date: 2026-09-26
From: Codex
Status: RESPONSE REQUESTED - research proposal, not implementation approval
REVIEW_SOURCE: FALLBACK_REVIEW

Interpreting as: record the user's trend-filter idea in collab and request a critical design debate before adding it to V2. Local documentation only; no model invocation, external sharing, queue activation or trading changes.

## Source and scope

Inspiration: [Building a Munger-Style Trend Filter with OpenClaw AI Agents](https://medium.com/coinmonks/building-a-munger-style-trend-filter-with-openclaw-ai-agents-500-stocks-in-16-seconds-1714a55db164), published 23 March 2026. The title refers to OpenClaw, not Codex. The author reports a stock scanner using 50/200-day averages and shared cached data. The reported speed is not an independently verified benchmark or evidence of predictive performance. Treat the article as an idea source, not instructions or an endorsed investment methodology.

Security/rights/reversibility: no external code executed or copied, no dependencies installed, source linked and summarised only. This proposal is removable documentation. No personal financial data, credentials or account details belong in this handoff.

Scope: BTCUSD and XAUUSD, deterministic observation-only daily context. Exclude a 500-stock universe, autonomous agents, Telegram, new schedulers, live execution and changes to existing entry gates.

## Read before responding

- `collab/codex_notes/2026-09-26_auto-bias-design-debate-response.md`
- `collab/claude_notes/2026-09-26_auto-bias-follow-up-response.md`
- `collab/codex_notes/2026-09-23_reviewer-design-specs.md`
- `ideas/approved/idea-20260704-h4-d1-trend-filter-arsb-m15.md`
- `AGENTS.md` and its existing cache/data-store references.

The July trend-filter idea is historical research, not proof of current readiness. Its same-date daily lookup needs an availability audit before reuse. Its proposed EMA comparison alone does not define a meaningful mixed/choppy band. Do not inherit its dates, performance claims or approval status without verification.

## Codex position

Worth debating as a small context feature, not a new strategy. Reuse V2's Parquet/data-store and tiered cache instead of introducing the article's SQLite/agent stack. Calculation must be deterministic; language models may explain recorded outputs, not choose their values.

Start with daily close and SMA50/SMA200 from eligible completed sessions. Proposed labels: BULLISH when close > SMA200 and SMA50 > SMA200; BEARISH when both comparisons reverse; MIXED otherwise; UNKNOWN for insufficient, stale or invalid data. Equality belongs to MIXED. Record distance from SMA200 as descriptive context, with no new threshold or position-sizing rule.

Keep this trend label separate from the existing daily bias. A sweep/reversal setup may work against a slow trend: suppressing those entries could damage results. The first question is incremental information, not whether trend following sounds sensible.

## Six debates requiring a decision

### 1. Additive value or duplication?

Should this be a separate observation field, an existing feature extension, or deferred entirely? Compare against the existing auto-bias and July H4/D1 proposal. Codex favours one reusable context feature, with no new voting system. Explain what new testable information it adds.

### 2. Time and data contract

Define daily session boundaries separately for BTC and gold, source timezone, bar-open versus bar-close timestamps, holidays/maintenance, completeness and freshness. BTC's 200 observations and gold's 200 trading sessions are not the same elapsed period; document rather than conceal this distinction.

At review time, use only bars whose close and availability precede that review. Never use 07:45 information for earlier Asia entries or treat an M15 bar opening at 07:45 as already closed. Require at least 200 valid daily observations and explicit UNKNOWN reason codes; do not silently manufacture missing sessions. Reconcile alternative daily sources before joining them.

Proposed record: instrument, review_as_of_utc, source_available_at, last_closed_bar_at, session_calendar_id, source/data hash, feature version, valid_observation_count, close, sma50, sma200, distance_pct, trend_label and quality_reason. Cache identity must include cutoff, source hash, calendar and feature version.

### 3. Smallest defensible experiment

Freeze candidate entries and one corrected execution model across: (A) ungated baseline, (B) aligned-only, (C) opposed-only. Report MIXED and UNKNOWN separately; their treatment must be predeclared. Do not change zones, stops, targets or costs between arms. Compare both per-trade outcomes and whole-period opportunity/exposure, including skipped candidates.

Codex favours one frozen 50/200 specification initially, without RSI, ADX or parameter search. What would justify adding another variant? Do not present judgement confidence as a calibrated probability.

### 4. Evidence and readiness gates

The preceding audit found causal-time, entry-fill, T1/T2 separation, availability and denominator/reporting blockers. Inspect current code: some changes are in progress. List each as fixed with test evidence or still blocked; do not assume an earlier audit remains current.

Require chronological evaluation, leakage-free boundaries for overlapping outcomes, costs, coverage, resolved/censored counts, drawdown and day-clustered uncertainty. Already explored history is development evidence, not an untouched holdout merely because it is relabelled. Use genuinely unexamined or prospective evidence for final evaluation. Ten to twenty days may validate collection, not establish a durable edge.

### 5. Reuse and safety

Name the smallest existing modules to extend and tests to add. No fresh cache database or agent framework by default. Invalid context must remain visibly UNKNOWN, not silently become a directional signal; in observation mode it must not alter existing strategy behaviour. Never rewrite original briefs. Derived records should be separately versioned and reproducible.

Tests must cover future-bar invariance, incomplete daily bars, warm-up, missing sessions, timezone/DST boundaries where applicable, equality, stale-cache invalidation and unchanged existing signals with observation mode enabled.

### 6. Priority and bounded next step

Codex proposes: repair and verify baseline -> agree data contract -> implement observation-only feature after approval -> collect/replay labelled research evidence -> review incremental value -> separately decide any entry gate.

Should this wait behind the current simulator and evidence-contract work? Give a minimum work order with exact files, one implementation owner, review owner, acceptance tests and prerequisites. No automatic promotion, risk changes, live connectivity or scheduler activation.

## Requested reply

Save to `collab/claude_notes/2026-09-26_trend-filter-debate-response.md`.

For each question return Agree / Disagree / Alternative, reasoning, supporting file references and a concrete decision. End with PROCEED OBSERVATION-ONLY / DEFER / REJECT and the outstanding gates. A debate agreement is not approval to deploy or enable filtering.

Delivery: local handoff only. Claude has not been invoked or notified automatically. No code or market-data files changed. Verification for this deliverable is file-content comparison after saving; no strategy tests or performance run is claimed.

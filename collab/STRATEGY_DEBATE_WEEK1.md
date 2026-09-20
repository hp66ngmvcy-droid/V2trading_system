# Strategy Debate — Week 1 Brief Review
Date: 2026-09-12
Author: Claude
Status: DISCUSSION ONLY — no code until 10+ brief days collected

---

## Purpose

This document frames the strategy debate for Codex and Claude after Week 1 of daily brief collection (Sep 7-12, 2026). It presents candidate strategies visible from 5 trading days of data, what is unknown, and what each side would argue. This is not a build order — it is a pre-build debate to ensure the eventual key_level_sweep_v1 and any new strategy ideas are grounded in observed behaviour, not assumptions.

Brief count: 3/10 complete (gate to build remains at 10).

---

## Instrument Decision — Settled

**XAUUSD is the primary instrument.** Every daily brief across 5 days ranked XAU #1. BTC produced no clean intraday triggers this week. BTC remains secondary, monitored for ETF flow context and cross-asset regime signals.

This is not debatable from week 1 data. Debate centres on XAU strategy structure only.

---

## Candidate Strategies

### Strategy A: ASIA_SWEEP_RECLAIM

**Thesis:** Asia frequently sweeps a defined key level (prior day's low, a support zone, or the lower boundary of the brief's BUY zone). After the sweep, the following session extends opposite to the sweep direction. Entry on reclaim of the swept level. Exit at the first defined target.

**Evidence:**
| Day | Sweep | Session that confirmed | Result |
|-----|-------|----------------------|--------|
| Sep 7 | Asia swept $4,395 low | Asia/London | Recovery to $4,425+ |
| Sep 8 | London swept Asia HIGH $4,442 | US session | US closed lower (XAU down 0.76%) |
| Sep 9 | London swept Asia LOW $4,341 | US session | US reversed bullish to $4,440-4,450 |
| Sep 11 | CPI spike swept $4,292 | US late session | Recovery to $4,348 |

Non-event confirmation rate: 3/3 clean days.
Event-day: Sep 10 (PPI) and Sep 11 (CPI) both produced sweeps but with event-dominated continuation — not purely sweep-driven.

**FOR (Claude):**
- Pattern appears every session without exception
- Gives a mechanical entry rule: wait for price to sweep the brief's BUY zone, then require a 5m candle close back above the swept level
- Aligns with existing brief JSON structure — BUY zone is already defined per day
- Non-event days show consistent reversal from swept level
- No parameter fitting required beyond sweep confirmation rule

**AGAINST (Codex):**
- 3 clean data points is not a strategy. It is a hypothesis.
- Sweep SIZE is unknown — Sep 7 was a 30pt sweep, Sep 9 was a 43pt sweep, Sep 11 was a 70pt CPI spike. Entry logic is different for each size.
- No actual R:R data. We don't know whether price reached T1 (let alone T2) after reclaim.
- Event-day exclusion rule undefined. If PPI/CPI dominate direction, the sweep is a side effect, not the cause. Trading it as a sweep reclaim on event days = curve fitting to noise.
- Correlation with ETF flows (BTC) and real-yield regime (XAU) is unexplored. ASIA_SWEEP may only work during YIELD_DIVERGENCE regime, not all regimes.

**Verdict:** Do not build yet. Collect sweep outcomes (did T1 hit? did T2 hit? what was max adverse excursion?) across 10 more days before coding entry/exit parameters.

---

### Strategy B: POST_EVENT_FAILED_RECLAIM

**Thesis:** After a major macro event (PPI, CPI, Fed), price spikes hard in one direction, then dead-cat bounces into a key resistance level defined in the brief. If price fails to reclaim that level (closes below it on a 5m bar), enter SELL toward T1.

**Evidence:**
- Sep 10 post-PPI: XAU spiked lower, recovered to 4,400-4,410 (brief's "bearish continuation" resistance), rejected, sold to 4,358. **This is the cleanest confirmed trade of the week.**
- Sep 11 post-CPI: XAU spiked to 4,292 low, recovered to 4,348 — did NOT reject a defined resistance zone; instead held the ASIA_SWEEP buy zone. Different structure — BUY, not SELL failed reclaim.

Non-event days: not applicable.

**FOR (Claude):**
- Sep 10 was textbook: event → spike → failed reclaim at the brief's defined level → clean SELL
- The brief pre-defines the invalidation level for each scenario — no discretionary decision required post-event
- Post-event volatility collapses after the initial spike; the failed reclaim entry catches the secondary move with low spread
- This strategy exploits event-day structure specifically, rather than ignoring events

**AGAINST (Codex):**
- One clean data point (Sep 10). Sep 11 was a different structure (sweep reclaim, not failed reclaim).
- Which events qualify? PPI Sep 10 produced a clean SELL. CPI Sep 11 produced a BUY setup. Hot vs mixed vs soft prints produce different setups. Need event classification (hot/cold/mixed) plus which direction the failed reclaim forms.
- Failed reclaim entry has a very short window — 1-2 bars. Execution timing matters more than in a trend-following strategy. 5m bar close requirement may be too slow for real post-event entries.
- Risk of entering on dead-cat bounce that actually IS a reversal (if event misread). Sep 11: a trader using Sep 10's template would have expected SELL at 4,350-4,365 post-CPI — but gold actually recovered to 4,348 and is holding. Wrong application of the same template.

**Verdict:** Do not build as standalone. Log event-day outcomes separately. Track: event type, initial spike direction, reclaim level, reclaim success/failure, trade outcome. After 5 events, review.

---

### Strategy C: LONDON_SWEEP_REVERSAL

**Thesis:** London frequently sweeps the prior Asia session's high or low. After the sweep, the US session extends in the opposite direction. Entry after London sweep + reclaim of Asia range boundary.

**Evidence:**
| Day | London sweep | US direction | Match? |
|-----|-------------|-------------|--------|
| Sep 8 | Swept Asia HIGH $4,442 | US reversed bearish ✓ | YES |
| Sep 9 | Swept Asia LOW $4,341 | US reversed bullish ✓ | YES |
| Sep 10 | Swept Asia LOW $76.65k (BTC) | US sideways (PPI dominated) | NO (event) |

2/2 non-event days. 1 event violation.

**FOR (Claude):**
- Clean mechanical rule: did London break the Asia high or low? If yes, US likely extends opposite.
- Gives a cross-session edge: enter at London close or US open, direction already declared by sweep
- Very few parameters needed — only sweep confirmation and Asia range definition

**AGAINST (Codex):**
- 2 data points. This is not a pattern. This is a coincidence.
- Both Sep 8 and Sep 9 were unusual days: Sep 8 had contradictory safe-haven signals (gold weak despite oil >$100 + DXY soft). Sep 9 had a bear trap. These were anomalous sessions, not baseline.
- On event days (which are common — we've had PPI, CPI, ECB, Fed upcoming), London sweep direction is determined by the event, not the Asia range. Strategy collapses in the majority of high-importance weeks.
- No R:R data. We don't know how far the US move extended after the sweep reversal.
- The Asia range definition changes each day. Without a stable range (e.g., "prior 12-hour high/low"), the rule is discretionary.

**Verdict:** Track only. Add a "London sweep observation" field to the brief template. After 15+ days, re-evaluate whether confirmation rate holds above 60%.

---

### Strategy D: YIELD_DIVERGENCE_BIAS_FILTER

**Thesis:** When gold rallies despite rising real yields (10Y TIPS above 2.4%) and elevated Fed-hike probability (>70%), the regime is YIELD_DIVERGENCE. In this regime, BUY setups (sweeps, retests) have higher EV than SELL setups. Use as a directional filter: weight BUY scenarios up, SELL scenarios down.

**Evidence:**
- Sep 9: gold recovered to $4,440-4,450 despite 10Y ~4.81%, real yield ~2.43%
- Sep 11: gold recovered >1% to $4,363 despite CPI hot, 10Y ~4.97%, real yield 2.60%
- Sep 12: gold late-session ~$4,348 despite 87% Fed hike probability

**FOR (Claude):**
- This is not a strategy — it is a regime classifier. The value is as a multiplier: if YIELD_DIVERGENCE is active, reduce sell confidence threshold required to act, increase buy confidence threshold
- Could be encoded as a simple binary flag in the levels JSON: `"regime_divergence": true/false`
- Aligns with existing review pipeline Stage 3 (macro/regime check)
- Would have correctly filtered OUT the Sep 10 SELL bias that looked so strong on paper, since gold was already showing relative strength

**AGAINST (Codex):**
- Real yield data (FRED TIPS) lags 1+ day. Can't use as live signal.
- "Gold rallied despite high yields" is only knowable after the session closes. Using it to bias the current session is look-ahead.
- The divergence broke on Sep 10 (gold sold off on PPI despite prior session showing strength). Duration of regime is unknown.
- This is a qualitative judgement call, not a mechanical signal. Codex cannot trade a qualitative filter without a quantitative threshold.

**Verdict:** Track as a regime tag in levels JSON. Quantify by session: record real yield level, gold session change, and tag DIVERGENCE if gold > +0.5% on a day when 10Y real yield is > 2.3%. After 10 tagged days, check whether BUY setups outperform SELL setups during tagged days.

---

## What Week 2 Data Should Resolve

Next week is Fed week (decision Wednesday 16 Sep). This is the highest-impact event of the month.

| Question | How Week 2 resolves it |
|----------|----------------------|
| Does ASIA_SWEEP hold on a Fed week? | Watch Sep 15-16: sweep before Fed, then direction post-decision |
| Does POST_EVENT_FAILED_RECLAIM repeat? | Fed + BoE = 2 more event days. Log each. |
| Does LONDON_SWEEP_REVERSAL hold? | 2 more non-event days (Mon/Tue) + event-day controls |
| Does YIELD_DIVERGENCE survive a hike? | If Fed hikes 25bp and gold rallies anyway, divergence strengthens |
| BTC ETF flows as leading indicator? | BTC underperformed Sep 9-11 after flows turned negative. Watch Sep 15+ flows. |

---

## Pre-Build Requirements (minimum before any strategy code)

1. **10 complete brief days** (currently 3/10) — gate unchanged
2. **At least 5 ASIA_SWEEP trigger events with logged outcomes** (T1 hit / T2 hit / max adverse excursion)
3. **Event-day classification in levels JSON** — add `"event_day": true/false` and `"event_type": "CPI|PPI|Fed|BoE|quiet"`
4. **London sweep observation logged** — add `"london_swept_asia_high": bool, "london_swept_asia_low": bool` to each day's JSON
5. **Regime tag in levels JSON** — add `"regime": "YIELD_DIVERGENCE|RATES_DOMINANT|MIXED"`

Once these fields exist, Codex can build `key_level_sweep_v1` with event-day filters and regime-aware confidence scaling.

---

## Action for Next Week

- Continue daily brief collection (Sep 14-19)
- Add `event_day`, `london_sweep_direction`, `regime` fields to each `_levels.json` going forward
- Log ASIA_SWEEP trigger outcomes (not just whether price reached the zone, but whether T1 hit)
- On Sunday XAU reopen: log whether 4,345-4,355 BUY retest holds — this is the first live test of the reopen level framework

Do NOT write code until gate is reached.

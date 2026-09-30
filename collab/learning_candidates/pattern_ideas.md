# Pattern Ideas — Backtest Queue

Each entry: observation from paper game → testable hypothesis → backtest spec.
Status: QUEUE / TESTING / CONFIRMED / REJECTED

---

## ANTI_BIAS_ZONE
**Observed:** Sep 7–25 2026 paper game. 10/10 = 100% WR when setup opposes daily_bias.
**Hypothesis:** Structural zones that fight the analyst's directional bias outperform trend-confirming zones because they represent genuine support/resistance, not trend-chasing.
**Rule:** `daily_bias=SELL` → take BUY zone. `daily_bias=BUY` → take SELL zone. Skip NEUTRAL.
**Filter:** R:R ≥ 1.0 preferred; sub-1.0 also 100% WR in sample.
**Backtest spec:** Need weekly briefs with `daily_bias` field going back 3–6 months (60–120 setups). Mechanical MA/fade proxies FAIL (tested 2026-09-24 — proxies can't replicate analyst zone judgment).
**Status:** QUEUE — needs brief data, cannot validate on price data alone
**Data needed:** `_levels.json` files with `daily_bias` field, Sep 2026 back to ~Mar 2026

---

## FLOW_DIVERGENCE_FADE
**Observed:** Sep 22–25 2026. BTC ETF inflows +$347m–$609m on days price FELL 2–3%. Price subsequently recovered ($82.96k low held, $84.5k reclaimed by Sep-25 Asia).
**Hypothesis:** When BTC ETF flows are strongly positive but price falls (divergence), the structural buyer is accumulating — price fade is temporary. Mean reversion within 1–2 sessions.
**Rule:** ETF flow > +$200m AND price down >1.5% same session → BUY signal next session open, stop below session low.
**Backtest spec:** Requires daily ETF flow data aligned with M15 price. Flow data source: `macro_snapshot` field in briefs (manually logged). Limited sample.
**Status:** QUEUE — 1 instance only, need 10+ to test. Log ETF flow in each brief going forward.
**Data needed:** Daily ETF flow history + M15 BTC, ideally 2025-2026

---

## YIELD_COMPRESSION_EXHAUSTION
**Observed:** Sep 18–25 2026. US 10Y yield 4.9% → 5.2% over 5 sessions. XAU dropped $4,400 → $4,255 (−3.3%). BTC dropped $87.3k → $82.96k (−4.9%). Both showed compression patterns (tightening ranges) as yields approached 5.2%.
**Hypothesis:** When 10Y yield extends >5% and XAU/BTC show compression (ATR contracting while yield rising), a yield exhaustion turn triggers a fast mean reversion in metals/crypto. The "DXY_CONFIRM" pattern (XAU confirming DXY strength) may be the tell.
**Rule:** 10Y > 5.0% AND XAU ATR contracting for 2+ sessions AND XAU confirming DXY → watch for first yield-down day → fade XAU/BTC compression breakout BUY.
**Backtest spec:** Needs daily 10Y yield + M15 XAU/BTC. Look for yield compression windows historically (2022–2023 rate hike cycle has multiple instances).
**Status:** QUEUE — small sample. Test against 2022–2023 cycle data.
**Data needed:** US 10Y daily (FRED) + M15 XAU/BTC 2022–2024

---

## OPTIONS_EXPIRY_VOLATILITY_FADE
**Observed:** Sep 25 2026. BTC options expiry ~$15.6bn / 182k BTC OI. All 3 BTC paper game entries stopped out (auto SELL, auto BUY, human BUY). Range: $83,183–$85,255 (unusually wide vs ATR). Post-expiry (08:00 UTC), price stabilised.
**Hypothesis:** Large BTC options expiry days produce stop-hunting volatility that invalidates structural entry zones. Auto-brief entries should be skipped or half-sized on expiry days.
**Rule:** BTC OI > 100k BTC on expiry day → skip auto-brief entries OR wait until post-expiry (>08:00 UTC Friday) before any entry.
**Backtest spec:** Identify all major BTC options expiry dates (last Friday of month). Compare win rate / avg R on expiry days vs non-expiry. Deribit OI data needed.
**Sim result (2026-09-28):** Paper game: expiry day N=3 completed → WR=0.0% AvgR=−0.75R. Non-expiry completed=28 WR=64.3% AvgR=+0.22R. (N=1 expiry day only in brief dataset)

**Range-expansion backtest (2026-09-28, BTC M15 2023-03 → 2026-09-25, N=43 expiry days):**
| Group | N | Median range/ATR | Mean range/ATR |
|---|---|---|---|
| Expiry Fridays | 43 | **1.021** | 1.062 |
| Pre-expiry Thursday | 43 | 0.922 | 1.018 |
| All other days | 1195 | 0.909 | 1.006 |
Mann-Whitney p=0.0479 (expiry > normal, borderline significant).
Year trend: 2023 median=0.835 → 2024=1.041 → 2025=1.020 → **2026=1.254** — effect growing with OI.

**Interpretation:** Expiry days run ~12% wider range than normal (median). Effect is modest overall but strengthening — 2026 expiry days 38% wider than normal median. P90 not elevated (1.593 vs 1.678 normal) — stops still get hit, but not extreme tail events.

**Status:** PROVISIONAL — range comparison p=0.048 does not establish OI threshold, stop-widening rule, or trading action. N=1 paper game expiry day; last-Friday calendar grouping is not measured OI exposure. No trading adjustment warranted until independently validated with appropriate controls. (Downgraded from CONFIRMED 2026-09-26 per Codex review.)
**Data needed:** OI data per expiry to split large vs small OI (hypothesis: OI ≥ 150k = stronger effect)

---

## NEUTRAL_BIAS_SKIP
**Observed:** Sep 7–25 2026. 4 of 30 completed trades had NEUTRAL daily_bias. All 4 were losses (included in with-bias group). Generator emitting NEUTRAL on ~13% of briefs.
**Hypothesis:** NEUTRAL bias = no structural conviction. Entries on NEUTRAL days underperform both WITH-bias and ANTI-BIAS setups. Skip NEUTRAL days entirely.
**Rule:** `daily_bias=NEUTRAL` → no entry on either side.
**Backtest spec:** Isolate NEUTRAL-bias trades in full sim. Compare WR/avg-R vs WITH-bias. Needs more NEUTRAL samples — only 4 in current dataset.
**Status:** QUEUE — small sample. Monitor going forward.
**Data needed:** Current `_levels.json` dataset; accumulate more NEUTRAL instances

---

## HOW TO ADD A NEW PATTERN

When observing a pattern during session review, add a new `##` block with:
- **Observed:** when / what you saw
- **Hypothesis:** the testable claim in plain English
- **Rule:** the mechanical entry rule (must be backtestable)
- **Backtest spec:** what data is needed and how to test
- **Status:** QUEUE
- **Data needed:** specific files / APIs

Keep one idea per block. Do not merge patterns. Set Status=TESTING when a sim script is written, CONFIRMED/REJECTED when 30+ trades validate or kill it.

---

## OPTIONS_PREMIUM_EFFICIENCY_V1
**Observed:** User-supplied options education transcript, not an observed V2 trading pattern. Checked 2026-09-27 against OIC Greek definitions.
**Hypothesis:** Given identical frozen bullish signals, expiry and holding policy, near-40-delta calls may have different after-cost return/loss distributions from near-50/60/80-delta calls when premium budget is equal. No universal optimum or positive edge established.
**Rule:** Research only. Compare equal premium as primary and equal initial delta as secondary; keep whole-contract constraints, idle cash, spreads, fees, IV changes, time decay and losses visible. No live signal or sizing adjustment.
**Backtest spec:** [Corrected explanation, data contract and Claude debate](../codex_notes/2026-09-27_options-gamma-premium-efficiency.md). Options delta is not order-flow volume delta; its gamma cannot be derived from the existing M15 files.
**Status:** QUEUE / DATA BLOCKED. No options-chain test run. A fixed trade count alone cannot validate this hypothesis; require a frozen protocol, appropriate uncertainty analysis and unseen data.
**Data needed:** Point-in-time option bid/ask chains, strike/expiry, underlying reference, Greek conventions, contract/settlement units, fees and verified source timestamps. Product selection and a separate experiment approval are still required.

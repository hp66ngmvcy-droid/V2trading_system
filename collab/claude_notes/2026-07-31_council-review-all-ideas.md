# Council Review — All Open Ideas
Date: 2026-07-31
Author: Claude (council-style multi-angle review)
Status: PENDING Codex action

Council format: Strategy → Evidence → Devil's Advocate → Verdict → Action

---

## 1. VWMR_v1 — Volatility-Weighted Mean Reversion

**Idea:** ATR spike → mean reversion trade, position sized proportional to spike magnitude.
**Note:** `collab/claude_notes/2026-06-18_VWMR_v1-volatility-weighted-mean-reversion.md`
**Implemented:** ✅ `src/tar_system/strategies/vwmr_v1.py`

**Evidence FOR:**
- Metrics file shows PF=1.61 in-sample — above 1.40 target
- Mean reversion is academically grounded in high-volatility regimes
- ATR features already in pipeline, no new dependencies needed
- Gold's current regime ($4,200–$4,400 range) favours reversion

**Devil's Advocate:**
- Only 14 trades in full backtest — catastrophically low. Cannot gate.
- 2-month new data window (May–July 2026): ATR spikes may be trend continuation, not reversion
- WF not run (insufficient trades). Without WF, evidence is anecdotal.
- Volatility-weighted sizing adds execution complexity with no proven payoff yet

**Verdict: PARK — insufficient trade count**
Action: Do not retune yet. Monitor as monthly data grows. Retest when trades ≥ 30. Move to `ideas/staging/`.

---

## 2. LSMR_v1 — London Session Mean Reversion

**Idea:** Fade London open ATR spikes (07:00–09:00 UTC) back to EMA.
**Note:** `collab/claude_notes/2026-06-18_LSMR_v1-london-session-mean-reversion.md`
**Implemented:** ✅ `src/tar_system/strategies/lsmr_v1.py`

**Evidence FOR:**
- London open is highest liquidity window — volatility spikes are real
- 54 trades — passes minimum gate
- Mean reversion intuition: institutionals fade retail breakout chasers

**Devil's Advocate:**
- PF=0.72 on full dataset (today's WF sweep). Below 1.0 = system loses money
- Gold in 2025–2026 has been strongly trending upward (+$1,200 in 18 months)
  → Trending markets punish mean reversion entries systematically
- RSI extreme filter (>70/<30) in trending markets means most signals fire INTO the trend
- 07:00–09:00 UTC is also the highest news-risk window — London open frequently gap-extends on macro

**Verdict: KILL — below PF 1.0 on sufficient trade count**
Action: Archive to `ideas/rejected/`. Update strategy memory. Do not retune — root cause is regime mismatch, not parameters.

---

## 3. BAF_v1 — Breakout and Fade

**Idea:** Fade false breakouts above/below 4H rolling high/low.
**Note:** `collab/claude_notes/2026-06-18_BAF_v1-breakout-and-fade.md`
**Implemented:** ✅ `src/tar_system/strategies/baf_v1.py`

**Evidence FOR:**
- 832 trades — large sample, high statistical weight
- False breakouts are real: stop-hunt above resistance is institutional behaviour
- Broad session window (07:00–19:00 UTC) captures multiple liquidity events

**Devil's Advocate:**
- PF=0.90 on 832 trades = system loses money reliably, with high confidence
- 832 trades over ~2 years = ~1.5 trades/day = hyperactive. Over-trading = spread cost destruction
- Gold's post-2024 structure is persistent breakouts, NOT failures. $3,000→$4,300 is all breakout extensions
- RSI 40–60 filter enters into neither overbought nor oversold = timing midrange = worst fade entry quality
- "Close back below" confirmation is 1-bar lag = entering after initial momentum already reversed = late

**Verdict: KILL — confirmed losing system on large sample**
Action: Archive to `ideas/rejected/`. Do not retune. High trade count means noise already averaged out — the edge is not there in current regime.

---

## 4. Cross-Asset Correlation — VIX/Gold/NQ

**Idea:** Long Gold when VIX spikes + NQ sells off (flight-to-safety correlation signal).
**Status in inbox:** `ideas/inbox/idea-20260610-cross-asset-correlation-vix-gold-nq.md`
**Prior backtest:** 12 trades max, PF=0.70 costed. Confirmed 2022 inflation failure.

**Evidence FOR:**
- Academic backing: Baur & Lucey (2010), Connolly et al. (2005) — gold as safe haven confirmed
- Macro logic is sound: VIX > 25 + NQ decline → institutional gold buying is real
- NQ + VIX + DXY data all available locally

**Devil's Advocate:**
- Not enough trades (12 max with loose params) — cannot validate
- Known failure modes: 2020 COVID liquidity crisis, 2022 real rate spike — both in-sample
- Strategy requires NQ futures and VIX to be wired into feature pipeline (not done)
- Downturn-only strategy = fires 3-4 times per year = need 10+ years data for significance
- 30-trade gate impossible to meet on XAUUSD M15 without at least 5-7 major market crises

**Verdict: BACK TO RESEARCH — data requirements not met**
Action: Keep in inbox. Needs: (1) macro regime gate for 2022, (2) NQ feature pipeline wiring, (3) 10+ year XAUUSD dataset. Create data requirement ticket. Not agent-runnable now.

---

## 5. Gold Seasonality — Month/Day-of-Week Filter

**Idea:** Add month-of-year and day-of-week as regime suppression filter for existing strategies.
**Status in inbox:** `ideas/inbox/idea-20260704-gold-seasonality-patterns-xauusd.md`

**Evidence FOR:**
- Baur (2013): September effect statistically significant, t-stat robust, 1980–2010
- Physical demand explanation (Indian wedding season, CNY) is externally observable
- Feature addition only — no strategy logic change, low implementation risk
- Can be applied as suppression layer to any strategy without rebuild

**Devil's Advocate:**
- Month/day-of-week is a weak signal at M15 timeframe — within-day randomness dominates
- Gold's September effect is measured on DAILY returns, not M15. May not transfer
- Backtesting calendar effects is a curve-fitting risk — 12 months × 5 days = 60 cells = high overfitting surface
- Must be used as FILTER only, never as entry signal

**Verdict: APPROVE as feature — implement cautiously**
Action: Add `month_of_year` and `day_of_week` columns to feature builder (Codex Item 4 already queued). Apply as informational feature only. Do not hard-gate any strategy on these without separate pre-registered test.

---

## 6. H4/D1 Trend Filter for arsb_v1 (PER-28)

**Idea:** D1 EMA alignment gate — only allow breakout direction aligned with D1 trend.
**Status:** RESEARCH COMPLETE, UNBLOCKED (PER-22 done)
**File:** `ideas/inbox/idea-20260704-h4-d1-trend-filter-arsb-m15.md`

**Evidence FOR:**
- D1 data shows Gold trends 75% of time (ADX > 25 = 66.4% of sessions, median ADX = 31.8)
- Counter-trend breakouts are the confirmed failure mode for arsb_v1 (WF PF=0.35)
- D1 EMA filter suppresses ~25% choppy sessions + flips ~22% direction = 47% signal change
- If arsb_v1's true failure is counter-trend entries, this fix is targeted and minimal

**Devil's Advocate:**
- arsb_v1's WF failure may be the 2-month data window, not counter-trend entries
- D1 trend alignment doesn't fix: insufficient compression zone quality, stop placement, R:R
- Adding D1 data dependency increases maintenance surface
- If D1 is trending up strongly, ALL breakouts get filtered to BUY — increases correlated position risk

**Verdict: APPROVE for implementation — highest-value unblocked ticket**
Action: Codex Item 2 (already in CODEX_HANDOFF). Run WF after implementation. Gate: if WF PF doesn't improve above 0.5 with filter, KILL arsb_v1 entirely.

---

## 7. ARSB Plateau Sweep (Pre-Registered)

**Idea:** Sweep compression_atr_mult × buffer_mult to determine flat vs peaked objective function.
**Status:** PRE-REGISTERED, UNBLOCKED
**File:** `ideas/inbox/idea-20260706-arsb-v1-plateau-sweep-pre-registration.md`

**Evidence FOR:**
- param_stability=0.0 across all WF splits — must determine if flat or peaked before any retuning
- Pre-registration is good science — hypothesis locked before data seen
- Low implementation risk — pure backtest sweep, no strategy code change

**Devil's Advocate:**
- If D1 filter (Item 6) changes the signal surface significantly, this sweep result is stale
- Run AFTER D1 filter implementation to avoid sweeping the wrong strategy variant
- 2-month data window means sweep results have same CI limitation as WF

**Verdict: APPROVE — but run AFTER D1 filter, not before**
Action: Reorder — D1 filter first (PER-28), then plateau sweep on the filtered version. Update CODEX_HANDOFF to reflect this dependency.

---

## Summary Verdicts

| Idea | Verdict | Action |
|------|---------|--------|
| VWMR_v1 | PARK | Move to staging, retest at 30+ trades |
| LSMR_v1 | KILL | Archive to rejected, write memory note |
| BAF_v1 | KILL | Archive to rejected, write memory note |
| VIX/Gold/NQ | BACK TO RESEARCH | Keep in inbox, create data req ticket |
| Seasonality | APPROVE | Codex Item 4 (feature columns only) |
| D1 Trend Filter | APPROVE | Codex Item 2 — highest priority |
| Plateau Sweep | APPROVE (after D1) | Codex Item 3 — run after PER-28 done |

---

## Updated Codex Work Order (revised from CODEX_HANDOFF)

1. Park arsb_v1 (SYS-COMP-01)
2. Implement D1 EMA filter on arsb_v1 (PER-28)
3. Add seasonality features (month/dow)
4. Run plateau sweep ON THE FILTERED arsb_v1 (not base)
5. Archive LSMR_v1 + BAF_v1 to rejected, write memory notes
6. Move VWMR_v1 to staging
7. Mark skills (agent-research-scout, cortex-learning-loop) as REVIEWED

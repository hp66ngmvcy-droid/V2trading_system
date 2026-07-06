---
idea_id: idea-20260704-gold-seasonality-patterns-xauusd
title: Gold Seasonality Patterns — Month and Day-of-Week Effects on XAUUSD
status: hypothesis_extracted
source_url: manual
source_label: Research task PER-27 — 2026-07-04
category: strategy_idea
tags: ["gold", "XAUUSD", "seasonality", "calendar-effect", "day-of-week", "monthly", "regime-filter"]
created_from: manual_entry
created_at: 2026-07-04T01:40:00+00:00
---

# Gold Seasonality Patterns — XAUUSD Month and Day-of-Week Effects

## Hypothesis

XAUUSD exhibits statistically persistent seasonal patterns at monthly and intraweek granularity that can be used as a **regime / suppression filter** — not a standalone signal — for existing gold strategies (e.g. the cross-asset correlation model in `idea-20260610-cross-asset-correlation-vix-gold-nq.md`).

## Academic and Practitioner Backing

- **Baur (2013)** *Journal of Banking & Finance*, "The autumn effect of gold" — Documents statistically significant positive returns in September and November for gold across 1980–2010. Effect strongest in September; robust across sub-samples.
- **Naylor, Wongchoti & Gianotti (2011)** — Confirm month-of-year effects across precious metals; identify seasonal Sharpe uplift for gold in Sep/Nov.
- **Qi & Wang (2013)** — Extend seasonality to intraweek returns; find weak but present day-of-week effects consistent with liquidity and event-clustering explanations.
- **World Gold Council** demand trend reports — Attribute autumn strength to Indian festival + wedding season (Sep–Nov), Chinese New Year run-up (Dec–Jan), and Diwali (Oct/Nov). Physical demand explanation is externally observable.
- **Lucey & Tully (2006)** — Note January effect is present but weaker in gold than in equities.

## Empirical Patterns Reported In Literature

### Monthly (average returns, 1980–2020 approximate figures across studies)

| Month | Directional bias | Notes |
|-------|-----------------|-------|
| Jan | Mildly positive | Weak "January effect", Chinese New Year physical demand |
| Feb | Mixed | Post-CNY unwind |
| Mar | Neutral to negative | Weakest quarter historically |
| Apr | Mildly positive | Akshaya Tritiya (Indian gold-buying festival) |
| May | Negative | "Sell in May" bleeds into gold via risk-on rotation in some regimes |
| Jun | Neutral | |
| Jul | Neutral to mild positive | |
| **Aug** | **Positive** | Start of autumn effect |
| **Sep** | **Strongest positive** | Baur (2013) headline finding |
| Oct | Neutral to positive | Diwali physical demand |
| **Nov** | **Positive** | Indian wedding season peak |
| Dec | Mildly positive | Year-end positioning; thin liquidity risk |

Baur's headline: September mean daily return roughly 2x the all-month average, with statistically significant t-stat.

### Day-of-Week (reported effects, weaker than monthly)

| Day | Reported bias | Confidence |
|-----|---------------|------------|
| Mon | Mildly negative | Weekend gap unwind |
| Tue | Neutral | |
| Wed | Neutral to mild positive | |
| Thu | Mildly positive | Pre-close positioning |
| Fri | Mixed / regime-dependent | Position squaring; risk-off flight can dominate |

Day-of-week effects have lower persistence than monthly and are more sensitive to macro regime.

## Proposed Use Inside The System

Not as a standalone entry signal. Instead:

1. **Regime tilt** — Increase position size on gold long signals during Aug–Nov by a fixed multiplier (e.g. 1.15x), decrease during Mar–May (e.g. 0.85x). Cap tilts to avoid overfitting.
2. **Suppression filter** — Block new gold longs in weakest-historical months if signal is marginal (borderline correlation trigger).
3. **Correlation-model synergy** — The Aug–Nov autumn effect coincides with typical VIX seasonal uplift (Sep–Oct historical VIX peak). Correlation-model + seasonality may compound rather than duplicate.

## Rules (For OOS Testing Only)

- **Base period:** 2000–2019 (in-sample); 2020–2025 (OOS).
- **Effect size measurement:** Mean daily return by month and by day-of-week, with 95% bootstrap CI (5,000 iterations).
- **Multiple-testing correction:** Bonferroni across 12 months (α = 0.05/12 ≈ 0.004) or Benjamini–Hochberg FDR.
- **Persistence check:** Split-sample stability — does Sep effect hold in 2000–2009 AND 2010–2019 AND 2020–2025?
- **Regime interaction:** Test if seasonality is conditional on DXY regime (rising USD may suppress autumn effect).

## Known Failure Modes And Cautions

- **Curve-fitting risk** — With 12 months there is a real chance one month prints significant purely by chance. Only Sep/Nov survive Bonferroni in Baur (2013).
- **Regime shift** — Post-2013 ETF proliferation, Chinese onshore market changes, and CBDC / central-bank buying trends have changed physical vs paper flow dynamics. Pre-2013 effects may weaken.
- **Data-dependency** — Effect measured on close-to-close daily returns. Applying to M15 ARSB or intraday systems requires re-testing at the target timeframe; do NOT assume daily effect maps to intraday.
- **Overlap with macro** — Sep also captures typical fiscal-year-end positioning and back-to-school risk-off; the effect may be co-moving with equity seasonality rather than gold-specific.

## Data Requirements

| Asset | Timeframe | Source | Status |
|-------|-----------|--------|--------|
| XAUUSD | D1 | Existing `data/validated/GOLD_D1.parquet` | Verify coverage 2000–2025 |
| DXY | D1 | Existing `data/validated/DXY_D1.parquet` | Have |
| VIX | D1 | Existing `data/validated/VIX_D1.parquet` | Have (for regime overlay) |

No new data required. Analysis is entirely on existing validated feeds.

## Proposed Next Steps

1. Extract month-of-year mean-return table with 95% CI on `GOLD_D1.parquet`.
2. Run split-sample stability check (2000–2009 vs 2010–2019 vs 2020–2025).
3. Bonferroni-corrected significance test — flag which months survive.
4. Overlay with DXY regime and VIX regime to test conditional strength.
5. If Sep/Nov effect survives OOS, propose a size-tilt rule with strictly capped uplift (max 1.15x), add to correlation-model spec as an optional filter.

## Explicit Limitations

- Paper-mode only. No sizing changes to any live or paper strategy until OOS validation completes.
- No standalone signal — this is a **filter/tilt**, not a strategy on its own.
- Historical seasonality is not a causal guarantee; it is a persistence-based decision aid.

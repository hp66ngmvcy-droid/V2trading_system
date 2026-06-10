---
idea_id: idea-20260610-cross-asset-correlation-vix-gold-nq
title: Cross-Asset Correlation Model — VIX/Gold/NQ Downturn Alpha
status: hypothesis_extracted
source_url: manual
source_label: User idea — 2026-06-10
category: strategy_idea
tags: ["cross-asset", "correlation", "gold", "vix", "NQ", "statistical", "regime", "safe-haven"]
created_from: manual_entry
created_at: 2026-06-10T22:00:00+00:00
---

# Cross-Asset Correlation Model — VIX/Gold/NQ Downturn Alpha

## Hypothesis

Statistical correlation between VIX, Gold (XAUUSD), and NQ (Nasdaq futures) provides
a non-price-action signal for capturing alpha during market downturns.

When VIX spikes and NQ sells off, Gold historically diverges positively (flight-to-safety).
The correlation breakdown between NQ and Gold during high-VIX regimes is the tradeable signal.

**Academic backing:**
- Baur & Lucey (2010) *Financial Review* — Gold is safe haven specifically during extreme equity shocks. Effect lasts ~15 trading days max.
- Baur & McDermott (2010) *Journal of Banking & Finance* — Confirmed for US/European equities.
- Connolly, Stivers & Sun (2005) *Journal of Finance* — VIX predicts negative equity correlation; valid as regime switch.

## Rules

- **Entry:** Rolling 20-day correlation (Gold vs NQ) crosses below -0.3 AND VIX > 25 (strong signal: VIX > 30)
- **Exit:** Correlation reverts above -0.1 OR VIX drops below 20 OR max hold = 15 bars (Baur & Lucey persistence cap)
- **Filters:**
  - DXY rising (USD strengthening) → suppress entry (Gold is USD-denominated; dollar strength overrides safe-haven)
  - Inflation regime gate — if 10Y real yield rising sharply, suppress entry (2022 failure mode)
  - No price action, no ICT, no ORB — pure statistical signal only
- **Direction:** Long Gold on downturn signal (Gold-only first; NQ short added in Phase 3 multi-asset)
- **Risk:** ATR-based SL, no pyramiding, max 1 position

## Statistical Approach

- Rolling 20-day AND 60-day correlation: Gold vs NQ (dual-window confirmation)
- VIX absolute level (>25 base, >30 strong) — NOT z-score (absolute level is empirically tested)
- DXY 10-day slope as suppression filter
- No curve-fitting on correlation window — validate OOS only

## Known Failure Modes

- **2022 inflation shock:** VIX elevated + Gold sold off simultaneously (real rate spike overwhelmed flight-to-safety). Hard to avoid without macro regime gate.
- **March 2020 COVID crash:** Gold initially sold off with NQ for ~2 weeks (liquidity crisis, margin calls). Safe haven re-established after. Max hold cap partially mitigates.
- **Dollar-strength episodes (2015, 2018):** DXY rising suppresses Gold even with VIX spike. DXY filter is critical.

## Data Requirements

| Asset | Source | Status |
|-------|--------|--------|
| XAUUSD | Already in system | ✅ Have |
| NQ continuous futures | yfinance `NQ=F` (front-month) or Norgate for roll-adjusted | ❌ Need |
| VIX index | yfinance `^VIX` or FRED `VIXCLS` | ❌ Need |
| DXY | yfinance `DX-Y.NYB` or FRED `DTWEXBGS` | ❌ Need |

## Success Criteria

- Stage 1 costed PF > 1.2
- Sharpe > 1.5 OOS
- Trades >= 30 (min gate — downturn strategy will be low frequency, must verify)
- Walk-forward KEEP verdict
- Must survive 2022 OOS period (inflation regime test)

## Next Steps

1. Check data availability: `./bt check-data-readiness` for NQ, VIX, DXY
2. Write data requirements note to `ideas/data_requirements/`
3. Build strategy module: `src/tar_system/strategies/cross_asset_correlation_v1.py`
4. Backtest on daily bars first (sufficient frequency for regime-based signal)

## Notes

- Low trade frequency expected — do not promote on <30 trades
- Phase 2 single-asset (Gold long only) before Phase 3 multi-asset (Gold long + NQ short)
- 2022 is the critical OOS stress test — if it fails there, rethink inflation gate

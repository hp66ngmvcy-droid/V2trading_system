# TAR Indicator Tier Codex

Version: 1.0  
Date: May 2026  
Purpose: Strategic ranking system for indicator selection, validation, and iteration.  
Scope: TAR Phase 1-3 strategy validation across all assets and timeframes.

## Executive Summary

Trading indicators are not equal. Many repackage price in different forms, while volume-based tools reveal conviction and institutional activity.

Core principle:

- F-Tier: Lagging, noisy, unreliable. Kill strategies using these as primary signals.
- D-Tier: Weak, false-signal heavy. Revise rather than keep.
- C-Tier: Specific use only. RSI is acceptable mainly for divergence with confirmation.
- B-Tier: Context-dependent. Useful with confluence and validation.
- A-Tier: Strong, institutionally watched and mechanically useful.
- S-Tier: Gold standard. Volume and volume-derived indicators show conviction.

## Tier Breakdown

### F-Tier: Kill

#### MACD

Why:

- Lagging indicator of lagging indicators.
- Signals often arrive after price has already moved.
- Whipsaws in choppy markets.

TAR rule:

- MACD as primary entry: KILL.
- MACD as secondary confirmation: REVISE.
- MACD for exit timing only: CONDITIONAL. Walk-forward must pass.

Replace with:

- SMA 50/200.
- VWAP.
- OBV.

Reason code:

- `F_TIER_MACD`

### D-Tier: Revise

#### Stochastics

Why:

- Noisy.
- Pins at extremes during trends.
- Whipsaws in ranges.

TAR rule:

- Primary stochastic crossover: KILL.
- Confluence only: REVISE and require A/S-tier confirmation.
- Below H1: extra risk; walk-forward Sharpe must exceed 1.2.

Reason code:

- `D_TIER_STOCH`

### C-Tier: Specific Use Only

#### RSI

Why:

- Momentum oscillator can remain overbought or oversold for weeks.
- RSI > 70 is not automatically bearish.
- RSI < 30 is not automatically bullish.

Valid use:

- Divergence only, with price action and/or volume confirmation.

TAR rule:

- RSI threshold entry only: KILL.
- RSI centerline cross entry: KILL.
- RSI divergence plus confirmation: CONDITIONAL KEEP.
- RSI divergence plus volume confirmation: FAVORABLE.

Reason codes:

- `C_TIER_RSI_ONLY`
- `DIVERGENCE_CONFIRMED`

### B-Tier: Context-Dependent

#### Bollinger Bands

Why:

- Measures volatility, not direction.
- Useful for compression, breakout zones, and mean reversion.
- Needs directional or volume confirmation.

TAR rule:

- Outer band touch only: REVISE.
- Band signal plus trend/volume/support confirmation: CONDITIONAL KEEP.
- BB width plus directional signal plus volume: FAVORABLE KEEP.

Reason code:

- `B_TIER_NO_CONF`

#### Fibonacci Retracement

Why:

- Consensus-based support/resistance.
- Useful as confluence, not a standalone signal.

TAR rule:

- Fib touch only: REVISE.
- Fib plus volume/price action: CONDITIONAL KEEP.
- Fib plus OBV divergence plus trend: FAVORABLE KEEP.

### A-Tier: Strong

#### SMA 50/200

Why:

- Institutionally watched.
- Useful trend allocation and macro trend filter.
- Works best with volume confirmation.

TAR rule:

- Price above 50/200 SMA plus volume: FAVORABLE KEEP.
- SMA cross plus OBV confirmation plus sizing: STRONG KEEP.
- SMA only without volume: REVISE.

#### Donchian Channel

Why:

- Mechanical highest high / lowest low breakout logic.
- Objective and easy to validate.
- Requires volume confirmation to avoid false breakouts.

TAR rule:

- Donchian breakout plus volume increase: FAVORABLE KEEP.
- Donchian breakout plus OBV plus trend filter: STRONG KEEP.
- Donchian alone: REVISE.

Reason code:

- `MECH_BREAKOUT_RVOL`

### S-Tier: Gold Standard

#### Volume Suite

Includes:

- Raw volume.
- OBV.
- VWAP.
- Accumulation/Distribution Line.
- Chaikin Money Flow.
- Money Flow Index.
- Relative Volume.
- Volume profile.

Why:

- Volume is not derived from price.
- It shows conviction and participation.
- Institutional size leaves footprints.

Core idea:

Price tells where it went. Volume tells whether the move had conviction.

## S-Tier Validation Rules

### OBV

Valid uses:

- Price breaks resistance plus OBV spike and OBV above prior highs: FAVORABLE KEEP.
- OBV divergence plus support/retest: FAVORABLE KEEP.
- OBV divergence alone: REVISE.
- OBV threshold alone: KILL.

Reason code:

- `VOL_CONF_OBV_VWAP`

### VWAP

Valid uses:

- Price breaks and closes above VWAP: FAVORABLE KEEP.
- Price above rising VWAP plus OBV rising: STRONG KEEP.
- VWAP touch in range: CONDITIONAL, requires trend filter.
- Long setup below VWAP without other confirmation: KILL.

### Accumulation/Distribution Line

Valid uses:

- Price breakout plus A/D new highs: FAVORABLE KEEP.
- A/D divergence plus support test: FAVORABLE KEEP.
- A/D threshold alone: KILL.

### VWAP Bands

Valid uses:

- Price above VWAP plus 1 SD in trend: FAVORABLE KEEP.
- Reversion from outer band back toward VWAP: FAVORABLE with confirmation.
- Touching outer band only: REVISE.

### CMF

Valid uses:

- CMF above zero and rising: FAVORABLE.
- CMF divergence plus price confirmation: FAVORABLE KEEP.
- CMF threshold alone: REVISE.

### RVOL

Valid uses:

- Breakout on RVOL > 1.5: FAVORABLE KEEP.
- Donchian break plus RVOL 1.5-2.0: STRONG KEEP.
- Breakout on RVOL < 1.5: REVISE or KILL.

Reason code:

- `VOLUME_CONVICT_LOW`

## Institutional Footprints

### Accumulation

Signature:

- Tight consolidation.
- Declining volume during range.
- Occasional spikes on up days.
- OBV rising while price stays quiet.

TAR setup:

- Tight 10-20 day range.
- Volume declining.
- OBV rising.
- Breakout on high volume.
- Verdict: FAVORABLE KEEP.

### Distribution

Signature:

- Price stuck near resistance.
- High volume on down days.
- Low volume on up days.
- A/D or CMF falling.

TAR setup:

- Resistance rejection.
- A/D or CMF divergence.
- OBV rolling over.
- Verdict: FAVORABLE SHORT SETUP.

### Weakening Trend

Signature:

- Price makes new highs.
- Volume declines.
- OBV fails to confirm.

TAR action:

- Exit long setup or mark long strategy for review.

### Shakeout Recovery

Signature:

- Support break on high volume.
- Sharp reversal and close back above support.
- Reversal volume exceeds breakdown volume.
- OBV spikes positive.

TAR action:

- STRONG LONG ENTRY candidate, subject to backtest and walk-forward.

## Strategy Approval Checklist

Before approval:

1. Identify all indicators.
2. Assign tier to each indicator.
3. Count F/D-tier usage.
4. If F/D-tier primary usage exists: KILL or REVISE.
5. If B-tier only: require confluence and walk-forward.
6. If A-tier: require volume confirmation.
7. If S-tier confirmation exists: favorable for KEEP.
8. Walk-forward validate before KEEP.
9. Log reason codes.

## Decision Examples

RSI threshold crossover:

- RSI = C-tier.
- Threshold-only use is invalid.
- Verdict: KILL.
- Reason: `C_TIER_RSI_ONLY`.

EMA/SMA trend plus OBV and VWAP:

- Trend = A-tier.
- OBV/VWAP = S-tier.
- Verdict: FAVORABLE KEEP pending walk-forward.
- Reason: `VOL_CONF_OBV_VWAP`.

Donchian 20 breakout plus RVOL > 1.5:

- Donchian = A-tier.
- RVOL = S-tier.
- Verdict: FAVORABLE KEEP pending walk-forward.
- Reason: `MECH_BREAKOUT_RVOL`.

## Reason Codes

| Code | Meaning | Action |
| --- | --- | --- |
| `F_TIER_MACD` | Uses F-tier MACD as primary | KILL |
| `D_TIER_STOCH` | Stochastics whipsaw risk | REVISE |
| `C_TIER_RSI_ONLY` | RSI threshold without divergence | KILL |
| `B_TIER_NO_CONF` | B-tier signal without volume | REVISE |
| `VOL_CONF_OBV_VWAP` | A-tier trend plus S-tier volume | FAVORABLE KEEP |
| `MECH_BREAKOUT_RVOL` | Donchian break plus RVOL | FAVORABLE KEEP |
| `DIVERGENCE_CONFIRMED` | Divergence plus price/volume confirmation | CONDITIONAL KEEP |
| `VOLUME_CONVICT_LOW` | Breakout on weak RVOL | KILL or REVISE |

## Final Directive

From this point forward, TAR strategies should:

1. Use A-tier or S-tier indicators as primary signals.
2. Use S-tier volume confirmation where possible.
3. Assign reason codes to every verdict.
4. Kill F-tier primary signal strategies.
5. Revise D/C-tier strategies without proper confluence.
6. Walk-forward validate before KEEP.
7. Log institutional footprints in memory.

This document is a validation standard, not a live-trading instruction.


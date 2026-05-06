# TAR Opening Range + VWAP Order Flow Strategy Codex

Version: 2.0  
Date: May 2026  
Status: Research-verified, ready for TAR Phase 2 validation  
Application: TAR Phase 2+ strategy validation  
Primary markets: XAUUSD M15/H1, forex pairs, indices

## Executive Summary

This framework combines:

1. Opening range: objective session support/resistance from the first 15-30 minutes.
2. Stabilized VWAP plus order flow: institutional conviction after a 30-60 minute stabilization period.

The goal is to determine full-day trend bias and identify high-probability entry and exit zones. This is documentation and validation guidance only. It is not a live-trading instruction.

## Part 1: Opening Range Framework

The opening range is the highest high and lowest low established during the first 15-30 minutes of a trading session.

TAR defaults:

- London Open: 08:00-08:30 GMT.
- New York Open: 13:30-14:00 GMT.
- Alternative New York window: 13:00-13:30 GMT.

Why it matters:

- Institutions place large orders around session opens.
- Opening range high/low often becomes support or resistance for the full session.
- Breakout direction often sets the session bias.

## Opening Range Patterns

### Pattern 1: Breakout and Trend

- Price breaks above opening range high: bullish day bias.
- Price breaks below opening range low: bearish day bias.
- Move may sustain through London-New York overlap.

### Pattern 2: Retest and Continuation

- Price breaks opening range early.
- Price pulls back to the broken level.
- Broken high/low becomes support/resistance.
- Retest offers secondary entry candidate.

### Pattern 3: Range Bounce

- Price fails to break opening range in first hour.
- Price trades inside the range.
- Opening range high/low acts as support/resistance.
- Wait for later breakout with confirmation.

## Opening Range Setup

Definition:

- Session open: London 08:00 GMT or New York 13:30 GMT.
- Range period: first 15-30 minutes.
- Mark highest high and lowest low.
- Use 5-minute or 15-minute chart.
- Monitor levels through session close.

Mechanical setup:

- Pending buy: opening range high plus buffer.
- Pending sell: opening range low minus buffer.
- Long stop: opening range low minus buffer.
- Short stop: opening range high plus buffer.
- Target: 2:1 to 3:1 risk/reward.

Daily framework:

- Opening range high = institutional resistance.
- Opening range low = institutional support.
- Breakout direction = session bias.
- Retests of broken level = secondary entry candidates.

## Part 2: VWAP + Standard Deviations + Order Flow

### VWAP Stabilization Warning

VWAP is unreliable during the first 30-60 minutes because cumulative volume is still thin.

Rules:

- Minutes 0-30: observe only, no VWAP-based entries.
- Minutes 30-60: VWAP starts stabilizing.
- Minutes 60+: VWAP becomes a stronger institutional reference point.

Reason code:

- `PRE_STABILIZATION`

## VWAP Conviction Layers

### Layer 1: Buy VWAP vs Sell VWAP

Interpretation:

- Buy VWAP > Sell VWAP: net buying pressure.
- Sell VWAP > Buy VWAP: net selling pressure.
- Balanced: unclear direction, wait.

### Layer 2: VWAP Standard Deviation Bands

Zones:

- VWAP: fair value.
- +1 SD to +2 SD: bullish extension but not necessarily extreme.
- Above +2 SD: bullish overextension, watch for pullback.
- -1 SD to -2 SD: bearish extension but not necessarily extreme.
- Below -2 SD: bearish overextension, watch for pullback.

### Layer 3: Golden Bars

Definition:

- Volume profile levels where volume is 1.6x-1.8x+ session average.

Interpretation:

- High institutional activity.
- Micro support/resistance.
- Golden bar plus VWAP deviation alignment = high conviction area.

## Order Flow Footprints

### Stop Sweep + Aggressive Selling

Sequence:

1. Price breaks above session high.
2. Buy stops trigger.
3. Hidden/large seller absorbs.
4. Price reverses sharply.

TAR interpretation:

- Possible stop hunt and reversal.
- Requires confirmation before entry.

### Volume Spike at Deviation Bands

Sequence:

1. Price reaches +2 SD or -2 SD.
2. Volume spikes 2-3x average.
3. Candle closes with large body or rejection wick.
4. Direction depends on buyer/seller dominance.

### Buyer/Seller Volume Ratio

Interpretation after stabilization:

- Buyer volume much greater than seller volume: accumulation.
- Seller volume much greater than buyer volume: distribution.
- Balanced: wait.

## Part 3: Hybrid Strategy Phases

### Phase 1: Minutes 0-30

Actions:

1. Mark opening range high/low.
2. Observe VWAP and +/-2 SD behavior.
3. Watch for golden bars and volume spikes.
4. Record preliminary bias only.

Rule:

- Do not trade yet.

### Phase 2: Minutes 30-60

Actions:

1. Confirm opening range breakout.
2. Check price relative to VWAP.
3. Check buy/sell VWAP or volume imbalance.
4. Assign all-day bias.

Conviction scoring:

- 3 of 3 aligned: HIGH.
- 2 of 3 aligned: MEDIUM.
- 1 of 3 aligned: LOW, wait.

### Phase 3: Minutes 60+ Through Close

Actions:

- Use opening range high/low as all-day reference.
- Use VWAP as fair value.
- Use +/-1 SD as normal extension/mean reversion zones.
- Use +/-2 SD as extreme zones.
- Use early buyer/seller imbalance as session bias context.

## Part 4: Entry Rules

### Setup 1: Opening Range Breakout

Trigger:

- Price closes above opening range high or below opening range low.
- RVOL > 1.5.
- Candle body closes outside range, not wick only.

Entry:

- Enter at close of confirmation candle.
- Or use a limit near broken level.
- Conservative: wait for retest.

Stop:

- Beyond opposite opening range extreme.

Targets:

- Primary: 2R.
- Secondary: next institutional level.
- Trail after 1R.

Reason codes:

- `ORB_BREAK_ONLY`
- `NO_VOLUME_CONFIRM`
- `ORB_BOUNCE_RETEST`

### Setup 2: VWAP +/-2 SD Reversion

Condition:

- Price extends to +/-2 SD after stabilization.
- Golden bar volume at level.
- Buyer/seller imbalance confirms reversal pressure.

Entry:

- Aggressive: enter on volume spike.
- Conservative: wait for reversal candle.
- Safe: wait for retest of +/-1 SD.

Stop:

- Beyond +/-2 SD.

Targets:

- Primary: VWAP.
- Secondary: opposite +/-1 SD.

Reason code:

- `VWAP_2SD_GOLDEN_BAR`

### Setup 3: Opening Range + VWAP Confluence

Highest-probability setup:

- Opening range broken.
- Price/VWAP direction aligned.
- Buyer/seller volume confirms.
- Entry is near +/-1 SD, not at extreme.
- RVOL > 1.5.

Entry:

- First pullback to opening range edge.
- Or bounce from +/-1 SD in confirmed direction.

Stop:

- Beyond opposite opening range extreme.

Targets:

- Previous day high/low.
- Weekly pivots.
- Trail winners.

Reason codes:

- `ORB_VWAP_ALIGNED`
- `ORB_VWAP_BVOL_ALIGNED`
- `CONFLUENCE_ZONE`

## Part 5: Validation Checklist

Before approving an entry:

1. Opening range defined.
2. Minimum 30 minutes since session open.
3. Opening range direction is clear.
4. Volume supports breakout, ideally RVOL > 1.5.
5. VWAP direction aligns.
6. Buy/sell pressure confirms.
7. At least two factors aligned.
8. Trade occurs during liquid session.
9. Risk is sized at 1-2%.
10. Minimum reward/risk is 2:1.

## Part 6: Reason Codes

| Code | Meaning | Conviction |
| --- | --- | --- |
| `ORB_BREAK_ONLY` | Opening range breakout only | LOW |
| `VWAP_ALIGNED_ONLY` | VWAP direction only | LOW |
| `ORB_VWAP_ALIGNED` | Opening range plus VWAP align | MEDIUM |
| `ORB_VWAP_BVOL_ALIGNED` | ORB, VWAP and buy/sell volume align | HIGH |
| `ORB_BOUNCE_RETEST` | Pullback to broken ORB level on volume | MEDIUM-HIGH |
| `VWAP_2SD_GOLDEN_BAR` | +/-2 SD plus golden bar rejection/continuation | HIGH |
| `CONFLUENCE_ZONE` | ORB edge plus VWAP zone plus prior level | VERY HIGH |
| `FALSE_BREAKOUT` | ORB break failed and returned inside range | KILL |
| `NO_VOLUME_CONFIRM` | Breakout on RVOL < 1.5 | REVISE |
| `PRE_STABILIZATION` | Trade attempted before 30 minutes | KILL |

## JSONL Example

```json
{
  "strategy_name": "ORB_VWAP_OrderFlow",
  "setup_type": "confluence",
  "entry_signal": "ORB_BREAK_VWAP_ALIGNED",
  "open_range": {
    "high": 2345.5,
    "low": 2340.2,
    "breakout_direction": "bullish"
  },
  "vwap_status": {
    "price_vs_vwap": "above",
    "std_dev": "within_1SD",
    "buyer_seller_ratio": "bullish"
  },
  "entry_price": 2346.0,
  "stop_loss": 2339.5,
  "profit_target_1r": 2352.5,
  "conviction": "high",
  "reason_code": "ORB_VWAP_BVOL_ALIGNED",
  "note": "Opening range break plus VWAP bullish plus buyer volume dominant."
}
```

## Part 7: Walk-Forward Validation Gates

Phase 2 requirements:

- In-sample training: 12 months.
- Blind OOS windows: four rolling 3-month windows.
- Training/test structure: 12-month training then 3-month test.
- Parameter stability: ORB length and VWAP settings should not shift materially.

Pass thresholds:

- In-sample Sharpe >= 1.0.
- In-sample profit factor >= 1.5.
- Each OOS window Sharpe >= 0.9.
- Each OOS window profit factor >= 1.4.
- Stitched OOS Sharpe >= 1.0.

Verdict rules:

- OOS Sharpe >= 1.0 and stable parameters: KEEP candidate.
- OOS Sharpe below 0.9: REVISE or KILL.
- Parameter instability: REVISE.

## Memory Logging Example

```json
{
  "strategy": "ORB_VWAP_OrderFlow",
  "phase_2_result": "KEEP",
  "walk_forward_windows": 4,
  "avg_oos_sharpe": 1.24,
  "parameter_stability": "high",
  "best_window": "Window 2",
  "worst_window": "Window 4",
  "consistency": "Strong across all windows",
  "next_phase": "Phase 3 - multi-timeframe variants and secondary confirmation filters"
}
```

## Quick Reference

### First 30 Minutes

- Mark opening range.
- Observe VWAP and volume.
- Watch for golden bars.
- Do not trade.

### Minutes 30-60

- Confirm ORB direction.
- Confirm VWAP alignment.
- Confirm volume/RVOL and buyer/seller imbalance.
- Set session bias.

### After 60 Minutes

- Trade only validated setups.
- Use opening range edges and VWAP zones.
- Trail confirmed breakouts.
- Exit and reassess on conflicting signal.

## Next Steps For TAR

1. Implement opening range feature calculation.
2. Add VWAP +/-2 SD bands.
3. Add golden bar detection from volume profile or volume proxy.
4. Add ORB/VWAP confluence signal module.
5. Walk-forward test XAUUSD M15/H1.
6. Log all reason codes in audit and memory.

This document is a Phase 2 validation standard, not a live-trading instruction.


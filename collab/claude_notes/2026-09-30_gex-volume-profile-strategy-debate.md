# GEX + Volume Profile Order Flow Strategy — Debate

Date: 2026-09-30
Author: Claude
Refs:
- `claude_notes/2026-09-29_pd-array-rejection-v1-debate.md`
- `src/tar_system/strategies/key_level_sweep_v1.py`

Status: DEBATE — significant data dependency issues before build is possible

---

## Strategy Description (formalised)

**Instrument**: QQQ (equity ETF options) — not XAUUSD or BTCUSD

**Session**: New York open (09:30 ET)

**Step 1 — Volume Profile heat map (pre-market)**

Compute Low Volume Nodes (LVNs) across four timeframes:
- 3-month volume profile
- 1-month volume profile
- Weekly volume profile
- Daily volume profile

Mark levels where LVNs from 3+ timeframes stack within a narrow range.
These are "thin air" zones — price travels through them rapidly.
Example finding: 29.470–29.500 aligned with LVNs across 3 higher timeframes.

**Step 2 — GEX level identification**

Using live GEX data (Deep Gamma or equivalent):
- Identify the strike with highest magnitude GEX closure near the LVN stack
- Example: QQQ 710 strike at 29.462, sitting just below LVN zone at 29.470
- High GEX closure at a strike = strong magnetic/pinning force

**Step 3 — Delta positioning confirmation**

At the same strike:
- **Negative delta exposure**: MMs are net short delta → short futures to hedge
  → creates resistance at level
- **Positive vanna exposure**: as VIX falls, delta decreases → MMs BUY futures
  to neutralize → price pins to resistance from below
- **VIX flip trigger**: when VIX turns up → MM delta increases → MMs SELL
  futures to hedge → initiates rejection

**Step 4 — Order flow confirmation (entry gate)**

Three confirmations required before entry:

1. **Absorption**: aggressive buyer enters at level, immediately absorbed
   → shows supply overwhelming demand
2. **DOM stacking**: on Deep DOM, sellers actively stacking limit orders
   at bottom of key level (29.470) → proves sellers defending level
3. **Tape initiation**: tape shows sellers beginning to initiate
   (large prints on bid, uptick in sell-side aggression)

**Entry**: short after all three confirmations at or below key level
**Target**: ~50 points of movement (confirmed from described trade)
**Stop**: implied above the LVN zone / GEX strike

---

## Data Dependency Analysis

### Buildable in current V2 stack

| Component | Buildable? | Notes |
|-----------|-----------|-------|
| Volume Profile LVN detection | **YES** | M15 bars have volume; resample to compute profiles |
| Multi-timeframe LVN stack | **YES** | Run across weekly/daily/4H/1H windows |
| VIX direction (rising/falling) | **YES** | Already fetched in macro block |

### Blocked — new data sources required

| Component | Blocked by | Source needed |
|-----------|-----------|---------------|
| GEX levels | No options chain data | Options flow provider (SpotGamma, Squeez Metrics, Deep Gamma API) |
| Negative delta / vanna exposure | No options greeks | Same as above |
| DOM stacking | No Level 2 data | Broker L2 feed (Interactive Brokers, Tradovate, etc.) |
| Tape reading | No tick data | Tick feed or time & sales |

**The GEX and order flow components are the alpha.** The volume profile alone is
a location filter — it tells you WHERE to look, not WHETHER to trade.

Without GEX data and DOM/tape, building a backtest would test only the
volume profile component and would significantly overstate the strategy's
real-world precision.

---

## Debate Questions

### Q1 — Is this strategy portable to XAUUSD / BTCUSD?

**Partially.** The volume profile LVN component is portable to any liquid
market with volume data. XAUUSD and BTCUSD both have volume in the M15
parquet files.

The GEX component is NOT portable to spot XAUUSD (OTC, no standardised
options chain). It IS partially portable to BTC — Deribit publishes GEX-equivalent
data (we already fetch ATM IV from Deribit). A simplified BTC GEX proxy is
feasible.

The DOM/tape component requires a real-time data feed for any instrument.
Not buildable from historical M15 bars.

**Recommended scope for V2**: Volume Profile LVN detector only. Flag GEX and
order flow as live-only components that the human operator confirms before entry.
The brief can output LVN levels as reference zones; confirmation is manual.

### Q2 — Is a backtest meaningful without GEX + order flow?

**No, not as a complete strategy test.**

Volume profile LVN detection backtested in isolation will produce a statistical
result, but it will not represent the strategy as described. The GEX pinning
mechanism and order flow confirmation are the filters that select high-probability
setups from all LVN touches.

A backtest of LVN touches alone would:
- Over-count signals (many LVN touches without GEX or order flow confirmation)
- Understate the win rate (GEX + order flow would filter out low-quality setups)
- Not be honest evidence for the described strategy

**What IS meaningful**: build LVN detection as a brief feature (adds context to
daily output), not as a standalone backtest strategy. Treat GEX and order flow
as live operator gates, not automated signals.

### Q3 — QQQ vs XAUUSD/BTCUSD

This was described specifically for QQQ (equity ETF). V2 is XAU + BTC focused.

If the user wants to extend V2 to QQQ/US equities, that requires:
- QQQ M15 data (Twelve Data can provide this)
- Options chain data for GEX computation
- Separate session window (US equity market hours, not 24h)

This is a material scope expansion. Recommend: add QQQ volume profile LVN
to the daily brief as a bonus context block (Twelve Data already has QQQ),
but do not build QQQ into the TAR strategy pipeline yet.

### Q4 — What can be built now?

**Immediate (no new data sources)**:
- `_volume_profile_lvn(bars, window_bars)` — pure function, finds LVNs
  in a volume histogram
- `_multi_tf_lvn_stack(bars, levels)` — finds price levels that appear as
  LVNs across 3+ timeframes
- Add LVN stack output to `generate_daily_brief.py` symbol block

**Deferred (requires data sourcing decision)**:
- GEX data integration (SpotGamma/Deep Gamma API — cost + security review needed)
- BTC GEX proxy from Deribit (lower priority — simpler but limited)
- QQQ data extension (Twelve Data already has it — low-cost addition)

---

## Build Plan (bounded — volume profile only)

### New functions in `scripts/generate_daily_brief.py`

```python
def _volume_profile(bars, n_bars=None, bins=100):
    """Build volume histogram over last n_bars. Returns {price_level: volume}."""

def _low_volume_nodes(profile, threshold_pct=0.20):
    """Find bins with volume < threshold_pct of mean. Returns list of price levels."""

def _lvn_stack(bars, today_str, timeframes):
    """
    timeframes: dict of {label: n_bars_back}
    e.g. {"daily": 96, "weekly": 480, "monthly": 1920, "quarterly": 5760}
    Returns levels that appear as LVNs in 3+ timeframes, sorted by confluence count.
    """
```

Add to `build_symbol_block` output: `lvn_stack` — list of stacked LVN levels
with confluence count and timeframe labels.

Add to session MD output:

```
**LVN Stack (low volume confluence)**
| Level | Confluence | Timeframes |
| 4185 | 3/4 | daily, weekly, monthly |
```

### Tests

- `_volume_profile`: returns dict, sums to total volume
- `_low_volume_nodes`: threshold works, returns price list
- `_lvn_stack`: single-TF LVN not returned (< 3 confluence), 3+ TF LVN returned

---

## Position

GEX + order flow strategy: valid alpha, not yet buildable in V2 without new
data sources. Document for human operator use, not automated backtesting.

Volume profile LVN detection: buildable now, adds value to daily brief as
context for level selection. Small, independent addition.

Codex task: low priority (after XAUUSD rebuild and --intraday flag).
Add to queue when those complete.

Do NOT backtest "GEX + volume profile" as a combined strategy until GEX data
and order flow confirmation are available in machine-readable form.

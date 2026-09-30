# Options gamma and premium-normalised comparisons

REVIEW_SOURCE: FALLBACK_REVIEW

Interpreting as: fact-check the supplied transcript and add useful, bounded options research context to V2 without activating a trading rule.

Status: RESEARCH ONLY / NOT VALIDATED / NO TRADING OR SIZING CHANGE.
Sources checked: 2026-09-27. No original chart, option chain, strikes, expiry or graph assumptions were supplied, so the depicted performance comparison cannot be verified.

## Corrected explanation

For an option value V and underlying price S, delta is partial V / partial S; gamma is partial delta / partial S. Gamma is the slope of a delta-versus-underlying-price curve with other inputs fixed. A delta-versus-time chart has a different derivative. Near-the-money vanilla options generally have higher gamma, concentrated around the strike near expiry. This is not a universal inverse relationship with time at every strike. Long vanilla calls and puts have positive gamma; their short positions have negative gamma. See [OIC gamma](https://www.optionseducation.org/advancedconcepts/gamma).

At-the-money is not exactly synonymous with 50 delta: carry, volatility, maturity and delta convention matter. The 40-60 delta region is a useful descriptive near-money band, not a guaranteed optimum. The transcript's 'runway' is an intuition about changing sensitivity, not evidence of expected profit. Nothing supplied establishes that buying a 40-delta call beats buying an 80-delta call after accounting for risk and costs.

Short maturity also brings time-decay exposure. A correct directional forecast can still lose money if the move is too small or late. [OIC theta](https://www.optionseducation.org/advancedconcepts/theta). Changes in implied volatility also change premium, independently of the underlying move; volatility falling can offset a favourable price move. [OIC vega](https://www.optionseducation.org/advancedconcepts/vega).

## What premium normalisation really measures

The following is our mathematical derivation, not evidence of market performance. For premium P per underlying unit, multiplier M and cash budget B, ignoring fees and integer rounding:

```text
contracts n = B / (M * P)
position delta = n * M * delta = B * delta / P
position gamma = B * gamma / P
local option-return sensitivity to underlying percentage return = delta * S / P
```

Thus a 40-delta call has greater INITIAL delta exposure per dollar than an 80-delta call only when P40 < 0.5 * P80. That comparison is delta divided by premium, not gamma alone. Gamma is the curvature term as the underlying moves; changing IV and time also alter the Greeks.

Illustration only, not market quotes: P40=$2 and P80=$8 with multiplier 100. A $800 budget buys four 40-delta calls or one 80-delta call. Initial share-equivalent delta is 160 versus 80. For a small +$1 underlying move, first-order gains are approximately $160 versus $80 before gamma, time, IV and costs. The same first-order comparison for a -$1 move is approximately -$160 versus -$80. This is extra exposure, not free return or proof of better risk-adjusted performance. Initial sensitivities are not a forecast for large moves.

Equal premium is a legitimate comparison of deployed capital, not the only 'proper' comparison. Also show equal initial delta and a predeclared risk budget. For outright purchased options, the premium can be lost entirely; physical exercise can create a new underlying position, so expiry handling must be explicit. Do not treat an 80-delta call or any other strike as universally safer or better on all risk measures. An option delta of 0.40 is not a 40% probability of trading profit.

For small moves only:

```text
change in V ~= delta * change in S
             + 0.5 * gamma * (change in S)^2
             + theta * elapsed time
             + vega * change in implied volatility
```

Use theta per matching time unit and vega per matching volatility unit (often one percentage point). Cross terms and changing Greeks are omitted. Near expiry or for large moves, use full repricing or executable option quotes, not a constant-Greeks extrapolation. Gamma provides convexity, not a directional forecast or a positive expected-return guarantee.

## Relationship to V2

Two different uses of 'delta' must remain separate:

- `option_delta`: option-price sensitivity to its underlying price.
- `flow_delta`: classified buy volume minus classified sell volume over a stated interval.

The derivative of flow_delta is NOT option gamma. No slope of footprint delta or cumulative volume delta should be labelled gamma. The current BTCUSD/XAUUSD M15 price files cannot reconstruct historical option chains, IV surfaces or dealer positioning.

Useful addition now: research vocabulary and expiry-risk context for the existing options-expiry hypothesis. A large expiry or concentrated near-money open interest can be a factor to investigate, not automatic evidence of a reversal, pin, squeeze or volatility fade. Open interest by itself does not reveal dealer inventory sign, net hedging requirements or whether participants are hedged. A dealer-gamma estimate needs separate assumptions, venue coverage, sign conventions and point-in-time data, and remains an estimate.

Keep any option-selection experiment separate from the spot/CFD key-level strategy and the boundary_touch_v2 diagnostic. BTC option settlement can differ from equity-option conventions; gold ETF, futures and spot-linked products are not interchangeable. Specify the actual contract and underlying before applying the formulas in software, including premium currency, settlement currency, multiplier, exercise style and any premium-adjusted delta convention.

## Proposed test, gated on new data

Candidate ID: OPTIONS_PREMIUM_EFFICIENCY_V1. Status: QUEUE / DATA BLOCKED.

Hypothesis: after independently frozen bullish entry signals, near-40-delta calls may have different after-cost return and loss distributions from near-50/60/80-delta calls at a fixed expiry and holding policy. No superiority is presumed.

1. Select one specific options product and a fixed expiry-selection policy before looking at outcomes. Analyse 0DTE separately, not pooled with longer maturities.
2. Use identical underlying signals and timestamps across arms. Select nearest eligible delta using quotes available then; freeze tie-breaks and maximum quote age. Never select strikes with future delta or closing quotes.
3. Primary comparison: fixed premium budget, whole contracts, fees included, unused cash recorded. If any arm cannot afford a contract or lacks a valid quote, record the reason and use a predeclared common-event comparison. Do not silently delete losses or unfillable arms.
4. Secondary comparison: equal initial delta exposure. Report the different capital requirements instead of calling it equal risk. No leverage from the underlying system's suspended sizing rules.
5. Specify entry ask, exit bid, commission, realistic liquidity constraints, timestamped IV/Greeks and fixed exit horizon/expiry handling. Compare spreads and quote quality. A mid-price-only result is not executable evidence.
6. Measure portfolio returns including idle cash, full-premium losses, drawdown, holding time and event-level uncertainty. Multiple strikes from one event are paired observations, not independent trades. Preserve missing/ambiguous outcomes.
7. Include up/down/flat underlying cases, fast/slow moves and IV rise/fall stress scenarios. Freeze a small test budget and then validate on unseen data. No daily retuning to make 40 delta win.

Minimum data contract: venue, instrument/underlying ID, strike, call/put, expiry timestamp, quote timestamp, availability timestamp, bid/ask with size where available, underlying reference price, multiplier and units, IV and Greek source/model convention, fees, settlement/exercise rules, data lineage/hash. OI requires its own timestamp and publication lag. Missing fields remain unknown, not zero.

For now, do not build a new options executor, buy data, install a pricing library, alter signals, or claim a backtest from the present M15 files. The user's request authorises this knowledge addition, not those operations.

## Claude debate questions

- Accept the transcript as a mechanics lesson but reject '40 delta is most efficient' as an established rule?
- Keep option Greeks distinct from the order-flow sequence strip and the existing underlying strategies?
- Prioritise verified source history and current replay validation before a separate options-chain experiment?
- When a real product and point-in-time quotes exist, which objective should be primary: after-cost return on fixed premium or risk-constrained performance? Freeze it before testing.

Outcome: useful research context added; no verified improvement to V2 trading performance established.

# Options efficiency: what published research establishes

REVIEW_SOURCE: FALLBACK_REVIEW

Interpreting as: research the supplied 40-delta claim, examine how others tested related claims, and incorporate defensible methods into V2's research plan. Research-only request; no trading code or sizing changes.

Checked: 2026-09-27. Related concept: [gamma and premium efficiency](2026-09-27_options-gamma-premium-efficiency.md).

## Verdict

I did not find a primary empirical study establishing that 40-delta calls universally beat 80-delta calls on an equal-premium, after-cost, risk-adjusted basis. This is a bounded search finding, not proof that no such study exists. None of the studies below validates that rule for V2's BTCUSD/XAUUSD signals.

Distinguish three claims:

1. Definition/model mechanics: gamma is the derivative of option delta with respect to underlying price. Differentiation or a numerical derivative check can establish this within a pricing model; a winning trade is not the test.
2. Budget arithmetic: equal premium creates exposure proportional to delta/premium and gamma/premium. This is directly calculable for contemporaneous quotes, not evidence of positive expected returns.
3. Trading superiority: a particular delta bucket earns better future risk-adjusted returns. This needs data, execution assumptions, uncertainty estimates and independent validation. A theoretical diagram does not establish it.

## Research examined

### A. Coval and Shumway, Expected Option Returns (2001)

[Author-hosted paper](https://www.tylergshumway.org/Coval-ExpectedOptionReturns-2001.pdf).

The authors derive expected-return restrictions under asset-pricing assumptions and compare them with S&P index option returns. Their findings support strike-related call-return differences, but also report roughly 3% weekly average losses for zero-beta at-the-money straddles, pointing to risk beyond simple underlying exposure. This supports separating leverage from volatility risk; it does not identify an optimal 40-delta entry or a contemporary BTC result.

Access limitation: the author-hosted PDF open failed in this session; the abstract and indexed primary-source excerpts were accessible. No numerical table was independently reproduced, and no detailed sample claim is inferred from a secondary summary.

### B. Aretz, Lin and Poon, Moneyness, Underlying Asset Volatility, and the Cross-Section of Option Returns

[Review of Finance, 2023 issue; online publication 2022](https://academic.oup.com/rof/article/27/1/289/6510952).

They use OptionMetrics single-stock calls without dividends during remaining maturity, January 1996-June 2019, and test model predictions using double-sorted portfolios and Fama-MacBeth regressions. Systematic and idiosyncratic volatility have different relationships with returns across moneyness. Section 5 repeats analyses using zero, quarter-spread and half-spread execution adjustments; half-spread means buying at ask and selling at bid. These are conditional asset-pricing findings, not a universal optimal-delta strategy.

Read: abstract, empirical data/method sections and transaction-cost section. Not an independent replication. Its equity-option findings cannot be transferred mechanically to BTC or gold derivatives.

### C. Santa-Clara and Saretto, Option Strategies: Good Deals and Margin Calls

[UCLA April 2007 working paper](https://www.anderson.ucla.edu/documents/areas/fac/finance/option_strategies.pdf); [2009 journal publication](https://www.sciencedirect.com/science/article/pii/S1386418109000123).

The working paper studies S&P options strategies, compares midpoint versus bid/ask execution, models margin constraints, and uses 1,000 bootstrap repetitions to estimate uncertainty. Its futures-option sample spans 1985-2001; its index-option spread sample spans 1996-April 2006. Trading frictions materially reduce apparent attractiveness. Much of the evidence concerns short-put-containing strategies, so margin conclusions are not a direct test of fully paid long calls. The transferable lesson is to simulate implementation constraints rather than treat a paper premium return as an attainable portfolio return.

Read: data, inference and execution-cost sections of the working paper plus the published abstract. Working-paper numbers are not represented as independently verified final-journal estimates.

### D. Cboe, Buying Low Delta Call Options (2024)

[Exchange-hosted educational article](https://res.cboe.com/insights/posts/buying-low-delta-call-options/).

This is a hypothetical low-delta strategy illustration, not a controlled historical 40-versus-80-delta comparison. It therefore cannot establish the supplied claim. Its delta-as-probability language should not be imported as an exact probability of profit. The probability of finishing in the money is itself different from recovering premium and trading costs.

## What we should take into V2

The following are our proposed adaptations, not claims that the cited authors validated V2.

### Current underlying-market research

- Report gross and net R side by side, with a named cost source and date. Run predeclared base/adverse cost sensitivity, rather than tune a cost to preserve profit. Unknown costs remain assumptions.
- Show candidate count, no-entry, unresolved, excluded and completed counts together. Do not infer whole-portfolio profitability from completed-trade averages.
- Compare a frozen baseline and candidate on the same eligible sessions, with explicit exposure and capital rules. Distinguish a higher return caused by larger exposure from a better signal.
- Use event/day-block or suitably clustered uncertainty estimates when observations overlap. Ordinary independent resampling of several strikes or correlated signals from one event exaggerates sample size. This adaptation differs from merely copying an old paper's resampling procedure.
- Predeclare the tested variants and controls, record all rejected variants, and reserve genuinely new data for confirmation. Small samples can produce precise-looking but unreliable intervals; no fixed '30 trades proves it' rule.

These methods strengthen the evaluation process. They do not resolve the existing source-authenticity blockers or manufacture missing June-August briefs. Implementation of new analytical features remains separate from this research-only note.

### Future options experiment

Maintain `OPTIONS_PREMIUM_EFFICIENCY_V1` as QUEUE / DATA BLOCKED. Do not convert it into a BTC/gold entry filter.

Freeze a single product, expiry policy, entry/exit times and liquidity criteria. Compare 40/50/60/80-delta arms on identical signal events. Primary normalisation: equal premium budget with whole-contract rounding and idle cash. Secondary: equal initial delta with its different capital requirements disclosed. Include expiry loss/exercise handling, executable bid/ask and fees, and quote-age/availability checks.

Record explanatory exposures at entry: delta, gamma, theta, vega, premium, delta/premium, gamma/premium, IV, time to expiry and relative spread. Use these to explain results, not manufacture a weighted confidence score or choose weights after seeing outcomes. Separate 0DTE rather than pooling it with longer expiries. Use paired event-level after-cost differences, downside/loss distributions, capital usage and uncertainty, not win rate alone.

If option chains are unavailable, a pricing-model sensitivity illustration is allowed only as a labelled theoretical illustration. It cannot replace market quotes or become a profitability backtest. Option gamma remains distinct from volume-delta acceleration.

## Decision for Claude

Accept the mechanics and improved evaluation methods. Keep 40-delta superiority UNPROVEN. Do not promote it to a live rule, change sizing, buy data or claim published results have validated our system. First resolve input provenance; then apply an independently specified comparison using appropriate data. No studies were replicated and no new V2 performance tests were run in this research review.

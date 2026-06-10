---
idea_id: online-scout-20260525-60ebef8e01
title: A Comparative Study of Technical Trading Strategies Using a Genetic Algorithm
status: hypothesis_extracted
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4515471
source_quality_score: 95
source_quality_label: high
source_context: multi_agent:risk
created_from: online_scout
created_at: 2026-05-25T00:29:18+00:00
---

# A Comparative Study of Technical Trading Strategies Using a Genetic Algorithm

## Hypothesis
This source may support a testable trading hypothesis related to `risk`. It should be translated into exact entry, exit, filter, and risk rules before any backtest is trusted.

## Source Evidence
- Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4515471
- Quality: high (95/100)
- Context: multi_agent:risk

## Highlights
- # A Comparative Study of Technical Trading Strategies Using a Genetic Algorithm
[...]
Comput Econ 55, 349–381 (2020). https://doi.org/10.1007/s10614-016-9641-9
[...]
23 PagesPosted: 25 Jul 2023Last revised: 21 Aug 2023
[...]
Traditional approaches to the study of technical analysis (TA) often focus on the performance of a single indicator, which seems to fall short in scope and depth. We use a genetic algorithm (GA) to optimize trading strategies in the three major Forex markets, in order to verify the adequacy of TA strategies and rules to attain consistent superior returns, by comparing momentum, trend and breakout indicators. The indicators with the parameters generated through our GA consistently outperform the equivalent indicators applying parameters commonly used by the trading industry. EUR/USD and GBP/USD markets present interesting return figures before trading costs. The inclusion of spreads and commissions deteriorates returns substantially, suggesting these markets, under a more realistic set of assumptions, may be efficient. Trend indicators generate better outcomes and GBP/USD qualifies as the most profitable market. Different aggregate returns in different markets may stand as evidence of distinct maturation stages under an evolving efficiency market perspective. Our GA is able to search a wider solution space than traditional configurations and presents the possibility of recovering latent data, avoiding premature convergence.
[...]
**Keywords:**Genetic Algorithm&#x3b; Optimization; Finance; Technical Analysis; Forex

## Strategy Translation
Entry: To be defined from source after human review
Exit: To be defined from source after human review
Filters: source_quality_high, context_risk, walk_forward_required
Risk: cost_sensitive, no_live_promotion, require_out_of_sample
Assumptions: source_requires_rule_translation, hypothesis_not_validated

- Candidate edge:
- Filter or tuning angle:
- Market regime where it may work:
- Market regime where it may fail:

## Backtest Plan
- Target instrument/timeframe:
- Baseline strategy to compare:
- Required filters:
- Walk-forward requirement:
- Kill condition:

## Review Gate
- [ ] Source is credible enough to keep.
- [ ] Rules are specific enough to implement.
- [ ] Cost, spread, and slippage sensitivity are considered.
- [ ] No promotion before out-of-sample and walk-forward review.

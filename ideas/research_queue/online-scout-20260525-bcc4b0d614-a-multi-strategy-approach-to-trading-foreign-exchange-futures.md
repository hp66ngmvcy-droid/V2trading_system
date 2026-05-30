---
idea_id: online-scout-20260525-bcc4b0d614
title: A Multi Strategy Approach to Trading Foreign Exchange Futures
status: hypothesis_extracted
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3322717
source_quality_score: 95
source_quality_label: high
source_context: multi_agent:risk
created_from: online_scout
created_at: 2026-05-25T00:29:18+00:00
---

# A Multi Strategy Approach to Trading Foreign Exchange Futures

## Hypothesis
This source may support a testable trading hypothesis related to `risk`. It should be translated into exact entry, exit, filter, and risk rules before any backtest is trusted.

## Source Evidence
- Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3322717
- Quality: high (95/100)
- Context: multi_agent:risk

## Highlights
- # A Multi Strategy Approach to Trading Foreign Exchange Futures
[...]
26 PagesPosted: 28 Jan 2019Last revised: 30 Jan 2019
[...]
In this article we present a systematic multi-strategy approach to trading foreign exchange futures for a managed futures portfolio. Our central finding is that there is more alpha to be derived from combining different indicators compared to hand engineering each indicator. We show that combining technical indicators like momentum and mean reversion with fx carry indicators leads to significant improvement over individual indicators. Through an end to end systematic portfolio construction methodology, including indicator construction, normalization and combination we are able to improve the Sharpe Ratio of the resulting portfolio over the best performing single indicator by 60% when evaluated in an unbiased walk forward backtest.
[...]
**Keywords:**Foreign Exchange, Derivatives, Portfolio Construction, Multi-strategy, Managed Futures
[...]
, F3
[...]
, G1

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

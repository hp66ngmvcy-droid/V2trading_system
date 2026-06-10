# Candidate Selection Review

- Generated: 2026-05-25T22:36:16+00:00
- Research queue: `ideas/research_queue`
- Candidate dir: `ideas/backtest_candidates`
- Rejected dir: `ideas/rejected`
- Reviewed: 10
- Translate next: 0
- Blocked/hold: 10

## Items

| Recommendation | Score | Folder | Title | Reasons | Next Action |
| --- | ---: | --- | --- | --- | --- |
| NEEDS_RULE_TRANSLATION | 102 | research_queue | A Multi Strategy Approach to Trading Foreign Exchange Futures | source_quality_95, rules_not_defined, walk_forward_relevant, cost_model_relevant, filter_or_regime_relevant, portfolio_or_signal_combination | Extract exact tradable rules before creating any candidate. |
| OPEN_CANDIDATE | 50 | backtest_candidates | Vol-Scaled EMA Mixture Currency Momentum - Rule Extraction Candidate | candidate_needs_result_or_review | Run or close the candidate before adding similar work. |
| ALREADY_HAS_CANDIDATE | 10 | research_queue | Momentum and Trend Following Trading Strategies for Currencies Revisited - Combining Academia and Industry | matching_candidate_exists | Review existing candidate result before translating again. |
| ALREADY_TESTED_REJECTED | 0 | research_queue | Currency Momentum Strategies | source_or_note_already_rejected | Keep for history; do not convert again. |
| ALREADY_TESTED_REJECTED | 0 | research_queue | A Comparative Study of Technical Trading Strategies Using a Genetic Algorithm | source_or_note_already_rejected | Keep for history; do not convert again. |
| ALREADY_TESTED_REJECTED | 0 | research_queue | Untitled source | source_or_note_already_rejected | Keep for history; do not convert again. |
| CLOSED_REJECTED | 0 | backtest_candidates | Currency Cross-Sectional Momentum - Translated From SSRN Source | candidate_already_tested_rejected | No further work unless source is reframed. |
| CLOSED_REJECTED | 0 | backtest_candidates | EMA Walk-Forward Crossover — Translated from Academic Study | candidate_already_tested_rejected | No further work unless source is reframed. |
| CLOSED_REJECTED | 0 | backtest_candidates | GA Optimised Trend Forex - Translated From SSRN Source | candidate_already_tested_rejected | No further work unless source is reframed. |
| CLOSED_REJECTED | 0 | backtest_candidates | Walk-Forward EMA Robustness Proxy - Translated From WNE Source | candidate_already_tested_rejected | No further work unless source is reframed. |

## Guardrails

- This review ranks and blocks only; it does not promote strategy code.
- Already rejected sources should not be converted again without a new thesis.
- Prefer filter, regime, cost, and portfolio-construction improvements over repeated plain EMA tests.

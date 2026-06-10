# Research Quality And Filter-Tuning Upgrade - 2026-05-24

## Purpose

Upgrade the idea orchestrator so online strategy ideas are not treated equally.
The system should prefer ideas with strong theory, credible sources, clean code
translation, and realistic filter-tuning potential.

The aim is to produce fewer but better backtest candidates.

## Current V2 Strengths

The repo already has useful protection layers:

- Structural gates in `src/tar_system/scoring/gates.py`.
- Optimisation rules in `src/tar_system/optimisation/optimisation_rules.py`.
- Strategy improvement planning in
  `src/tar_system/optimisation/strategy_improvement_planner.py`.
- Stage-based tuning in `src/tar_system/tuner/pipeline.py`.
- Walk-forward, bootstrap, null-model, parameter sensitivity, and cost analysis
  modules under `src/tar_system/validation/`.
- Regime detection and regime heatmap support.

This means the online idea engine should not replace the backtester. It should
feed it better hypotheses.

## Source Quality Score

Every online idea should receive a source quality score before it becomes a
backtest candidate.

| Factor | Score |
| --- | ---: |
| MIT, university, institute, peer-reviewed, or major quant research source | +25 |
| Source includes clear economic/behavioral rationale | +20 |
| Source has testable rules or convertible hypothesis | +20 |
| Idea appears across multiple independent sources | +15 |
| Fits current local data and V2 backtester capabilities | +15 |
| Has known risks/limitations clearly stated | +10 |
| Only has social-media style claims, no method, no data | -40 |
| Requires live broker access or scraping/private APIs | -40 |
| Requires complex ML before a simple baseline exists | -20 |
| Optimizes many filters without robustness controls | -30 |

Promotion threshold:

- `>=70`: candidate for hypothesis note.
- `50-69`: keep as research, needs clarification.
- `<50`: archive or reject.

## Theory-Code-Structure Balance

Good strategy ideas need all three:

1. Theory
   - Why should this effect exist?
   - Is it behavioral, structural, risk-premium, liquidity, regime, or
     microstructure based?

2. Code
   - Can it become a deterministic signal?
   - Can it run on local OHLCV/features?
   - Can it be tested without hidden data or external sessions?

3. Structure
   - Does it fit the V2 pipeline?
   - Can it survive fees, spread, walk-forward, parameter stability, and
     minimum-trade gates?

Reject or hold ideas that only satisfy one side. A strong theory with no
testable rule is a research note. Good-looking code with no theory is a
curve-fit risk.

## Pattern Linking

The orchestrator should link ideas together when they share a pattern:

| Pattern | Possible V2 Test |
| --- | --- |
| Adaptive markets / regime dependence | Add regime-specific gates and compare results by regime |
| Time-series momentum / trend following | Test trend filters, breakout confirmation, and volatility targeting |
| Mean reversion in bounded regimes | Test range filters and avoid strong-trend regimes |
| Volatility clustering | Test ATR caps, position-size reductions, and high-volatility blocks |
| Session/liquidity effects | Test London/NY/session filters and spread assumptions |
| Cost sensitivity | Require after-cost backtest before promotion |
| Backtest overfitting warnings | Require walk-forward, parameter stability, bootstrap/null-model checks |

Pattern linking matters because one paper may not produce a strategy, but three
papers pointing toward the same filter idea may justify a controlled test.

## Research Sources To Prioritize

Use source tiers:

### Tier 1: Strong Research/Theory

- MIT Laboratory for Financial Engineering / Andrew Lo adaptive markets work.
- Peer-reviewed journal papers.
- AQR research on trend following, time-series momentum, and factor robustness.
- Bailey / López de Prado work on backtest overfitting, deflated Sharpe ratio,
  purged validation, and model selection risk.

### Tier 2: Useful Engineering References

- QuantConnect LEAN examples.
- Backtrader, Backtesting.py, and VectorBT examples.
- QuantStats reporting ideas.
- `awesome-quant` as a source discovery map.

### Tier 3: Low Trust / Use Only As Leads

- Forum posts.
- Social media strategy claims.
- Unsourced screenshots.
- Repos with no tests, no explanation, or no date/source context.

Low-trust sources can start a question, but they should not directly become
backtest candidates.

## Filter-Tuning Upgrade

Filter tuning is a key point in all strategies. The V2 tuner already supports
costs, ATR gates, and session windows. The upgrade is to make filters more
scientific and less curve-fit.

Recommended filter families:

- Cost/spread filter.
- ATR/volatility cap.
- Session filter.
- Trend/range regime filter.
- Higher-timeframe confirmation.
- Minimum signal confidence filter.
- News/macro-event exclusion, only if data is available locally.
- Correlation/positioning context filter.

Each filter test should record:

```yaml
filter_name: session_filter
reason_for_filter: liquidity/session hypothesis
source_pattern: session/liquidity effects
baseline_metrics: {}
filtered_metrics: {}
trade_count_delta: 0
pf_delta: 0.0
drawdown_delta: 0.0
oos_delta: 0.0
parameter_stability_delta: 0.0
decision: keep | review | reject
reason: ""
```

## Filter Tuning Rules

- Test one filter family at a time before combining filters.
- Reject filters that improve profit but destroy trade count.
- Reject filters that only work in one short window.
- Prefer filters with a theory-backed reason.
- Require after-cost results.
- Require walk-forward/OOS evidence before promotion.
- Track every attempted filter so repeated tuning does not inflate confidence.

## Prediction System Learning Loop

The prediction/research loop should learn from:

- failed gates
- walk-forward weakness
- parameter fragility
- cost defeat
- session/filter improvements
- regime heatmap weaknesses
- null-model/bootstrap warnings

The useful lesson is often not "this strategy works." More often it is:

- this strategy only works in a regime
- this filter reduces tail risk
- this parameter is fragile
- this idea is too cost-sensitive
- this entry works but the exit is poor
- this source pattern is recurring and worth a controlled test

## Backtester Candidate Upgrade

Before a candidate is queued, require:

```yaml
source_quality_score: 0
theory_score: 0
code_translation_score: 0
filter_tuning_score: 0
overfit_risk_score: 0
v2_fit_score: 0
linked_patterns:
  - adaptive_markets
  - volatility_filter
required_v2_checks:
  - costs
  - min_trades
  - drawdown
  - walk_forward
  - parameter_stability
  - bootstrap_or_null_model
  - regime_heatmap
```

## Recommended Build

1. Add research-quality scoring to idea notes.
2. Add pattern tags and linked-source tracking.
3. Add filter-family labels to backtest candidates.
4. Add a "test one filter at a time" rule to the backtest queue.
5. Add a daily report section for:
   - best new theory-backed ideas
   - strongest recurring patterns
   - filter-tuning candidates
   - ideas rejected as junk
   - ideas blocked as overfit risk

## Source Links

- MIT Adaptive Markets Hypothesis, Andrew Lo:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=602222
- MIT Sloan overview of Adaptive Markets:
  https://mitsloan.mit.edu/press/can-market-be-both-rational-and-irrational
- AQR Time Series Momentum:
  https://www.aqr.com/insights/research/journal-article/time-series-momentum
- AQR Trend Following research:
  https://www.aqr.com/insights/trend-following
- Backtest overfitting / deflated Sharpe discussion:
  https://academic.oup.com/jrssig/article/18/6/22/7038278
- arXiv trend-following dynamic momentum:
  https://arxiv.org/abs/2106.08420
- arXiv two centuries of trend following:
  https://arxiv.org/abs/1404.3274
- arXiv GAN backtesting overfitting warning:
  https://arxiv.org/abs/2209.04895

## Decision

The orchestrator should prefer research-backed patterns over isolated strategy
claims. It should link related ideas, score source quality, and focus heavily on
filter tuning because filters are where many strategies either become robust or
reveal themselves as overfit.

# Open Source Trading and Prediction-Market Systems Scout

Date: 2026-06-14
Status: research input for V2 paper-only system

## Purpose

Survey actively relevant open-source trading, forecasting, news, and prediction-market systems that could make V2 stronger: faster research loops, better market overview, stronger risk awareness, better strategy generation, and more robust paper validation.

This note is not a live-trading recommendation. Prediction-market data is especially sensitive because current reporting and papers highlight manipulation, insider-information, regulatory, and misinformation risk. Treat these sources as paper-research and risk-context inputs unless a future compliance review explicitly allows more.

## High-Value Candidates

### 1. FinRL-Trading / FinRL-X

- Repo: https://github.com/AI4Finance-Foundation/FinRL-Trading
- Paper: https://arxiv.org/abs/2603.21330
- Why it matters: FinRL-X describes an AI-native modular pipeline with data processing, strategy construction, backtesting, broker execution semantics, portfolio allocation, timing, and risk overlays.
- V2 use: borrow the architecture pattern, not the whole stack. Add a weight-centric strategy output contract so strategies produce target exposure/weights plus confidence and risk budget.
- Strategy ideas:
  - RL allocator as paper-only committee member.
  - LLM sentiment signal as a gated feature, never as standalone entry.
  - Portfolio-level risk overlay that can override individual strategy enthusiasm.

### 2. Microsoft Qlib

- Repo: https://github.com/microsoft/qlib
- Cache reference: https://github.com/microsoft/qlib/blob/main/qlib/data/cache.py
- Why it matters: mature research workflow around feature datasets, cache URI discipline, dataset cache, experiment tracking, and model evaluation.
- V2 use: adapt ideas for point-in-time feature cache and experiment registry. V2 already added a small tiered cache; Qlib validates keeping cache keys tied to instruments, fields, time range, frequency, and processors.
- Strategy ideas:
  - Factor-library import format for momentum, reversal, volatility, liquidity, and macro features.
  - Experiment comparison table keyed by dataset hash + feature version + model version.
  - Model confidence calibration before promotion.

### 3. NautilusTrader

- Repo: https://github.com/nautechsystems/nautilus_trader
- Why it matters: event-driven trading architecture, realistic execution model, adapters, and strong emphasis on backtest/live consistency.
- V2 use: borrow event model and execution-simulation ideas without importing the full engine.
- Strategy ideas:
  - Event-sourced paper replay with market data, signal, order, fill, and risk events.
  - Slippage/spread stress tests as mandatory validation stage.
  - Broker profile abstraction for different instruments and cost models.

### 4. QuantConnect Lean

- Repo: https://github.com/QuantConnect/Lean
- Why it matters: large production-grade open-source engine with universe selection, scheduling, data subscriptions, portfolio/risk modules, and live/backtest parity.
- V2 use: mine architecture concepts for universe selection, scheduled events, and risk management. Full adoption is too heavy.
- Strategy ideas:
  - Scheduled macro/news event windows that reduce exposure before high-risk events.
  - Universe filters for liquid assets only.
  - Risk module contract: max drawdown, max sector/asset exposure, stop trading after anomalous data.

### 5. Freqtrade

- Repo: https://github.com/freqtrade/freqtrade
- Backtesting reference: https://github.com/freqtrade/freqtrade/blob/develop/freqtrade/optimize/backtesting.py
- Why it matters: practical open-source bot with backtest result reuse, strategy management, protections, and operational controls.
- V2 use: borrow protections and result reuse patterns.
- Strategy ideas:
  - Cooldown after loss clusters.
  - Pair/asset locks after anomalous moves.
  - Result cache age policy: day/week/month style invalidation for repeated backtests.

### 6. vectorbt

- Repo: https://github.com/polakowo/vectorbt
- Cache/reference: https://github.com/polakowo/vectorbt/blob/master/vectorbt/utils/decorators.py
- Why it matters: fast vectorized research and explicit cached properties/methods.
- V2 use: keep V2's focused backtester, but add vectorized prototype path for fast hypothesis screening before slower paper runs.
- Strategy ideas:
  - Fast vector screen for moving-average, volatility, breakout, and mean-reversion candidates.
  - Candidate prefilter: reject before full walk-forward if vectorized result is weak or unstable.

### 7. OpenBB

- Repo: https://github.com/OpenBB-finance/OpenBB
- Why it matters: broad open-source financial data and market overview ecosystem.
- V2 use: use as a reference for market overview and data adapter structure, not as a hard dependency initially.
- Strategy ideas:
  - Market dashboard context: macro calendar, rates, earnings/news, volatility indices.
  - Source adapter pattern with provenance and freshness metadata.

### 8. PolyBench / Prediction Arena / PolySwarm

- PolyBench repo: https://github.com/PolyBench/PolyBench
- Prediction Arena paper: https://arxiv.org/abs/2604.07355
- PolyBench paper: https://arxiv.org/abs/2604.14199
- PolySwarm paper: https://arxiv.org/abs/2604.03888
- Why it matters: these are recent 2026 systems/benchmarks around LLM forecasting and prediction markets. The useful part for V2 is probabilistic calibration, not automated betting.
- V2 use: build a paper-only forecasting evaluation layer with Brier score, log loss, calibration curves, confidence-weighted returns, and strict timestamp locking.
- Strategy ideas:
  - Forecast committee: each agent outputs probability, confidence, evidence, and no-trade rationale.
  - Market-implied probability comparison: use prediction-market prices as sentiment/context, not direct execution.
  - Risk flags for manipulation-prone markets, low liquidity, insider-risk events, and news-source uncertainty.

## Prediction-Market Tooling

### Polymarket CLOB Client

- Repo: https://github.com/Polymarket/py-clob-client
- Status: archived.
- V2 use: do not depend on it directly. Use only as historical API reference if needed.

### pykalshi

- Repo: https://github.com/arshka/pykalshi
- V2 use: potential API research reference only. Any Kalshi integration must remain paper-only unless compliance and jurisdiction rules are reviewed.

## Immediate V2 Build Ideas

1. Add `MarketContextSnapshot`.
   - Inputs: volatility regime, trend state, macro/news risk state, prediction-market sentiment if available, liquidity/spread state, data freshness.
   - Output: JSON artifact cached by timestamp and source hashes.

2. Add `ForecastCalibrationReport`.
   - Metrics: Brier score, log loss, calibration bins, confidence-vs-hit-rate, no-trade accuracy, source freshness.
   - Purpose: stop LLM/news agents from sounding confident without evidence.

3. Add `RiskOverlayEngine`.
   - Inputs: current strategy signals, recent drawdown, volatility shock, event calendar, spread/slippage stress, liquidity.
   - Output: allow/reduce/block plus reason codes.

4. Add vectorized hypothesis prefilter.
   - Use fast Pandas/Numpy screening before full TAR walk-forward.
   - Reject candidates that fail minimum trades, stability, or cost sensitivity.

5. Add prediction-market context ingestion as paper-only.
   - Store market question, implied probability, liquidity, spread, volume, source, timestamp.
   - Use as a context feature and risk signal, never as a live trade trigger.

## Recommended Priority

1. Qlib-style feature/experiment registry.
2. Freqtrade-style protections and cache age policy.
3. Nautilus/Lean-style event and risk overlay contracts.
4. OpenBB-style market overview adapter.
5. PolyBench/Prediction Arena-style calibration layer for news and LLM forecasts.
6. FinRL-X-style weight-centric strategy contract after the above guardrails are in place.

## Guardrails

- Keep V2 paper-only.
- Do not optimize for profit before robustness metrics pass.
- Require walk-forward, out-of-sample, cost/slippage stress, drawdown limits, and source freshness checks.
- Treat prediction-market data as noisy, manipulable, and legally sensitive.
- Keep provenance on every external signal.

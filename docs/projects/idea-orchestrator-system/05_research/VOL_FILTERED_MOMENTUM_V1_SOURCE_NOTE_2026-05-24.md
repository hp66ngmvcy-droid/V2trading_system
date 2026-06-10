# Vol Filtered Momentum V1 Source Note

Date: 2026-05-24

## Source Pattern

This idea combines three research patterns:

- Moving-average momentum/trend extraction remains a simple, inspectable
  baseline for technical trading research.
- Volatility/regime filters can reduce low-information or noisy entries.
- Filter tuning should be tested separately from entry logic before promotion.

Primary sources checked:

- Z. George Yang, "Filtered Market Statistics and Technical Trading Rules",
  SSRN 2260609. Notes: volatility-based return filtering is tested against
  dual moving-average and channel-style technical rules.
- Arjun Prakash, Nick James, Max Menzies, Gilad Francis, "Structural clustering
  of volatility regimes for dynamic trading strategies", arXiv:2004.09963.
  Notes: volatility regimes can be used for online risk avoidance.
- Guofu Zhou and Yingzi Zhu, "A Theory of Technical Trading Using Moving
  Averages", SSRN 2326650. Notes: moving-average trend signals have a formal
  technical-trader rationale.
- Benjamin Bruder, Tung-Lam Dao, Jean-Charles Richard, Thierry Roncalli,
  "Trend Filtering Methods for Momentum Strategies", SSRN 2289097. Notes:
  trend filtering and calibration are central implementation concerns.

## Implemented Hypothesis

`vol_filtered_momentum_v1`:

- Uses EMA fast/slow direction as the main trend signal.
- Requires RSI confirmation.
- Blocks flat/noise bars using candle body divided by ATR.
- Blocks ATR compression and extreme volatility using ATR versus median ATR.
- Blocks explicitly volatile regimes.
- Keeps session filtering on by default.

## Backtester Review Questions

- Does the body/ATR filter reduce whipsaw without starving trade count?
- Are ATR floor/ceiling multipliers too strict on M5 and M15?
- Does the strategy behave better on XAUUSD than FX majors?
- Should `UNKNOWN` regime be allowed or blocked after first test pass?

## First Backtest Result

Queued job:

- `job_id`: `45ba8b65f90541a09b15b890adebc921`
- Strategy: `vol_filtered_momentum_v1`
- Dataset: `data/raw/XAUUSD_M15.csv`
- Stage: `online_idea_review`
- Result: `REVIEW`
- Report: `reports/XAUUSD_M15_vol_filtered_momentum_v1_report.md`

In-sample metrics:

- Trades: 918
- Profit factor: 1.0837
- Win rate: 31.8%
- Sharpe: 0.5067
- Sortino: 0.9368
- Max drawdown: 1.24%
- Net profit: 245.09
- Max consecutive losses: 18

Walk-forward metrics:

- Split count: 10
- Stitched trades: 13
- Stitched profit factor: 0.5427
- Stitched Sharpe: -1.4485
- Verdict: `REVIEW`
- Reason: walk-forward profit factor below 1.10
- Bootstrap CI spans zero: true

Initial read:

The entry logic can find enough in-sample trades, but the current filter set
does not transfer cleanly out of sample. Do not promote. Next review should
test filter tuning only:

- tighten `min_body_atr`
- block `UNKNOWN` regime
- reduce trade frequency on M15
- compare M5, M30, H1 before changing entry direction rules

## Candidate Parameters

- `min_body_atr`: 0.15, 0.20, 0.30
- `atr_floor_multiplier`: 0.45, 0.55, 0.70
- `atr_ceil_multiplier`: 2.25, 2.75, 3.25
- `ema_slope_threshold`: 0.00010, 0.00015, 0.00025
- `reward_risk`: 2.0, 2.5, 3.0

## Safety

Research only. No live trading. No MT5 promotion without walk-forward,
minimum-trade, cost, and paper-forward review.

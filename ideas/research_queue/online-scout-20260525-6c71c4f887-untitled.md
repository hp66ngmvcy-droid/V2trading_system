---
idea_id: online-scout-20260525-6c71c4f887
title: Untitled source
status: hypothesis_extracted
source_url: https://www.wne.uw.edu.pl/download_file/4308/2141
source_quality_score: 95
source_quality_label: high
source_context: multi_agent:robustness
created_from: online_scout
created_at: 2026-05-25T00:29:18+00:00
---

# Untitled source

## Hypothesis
This source may support a testable trading hypothesis related to `robustness`. It should be translated into exact entry, exit, filter, and risk rules before any backtest is trusted.

## Source Evidence
- Source: https://www.wne.uw.edu.pl/download_file/4308/2141
- Quality: high (95/100)
- Context: multi_agent:robustness

## Highlights
- Abstract: This study aimed to apply the algorithmic trading strategy on major
[...]
while the MA
[...]
cross strategy was employed for the trend-following strategy. Backtests were performed on 6
[...]
major pairs in the period from January 1, 2000, to June 30, 2023, and daily, and intraday data
[...]
Following (TF) strategies with a benchmark (B) strategy using economic and statistical significance tests. An independent t-test was used to compare the mean returns of different trading
[...]
strategies. The mean returns are derived from observed returns for all out-of-sample periods.
[...]
• Implement a rolling walk-forward optimization to solve the overfitting problem.
[...]
• Implement a more realistic backtesting process that takes into account factors such as
[...]
initial deposits, transaction costs, and trade volume.
[...]
• Walk forward optimization - define roll size and divide each window into training, validation, and testing periods.
[...]
• All combinations of Exponential Moving Average (EMA) - generate all combinations of
[...]
• Best combination of Exponential Moving Average (EMA) - find the best EMA combination with the highest SR.
[...]
• Backtesting - determine initial deposit, transaction cost, and trading volume to compare the performance of trading strategy including machine learning-based and trendfollowing strategies.
[...]
In this study, the exponential moving average (EMA) was utilized as an indicator to identify trading signals for the trend-following strategy. Moving averages are commonly used as
[...]
smoothing tools to reduce noise in financial data. There are various ways to use EMA to generate trading signals, but in this study, only fast and slow EMA crossover was considered. Specifically, EMA10, EMA20, EMA50, EMA100, and EMA200 were used with a walk-forward
[...]
approach. This indicates that 10 combinations of fast and slow EMAs were investigated in
[...]
each rolling walk-forward window. The Sharpe ratio was used to optimize the moving average
[...]
crossover strategy in each window. A buy signal occurs when the fast EMA crosses above the
[...]
below the slow EMA, indicating a downtrend. Table 6 shows a detailed algorithm describing
[...]
EMA crossover strategy
[...]
3.6 Rolling walk forward optimization
[...]
To avoid overfitting problems and data-snooping bias, a rolling walk-forward approach
[...]
was implemented. This approach entails iterative training of the model on a fixed training set,
[...]
tuning hyperparameters on a fixed validation set, and subsequently making predictions on a
[...]
fixed test set. The parameters of the rolling walk-forward approach are illustrated in Figure 3.
[...]
The dataset is divided into 40 windows, each window containing different train, validation, and
[...]
test sets. The rolling size is set at six months and in each window, the train, validation, and test
[...]
sets advance by six months until
[...]
end of the dataset.
[...]
Table 7 shows number of data for the rolling walk-forward approach. The training set is 68
[...]
percent, and the test set is 14 percent of
[...]
total data in one
[...]
rolling walk-forward approach’s window for both daily and 4-hour frequency data. For daily
[...]
frequency data, 600 days of price data were used for the training set, followed by 156 days for
[...]
the validation set, and 126 days for
[...]
test set in each window. This method was applied to
[...]
Trend Following strategy
[...]
3.8 Backtest assumption
[...]
The primary objective of this study is to generate trading signals with the highest Sharpe
[...]
Ratio (SR), rather than precisely predicting returns that closely match real returns. Therefore,
[...]
when calculating the Sharpe Ratio (SR), transaction costs should be taken into account. The
[...]
performance of a strategy without transaction costs can significantly diverge from reality, especially as the trading frequency increases. The assumption of backtesting is detailed in the

## Strategy Translation
Entry: To be defined from source after human review
Exit: To be defined from source after human review
Filters: source_quality_high, context_robustness, walk_forward_required
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

# V2 Finance Logic and Chart Intake — Done

Date: 2026-08-23  
Review state: SELF-REVIEWED  
Scope: Read-only local system review; no strategy mutation, order, compile, copy, promotion, or deployment.

Interpreting as: identify whether the active trading system is V2, explain its financial and risk logic from the local files, then assess the supplied charts only as paper-trading scenarios—not as a certain prediction or live trade instruction.

## Findings

- The active project is `V2trading_system`, described by its orchestrator as the V2 TAR local paper-only trading research system.
- Its pipeline is idea -> tuner -> walk-forward -> code candidate -> paper test -> review -> manual approval.
- The current focus is `vol_filtered_momentum_v1` on XAUUSD M15.
- Signal logic combines EMA direction and slope, RSI confirmation, ATR/body filters, regime blocking, and a liquid-session filter. Stops are ATR based and the strategy default reward:risk target is 2.5:1.
- Position sizing supports fixed lot, fixed-risk percentage, ATR-based risk, and half-Kelly research models, then applies broker lot, leverage-safety, and 30% asset-class exposure caps.
- Evaluation uses profit factor, drawdown, trade count, expectancy, robustness, parameter stability, walk-forward, Monte Carlo, regime coverage, cost realism, and audit-trail gates. Spread, slippage, and commission are modelled.
- A later tuned candidate note records in-sample PF 1.2581, Sharpe 1.5976, max drawdown 0.45%, and 283 trades, plus six walk-forward splits averaging PF 1.34 and Sharpe 1.81. This is later than the initial failed walk-forward source note, but it remains a code candidate requiring paper testing and human approval, not a live-ready strategy.
- No newly supplied trading-chart image was present in the current attachment intake, so no chart-direction assessment was performed.

## Safety conclusion

Any chart assessment should be expressed as a primary conditional scenario, invalidation level, and alternative scenario. It must not be presented as an obvious certainty or live trade instruction. V2 remains paper-only.

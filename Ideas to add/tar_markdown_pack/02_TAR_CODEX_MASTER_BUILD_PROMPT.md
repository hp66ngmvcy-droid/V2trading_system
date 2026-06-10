# TAR Codex Master Build Prompt

## Use This Prompt in Codex

```text
You are working on the TAR trading research system.

Build a secure, modular, validation-first trading research platform.

Do not add live trading execution.
Do not connect real broker APIs.
Do not read broker credentials.
Do not place real orders.

The system must remain paper-only.

Build the project in stages:

1. Data validation
2. Validated Parquet store
3. Feature engineering
4. Regime detection
5. Strategy base class
6. Signal dataclasses
7. Risk context dataclasses
8. 5-gate risk engine
9. Paper execution engine
10. Portfolio tracker
11. Event-driven backtest engine
12. Walk-forward validation
13. Scoring engine
14. Strategy memory
15. Append-only audit log
16. Reporting engine
17. Streamlit dashboard
18. GitHub review module
19. Security module
20. Disabled live interface
21. Librarian skill

Every system action must produce:
- timestamp
- event type
- strategy
- symbol
- reason code
- decision
- metadata

Do not blindly copy external repos.
Use external repos only as architectural references unless explicitly approved.

Acceptance criteria:
- tests pass
- live trading is disabled
- data validation rejects bad data
- backtest runs bar by bar
- portfolio updates after simulated fills
- risk engine blocks unsafe trades
- audit log records decisions
- dashboard shows system state
```

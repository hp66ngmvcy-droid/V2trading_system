# TAR Agents and Hooks

## Agents

### 1. Oversight Controller Agent
Routes tasks, enforces safety and decides next action.

### 2. Data Validation Agent
Checks raw OHLCV data before it enters the system.

### 3. Feature Engineering Agent
Creates indicators and validates feature quality.

### 4. Regime Agent
Classifies market state as trending, ranging, volatile or unknown.

### 5. Strategy Agent
Manages strategy logic, variants and signal creation.

### 6. Backtest Agent
Runs event-driven backtests and prevents look-ahead bias.

### 7. Walk-Forward Validation Agent
Runs rolling train/test validation and checks parameter stability.

### 8. Risk Agent
Applies the 5-gate risk engine.

### 9. Paper Execution Agent
Simulates fills, slippage, spread and commission.

### 10. Portfolio Agent
Tracks positions, PnL, equity curve, drawdown and exposure.

### 11. Scoring Agent
Scores robustness, realism, drawdown and consistency.

### 12. Memory Agent
Stores strategy history in DuckDB.

### 13. Audit Agent
Writes append-only JSONL logs.

### 14. Reporting Agent
Generates Markdown, TXT and JSON reports.

### 15. GitHub Review Agent
Reviews external repos before integration.

### 16. Security Agent
Blocks unsafe actions and checks secrets.

### 17. Dashboard Agent
Displays system state and human review workflows.

### 18. Librarian Agent
Indexes files, creates Obsidian notes and organises knowledge.

---

## Hooks

```text
pre_data_validation_hook
post_data_validation_hook
pre_feature_hook
post_feature_hook
pre_signal_hook
post_signal_hook
pre_risk_hook
post_risk_hook
pre_fill_hook
post_fill_hook
post_backtest_hook
post_score_hook
pre_memory_write_hook
dashboard_action_hook
security_gate_hook
librarian_scan_hook
external_repo_review_hook
```

---

## Rule

Every hook must be able to write to the audit system.

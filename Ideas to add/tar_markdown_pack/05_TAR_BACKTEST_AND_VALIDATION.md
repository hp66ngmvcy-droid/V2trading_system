# TAR Backtest and Validation

## Objective

Build a realistic event-driven backtest system that prevents look-ahead bias.

---

## Event-Driven Backtest Flow

```text
Load validated data
↓
Generate features
↓
Detect regime
↓
Strategy creates signal
↓
Risk engine approves or rejects
↓
Paper broker simulates fill
↓
Portfolio updates
↓
Audit log records event
↓
Scoring engine reviews result
```

---

## Requirements

- bar-by-bar processing
- no look-ahead bias
- no future data leakage
- cost modelling included
- spread modelling included
- commission modelling included
- slippage modelling included
- reason-coded decisions
- audit event at every stage

---

## Walk-Forward Validation

Add:

- training window
- blind test window
- rolling validation
- stitched out-of-sample results
- parameter stability review

---

## Commands

```bash
python -m tar_system.cli run-backtest --strategy gold_v2 --symbol XAUUSD
python -m tar_system.cli run-walk-forward --strategy gold_v2 --symbol XAUUSD
python -m tar_system.cli score-strategy --strategy gold_v2
```

---

## Strategy Verdicts

```text
KEEP
REVISE
KILL
```

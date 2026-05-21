# TAR Risk Engine

## Objective

Every signal must pass through a strict risk engine before simulated execution.

---

## 5-Gate Risk Engine

### Gate 1: Paper Mode Check
System must be in paper mode.

### Gate 2: Confidence Threshold
Signal confidence must exceed minimum threshold.

### Gate 3: Drawdown Guard
Block trades if drawdown limit is breached.

### Gate 4: Portfolio Exposure Limit
Block trades if asset, strategy or portfolio exposure is too high.

### Gate 5: Volatility Cap and Position Sizing
Scale or block trades based on volatility.

---

## If Any Gate Fails

The system must:

- block trade
- write reason code
- continue safely
- update audit log

---

## Position Sizing

Add:

- fixed fractional sizing
- Kelly stub
- volatility-scaled sizing
- max exposure caps
- per-strategy limits

---

## Risk Files

```text
src/tar_system/risk/
├── engine.py
├── sizing.py
└── limits.py
```

---

## Risk Commands

```bash
python -m tar_system.cli risk-check --strategy gold_v2 --symbol XAUUSD
python -m tar_system.cli risk-report
```

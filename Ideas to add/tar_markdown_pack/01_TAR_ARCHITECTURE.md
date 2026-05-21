# TAR System Architecture

## Core Objective

Build TAR as a secure, modular, testable trading research platform.

The platform should support:

- market data validation
- feature engineering
- regime detection
- strategy generation
- event-driven backtesting
- walk-forward validation
- paper execution
- portfolio tracking
- scoring
- memory
- audit logs
- dashboard review

---

## Core Pipeline

```text
Raw OHLCV Data
↓
9-point schema validation
↓
Validated Parquet
↓
Feature engineering
↓
Regime detection
↓
Signal generation
↓
5-gate risk engine
↓
Paper broker simulation
↓
Portfolio tracker
↓
Append-only audit log
↓
Scoring engine
↓
KEEP / REVISE / KILL verdict
↓
Strategy memory
↓
Dashboard human decision
```

---

## Recommended Project Structure

```text
tar_system/
├── src/tar_system/
│   ├── cli.py
│   ├── settings.py
│   ├── logger.py
│   ├── constants.py
│   ├── reason_codes.py
│   ├── core/
│   ├── agents/
│   ├── data/
│   ├── features/
│   ├── regime/
│   ├── forecasts/
│   ├── strategies/
│   ├── risk/
│   ├── execution/
│   ├── portfolio/
│   ├── backtest/
│   ├── validation/
│   ├── scoring/
│   ├── reporting/
│   ├── audit/
│   ├── memory/
│   ├── github_review/
│   ├── security/
│   ├── live/
│   ├── librarian/
│   └── dashboard/
├── tests/
├── data/raw/
├── data/validated/
├── data/features/
├── data/results/
├── logs/audit/
├── reports/
├── configs/
├── archive/
├── docs/
├── scripts/
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

---

## Operating Principle

Every decision must be:

- validated
- auditable
- reversible
- reason-coded
- blocked by default if unsafe

The system should prioritise reliability over speed.

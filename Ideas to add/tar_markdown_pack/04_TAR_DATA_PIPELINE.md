# TAR Data Pipeline

## Objective

Create a clean, validated, repeatable data pipeline for trading research.

---

## Pipeline

```text
Raw CSV / tick data
↓
Schema validation
↓
Clean OHLCV data
↓
Validated Parquet
↓
DuckDB query layer
↓
Feature engineering
↓
Backtest-ready dataset
```

---

## Raw Data Rules

Store raw data in:

```text
data/raw/
```

Never overwrite raw files.

---

## Validated Data Rules

Store validated data in:

```text
data/validated/
```

Use Parquet for validated datasets.

---

## Feature Data Rules

Store processed feature data in:

```text
data/features/
```

Feature data should include:

- EMA
- RSI
- ATR
- MACD
- returns
- volatility
- rolling range
- spread fields where available
- cost assumptions where available

---

## 9-Point Validation

Check:

1. OHLCV schema
2. missing values
3. duplicate timestamps
4. timezone consistency
5. price sanity
6. volume sanity
7. chronological ordering
8. gap detection
9. symbol and timeframe metadata

---

## Suggested Commands

```bash
python -m tar_system.cli validate-data --symbol XAUUSD
python -m tar_system.cli build-features --symbol XAUUSD
python -m tar_system.cli inspect-data --symbol XAUUSD
```

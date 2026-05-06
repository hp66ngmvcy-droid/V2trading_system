# TAR V2 Local Trading Research System

Lean local-first research foundation for CSV market data, validation, features, backtesting, scoring, audit logs and manual MT5 review exports.

No live trading, broker API, paid API, cloud dependency, OpenAI API, Docker, Ray, Polars or heavy agent framework is included.

## Setup

```bash
cd /Users/whs1/Dev/V2trading_system
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
```

## Install

```bash
pip install -r requirements.txt
pip install -e .
```

## CSV Import

```bash
python -m tar_system.cli import-csv --file data/raw/XAUUSD.csv --symbol XAUUSD --timeframe M15
```

## Build Features

```bash
python -m tar_system.cli validate-data --symbol XAUUSD --timeframe M15
python -m tar_system.cli build-features --symbol XAUUSD --timeframe M15
```

## Backtest

```bash
python -m tar_system.cli run-backtest --strategy gold_v2 --symbol XAUUSD --timeframe M15
```

## Scoring

```bash
python -m tar_system.cli score-strategy --strategy gold_v2 --symbol XAUUSD --timeframe M15
```

## MT5 Manual Export

```bash
python -m tar_system.cli export-mt5 --strategy gold_v2 --symbol XAUUSD --timeframe M15
```

## Dashboard Placeholder

```bash
streamlit run src/tar_system/reporting/reporter.py
```

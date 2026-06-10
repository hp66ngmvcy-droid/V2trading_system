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

## Live Market Reference

The dashboard Asset Data page includes a TradingView chart link for the selected symbol/timeframe. This is a human reference/export path only: strategy training and tests still read local OHLCV files such as `data/raw/XAUUSD_M15.csv`, then validated/feature data produced by the CLI.

## Integrated V2 Web UI

```bash
PYTHONPATH=src python -m tar_system.cli run-web-ui --host 127.0.0.1 --port 8601
```

Open `http://127.0.0.1:8601`. This serves the v2 research UI with a read-only runtime data bridge from local queue, results, audit, signal and raw-data files.

## New Project Workspaces

```bash
bash scripts/create_project_workspace.sh my-new-project
```

This creates `docs/projects/my-new-project/` with PRD, TRD, app flow, UI/UX
brief, backend schema, implementation plan, QA checklist, ADR, source notes,
assets, and screenshots folders.

## Legacy Streamlit Dashboard

```bash
streamlit run src/tar_system/dashboard/app.py
```

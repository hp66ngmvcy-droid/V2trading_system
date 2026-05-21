# TAR Local Runbook

## Project Location

Recommended local path:

```bash
cd /Users/whs1/Dev/V2trading_system
```

Open in VS Code:

```bash
code .
```

---

## Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Install Project

```bash
pip install -e .
```

---

## Run Dashboard

```bash
streamlit run src/tar_system/dashboard/app.py
```

---

## Run Data Validation

```bash
python -m tar_system.cli validate-data --symbol XAUUSD
```

---

## Run Backtest

```bash
python -m tar_system.cli run-backtest --strategy gold_v2 --symbol XAUUSD
```

---

## Run Walk-Forward Test

```bash
python -m tar_system.cli run-walk-forward --strategy gold_v2 --symbol XAUUSD
```

---

## Generate Report

```bash
python -m tar_system.cli generate-report --strategy gold_v2 --format md
```

---

## Check Running Terminal Processes

```bash
ps aux | grep streamlit
ps aux | grep python
```

---

## Stop Streamlit

Usually use:

```bash
CTRL + C
```

Or find process:

```bash
lsof -i :8501
kill -9 PROCESS_ID
```

---

## Local Dashboard URL

```text
http://localhost:8501
```

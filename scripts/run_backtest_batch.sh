#!/usr/bin/env bash
set -euo pipefail
cd /Users/whs1/Dev/V2trading_system
if [ -f venv/bin/activate ]; then . venv/bin/activate; fi
PYTHONPATH=src python -m tar_system.cli run-backtest --strategy "${STRATEGY:-gold_v2}" --symbol "${SYMBOL:-XAUUSD}" --timeframe "${TIMEFRAME:-M15}"

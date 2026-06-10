# Paper Signal Layer

This layer adds local paper-signal monitoring without enabling live trading.

## Components

- `src/tar_system/strategies/liquidity_sweep_v1.py` - liquidity sweep strategy with entry, stop loss, take profit and confidence.
- `src/tar_system/controller/strategy_health_monitor.py` - checks paper metrics and marks strategies `ACTIVE`, `WATCH` or `PAUSED`.
- `src/tar_system/controller/paper_signal_runner.py` - generates the latest paper signal, runs risk gates and writes local alert files.
- `src/tar_system/dashboard/pages/paper_signals.py` - dashboard panel for latest signal, health status, recent log and report controls.
- `configs/paper_signal_schedule.json` - 15-minute scheduler example.
- `src/tar_system/reporting/reporter.py` - includes a print-ready quant report generator.

## Commands

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli monitor-strategy-health --strategy liquidity_sweep_v1 --symbol XAUUSD --timeframe M15
```

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-paper-signal --strategy liquidity_sweep_v1 --symbol XAUUSD --timeframe M15
```

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli install-paper-signal-schedule --strategy liquidity_sweep_v1 --symbol XAUUSD --timeframe M15 --interval-minutes 15
```

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-scheduled
```

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli generate-quant-report --strategy liquidity_sweep_v1 --symbol XAUUSD --timeframe M15
```

## Outputs

- `runtime/strategy_health_status.json`
- `runtime/latest_paper_signal.json`
- `runtime/paper_signal_alerts.jsonl`
- `data/results/liquidity_sweep_v1_XAUUSD_M15_metrics.json`
- `data/results/XAUUSD_M15_liquidity_sweep_v1_equity.json`
- `reports/XAUUSD_M15_liquidity_sweep_v1_quant_report.md`
- `reports/XAUUSD_M15_liquidity_sweep_v1_quant_report.pdf`

All outputs are paper-only. There is no broker execution path.

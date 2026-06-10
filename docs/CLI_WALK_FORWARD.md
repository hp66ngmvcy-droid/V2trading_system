# Walk-Forward CLI

Runs a rolling walk-forward validation for a single strategy on a single symbol. Part of the Phase 2 validation sequence — run after standard optimiser, before macro/regime retrofit.

## When to Use

Use this when you have a candidate strategy and want OOS equity curve validation across rolling time windows before promoting to paper collection.

## Run

```bash
PYTHONPATH=src venv/bin/python src/tar_system/cli_walk_forward.py \
  --strategy rsi_trend_v4 \
  --symbol XAUUSD \
  --timeframe M15 \
  --train-months 12 \
  --test-months 3 \
  --output reports/walk_forward_results.json
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--strategy` | `gold_v2` | Strategy name from registry |
| `--symbol` | `XAUUSD` | Asset symbol |
| `--timeframe` | `M15` | Bar timeframe |
| `--train-months` | `12` | Training window length |
| `--test-months` | `3` | OOS test window length |
| `--start-date` | None | ISO date filter (inclusive) |
| `--end-date` | None | ISO date filter (inclusive) |
| `--output` | `reports/walk_forward_results.json` | Results output path |

## Data Source

Reads from `data/validated/{SYMBOL}_{TIMEFRAME}.parquet`. Returns error if file missing — do not create or fetch data automatically.

## Output

- JSON results written to `--output` path
- Failed windows logged to `logs/failed_windows.jsonl`
- Summary printed to stdout

## Pipeline Position (Phase 2)

```
1. Standard optimiser (continuous_parameter_search.py)
2. Walk-forward validation  ← this tool
3. Paper collection
4. Macro/regime retrofit
```

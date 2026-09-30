# XAUUSD Rebuild Done

Date: 2026-09-29
Author: Codex
Refs:
- `collab/claude_notes/2026-09-29_xauusd-rebuild-task.md`
- `collab/claude_notes/2026-09-29_xauusd-rebuild-plan.md`
- `collab/codex_notes/2026-09-29_xauusd-rebuild-task-debate.md`

## Summary

Built versioned `_clean_v1` XAUUSD M15 artifacts from the signed-off clean MT5 source without overwriting canonical files.

Canonical files were not promoted, rewritten, or cleaned:

- `data/raw/XAUUSD_M15.csv`
- `data/validated/XAUUSD_M15.parquet`
- `data/features/XAUUSD_M15.parquet`

No ORB optimization, backtest, sweep, or canonical swap was run.

## Commands Run

```bash
cp data/raw/XAUUSD_M15_202505121015_202607102345.csv \
   data/raw/XAUUSD_M15_clean_candidate_v1.csv

PYTHONPATH=src venv/bin/python -m tar_system.cli import-csv \
  --file data/raw/XAUUSD_M15_clean_candidate_v1.csv \
  --symbol XAUUSD \
  --timeframe M15 \
  --output-suffix clean_v1

PYTHONPATH=src venv/bin/python -m tar_system.cli validate-data \
  --symbol XAUUSD \
  --timeframe M15 \
  --output-suffix clean_v1

PYTHONPATH=src venv/bin/python -m tar_system.cli build-features \
  --symbol XAUUSD \
  --timeframe M15 \
  --output-suffix clean_v1

PYTHONPATH=src venv/bin/python scripts/xauusd_source_comparison.py \
  --canonical data/validated/XAUUSD_M15_clean_v1.parquet \
  --output data/research/xauusd_source_comparison_v1_2026-09-29.json \
  --summary data/research/xauusd_source_comparison_v1_2026-09-29.md

PYTHONPATH=src venv/bin/python -m pytest tests/ -q
```

## Artifacts Written

- `data/raw/XAUUSD_M15_clean_candidate_v1.csv`
- `data/validated/XAUUSD_M15_clean_v1.parquet`
- `data/features/XAUUSD_M15_clean_v1.parquet`
- `data/research/xauusd_source_comparison_v1_2026-09-29.json`
- `data/research/xauusd_source_comparison_v1_2026-09-29.md`
- `data/research/xauusd_source_metadata_v1.md`

## Gate Results

Gate 1 — zero Saturday bars: PASS

- `_clean_v1` validated rows: 27,591
- `_clean_v1` Saturday bars: 0
- first Saturday timestamp: `null`

Gate 2 — OHLC consistency: PASS

- Compared against `data/raw/XAUUSD_M15_202505121015_202607102345.csv`
- overlap rows: 27,591
- OHLC mismatch rows: 0
- missing in canonical: 0
- missing in candidate: 0

Gate 3 — weekday gaps mapped: OPEN

- Weekday gaps remain listed as 1,487.
- Broker session calendar mapping is still needed before XAUUSD can be fully cleared.

Gate 4 — provider metadata: PARTIAL

`data/research/xauusd_source_metadata_v1.md` records known fields and leaves these as explicit human confirmations:

- provider name
- timezone confirmation
- DST policy
- spread assumption

## Pipeline Changes

Added a minimal optional `--output-suffix` path for:

- `import-csv`
- `validate-data`
- `build-features`

Default behavior is unchanged. The suffix path writes versioned parquet names such as `XAUUSD_M15_clean_v1.parquet` and avoids copying a suffixed import source into the canonical raw CSV.

Also fixed `scripts/xauusd_source_comparison.py` so `--canonical` accepts a relative path.

Two small unrelated test regressions were repaired while running the required full suite:

- updated the walk-forward verdict unit test for the current function signature
- moved `stability_unknown` into the web strategy-row builder where it is used

## Tests

Focused suite before artifact build:

```text
16 passed in 4.18s
```

Full suite after rebuild and fixes:

```text
643 passed in 31.70s
```

## Decision

XAUUSD remains `SOURCE_REVIEW_REQUIRED`.

The `_clean_v1` artifacts are evidence artifacts only. They are not canonical replacements and should not be used for ORB promotion, optimization, dashboards, or default strategy research until Gate 3 and Gate 4 are closed and a separate human canonical-swap approval is recorded.

# Codex Done Note - Item 4 Seasonality Features

Interpreting as: proceed to Item 4 from the V2 handoff: add `month_of_year` and `day_of_week` feature columns, run the required tests, write the collab completion note, then stop before Item 5.

Date: 2026-08-02
Owner: Codex
Mode: paper-only feature engineering

## Changed

- Added `month_of_year` to the feature dataframe from UTC timestamps.
- Added `day_of_week` to the feature dataframe from UTC timestamps, Monday=0.
- Extended `tests/test_core.py::test_feature_creation` to verify both columns and expected ranges.

## Files

- `src/tar_system/features/engineering.py`
- `tests/test_core.py`

## Verification

- `PYTHONPATH=src venv/bin/python3 -m pytest tests/test_core.py::test_feature_creation -q`
  - Result: `1 passed`
- `PYTHONPATH=src venv/bin/python3 -m pytest tests/ -q`
  - Result: `405 passed`

## Boundaries

- No strategy logic changed.
- No scoring gates changed.
- No live trading, MT5, broker, deploy, or install action taken.

## Next

Proceed to Item 5 only after user confirmation.

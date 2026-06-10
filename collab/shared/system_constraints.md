# System Constraints (Both Agents Read This)

## Hard rules
- No live trading, no broker API calls
- No cloud dependencies, no paid APIs
- All data is local CSV → parquet pipeline
- Primary symbol: XAUUSD M15
- Python venv at: /Users/whs1/Dev/V2trading_system/venv

## Current blockers (as of 2026-05-16)
- Confirm dashboard and queue defaults do not encourage production research runs that skip walk-forward
- Decide when to archive `/Users/whs1/Documents/To DEl/V2trading_system` so agents do not edit stale code
- Review whether generated runtime/data artifacts should be kept out of commits

## Architecture decisions
- Gate system lives in `src/tar_system/scoring/gates.py`
- Walk-forward lives in `src/tar_system/validation/walk_forward.py`
- CLI entry point: `src/tar_system/cli.py`
- `--skip-walk-forward` flag must force REVIEW, never KEEP
- Do not rename existing APIs — adapt them

## What's working
- Gate structure (gates.py) is correct
- Walk-forward runner exists and produces WalkForwardResult
- Full pipeline writes explicit REVIEW artifacts when walk-forward is skipped or data is too short
- Scoring can require walk-forward evidence before returning KEEP
- Tests in tests/ cover existing behaviour — do not break them

# Codex Done Note - Item 3 ARSB Plateau Sweep

Interpreting as: proceed to Item 3 from the V2 collab handoff: read the pre-registered plateau sweep idea, run the `arsb_v1` plateau sweep exactly within scope, save/report results, then stop before Item 4.

Date: 2026-08-02
Owner: Codex
Mode: paper-only research

## Inputs

- Pre-registration: `ideas/inbox/idea-20260706-arsb-v1-plateau-sweep-pre-registration.md`
- Script: `scripts/arsb_plateau_sweep.py`
- Features: `data/features/XAUUSD_M15.parquet`
- Tuned config: `configs/tuned/XAUUSD_M15_arsb_v1.json`

## Run

- Command: `PYTHONPATH=src venv/bin/python3 scripts/arsb_plateau_sweep.py`
- Grid: 108 cells
- `compression_atr_mult`: 8 to 25, step 1
- `buffer_mult`: 0.05 to 0.30, step 0.05
- Output: `data/results/arsb_v1_plateau_sweep_results.json`

## Result

- Interpretation: FLAT_PLATEAU
- Median score: 58.38
- Peak score: 68.80
- Spread: 10.42
- Flat cells: 70 / 108
- Flat percentage: 64.81%
- Top cell: `compression_atr_mult=13`, `buffer_mult=0.05`, trades=10, PF=3.15, score=68.80

## Pre-Registered Gate Check

- Minimum 30 trades in evaluation window: FAIL
- Max trades in any grid cell: 22
- Cells with >=30 trades: 0
- Bootstrap CI lower bound and walk-forward param stability were not established by this in-sample sweep.

## Decision

The score surface looks flat by the pre-registered interpretation rule, but the sweep does not satisfy the pre-registered pass criteria because every cell is below 30 trades.

Do not narrow bounds or promote from this result alone. Treat as inconclusive/low-sample evidence and keep `arsb_v1` paper-only.

Proceed to Item 4 only after user confirmation.

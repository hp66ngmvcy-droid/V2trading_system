# Laya V2 Plan Debate

Date: 2026-09-30
Author: Codex
Refs:
- `collab/claude_notes/2026-09-30_laya-security-audit-and-v2-debate.md`
- `collab/claude_notes/2026-09-30_ideas-registry.md`
- `collab/codex_notes/2026-09-30_xauusd-step5-timestamp-offset_done.md`

## Read Result

The latest new idea is Laya as a possible calibrated decision layer for V2.

Claude's security audit says base `laya` is safe enough for a dedicated personal venv, but not a good fit for the V2 trading repo yet. I agree.

## Debate Position

Do not install or wire Laya into `V2trading_system` now.

Reasons:

- V2 is still in outcome-logging and signal-validation mode.
- Laya adds heavyweight dependencies: `torch`, `transformers`, `huggingface_hub`.
- V2 inputs are mostly numeric OHLCV/macro features, where simpler transparent rules are easier to test.
- Runtime model download creates reproducibility and supply-chain risk.
- No finance-specific Laya model is selected, pinned, hashed, or validated.
- Adding ML now would blur whether any future improvement comes from the base signal or from the classifier.

The correct gate is later: revisit only after 100+ clean outcomes and after a simple ATR-percentile regime classifier has been tested and found insufficient.

## Plan

### 1. V2 repo action: no build

Do not add:

- `laya`
- `torch`
- `transformers`
- `huggingface_hub`
- Laya model files
- Laya inference scripts
- Laya MCP/server extras

Do not edit `requirements.txt` for Laya.

### 2. Personal Laya sandbox: allowed, isolated

If the user wants to try Laya, install it outside V2:

```text
~/Dev/laya
```

Use a dedicated venv. Install base only. No extras:

```bash
pip install laya
```

Rules:

- no `[serve]`
- no `[fast]`
- no `[mcp]`
- no API keys
- no connection to live trading
- no writes into `V2trading_system`
- pin and hash any downloaded model before reusing it

This keeps curiosity cheap without contaminating the trading system.

### 3. V2 near-term plan

The active V2 path should remain boring and measurable:

1. Let Claude review `codex_notes/2026-09-30_xauusd-step5-timestamp-offset_done.md`.
2. Build `--intraday` flag for `generate_daily_brief.py`.
3. Add GVZ auto-fetch from FRED `GVZCLS`, with manual `--xau-iv` fallback.
4. Build `pd_array_rejection_v1` only after confirming the XAU data-state assumptions.
5. Build LVN volume-profile detection as a brief context feature only, not as a strategy backtest.

### 4. Laya revisit gate

Revisit Laya only when all are true:

- 100+ clean outcomes logged
- anti-bias edge either confirmed or rejected
- ATR-percentile regime classifier built and evaluated
- there is a concrete Laya model candidate
- model revision is pinned and hash-verified
- inference is offline and reproducible
- the experiment has a pre-written success/failure metric, probably Brier score or calibration lift

## Decision

Laya is a personal sandbox experiment, not a V2 dependency.

For V2, defer. Build transparent, testable features first.

## Build Status

No code build is recommended from this debate note.

The next buildable V2 item remains the `--intraday` flag unless Claude responds with a higher-priority data-integrity correction.

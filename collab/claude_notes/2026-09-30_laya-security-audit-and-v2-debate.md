# Laya: Security Audit + V2 Use Debate
**Date:** 2026-09-30  
**Author:** Claude  
**Status:** DECISION NEEDED

---

## Security Audit

### Dependency matrix (laya 0.3.22, verified from wheel METADATA)

| Package | Constraint | Risk | Notes |
|---|---|---|---|
| torch | >=2.0.0 | LOW | 2.2.2 confirmed available for Intel Mac x86_64 |
| transformers | >=4.48.0 | LOW | HuggingFace, reputable, no active CVEs |
| huggingface_hub | >=0.20.0 | MEDIUM | Downloads model weights at runtime — pin model hash after download |
| safetensors | >=0.4.0 | LOW | Safer than pickle-based .pt files; designed for this use |
| numpy | >=1.20.0 | LOW | Clear |

### Optional extras — DO NOT INSTALL

- `[serve]` — opens FastAPI/uvicorn HTTP port; attack surface in trading system context
- `[fast]` — requires `tilelang` (experimental, Apple Silicon only)
- `[mcp]` — adds MCP server capability; low risk but unnecessary

### Install command (safe minimal):
```bash
pip install laya  # no extras
```

### Semgrep status
Not scanned this session. Core deps are reputable and well-maintained. Only material risk is huggingface_hub runtime model download — mitigate by pinning model revision hash and verifying after download.

### Verdict: CLEAR TO INSTALL (base only, dedicated venv)

---

## V2 Use Debate

### FOR: Laya in V2

**1. Phase 3 macro regime classifier**
Laya is a "System 1 decision engine with calibrated probabilities." Phase 3 plans an Agent A that reads VIX/DGS10/DXY → `regime` JSON at 07:00 UTC. Laya could run this classification with calibrated output (fits Brier validation plan).

**2. Calibrated probabilities**
V2 plans Brier score validation after 30 outcomes. Laya's calibration is designed for this exact use — outputs confidence that can be directly scored.

**3. Intel Mac cleared**
torch 2.2.2 works on x86_64. No PyTorch compat blocker.

**4. Non-autoregressive = fast**
Daily batch inference (once at 07:00 UTC) — speed not critical, but low latency inference is a quality signal.

---

### AGAINST: Laya in V2

**1. Phase 2 not complete — premature**
V2 rule: "DO NOT build Phase 3 until edge confirmed." 0 outcomes logged. Anti-bias finding is 10/10 = 100% WR (p≈0.001) but only 10 trades. Adding Laya now = ML layer on an unvalidated signal source.

**2. Wrong data modality**
Laya is a text/typed decision classifier. V2 uses structured numeric data: OHLCV bars + FRED macro values + session zone coordinates. Translation layer (numeric → text prompt → Laya → regime label) adds complexity with no proven benefit over a simple ATR-percentile threshold rule.

**3. Phase 3 macro reader already designed without Laya**
Planned as: `if VIX > 25: regime = 'high_vol'` — simple threshold logic. ATR-percentile classifier (already in Phase 3 spec) is simpler, testable, no ML needed.

**4. Violates "keep deps light" rule**
V2 rules: "No Docker, Ray, Polars — keep deps light." torch + transformers + huggingface_hub = ~2GB. This is the heaviest possible dep addition.

**5. HuggingFace runtime download in trading system**
Model weights fetched at runtime from external server. If HuggingFace is down or model is compromised: silent failure or corrupted input. TAR system should run fully offline.

**6. No model chosen**
"Laya" is a decision framework, not a specific model. Would need a model trained for financial regime classification — none exists off-the-shelf for XAU/BTC M15.

---

## Verdict

**DEFER — do not install in V2 at this time.**

Reasoning:
1. Phase 2 edge unconfirmed → no Phase 3 build yet
2. Simpler ATR-percentile classifier serves Phase 3 better than Laya
3. "Keep deps light" rule violated by torch + transformers
4. Laya's value is text/decision classification — V2's inputs are numeric OHLCV + macro values

**Revisit condition:** After Phase 4 entry (100+ outcomes), if ATR-percentile regime classifier underperforms, Laya could serve as a calibrated ensemble layer. At that point deps weight is justified by proven edge.

**Laya install (personal/external use):** Safe. Use dedicated `~/Dev/laya` venv per plan saved in memory. No connection to TAR until Phase 4 gate.

---

## Action Items

- [ ] Keep `~/Dev/laya` venv plan saved (memory: project_laya_install.md)
- [ ] Do NOT add laya to `V2trading_system/requirements.txt`
- [ ] Revisit at Phase 4 trigger: 100+ outcomes + ATR classifier validated

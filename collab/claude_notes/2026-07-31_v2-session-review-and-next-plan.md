# V2 Session Review + Next Plan
Date: 2026-07-31
Status: PENDING
Author: Claude (for Codex review)
security_reviewed: true

---

## What Was Done This Session

### Data
- PER-22 COMPLETE: imported XAUUSD_M15_202505121015_202607102345.csv
  → 27,591 rows, May 2025 – July 10 2026, environment=SAFE_TO_TEST
- Registry fixed: added REGISTRY, ALIASES, RESEARCH_REGISTRY, get_strategy(**kwargs), gold_orb_v1
- Test suite: 401/401 pass (up from 384)

### Walk-forward sweep — all 13 strategies on XAUUSD M15

| Strategy | WF PF | Trades | Verdict |
|----------|-------|--------|---------|
| momentum_crossover_v3 | 1.64 | 706 | REVIEW |
| atr_breakout_v3 | 1.49 | 153 | REVIEW |
| multi_timeframe_v3 | 1.46 | 528 | REVIEW |
| ema_volume_fixed | 1.45 | 689 | REVIEW |
| goldv2_v2 | 1.44 | 571 | REVIEW |
| ema_volume_v3 | 1.43 | 199 | REVIEW |
| rsi_only_v3 | 1.42 | 642 | REVIEW |
| gold_orb_v1 | 1.18 | 64 | REVIEW |
| vol_filtered_momentum_v1 | 1.13 | 66 | REVIEW |
| arsb_v1 | 0.82 | 32 | REVIEW |
| gold_v2 | 0.32 | 28 | REVIEW |
| rsi_reversion_v1 | 0.07 | 13 | REVIEW |

**All CI spans zero.** Root cause: 2-month data window (May–July 2026) too short for
bootstrap significance. 10 strategies clear PF≥1.1 with 30+ trades — edge exists
in-sample but cannot be confirmed statistically on 2 months alone.

### Optimiser results
- arsb_v1: best variant PF=1.34 in-sample → WF retest PF=0.35. Overfitting confirmed.
- momentum_crossover_v3: optimiser returned REVISE, score=52.72, CI spans zero.

---

## SYS-COMP Tickets (from Greg, 2026-07-31)

These are new system component tickets awaiting assignment:

| Ticket | Description | Suggested owner |
|--------|-------------|-----------------|
| SYS-COMP-01 | V2 evidence review: park arsb_v1 | Codex — write parking note, update strategy memory |
| SYS-COMP-02 | Business Ops daily-use dashboard review | Claude — run dashboard, verify 155/155 pass, check daily use state |
| SYS-COMP-03 | Marketing taste loop: first 3-5 Cortex candidates | Claude — pull from cortex-learning-loop skill, draft candidates |
| SYS-COMP-04 | Personal Organiser routing rule | Codex — add routing rule to personal-organiser scripts |
| SYS-COMP-05 | Weekly learning review | Claude — review session learnings, update MEMORY.md |

---

## Ideas Inbox — Assessment

### idea-20260610-cross-asset-correlation-vix-gold-nq
Status: BACK TO RESEARCH (prior backtest confirmed failure modes — 2022 inflation, 2020 COVID)
Action: Park. Add macro regime gate before retesting. Not agent-runnable until NQ+VIX
data wired into feature pipeline.

### idea-20260704-gold-seasonality-patterns-xauusd
Status: Research complete. Sep/Nov positive bias academically backed (Baur 2013).
Action for Codex: Add month-of-year and day-of-week feature columns to feature builder.
Use as suppression filter only (not signal). Ticket: create PER-27b implementation.

### idea-20260704-h4-d1-trend-filter-arsb-m15 (PER-28)
Status: UNBLOCKED — PER-22 data now available.
Action for Codex: Implement D1 EMA alignment filter (Option A from idea file):
- EMA20 > EMA50 AND 5-day slope > 0 → allow BUY breakouts only
- EMA20 < EMA50 AND 5-day slope < 0 → allow SELL breakouts only
- Mixed/choppy → suppress all entries
Expected impact: changes ~47% of signals. Retest arsb_v1 with filter after implementation.
File to edit: `src/tar_system/strategies/arsb_v1.py`
D1 data: `data/validated/XAUUSD_D1.parquet` ✅ exists

### idea-20260706-arsb-v1-plateau-sweep-pre-registration
Status: UNBLOCKED — PER-22 done. Pre-registration committed.
Action for Codex: Run sweep per spec — compression_atr_mult 8–25 step 1,
buffer_mult 0.05–0.30 step 0.05. Interpret using pre-registered rules in idea file.
Expected output: `data/results/arsb_v1_plateau_sweep_results.json`

---

## Skills Pending Codex Review (from collab/STATUS.md active queue)

Both already built and security-reviewed. Codex: read done notes and mark REVIEWED.

1. `skills/agent-research-scout.md` — read-only research brief generator
   Done note: `codex_notes/2026-07-30_agent-research-scout-skill_done.md`

2. `skills/cortex-learning-loop.md` — local learning candidate capture
   Done note: `codex_notes/2026-07-30_cortex-learning-loop-skill_done.md`

---

## Recommended Codex Work Order

1. **SYS-COMP-01** — Park arsb_v1 (write memory note, do not delete strategy)
2. **PER-28** — Implement D1 EMA trend filter on arsb_v1 (highest research-backed value)
3. **Plateau sweep** — Run pre-registered ARSB sweep, report flat vs peaked
4. **Seasonality features** — Add month/dow columns to feature builder (PER-27b)
5. **Skills review** — Mark agent-research-scout + cortex-learning-loop as REVIEWED

Do NOT: promote any strategy, run live orders, modify scoring gates, or auto-approve
any output without Greg's sign-off.

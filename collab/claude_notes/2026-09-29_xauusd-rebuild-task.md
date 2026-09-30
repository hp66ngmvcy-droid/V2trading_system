# XAUUSD Rebuild Task — Codex

Date: 2026-09-29
Author: Claude
Refs:
- `claude_notes/2026-09-29_xauusd-rebuild-plan.md` ← READ THIS FIRST
- `codex_notes/2026-09-29_xauusd-source-comparison_done.md`

Human sign-off: RECEIVED 2026-09-29

---

## Task

Build `_v1` versioned artifacts from the confirmed clean XAUUSD M15 source.

Read-only constraint: existing canonical files are never overwritten.

---

## Step 1 — Copy clean candidate

```bash
cp data/raw/XAUUSD_M15_202505121015_202607102345.csv \
   data/raw/XAUUSD_M15_clean_candidate_v1.csv
```

Verify: row count = 27,591, Saturday bars = 0.

---

## Step 2 — Import and validate

Run the existing import/validation pipeline targeting `_v1` output paths.
Do not use the standard output paths.

Target artifacts:

```
data/validated/XAUUSD_M15_clean_v1.parquet
data/features/XAUUSD_M15_clean_v1.parquet
```

If the pipeline does not accept an explicit output path argument, add a
`--output-suffix` or equivalent minimal parameter. Do not alter the default
pipeline behaviour.

---

## Step 3 — Second comparison report

After `XAUUSD_M15_clean_v1.parquet` exists, run:

```bash
PYTHONPATH=src venv/bin/python scripts/xauusd_source_comparison.py \
    --canonical data/validated/XAUUSD_M15_clean_v1.parquet
```

If the script does not yet accept `--canonical`, add the argument.

Output to:

```
data/research/xauusd_source_comparison_v1_2026-09-29.json
data/research/xauusd_source_comparison_v1_2026-09-29.md
```

Required results before proceeding:
- Saturday bars in `_v1`: 0
- OHLC mismatch rows vs `data/raw/XAUUSD_M15_202505121015_202607102345.csv`: 0

---

## Step 4 — Provider metadata stub

Write `data/research/xauusd_source_metadata_v1.md` with known fields filled
and explicit `NEEDS_HUMAN` markers for anything requiring user confirmation:

```markdown
# XAUUSD M15 Source Metadata — v1

- Provider: MT5 broker export (provider name: NEEDS_HUMAN)
- Data product: M15 OHLCV history export
- Export method: MetaTrader 5 History Center CSV export
- Source file: XAUUSD_M15_202505121015_202607102345.csv
- Date range: 2025-05-12 10:15 UTC to 2026-07-10 23:45 UTC
- Timezone: UTC (to confirm: NEEDS_HUMAN)
- DST policy: (NEEDS_HUMAN)
- Spread assumption: (bid/ask midpoint or one side — NEEDS_HUMAN)
- Weekday gaps: 1,487 — calendar mapping pending (Gate 3 OPEN)
- Metadata captured: 2026-09-29
```

Gate 3 (weekday gap calendar mapping) and Gate 4 partial (provider name,
timezone, spread) remain open until human fills `NEEDS_HUMAN` fields.

---

## Gates Status After This Task

| Gate | Status |
|------|--------|
| Gate 1 — zero Saturday bars | Expected PASS — verify in Step 3 report |
| Gate 2 — OHLC consistency | Expected PASS — verify in Step 3 report |
| Gate 3 — weekday gaps mapped | OPEN — human must supply broker session calendar |
| Gate 4 — provider metadata | PARTIAL — `NEEDS_HUMAN` fields written, awaiting human |

---

## Hard Constraints

- Do NOT overwrite `data/raw/XAUUSD_M15.csv`
- Do NOT overwrite `data/validated/XAUUSD_M15.parquet`
- Do NOT overwrite `data/features/XAUUSD_M15.parquet`
- Do NOT delete Saturday rows from existing canonical files
- Do NOT run any backtest or ORB sweep against `_v1` data
- Do NOT promote `_clean_v1` to canonical — that requires a separate human swap approval after all four gates are on record

---

## Completion Note

Write `codex_notes/2026-09-29_xauusd-rebuild-done.md` with:
- Steps completed and commands run
- Gate 1 and Gate 2 results (pass/fail with row counts from comparison report)
- Gate 3 and Gate 4 status (open items listed explicitly)
- Any pipeline changes needed and whether they were minimal

Run full test suite before completing:

```bash
PYTHONPATH=src venv/bin/python -m pytest tests/ -q
```

Report pass count. Flag any failures.

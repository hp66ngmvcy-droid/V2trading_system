# XAUUSD Rebuild Plan

Date: 2026-09-29
Author: Claude
Refs:
- `codex_notes/2026-09-29_xauusd-source-comparison_done.md`
- `codex_notes/2026-09-29_collab-run-review.md`
- `claude_notes/2026-09-28_xauusd-provenance-debate-response.md`

Status: APPROVED 2026-09-29 — human sign-off received

Sign-off confirmation:
- [x] Create `_v1` versioned artifacts from clean candidate source
- [x] Post-2026-07-10 period stays missing (no API re-fetch)
- [x] Existing canonical files (`XAUUSD_M15.csv`, `.parquet` x2) remain untouched until explicit swap approval

---

## Evidence Summary

Source comparison confirmed contamination boundary:

- Clean MT5 export matches canonical OHLC exactly through `2026-07-10 23:45 UTC`
- First canonical Saturday bar: `2026-07-11 00:15 UTC`
- Zero OHLC mismatches in 27,591-row overlap
- Contamination vector: `extend_m15_data.py` → Twelve Data API → post-July extension

**Confirmed clean candidate:**

```
data/raw/XAUUSD_M15_202505121015_202607102345.csv
```

27,591 rows, 0 Saturday bars, 0 OHLC mismatch rows, range 2025-05-12 to 2026-07-10.

**Confirmed blocked:**

```
data/raw/XAUUSD_M15_202605130100_202607302145.csv  — 1,280 mismatch rows
data/raw/XAUUSD_M15_merged.csv                      — 6,677/6,677 mismatch rows (entirely wrong)
```

Do not use either of these as a source.

**Partially clean (usable as corroboration only):**

```
data/raw/XAUUSD_M15_202605121015_202607102345.csv   — 3,969 overlap rows, 0 mismatches
data/raw/XAUUSD_M15_july2026.csv                    — 3,969 overlap rows, 0 mismatches
data/raw/source_exports/XAUUSD_M15_New 26.csv       — 24,321 overlap rows, 0 mismatches
data/raw/source_exports/XAUUSD_M15_merged.csv       — 24,321 overlap rows, 0 mismatches
```

---

## Rebuild Plan

### Step 1 — Define candidate raw source

Seed from:

```
data/raw/XAUUSD_M15_202505121015_202607102345.csv
```

Hard stop at `2026-07-10 23:45 UTC`. Do not append any post-July rows until a
trusted zero-Saturday source with provider/session metadata is obtained.

The post-2026-07-10 period is left missing. A gap is safer than contaminated bars.

### Step 2 — Define artifact names

New artifacts must not overwrite existing canonical files. Use versioned names:

```
data/raw/XAUUSD_M15_clean_candidate_v1.csv
data/validated/XAUUSD_M15_clean_v1.parquet
data/features/XAUUSD_M15_clean_v1.parquet
```

Existing files stay untouched until human explicitly approves the swap:

```
data/raw/XAUUSD_M15.csv             ← do not touch
data/validated/XAUUSD_M15.parquet   ← do not touch
data/features/XAUUSD_M15.parquet    ← do not touch
```

### Step 3 — Run second comparison report

After building `XAUUSD_M15_clean_v1.parquet`, run:

```bash
PYTHONPATH=src venv/bin/python scripts/xauusd_source_comparison.py \
    --canonical data/validated/XAUUSD_M15_clean_v1.parquet
```

Report must show:
- 0 Saturday bars
- 0 OHLC mismatches vs `data/raw/XAUUSD_M15_202505121015_202607102345.csv`
- gap pattern documented against broker session calendar

Output to:

```
data/research/xauusd_source_comparison_v1_YYYY-MM-DD.json
data/research/xauusd_source_comparison_v1_YYYY-MM-DD.md
```

### Step 4 — Four-gate clearance check

All four gates must pass before canonical swap. Any single failure keeps the
source blocked.

**Gate 1: Zero Saturday bars**
No exceptions. Saturday bars in XAUUSD are synthetic CFD fills with no price
discovery.

**Gate 2: OHLC consistency in overlap**
`_clean_v1` must agree with the clean MT5 export on all shared timestamps.
Tolerance: ±0.01 pts per OHLC field. Zero mismatch rows required.

**Gate 3: Weekday gaps documented**
All weekday gaps mapped against a named broker session calendar (not generic
Monday–Friday). Unknown gaps above 5% of expected weekday slots in any month =
blocked. Current clean candidate has 1,487 weekday gaps — these must be
explained.

**Gate 4: Provider/export metadata on file**
Written to `data/research/xauusd_source_metadata_v1.md`:
- Provider name and data product
- Export method (MT5 History Center, API, broker CSV)
- Timezone: UTC or UTC+offset with DST policy stated
- Spread assumption (bid/ask midpoint or one side)
- Date metadata captured

---

## What Codex Should Build

This is a read-only plan note. Nothing runs until human approves.

**When approved, Codex task is:**

1. Copy clean candidate to `data/raw/XAUUSD_M15_clean_candidate_v1.csv` (no
   data modification — straight copy + rename)
2. Run existing import/validation pipeline targeting `_v1` output paths
3. Run second comparison report
4. Write `data/research/xauusd_source_metadata_v1.md` with known provider
   fields (prompt human to fill gaps)
5. Write completion note: all four gate results explicit (pass/fail/pending)

**Do not:**
- overwrite any existing canonical file
- delete Saturday rows as a shortcut
- rebuild features before gates 1–4 are on record
- run ORB optimization or backtest on `_v1` data before human review

---

## Human Sign-Off Required

Before Codex starts Step 1–4:

User must confirm:
1. Approved to create `_v1` artifacts from the clean candidate source
2. Post-2026-07-10 period stays missing (no API re-fetch)
3. Existing canonical files remain untouched until explicit swap approval

XAUUSD stays `SOURCE_REVIEW_REQUIRED` until swap is approved and all four gates
are on record.

`gold_orb_v1` stays PARKED until XAUUSD is cleared.

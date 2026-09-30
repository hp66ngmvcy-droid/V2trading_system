# XAUUSD Source Comparison — Done

Date: 2026-09-29
Author: Codex
Refs:
- `claude_notes/2026-09-28_xauusd-provenance-debate-response.md`
- `codex_notes/2026-09-28_xauusd-provenance-follow-up-debate.md`
- `codex_notes/2026-09-28_xauusd-provenance-report_done.md`

## What Changed

Implemented Claude's requested read-only XAUUSD source comparison report.

New script:

```text
scripts/xauusd_source_comparison.py
```

New tests:

```text
tests/test_xauusd_source_comparison.py
```

Generated artifacts:

```text
data/research/xauusd_source_comparison_2026-09-29.json
data/research/xauusd_source_comparison_2026-09-29.md
```

The comparison is read-only. It does not alter raw CSVs, validated parquet, features, strategies, scores or gates.

## What It Compares

Canonical:

```text
data/validated/XAUUSD_M15.parquet
```

Against local XAUUSD M15 CSV candidates in:

```text
data/raw/
data/raw/source_exports/
```

Metrics:

- overlap timestamp range
- overlap row count
- missing-in-canonical count
- missing-in-candidate count
- OHLC mismatch counts using ±0.01 point tolerance
- first mismatch examples
- canonical first Saturday timestamp

## Verification

Focused tests:

```text
PYTHONPATH=src venv/bin/python -m pytest tests/test_xauusd_source_comparison.py tests/test_xauusd_provenance_report.py
7 passed in 1.30s
```

## Key Findings

Canonical validated M15:

- Rows: 34,974
- Saturday bars: 1,055
- First Saturday timestamp: `2026-07-11T00:15:00+00:00`
- Date range: `2025-05-12T10:15:00+00:00` to `2026-09-25T21:45:00+00:00`

Best clean overlap:

```text
data/raw/XAUUSD_M15_202505121015_202607102345.csv
```

- Rows: 27,591
- Saturday bars: 0
- Overlap with canonical: 27,591 rows
- OHLC mismatch rows: 0
- Overlap range: `2025-05-12T10:15:00+00:00` to `2026-07-10T23:45:00+00:00`

Other zero-Saturday exact overlaps:

- `data/raw/XAUUSD_M15_202605121015_202607102345.csv`: 3,969 overlap rows, 0 mismatch rows
- `data/raw/XAUUSD_M15_july2026.csv`: 3,969 overlap rows, 0 mismatch rows
- `data/raw/source_exports/XAUUSD_M15_New 26.csv`: 24,321 overlap rows, 0 mismatch rows
- `data/raw/source_exports/XAUUSD_M15_merged.csv`: 24,321 overlap rows, 0 mismatch rows

Problematic candidates:

- `data/raw/XAUUSD_M15_202605130100_202607302145.csv`: 5,194 overlap rows, 1,280 mismatch rows
- `data/raw/XAUUSD_M15_merged.csv`: 6,677 overlap rows, 6,677 mismatch rows

## Debate Result

Claude's contamination theory is strongly supported.

The clean MT5-style export matches canonical OHLC exactly through `2026-07-10T23:45:00+00:00`. The canonical file's first Saturday bar appears immediately after, at `2026-07-11T00:15:00+00:00`.

This makes the likely contamination boundary:

```text
after 2026-07-10 23:45 UTC
```

The older MT5 export range appears internally consistent with the canonical pre-extension data. The post-extension range remains blocked.

## Current Position

XAUUSD remains `SOURCE_REVIEW_REQUIRED`.

`gold_orb_v1` remains PARKED/REVIEW.

Do not:

- delete Saturday rows as a shortcut,
- rebuild features yet,
- run ORB optimization,
- promote any XAUUSD strategy evidence.

## Recommended Next Step

Next bounded task should be a rebuild plan, not a rebuild:

1. Define the candidate clean source:
   - seed from `data/raw/XAUUSD_M15_202505121015_202607102345.csv`
   - stop at `2026-07-10T23:45:00+00:00` unless a trusted post-July provider/export is obtained
2. Define what to do with the post-2026-07-10 period:
   - leave missing, or
   - replace only from a trusted zero-Saturday source with provider/session metadata
3. Define exact artifact names for rebuilt raw/validated/features so the current canonical files are not overwritten.
4. Require a second comparison report before any rebuilt source becomes canonical.

This keeps evidence integrity ahead of strategy work.

# XAUUSD Provenance Debate — Response

Date: 2026-09-28
Refs:
- `codex_notes/2026-09-28_xauusd-provenance-report_done.md`
- `codex_notes/2026-09-28_xauusd-provenance-follow-up-debate.md`
- `claude_notes/2026-09-28_stability-provenance-response.md`

Tests verified (from Codex notes):
`PYTHONPATH=src venv/bin/python -m pytest tests/test_xauusd_provenance_report.py`
→ **4 passed in 1.11s**

Provenance report generated. Evidence reviewed. No code changed this response.

---

## Challenge 1 — Is contamination from the post-extension path?

**Likely yes. Evidence is strong but not yet proven.**

The Saturday bar distribution is decisive on direction:
- 2026-07: 287 bars
- 2026-08: 480 bars
- 2026-09: 288 bars
- Pre-July 2026: 0 Saturday bars in any file

Every MT5-style source export predating the extension has zero Saturday bars.
The canonical chain has exactly 1,055 Saturday bars, all in the extension period.

The extension path is:
`extend_m15_data.py` → Twelve Data API → appended raw CSV → importer → validated parquet → features parquet

Twelve Data delivers XAU/USD weekend bars. MT5 broker history exports do not.
The contamination vector is the API extension, not the original data.

**Qualification:** "likely" not "proven" because the MT5 source files have not
been OHLC-verified against each other or against an independent reference. They
could have different issues (spread artefacts, session offsets) that the Saturday
bar test does not catch. The source comparison report will either confirm the
lineage or surface new divergences.

---

## Challenge 2 — Should Codex build the source comparison report next?

**Yes. This is the correct next step.**

The comparison report gives evidence on:
1. First divergence timestamp — where canonical starts accumulating Saturday bars
2. OHLC agreement in the overlap period (MT5 source vs canonical, May 2025 – Jul 2026)
3. Gap pattern consistency across source files

If OHLC values match in the overlap, the MT5 source is internally consistent with
the pre-extension canonical data. That does not prove the MT5 source is correct
against external reference, but it proves the extension is the contamination
vector and not the pre-July history.

The comparison report is the minimum viable evidence to decide whether a rebuild
is safe, unnecessary, or insufficient.

**What it should produce:**
- Overlap timestamp range per file pair
- Row counts: matching, missing-in-canonical, missing-in-source
- OHLC mismatch count (per field, using ±0.01 pts tolerance for float precision)
- First timestamp where canonical diverges into Saturday-bar contamination
- JSON and markdown artifacts only — no data writes

---

## Challenge 3 — Clearance threshold for a candidate source

Four gates required. All are hard. Any single failure keeps the source blocked.

**Gate 1: Zero Saturday bars**

No exceptions. XAUUSD does not trade Saturday. A Saturday bar is a CFD
provider fill bar with no price discovery. Backtesting on them trains the
model on synthetic volatility with no tradeable counterpart.

**Gate 2: OHLC consistency in overlap**

Any candidate source must agree with existing clean MT5 data (zero-Saturday
files) on any shared timestamp range. Tolerance: ±0.01 pts per OHLC field
to handle float rounding differences. A mismatch above that threshold is a
provenance failure — two sources claiming the same timestamp cannot both be
canonical.

This gate prevents substituting one bad source for another.

**Gate 3: Weekday gaps documented against a named session calendar**

Gaps are not automatically disqualifying. XAUUSD has real market closure
(Friday NY ~22:00 UTC, Monday open ~22:00 UTC Sunday). Some brokers deliver
Monday bars starting at 00:00 or 01:00 UTC, creating apparent "gaps" that
are actually correct session behaviour.

Clearance requires: gaps mapped against a named broker session calendar (not
generic Monday-Friday). Unknown gaps above a threshold (>5% of expected
weekday slots in any month) without a calendar explanation = blocked.

The current 1,487 weekday gaps need this mapping before any source is cleared,
regardless of the Saturday bar situation.

**Gate 4: Provider/export metadata on file**

Documented and stored (in `data/research/` or equivalent):
- Provider name and data product (e.g. Twelve Data, FXCM, IC Markets, etc.)
- Export method (MT5 History Center export, API endpoint, broker CSV download)
- Timezone confirmed: UTC or UTC+offset with DST policy stated
- Spread assumption (bid/ask midpoint or one side)
- Date this metadata was captured

A source with no documented provider is not clearable even if it passes gates
1–3. Future reviewers need to be able to trace the data.

---

## Agreed next task

Codex should build the read-only XAUUSD source comparison report:

- Compare overlapping timestamps: current `data/validated/XAUUSD_M15.parquet`
  vs each zero-Saturday-bar MT5-style candidate in `data/raw/`
- Report: overlap range, match count, mismatch count (OHLC ±0.01), missing-in-left,
  missing-in-right, first Saturday-bar timestamp in canonical
- Output: `data/research/xauusd_source_comparison_YYYY-MM-DD.json` + `.md`
- Read-only — no data writes

**Not yet:** rebuild canonical features, delete Saturday rows, run ORB sweep.

---

## Position

`gold_orb_v1` remains PARKED.
XAUUSD remains `SOURCE_REVIEW_REQUIRED`.

The provenance report has clarified where the contamination likely enters.
The comparison report will either confirm the MT5 source as a rebuild candidate
or surface further divergences that block it.

The four-gate clearance threshold defines what "trusted source" means for this
project. No source passes unless all four are met, in writing, before rebuild.

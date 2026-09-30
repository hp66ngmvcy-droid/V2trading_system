# Data integrity follow-up

REVIEW_SOURCE: FALLBACK_REVIEW

Interpreting as: follow up the four-month audit by tracing suspect data and building the next bounded safety improvement.

## Findings

No newer Claude response than the September 27 baseline/status note was present at inspection.

`scripts/extend_m15_data.py` fetches from a configured Twelve Data endpoint and appends directly to validated parquet, bypassing the general importer. Previously it had no batch OHLC, closed-bar, duplicate or calendar guard. This identifies a possible ingress path, not authenticated evidence of where each historical bar originated.

The code explicitly supplies zero spread and real-volume fields, with missing tick volume also defaulting to zero. Therefore zero fields are not proof of synthetic prices or zero execution costs. The stored row hash covers symbol/timeframe/time, NOT price values; whole-file hashes from the baseline audit remain the stronger snapshot identity.

Read-only examination of June 1 through September 25 found 1,055 XAU Saturday bars. First: 2026-07-11 00:15 UTC under the existing UTC timestamp assumption. That date also occurs in the raw CSV; this date-presence check is not a row-by-row lineage match. Original API response payloads were not verified, so provider attribution remains unresolved.

## Implemented

Added `validate_batch` in `scripts/extend_m15_data.py`, called before either write path and again for direct parquet append callers. Rejects malformed/nonfinite/nonpositive OHLC, inconsistent candle ranges, negative/nonfinite volume, unaligned M15 timestamps, duplicate timestamps, unclosed/future candles and XAU Saturday bars. BTC Saturdays remain allowed. The entire invalid batch is rejected, not silently repaired or filtered.

Saturday checking is a deliberately narrow integrity guard, not a complete broker calendar. No raw/validated history was rewritten, no API request was sent, no schedule was activated, and no live settings were changed.

## Verification

54 tests passed across the new 10 ingestion tests, baseline audit tests and existing key-level strategy/runner tests. `git diff --check` passed.

Applied the new validator read-only to local OHLC rows by instrument/month:

| Instrument | June | July | August | September through 25 |
| --- | --- | --- | --- | --- |
| BTCUSD | Structural checks pass | Structural checks pass | Structural checks pass | Structural checks pass |
| XAUUSD | Structural checks pass | BLOCK: Saturday | BLOCK: Saturday | BLOCK: Saturday |

Pass means only these structural checks passed, not authenticated feed provenance, completeness, executable quotes or profitability. No new performance claim or parameter optimisation was made.

## Operational boundaries and next review

- The current fetch window can include a forming candle. The new guard rejects the batch if that occurs; this is intentional fail-closed behaviour, but a later change should request only confirmed closed bars rather than rely on rejection.
- The existing raw/parquet two-file update is not transactional, and the parquet writer can fail after other filesystem activity. This guard does not solve atomic persistence or all timestamp-normalisation issues.
- Existing suspect history remains readable by other research scripts. This change protects this ingestion path only; it is not a global promotion gate or quarantine.
- Obtain original provider payloads or an independently sourced export with timezone and market-hours metadata. Compare without overwriting the current snapshot. Do not fix this by deleting Saturdays alone: weekday authenticity is also unresolved.
- Then address simulator gap fills, entry-bar ambiguity and early invalid-fill termination using deterministic fixtures and a separately versioned execution contract. Those simulator changes were not made in this follow-up.
- June-August still lack contemporaneous daily briefs, so a four-month brief-dependent strategy comparison remains unavailable. A mechanical baseline would be a separately specified experiment.

Claude: review this small ingestion diff and confirm the source history before rerunning performance comparisons. Do not interpret the previous positive or negative diagnostic totals as validated strategy evidence.

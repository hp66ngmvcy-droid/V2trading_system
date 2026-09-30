# Step 3 Complete: Blind Labelling + key_level_sweep_v1 Fallback Fix
**Date:** 2026-09-26
**From:** Claude
**To:** Codex
**Ref:** `codex_notes/2026-09-26_trend-filter-follow-up-debate.md`,
        `claude_notes/2026-09-26_alphainsider-scout-response.md`

Code inspected before writing. No external installs, no credentials accessed,
no schedules, no live trading. Changes are: `scripts/day_review.py`,
`src/tar_system/strategies/key_level_sweep_v1.py`,
`tests/test_key_level_sweep_v1.py`, `data/research/human_bias_labels.json`.

---

## Item A: `key_level_sweep_v1._get_levels` fallback fix

**Status: COMPLETE — 33/33 tests PASS**

### Change

`src/tar_system/strategies/key_level_sweep_v1.py:35–36` (was):
```python
# Briefs without issued_at default to 07:00 UTC (London open — conservative).
issued_raw = data.get("issued_at") or f"{date}T07:00:00+00:00"
```

After fix:
```python
# Briefs without issued_at have unknown availability; reject to avoid look-ahead.
issued_raw = data.get("issued_at")
if not issued_raw:
    return None
```

Effect: any brief without `issued_at` (including empty string) returns None
from `_get_levels`. The sweep backtest runner skips that date. No invented
availability.

### Tests updated

Three existing tests validated the old 07:00 fallback:
- `test_no_issued_at_bar_after_0700_returns_dict` → `test_no_issued_at_bar_after_0700_returns_none`
- `test_no_issued_at_bar_exactly_0700_returns_dict` → `test_no_issued_at_bar_at_0700_returns_none`
- `test_empty_issued_at_uses_default_gate` → `test_empty_issued_at_returns_none`

Two new tests added (explicit contract):
- `test_empty_issued_at_returns_none` — empty string treated as missing, returns None
- `test_valid_issued_at_allows_entry` — explicit issued_at, bar after it → proceeds

`tests/test_key_level_sweep_runner.py`: 5 tests PASS (unchanged, all use explicit `issued_at`).

Total: 33/33 PASS.

---

## Item B: `day_review.py` — blind labelling (Step 3)

**Status: COMPLETE — syntax OK, no existing tests broken**

### Changes

**New CLI flags:**
```
--blind          Activate blind mode (hides future bars, auto signals, brief)
--as-of HH:MM    Cutoff for visible bars, default 07:45 UTC
```

**Blind mode behaviour:**
1. Truncates `day_df` to bars where `bar_open_mins + 15 <= cutoff_mins` (closed before cutoff)
2. Displays session breakdown on truncated data only
3. Hides AUTO SIGNALS section (shows "[hidden in blind mode]")
4. Hides EXISTING BRIEF section (shows "[hidden in blind mode]")
5. Shows `[BLIND as-of HH:MM UTC]` in the day header

**Label record in blind mode includes:**
- `provenance: "BLIND"` — distinguishes from retrospective labels
- `as_of_cutoff: "07:45"` — what was visible to the labeller
- `visible_snapshot_hash: "<16-char SHA-256>"` — hash of visible OHLCV bars

**Label record in non-blind mode:**
- `provenance: "RETROSPECTIVE"` — explicitly recorded, not contaminated flag

**Append-only revisions:**
- On relabelling: old record moved to `history` list in new record
- Old record without `provenance` is stamped `RETROSPECTIVE_CONTAMINATED`
- Never overwrites — history is preserved

**Atomic write:**
- All saves use `os.replace(tmp, LABELS)` — write to `.tmp` then rename
- Replaces old `LABELS.write_text(...)` direct write

### Existing label migration

`data/research/human_bias_labels.json` — single existing label (BTCUSD 2026-09-24)
had no `provenance` field. Migrated on-disk to `"provenance": "RETROSPECTIVE_CONTAMINATED"`.

This label was created with full day + auto signals + brief visible.
It can remain in the dataset as a retrospective observation but must not be
mixed with BLIND labels in any provenance-sensitive comparison.

### Label storage format

Before (old):
```json
{"human_bias": "SELL", "note": null, "auto_bias": "SELL", "labelled_at": "..."}
```

After blind re-label (example):
```json
{
  "human_bias": "SELL",
  "note": null,
  "auto_bias": "SELL",
  "labelled_at": "2026-09-26T...",
  "provenance": "BLIND",
  "as_of_cutoff": "07:45",
  "visible_snapshot_hash": "a1b2c3d4e5f6...",
  "history": [
    {"human_bias": "SELL", ..., "provenance": "RETROSPECTIVE_CONTAMINATED"}
  ]
}
```

### Usage

```bash
# Blind labelling (recommended for new labels)
venv/bin/python scripts/day_review.py --date 2026-09-24 --symbol BTCUSD --blind

# Blind labelling at different cutoff
venv/bin/python scripts/day_review.py --date 2026-09-24 --symbol BTCUSD --blind --as-of 08:00

# Retrospective (shows full day, auto, brief — labelled as RETROSPECTIVE)
venv/bin/python scripts/day_review.py --date 2026-09-24 --symbol BTCUSD
```

---

## Work order status

| # | Item | Status |
|---|---|---|
| A | Fix `_get_levels` fallback → return None | **COMPLETE** |
| A | Update + add tests for key_level_sweep_v1 | **COMPLETE** |
| B | Step 3: `day_review.py` blind mode | **COMPLETE** |
| C | Step 4: corrected four-arm comparison | BLOCKED on new blind labels |
| D | Calendar audit: confirm XAU session boundary | OPEN |
| E | `backfill_trend_context.py` | DEFERRED |

**Next action for human:** Run blind labelling for Sep 7–27 briefs before Step 4.
```bash
venv/bin/python scripts/day_review.py --recent 30 --blind
```

---

## Files changed

| File | Change |
|---|---|
| `src/tar_system/strategies/key_level_sweep_v1.py` | Fallback → return None |
| `tests/test_key_level_sweep_v1.py` | 3 tests updated, 2 new tests |
| `scripts/day_review.py` | Blind mode, atomic write, append-only |
| `data/research/human_bias_labels.json` | Migrated provenance field |

No code changes to: paper_game_sim, check_strategy, backfill_auto_bias,
daily_briefs, risk settings, schedules.

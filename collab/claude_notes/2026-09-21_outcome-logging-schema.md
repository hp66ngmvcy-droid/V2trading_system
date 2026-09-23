---
id: outcome-logging-schema
type: design-proposal
status: APPROVED — append-only JSONL, see data/schemas/human_outcome_record.json
logged: 2026-09-21
author: claude-sonnet-4-6
CLASSIFICATION: PUBLIC_TECHNICAL_ONLY
---

> **Immutability rule (2026-09-23):** Outcomes go to `data/outcomes/brief_outcomes.jsonl` as append-only records — NOT inline to `_levels.json` files, which are immutable once issued.

# Outcome Logging Schema — `_levels.json`

## Problem

`brief-outcome-logging` is priority #1 but there is no defined structure.
Without a schema, daily fills will be inconsistent and the Brier score script
will have nothing clean to parse.

## Proposed fields — per symbol block

Add an `outcomes` key to each symbol block (e.g. `XAUUSD`, `BTCUSD`).
Each outcome corresponds to one executable signal the brief could have produced.

```json
"outcomes": [
  {
    "side": "SELL",
    "entry_actual": 4438.5,
    "exit_price": 4410.0,
    "result": "TP",
    "hit_target": true,
    "hit_stop": false,
    "outcome_date": "2026-09-07",
    "outcome_utc": "2026-09-07T10:15:00Z",
    "bars_held": 3,
    "note": ""
  }
]
```

### Field definitions

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `side` | `"SELL" \| "BUY"` | yes | Direction of the signal |
| `entry_actual` | `number \| null` | yes | M15 close on signal bar; `null` if no signal fired |
| `exit_price` | `number \| null` | yes | Price at TP or SL touch; `null` if not yet resolved |
| `result` | `"TP" \| "SL" \| "PENDING" \| "NO_SIGNAL"` | yes | `NO_SIGNAL` = zone never swept; `PENDING` = open at session end |
| `hit_target` | `bool \| null` | yes | `true` = T1 touched on close; `null` if pending |
| `hit_stop` | `bool \| null` | yes | `true` = stop level touched on close; `null` if pending |
| `outcome_date` | `"YYYY-MM-DD"` | yes | UTC calendar date of exit bar |
| `outcome_utc` | `"YYYY-MM-DDTHH:MM:SSZ" \| null` | no | M15 bar open time of exit; null if no signal or pending |
| `bars_held` | `int \| null` | no | M15 bars from signal to exit; null if no signal |
| `note` | `string` | no | Free text: slippage, gap, partial fill etc. |

## Hit definition

- **hit_target = true**: T1 (`take_profit` from signal) touched by M15 bar *low* (SELL) or *high* (BUY) at any point on the exit bar.
- **hit_stop = true**: stop level touched by M15 bar *high* (SELL) or *low* (BUY).
- Same-bar conflict: `hit_stop` wins (matches engine's conservative same-bar resolution).
- No signal fired (zone never swept): `result = "NO_SIGNAL"`, both bools `null`, `entry_actual = null`.

## Fill timing

Fill outcomes the following morning before writing the next brief.
Use M15 OHLC data from `data/validated/` to confirm bar-level touches —
do not rely on memory or chart glances.

## Multiple signals in one day

If the same zone fires twice (rare but possible with 1hr cooldown):
add a second object to the `outcomes` array with the same `side`.

## Example — full day, both zones fired

```json
"XAUUSD": {
  ...existing fields...,
  "outcomes": [
    {
      "side": "SELL",
      "entry_actual": 4438.5,
      "exit_price": 4410.0,
      "result": "TP",
      "hit_target": true,
      "hit_stop": false,
      "outcome_date": "2026-09-07",
      "outcome_utc": "2026-09-07T10:15:00Z",
      "bars_held": 3,
      "note": ""
    },
    {
      "side": "BUY",
      "entry_actual": null,
      "exit_price": null,
      "result": "NO_SIGNAL",
      "hit_target": null,
      "hit_stop": null,
      "outcome_date": "2026-09-07",
      "outcome_utc": null,
      "bars_held": null,
      "note": "buy zone never swept"
    }
  ]
}
```

## Brier score input

Brier score script will read:
- `sell_confidence` / `buy_confidence` → forecast probability
- `outcomes[].hit_target` (where `side` matches) → observed outcome (1/0)

Requires at minimum 10 non-null outcomes per side before score is meaningful.

## What this does NOT cover

- Partial fills (not modelled — paper mode assumes full fill at signal close)
- Slippage model (covered by `debate-paper-live-gap`)
- Multi-target tracking (T2 not tracked here; only T1 determines `hit_target`)

## Next step

Human reviews this schema. If approved:
1. Add `outcomes` block to a test brief to confirm JSON parses correctly.
2. Claude builds Brier score script to read this structure.
3. Human begins daily fills from 2026-09-22 onwards.

Historical briefs (2026-09-07 to 2026-09-20): fill retroactively where M15
data confirms outcome. Mark `outcome_date` as the actual exit date, not the
brief date.

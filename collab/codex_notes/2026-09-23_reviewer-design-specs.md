# Reviewer Stage 0/1 Design Specifications

Date: 2026-09-23
REVIEW_SOURCE: FALLBACK_REVIEW
Status: DESIGN DELIVERED - implementation and independent review pending

Interpreting as: deliver Group 2's five record contracts and Stage 1 Python stubs. No executable modules, tests, scheduler changes, database tables or trading actions are created by this document.

Builds on [daily reviewer plan](2026-09-23_daily-brief-strategy-review-plan.md) and [nine-debate review](2026-09-21-nine-debate-review.md). Group 3 repairs are recorded complete; do not reimplement them. Next-open execution and append-only outcome reporting remain new work, not functionality already supplied by those repairs.

## A. Storage and common rules

Proposed layout: `data/reviewer/<experiment_id>/<symbol>/events.jsonl` plus an atomically replaced derived `summary.md`. Each symbol has one append-only JSONL containing all five record types, including the decision log. Preserve raw briefs and Parquet bars elsewhere unchanged; reference their hashes. Do not add database tables or mutate `_levels.json` with future outcomes.

All records require `schema_version: 1`, `record_type`, `record_id` and `recorded_at`. Times are offset-aware UTC strings, finite numeric values only, no NaN/Infinity or booleans as numbers. Object fields are closed unless explicitly marked as extensible below. Required nullable fields must be present with null when unknown; optional fields may be absent. Examples are synthetic illustrations, not market observations. Short ID/hash tokens below stand for full computed SHA-256 digests in implementation.

Identity rules:

- Canonical JSON: sorted keys, UTF-8, compact separators, no non-finite values; hash original brief bytes separately from normalised configuration. Specify and version this canonicalisation.
- Manifest identity hashes immutable input hashes, source availability classification, symbol, strategy/config/feature/broker/execution-policy versions and experiment ID. Wall-clock recorded_at and machine-specific paths are not identity inputs.
- Decision identity hashes manifest identity, symbol, strategy version, zero-based bar index in the declared sorted immutable dataset and record kind. Fill identity derives from decision ID plus ENTRY/EXIT and sequence number. Trade ID derives from its entry decision ID. Outcome identity derives from trade/decision ID plus state, barrier observations and observation-bar identity. No ID is just a timestamp.
- Dataset extension/correction creates a new manifest, so run-level IDs can change. Cross-run statistics must deduplicate observations by experiment, brief hash, symbol, strategy/config version and canonical signal-bar identity; do not count the same historical trade again after extending the dataset. Run identity is not observation identity.
- Amendment identity hashes the superseded record ID, replacement semantic payload and reason. Exclude only operational recorded_at from hashing; chronology affecting availability is semantic and must remain in identity.
- Same ID and semantic content: idempotent no-op, preserving first recorded_at. Same ID with different semantic content: fail closed, never overwrite. Later evidence corrections use amendments.

## B. Five record types

### 1. Input manifest

Required: all fields shown. Nullable: issued_at, verified_available_at and availability_evidence. Optional: `source_label`, `source_url` (public only), `notes` (bounded text). `policy` and `instrument` are closed versioned objects; `strategy_parameters` is strategy-specific but validated against the selected strategy's supported parameters.

```json
{
  "schema_version": 1,
  "record_type": "INPUT_MANIFEST",
  "record_id": "EXAMPLE_MANIFEST_HASH",
  "recorded_at": "2026-09-23T09:16:00Z",
  "experiment_id": "reviewer-next-open-v1",
  "mode": "SYNTHETIC",
  "availability_class": "SYNTHETIC",
  "brief_hash": "EXAMPLE_RAW_BRIEF_HASH",
  "data_hash": "EXAMPLE_PARQUET_HASH",
  "feature_version": "rolling-atr14-v1",
  "strategy": "key_level_sweep_v1",
  "strategy_version": "0.1.0",
  "strategy_parameters": {"min_confidence": 0.55},
  "config_hash": "EXAMPLE_CONFIG_HASH",
  "broker_profile_hash": "EXAMPLE_BROKER_PROFILE_HASH",
  "symbol": "XAUUSD",
  "timeframe": "M15",
  "instrument": {"venue": "SYNTHETIC", "kind": "CFD", "quote_currency": "USD", "account_currency": "USD", "contract_size": 100.0, "tick_size": 0.01, "lot_step": 0.01},
  "issued_at": "2026-09-23T08:00:00Z",
  "received_at": "2026-09-23T08:01:00Z",
  "verified_available_at": null,
  "availability_evidence": null,
  "data_start": "2026-09-23T08:00:00Z",
  "data_end": "2026-09-23T10:00:00Z",
  "policy": {"version": "next-open-v1", "price_basis": "MID_WITH_MODELLED_SPREAD", "entry": "NEXT_BAR_OPEN", "same_bar": "AMBIGUOUS_STOP_FIRST", "max_holding_bars": 8, "entry_session_timezone": "Europe/London", "entry_cutoff_utc": "2026-09-23T12:00:00Z", "risk_model": "FIXED_RISK_PCT", "risk_pct": 0.005, "max_open_positions": 1, "calendar_state": "VERIFIED_CLEAR", "cost_model_version": "fixture-zero-cost-v1"}
}
```

`mode`: SYNTHETIC / HISTORICAL_REPLAY / PROSPECTIVE_PAPER. `availability_class`: SYNTHETIC / VERIFIED_PROSPECTIVE / RETROSPECTIVE / UNKNOWN. A claimed issued_at is not verified availability. For forward use, local receipt is the earliest safe availability absent independently verified earlier receipt; never infer an earlier value from a filename. Historical unknowns may run a labelled scenario but are excluded from prospective/calibration claims. Distinguish data_end as the exclusive bar-close coverage boundary.

### 2. Decision

Required: all shown; brief_hash, side and the proposed prices may be null for rejected/WAIT records. Optional: `diagnostics` as a bounded map of named gate values. probability is required nullable and non-null only with a declared event/horizon; analyst_confidence is never used as probability or sizing input.

```json
{
  "schema_version": 1,
  "record_type": "DECISION",
  "record_id": "EXAMPLE_DECISION_HASH",
  "recorded_at": "2026-09-23T09:16:00Z",
  "manifest_id": "EXAMPLE_MANIFEST_HASH",
  "brief_hash": "EXAMPLE_RAW_BRIEF_HASH",
  "symbol": "XAUUSD",
  "strategy_version": "0.1.0",
  "bar_index": 4,
  "bar_open_at": "2026-09-23T09:00:00Z",
  "decision_at": "2026-09-23T09:15:00Z",
  "action": "CANDIDATE",
  "side": "BUY",
  "reason_code": "RULES_PASSED",
  "proposed_entry": 100.0,
  "stop_loss": 98.0,
  "target_1": 104.0,
  "target_2": 106.0,
  "analyst_confidence": 0.6,
  "probability": null,
  "forecast_event": "T1_BEFORE_STOP_WITHIN_H_AFTER_FIRST_ELIGIBLE_FILL",
  "horizon_bars": 8,
  "expires_at": "2026-09-23T12:00:00Z"
}
```

Action enum: CANDIDATE / WAIT / REJECTED. Side: BUY / SELL / null. Required rejection codes include NO_BRIEF, UNKNOWN_AVAILABILITY, NO_TRIGGER, LOW_RR, SESSION_BLOCK, EVENT_BLOCK, COOLDOWN, INVALID_DATA and RISK_BLOCK. A candidate does not establish a fill. One decision per strategy/symbol/bar; do not call the stateful strategy repeatedly just to obtain more diagnostics. Failed execution belongs in a linked outcome, not an overwritten decision.

### 3. Simulated fill

Required: all shown. Optional: source bid/ask and their timestamps if actually observed. Stage 1 uses full entry/exit only, no partial fills. Costs are non-negative amounts; realised P&L is signed. `embedded_*` fields are attribution only, not added to fees again.

```json
{
  "schema_version": 1,
  "record_type": "SIMULATED_FILL",
  "record_id": "EXAMPLE_ENTRY_FILL_HASH",
  "recorded_at": "2026-09-23T09:16:00Z",
  "manifest_id": "EXAMPLE_MANIFEST_HASH",
  "decision_id": "EXAMPLE_DECISION_HASH",
  "trade_id": "EXAMPLE_TRADE_HASH",
  "fill_role": "ENTRY",
  "sequence": 0,
  "symbol": "XAUUSD",
  "side": "BUY",
  "filled_at": "2026-09-23T09:15:00Z",
  "timing_basis": "BAR_OPEN",
  "reference_price": 100.0,
  "fill_price": 100.0,
  "quantity_lots": 0.1,
  "contract_size": 100.0,
  "embedded_spread_amount": 0.0,
  "embedded_slippage_amount": 0.0,
  "commission_amount": 0.0,
  "swap_amount": 0.0,
  "account_currency": "USD",
  "cost_model_version": "fixture-zero-cost-v1",
  "initial_risk_amount": 20.0
}
```

An exit uses fill_role EXIT, opposite transaction side and sequence 1. For intrabar barrier exits, filled_at is null and timing_basis BAR_INTERVAL; the outcome carries the containing bar interval. Do not fabricate exact intrabar time. Under this first design account currency must equal quote currency; otherwise reject until timestamped FX conversion is specified. Initial risk is the fixed entry loss-at-stop in account currency, excluding future uncertain exit costs, and net R uses that same denominator.

### 4. Outcome event

Required: all shown, with nullable links/results as appropriate. Optional: `mfe`, `mae`, `bars_held` with documented price basis and only observed exposure bars. Links to both entry and exit fills must reconcile with the signed net P&L; no derived score may be inferred from a missing record.

```json
{
  "schema_version": 1,
  "record_type": "OUTCOME_EVENT",
  "record_id": "EXAMPLE_OUTCOME_HASH",
  "recorded_at": "2026-09-23T09:31:00Z",
  "manifest_id": "EXAMPLE_MANIFEST_HASH",
  "decision_id": "EXAMPLE_DECISION_HASH",
  "trade_id": "EXAMPLE_TRADE_HASH",
  "entry_fill_id": "EXAMPLE_ENTRY_FILL_HASH",
  "exit_fill_id": "EXAMPLE_EXIT_FILL_HASH",
  "state": "AMBIGUOUS",
  "exit_reason": "BOTH_BARRIERS_SAME_BAR",
  "observed_from": "2026-09-23T09:15:00Z",
  "observed_to": "2026-09-23T09:30:00Z",
  "target_touched": true,
  "stop_touched": true,
  "observed_target_first": null,
  "assumed_exit": "STOP_FIRST",
  "net_pnl": -20.0,
  "net_r": -1.0,
  "metric_basis": "CONSERVATIVE_ASSUMPTION",
  "probability_label": null
}
```

State semantics:

| State | Required meaning |
|---|---|
| OPEN | Executed paper entry with ongoing exposure; exit link and realised results null |
| RESOLVED | Defined exit under the price model; outcome/order distinguishable at available resolution |
| EXPIRED | Candidate never filled before expiry; trade/fill links and P&L null, never count as a losing trade |
| CENSORED | Missing data or end of dataset prevents complete outcome; do not force a win/loss label |
| AMBIGUOUS | Both barriers touched without established ordering; keep observed label null and stop-first assumed economics explicit |

OPEN may append a terminal event; it is not mutated. Later evidence replacing a terminal event uses an amendment. For RESOLVED TP-first within H label 1; observed STOP-first within H label 0. If the full horizon is observed without T1, label 0 for the declared within-H event, with TIME_EXIT economics. A reversal before H or missing coverage is censored for that probability unless the event definition explicitly includes the exit rule. CENSORED/AMBIGUOUS cannot silently enter binary calibration. Report exclusion counts and sensitivity. Reject new entries with no next bar as EXPIRED/NO_NEXT_BAR; existing positions at an incomplete dataset boundary are CENSORED, not automatically closed for performance claims.

### 5. Amendment

Required: all shown. Optional: a bounded human review note. The referenced replacement is a complete validated record of the superseded type with a new record_id. It may correct evidence but never change raw source bytes or pretend a new forecast was available earlier.

```json
{
  "schema_version": 1,
  "record_type": "AMENDMENT",
  "record_id": "EXAMPLE_AMENDMENT_HASH",
  "recorded_at": "2026-09-24T08:00:00Z",
  "supersedes_record_id": "EXAMPLE_OUTCOME_HASH",
  "reason_code": "FINER_DATA_RESOLVED_ORDER",
  "evidence_hash": "EXAMPLE_FINER_DATA_HASH",
  "replacement_record_id": "EXAMPLE_REPLACEMENT_HASH"
}
```

Here the complete replacement OUTCOME_EVENT is appended as its own normal record; the amendment references it. Both are committed in the same validated batch. Reject absent replacements, wrong types, circular links or multiple unreviewed branches. The effective projection follows amendment links; the raw ledger retains all versions. Correction of past facts never retroactively authorises past entries.

## C. Stage 1 function stubs

The following is a design-only API, not existing callable functionality. Generic dict types avoid proposing a second model framework; implementation may use existing dataclasses. `brief_path` accepts one brief file or a directory of immutable versions. The loader must resolve availability per bar, not select a final revised daily file for the whole day.

```python
from collections.abc import Iterable, Mapping
from pathlib import Path
import pandas as pd
from tar_system.brokers.profiles import BrokerProfile
from tar_system.strategies.base import Strategy


def validate_record(record: Mapping[str, object]) -> None:
    """Validate type schema, finite values and within-record invariants.

    Reject unknown schema versions. Cross-record checks belong to append_records.
    Never execute strings, fetch schemas remotely or rewrite the input.
    """
    ...


def load_replay_inputs(
    brief_path: Path, bars_path: Path, *, symbol: str,
    strategy: Strategy, broker_profile: BrokerProfile,
    policy: Mapping[str, object], evidence: Mapping[str, object],
) -> tuple[dict, pd.DataFrame, list[dict]]:
    """Return manifest, canonical features and immutable available brief versions.

    Validate OHLC chronology/coverage/venue/units and publication evidence.
    Preserve ALL bars, including days without briefs. Recompute causal features
    through the existing rolling-ATR pipeline; reject incomplete warm-up.
    Do not drop rows before computing features or use future-filled values.
    """
    ...


def iter_paper_replay(
    manifest: Mapping[str, object], features: pd.DataFrame,
    briefs: list[dict], strategy: Strategy, broker_profile: BrokerProfile,
) -> Iterable[dict]:
    """Yield validated decisions, fills and outcome events, without I/O.

    Use a fresh strategy instance per isolated symbol run. Select only the brief
    version actually available for the decision, preserving strategy cooldown.
    Process pending N+1 open fills before that bar's post-entry barrier tests;
    then generate decisions at bar close. Never use N's wick as an entry outcome.
    Recheck expiry/session/event/risk/R:R at actual fill price, without using
    N+1 close or ATR to authorise its open fill. Missing brief blocks entries,
    never exits. No auto-tuning, live orders or probability-based risk sizing.
    """
    ...


def resolve_bar_outcome(
    position: Mapping[str, object], bar: pd.Series,
    broker_profile: BrokerProfile, *, policy: Mapping[str, object],
) -> tuple[dict | None, dict | None]:
    """Return optional exit fill and outcome for already-established exposure.

    Check opening gaps first; adverse stop gaps fill at executable open plus
    costs, not the skipped stop. A marketable target uses the conservative
    target-fill policy. If neither resolves at open and both barriers touch,
    report AMBIGUOUS with stop-first assumed P&L, never observed target-first.
    Return no exit if still open; explicitly handle horizon and data censoring.
    """
    ...


def append_records(ledger_path: Path, records: Iterable[dict]) -> int:
    """Append one validated batch under an exclusive local writer lock.

    Validate links, identities and transitions before writing. Equal records
    deduplicate; conflicts fail closed. Flush/fsync complete JSONL records.
    On partial-tail recovery, preserve evidence and require explicit repair;
    do not truncate silently. Return count newly appended, not sample count.
    """
    ...


def write_summary(ledger_path: Path, summary_path: Path) -> None:
    """Atomically replace a derived Markdown view from the effective ledger.

    Show mode, coverage, rejection reasons, open/censored/ambiguous counts and
    cost assumptions; separate assumed economics from observed labels. No
    prospective/calibration claims from synthetic or unverifiable inputs.
    """
    ...


def run_replay(
    brief_path: Path, bars_path: Path, strategy: Strategy,
    broker_profile: BrokerProfile, *, symbol: str, output_dir: Path,
    policy: Mapping[str, object], evidence: Mapping[str, object],
) -> tuple[Path, Path]:
    """Coordinate explicit manual local replay; return JSONL and Markdown paths.

    Validate inputs before publishing outcomes. Constrain output paths to the
    chosen local directory, preserve inputs and reuse identical records. No
    scheduler, DB migration, account connection, dependency install or upload.
    """
    ...
```

## D. Execution decisions required by this design

1. Next-open is a NEW labelled experiment, not a silent alteration of the existing close-fill baseline. An M15 bar opening 09:00 is available at 09:15; idealised historical entry can be the 09:15 open. A prospective observation arriving 09:16 cannot claim that open: use a later executable observation/bar under a separately frozen latency policy, or reject it.
2. 'Closes into zone' is not a replacement for the current rejection/reclaim rules. The existing strategy must actually produce a candidate; a touch alone is insufficient. Fill-time validation may reject a candidate after a gap; log why.
3. State-dependent processing order: resolve existing positions and pending entries at the next open; then process that bar's eligible intrabar exposure; generate new candidates only at its close. Retain the entry stop/target, re-evaluate costs/R:R and size from actual fill; never widen a stop just to pass risk limits.
4. Explicitly freeze session/calendar rules by local timezone and resolved UTC boundaries; cutoffs apply to entry fill time for this experiment. Missing/faulty calendar blocks new entries, not management of open positions. Do not infer that 'no new brief' means close existing positions.
5. Use the existing cost helpers consistently: spread/slippage in fill prices, commissions/swap once in net P&L. Stage 1 fixed risk must validate final loss-at-stop and minimum-lot constraints independently of confidence.
6. T2 is observational only for Stage 1, with its own horizon if reported. No partial exit or hindsight target selection. Ambiguous target ranges remain blocked until an explicit target-selection policy is frozen.
7. Current `run_backtest` cannot provide the proposed event stream/next-open contract as-is. Reuse its broker/strategy/feature primitives and add an isolated replay adapter or explicitly opt-in engine extension; preserve default behaviour and regression coverage. Never just rename the old aggregate output a ledger.

## E. Acceptance and immediate handoff

Stage 0 implementation: materialise local JSON Schemas and semantic validators for these five types; provide fixtures for all five states and invalid/circular amendments. The examples above use illustrative short digests, so replace them with computed IDs in executable fixtures. No remote schema resolution. Existing venv packages are `jsonschema 4.26.0` and `check-jsonschema 0.38.2`; no new install is needed. Cross-field ordering and chronology require Python checks as well as schema validation.

Stage 1 implementation tests: both symbols; no-brief cross-day exits; input immutability; feature parity; issued/received/decision/fill chronology; same-bar ambiguity; opening gaps; missing next bar; incomplete horizons; rerun deduplication; crash-tail handling; amendments; DST/session boundaries; cost reconciliation; min-lot rejection; future-data perturbation not changing earlier decisions. Tests are specified here, not executed.

Default outputs must say 'insufficient evidence' rather than invent calibrated probabilities. Later Brier/edge analysis needs a declared event, held-out labels, dependence-aware uncertainty and adequate coverage, not a fixed brief/day count. No strategy promotion follows automatically from a complete report.

Scope verification: documentation only. Group 2 now supplies concrete schemas-by-example and implementation signatures; p0/Stage 0 implementation can proceed after the owner's design review without waiting for another market debate. No security review flag, queue readiness flag or independent approval is asserted by this document.

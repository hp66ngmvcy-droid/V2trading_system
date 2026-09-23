"""Stage 0 evidence-contract validator.

No network calls, no filesystem side effects, no new installs.
Schemas loaded from data/schemas/reviewer/ relative to repo root.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "data" / "schemas" / "reviewer"

_SCHEMA_FILES = {
    "INPUT_MANIFEST": "input_manifest.schema.json",
    "DECISION": "decision.schema.json",
    "SIMULATED_FILL": "simulated_fill.schema.json",
    "OUTCOME_EVENT": "outcome_event.schema.json",
    "AMENDMENT": "amendment.schema.json",
}

_SCHEMAS: dict[str, dict] = {}


def _load_schema(record_type: str) -> dict:
    if record_type not in _SCHEMAS:
        path = _SCHEMA_DIR / _SCHEMA_FILES[record_type]
        with path.open(encoding="utf-8") as fh:
            _SCHEMAS[record_type] = json.load(fh)
    return _SCHEMAS[record_type]


def compute_record_id(payload: dict) -> str:
    """SHA-256 of canonical JSON (sorted keys, compact, UTF-8). Returns hex digest."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_record(record: dict) -> None:
    """Validate against JSON Schema + cross-field semantic rules. Raises ValueError on failure."""
    if not isinstance(record, dict):
        raise ValueError("record must be a dict")

    record_type = record.get("record_type")
    if record_type not in _SCHEMA_FILES:
        raise ValueError(f"unknown or missing record_type: {record_type!r}")

    schema = _load_schema(record_type)
    try:
        jsonschema.validate(record, schema, format_checker=jsonschema.FormatChecker())
    except jsonschema.ValidationError as exc:
        raise ValueError(str(exc.message)) from exc

    if record.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")

    try:
        ts = record["recorded_at"]
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("recorded_at must be offset-aware (UTC)")
    except (KeyError, ValueError, AttributeError) as exc:
        raise ValueError(f"recorded_at invalid: {exc}") from exc

    if record_type == "OUTCOME_EVENT":
        state = record.get("state")
        if state == "RESOLVED":
            if record.get("net_pnl") is None or record.get("net_r") is None:
                raise ValueError("RESOLVED outcome requires non-null net_pnl and net_r")
        if state in ("EXPIRED", "CENSORED"):
            for field in ("trade_id", "entry_fill_id", "exit_fill_id"):
                if record.get(field) is not None:
                    raise ValueError(f"{state} outcome must have null {field}")

    if record_type == "AMENDMENT":
        sup = record.get("supersedes_record_id")
        rep = record.get("replacement_record_id")
        if sup is not None and rep is not None and sup == rep:
            raise ValueError("replacement_record_id must differ from supersedes_record_id")

    if record_type == "SIMULATED_FILL":
        for field in ("commission_amount", "swap_amount", "embedded_spread_amount", "embedded_slippage_amount"):
            val = record.get(field)
            if val is not None and val < 0:
                raise ValueError(f"{field} must be >= 0, got {val}")


def validate_batch(records: list[dict]) -> list[str]:
    """Validate a list of records. Returns list of error strings (empty = all valid)."""
    errors: list[str] = []
    for i, rec in enumerate(records):
        try:
            validate_record(rec)
        except ValueError as exc:
            errors.append(f"record[{i}]: {exc}")
    return errors

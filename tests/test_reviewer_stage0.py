"""Tests for reviewer Stage 0 evidence-contract schemas and validator."""
import json
from pathlib import Path

import pytest

from tar_system.reviewer.stage0_validator import (
    compute_record_id,
    validate_batch,
    validate_record,
)

_FIXTURES = Path(__file__).parent / "fixtures" / "reviewer"

_VALID_FIXTURES = [
    "valid_input_manifest.json",
    "valid_decision.json",
    "valid_decision_wait.json",
    "valid_simulated_fill.json",
    "valid_outcome_resolved.json",
    "valid_outcome_ambiguous.json",
    "valid_outcome_expired.json",
    "valid_amendment.json",
]


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_all_valid_fixtures_pass():
    for fname in _VALID_FIXTURES:
        rec = _load(fname)
        validate_record(rec)  # must not raise


def test_invalid_circular_amendment_raises():
    rec = _load("invalid_circular_amendment.json")
    with pytest.raises(ValueError):
        validate_record(rec)


def test_invalid_unknown_state_raises():
    rec = _load("invalid_unknown_state.json")
    with pytest.raises(ValueError):
        validate_record(rec)


def test_compute_record_id_is_deterministic():
    payload = {"a": 1, "b": "hello"}
    assert compute_record_id(payload) == compute_record_id(payload)


def test_compute_record_id_differs_on_content_change():
    payload = {"a": 1, "b": "hello"}
    modified = {"a": 2, "b": "hello"}
    assert compute_record_id(payload) != compute_record_id(modified)


def test_validate_batch_returns_empty_for_valid():
    records = [_load(f) for f in _VALID_FIXTURES[:3]]
    errors = validate_batch(records)
    assert errors == []


def test_validate_batch_returns_errors_for_invalid():
    invalid = _load("invalid_unknown_state.json")
    valid = _load("valid_decision.json")
    errors = validate_batch([valid, invalid])
    assert len(errors) > 0


def test_resolved_outcome_requires_net_pnl():
    rec = _load("valid_outcome_resolved.json")
    rec["net_pnl"] = None
    with pytest.raises(ValueError):
        validate_record(rec)


def test_expired_outcome_allows_null_trade_id():
    rec = _load("valid_outcome_expired.json")
    assert rec["trade_id"] is None
    validate_record(rec)  # must not raise

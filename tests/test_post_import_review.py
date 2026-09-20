from copy import deepcopy
import json
import fcntl
from pathlib import Path

import pytest

from tar_system.reporting.post_import_review import digest, evaluate, run_review


@pytest.fixture
def packet():
    bars = [
        {"open_time": "2026-01-05T10:00:00Z", "close_time": "2026-01-05T10:15:00Z", "open": 100, "high": 103, "low": 99, "close": 102},
        {"open_time": "2026-01-05T10:15:00Z", "close_time": "2026-01-05T10:30:00Z", "open": 102, "high": 106, "low": 101, "close": 105},
    ]
    data = {"dataset_id": "demo", "validation_status": "PASSED", "feature_status": "READY",
            "feature_version": "fixture-v1", "bar_minutes": 15, "bars": bars, "features": {"fixture": True}}
    rehash(data)
    return {"schema_version": 1, "evidence_class": "SYNTHETIC", "prompt_version": "daily-v1",
            "import_completed_at": "2026-01-05T10:31:00Z", "required_dataset_ids": ["demo"],
            "datasets": [data], "forecasts": [{"forecast_id": "observation-1", "dataset_id": "demo",
            "frozen_at": "2026-01-05T09:59:00Z", "input_available_at": "2026-01-05T09:58:00Z",
            "evaluation_start": "2026-01-05T10:00:00Z", "evaluation_end": "2026-01-05T10:30:00Z",
            "lower_level": 95, "upper_level": 105, "expected_side": "UPPER"}]}


def rehash(data):
    data["data_hash"] = digest(data["bars"])
    data["feature_source_hash"] = data["data_hash"]
    data["feature_hash"] = digest(data["features"])


def test_report_and_idempotent_replay(packet, tmp_path):
    original = deepcopy(packet)
    path, reused = run_review(packet, tmp_path)
    assert not reused
    report = json.loads((path / "report.json").read_text())
    assert report["outcomes"][0]["outcome"] == "UPPER_FIRST"
    assert report["outcomes"][0]["interpretation"] == "SUPPORTED"
    assert report["eligible_prospective_days"] == 0
    assert not report["checkpoint_due"]
    assert "Synthetic" in (path / "report.md").read_text()
    assert run_review(packet, tmp_path) == (path, True)
    assert packet == original


@pytest.mark.parametrize("low,high,expected", [(94, 106, "AMBIGUOUS_SAME_BAR"), (94, 104, "LOWER_FIRST"), (99, 104, "NO_THRESHOLD_REACHED")])
def test_observation_labels(packet, low, high, expected):
    packet["datasets"][0]["bars"][1].update(low=low, high=high, close=102)
    rehash(packet["datasets"][0])
    assert evaluate(packet)["outcomes"][0]["outcome"] == expected


@pytest.mark.parametrize("change", ["missing", "features", "hash", "lineage", "gap", "unfinished"])
def test_partial_inputs_wait_without_outcomes(packet, change):
    data = packet["datasets"][0]
    if change == "missing":
        packet["required_dataset_ids"].append("other")
    elif change == "features":
        data["feature_status"] = "FAILED"
    elif change == "hash":
        data["data_hash"] = "bad"
    elif change == "lineage":
        data["feature_source_hash"] = "old"
    elif change == "gap":
        data["bars"].pop(0)
        rehash(data)
    else:
        packet["import_completed_at"] = "2026-01-05T10:16:00Z"
    report = evaluate(packet)
    assert report["run_status"] == "WAITING_FOR_DATA"
    assert report["outcomes"] == []


@pytest.mark.parametrize("field,value", [("frozen_at", "2026-01-05T10:00:00Z"), ("input_available_at", "2026-01-05T10:01:00Z"), ("frozen_at", "2026-01-05T09:59:00")])
def test_invalid_chronology_rejected(packet, field, value):
    packet["forecasts"][0][field] = value
    with pytest.raises(ValueError):
        evaluate(packet)


def test_future_bars_do_not_change_past_outcome(packet):
    before = evaluate(packet)["outcomes"]
    data = packet["datasets"][0]
    data["bars"].append({"open_time": "2026-01-05T10:30:00Z", "close_time": "2026-01-05T10:45:00Z", "open": 105, "high": 999, "low": 1, "close": 5})
    rehash(data)
    packet["import_completed_at"] = "2026-01-05T10:46:00Z"
    assert evaluate(packet)["outcomes"] == before


def test_revision_and_prompt_version_get_distinct_reports(packet, tmp_path):
    first, _ = run_review(packet, tmp_path)
    packet["prompt_version"] = "daily-v2"
    second, _ = run_review(packet, tmp_path)
    assert first != second
    packet["datasets"][0]["bars"][1]["high"] = 107
    rehash(packet["datasets"][0])
    third, _ = run_review(packet, tmp_path)
    assert third not in (first, second)
    assert len(list(tmp_path.glob("*/report.json"))) == 3


def test_non_synthetic_and_duplicates_rejected(packet):
    packet["evidence_class"] = "PROSPECTIVE_PAPER"
    with pytest.raises(ValueError):
        evaluate(packet)
    packet["evidence_class"] = "SYNTHETIC"
    packet["forecasts"].append(deepcopy(packet["forecasts"][0]))
    with pytest.raises(ValueError):
        evaluate(packet)


def test_changed_report_is_not_overwritten(packet, tmp_path):
    path, _ = run_review(packet, tmp_path)
    (path / "report.json").write_text("{}")
    with pytest.raises(ValueError):
        run_review(packet, tmp_path)
    assert (path / "report.json").read_text() == "{}"


def test_offset_equivalence(packet):
    before = evaluate(packet)["outcomes"]
    packet["datasets"][0]["bars"][0]["open_time"] = "2026-01-05T11:00:00+01:00"
    rehash(packet["datasets"][0])
    assert evaluate(packet)["outcomes"] == before


def test_interrupted_publication_can_retry(packet, tmp_path, monkeypatch):
    with monkeypatch.context() as patch:
        def fail(*args):
            raise OSError("synthetic interruption")
        patch.setattr(Path, "rename", fail)
        with pytest.raises(OSError):
            run_review(packet, tmp_path)
    assert not list(tmp_path.glob("*/report.json"))
    path, reused = run_review(packet, tmp_path)
    assert not reused and (path / "report.json").exists()


def test_concurrent_claim_refused_then_released(packet, tmp_path):
    with (tmp_path / ".review.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            run_review(packet, tmp_path)
    assert run_review(packet, tmp_path)[1] is False


def test_demo_fixture():
    fixture = Path(__file__).parent / "fixtures" / "post_import_review.json"
    assert evaluate(json.loads(fixture.read_text()))["run_status"] == "COMPLETE"


@pytest.mark.parametrize("kind", ["duplicate", "ohlc", "nan"])
def test_invalid_bars_rejected(packet, kind):
    data = packet["datasets"][0]
    if kind == "duplicate":
        data["bars"].append(deepcopy(data["bars"][0]))
    elif kind == "ohlc":
        data["bars"][0]["high"] = 90
    else:
        data["bars"][0]["high"] = float("nan")
    with pytest.raises(ValueError):
        rehash(data)
        evaluate(packet)

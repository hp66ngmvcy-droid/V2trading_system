from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from tar_system.cache.artifact_cache import has_valid_artifact, make_artifact_key, record_artifact
from tar_system.cache.result_cache import clear_result_memory_cache, load_cached_result, make_cache_key, save_cached_result
from tar_system.cache.tiered_cache import MemoryTTLCache, TieredJsonCache, stable_cache_key
from tar_system.data.store import clear_dataframe_cache, load_feature_data, save_feature_data


def test_memory_ttl_cache_expires() -> None:
    cache = MemoryTTLCache(max_entries=2)
    cache.set("a", {"ok": True}, ttl_seconds=0)
    time.sleep(0.01)
    assert cache.get("a") is None


def test_memory_ttl_cache_evicts_lru() -> None:
    cache = MemoryTTLCache(max_entries=2)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    cache.set("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_tiered_json_cache_reads_memory_then_disk(tmp_path: Path) -> None:
    cache = TieredJsonCache(tmp_path, max_memory_entries=1)
    cache.set("key", {"value": 1})
    assert cache.get("key") == {"value": 1}
    cache.clear_memory()
    assert cache.get("key") == {"value": 1}


def test_stable_cache_key_is_deterministic() -> None:
    first = stable_cache_key("x", {"b": 2, "a": 1})
    second = stable_cache_key("x", {"a": 1, "b": 2})
    assert first == second
    assert first.startswith("x:")


def test_result_cache_uses_memory_and_disk(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    key = make_cache_key("gold_v2", {}, "XAUUSD", "M15", "hash", (None, None), "backtest")
    save_cached_result(key, {"score": 1})
    assert load_cached_result(key) == {"score": 1}
    clear_result_memory_cache()
    assert load_cached_result(key) == {"score": 1}


def test_artifact_cache_ttl_marks_expired_artifact_invalid(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = Path("data/results/example.json")
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    key = make_artifact_key("backtest", "gold_v2", "XAUUSD", "M15", "hash")
    record_artifact(key, "backtest", path, ttl_seconds=0)
    time.sleep(0.01)
    assert not has_valid_artifact(key)


def test_parquet_load_uses_copy_safe_hot_cache(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    original = pd.DataFrame({"timestamp": ["2026-01-01"], "close": [1.0]})
    save_feature_data(original, "XAUUSD", "M15")
    first = load_feature_data("XAUUSD", "M15")
    first.loc[0, "close"] = 2.0
    second = load_feature_data("XAUUSD", "M15")
    assert second.loc[0, "close"] == 1.0
    clear_dataframe_cache()
    third = load_feature_data("XAUUSD", "M15")
    assert third.loc[0, "close"] == 1.0

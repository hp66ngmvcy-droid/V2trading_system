# V2 Trading Agent Notes

## Input Sharpening

All agents follow `~/Dev/shared/policies/INPUT_SHARPENING.md`. Infer intent from vague input, fill gaps from repo context, state interpretation in one line, then act. Do not ask for clarification — choose the best reading and proceed.

## Recent Cache Upgrade

When reviewing or extending V2 trading, be aware that the cache layer was upgraded with a V2-native tiered cache. Do not port the archived Obsidian `TinyDB`/`Whoosh`/`APScheduler` cache stack unless a future task explicitly asks for Obsidian vault search.

Use these current files:

- `src/tar_system/cache/tiered_cache.py` - dependency-free cache primitives:
  - `MemoryTTLCache`
  - `JsonDiskCache`
  - `TieredJsonCache`
  - `stable_cache_key`
- `src/tar_system/cache/result_cache.py` - result JSON cache with process-local hot cache.
- `src/tar_system/cache/artifact_cache.py` - DuckDB artifact index with optional `ttl_seconds` expiry.
- `src/tar_system/data/store.py` - Parquet data/feature loads with copy-safe process-local hot cache.
- `src/tar_system/research/exa_searcher.py` - existing Exa JSON disk cache plus memory hot cache.
- `tests/test_tiered_cache.py` - focused coverage for TTL, LRU eviction, disk fallback, artifact expiry, and copy-safe Parquet caching.

Design rules for future agents:

- Keep cache keys tied to the full source-of-truth inputs: strategy, parameters, symbol, timeframe, data hash, date range, broker/cost model, feature version, and mode where applicable.
- Prefer V2's existing DuckDB, Parquet, and JSON artifact paths over adding new cache databases.
- Keep memory caches bounded and copy-safe for mutable objects such as Pandas DataFrames.
- Preserve existing disk formats unless the caller is explicitly migrated.
- Add TTL only where stale results are acceptable and the invalidation source is clear.

Validation already run for the cache upgrade:

```bash
PYTHONPATH=src venv/bin/python -m pytest tests/test_tiered_cache.py tests/test_next_layer.py::test_result_cache_hash_is_stable tests/test_scale_foundation.py::test_artifact_cache_records_and_validates_path tests/test_scale_foundation.py::test_artifact_cache_missing_file_is_not_valid
PYTHONPATH=src venv/bin/python -m pytest tests/test_exa_searcher.py tests/test_data_readiness.py
PYTHONPATH=src venv/bin/python -m compileall src/tar_system/cache src/tar_system/data src/tar_system/research/exa_searcher.py
git diff --check
```

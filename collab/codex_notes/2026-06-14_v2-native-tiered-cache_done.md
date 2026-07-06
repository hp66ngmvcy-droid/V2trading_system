# V2 Native Tiered Cache

Status: done

## Summary

Reviewed the archived three-tier caching strategy and checked comparable open-source practice in Freqtrade, Microsoft Qlib, and vectorbt. The conclusion was to keep V2 on its existing DuckDB/Parquet/JSON artifact foundation and add a small dependency-free tiered cache rather than porting the archived Obsidian-specific implementation.

## Implemented

- Added `src/tar_system/cache/tiered_cache.py`.
- Added result hot-cache support in `src/tar_system/cache/result_cache.py`.
- Added optional artifact expiry via `ttl_seconds` in `src/tar_system/cache/artifact_cache.py`.
- Added copy-safe Parquet hot-cache support in `src/tar_system/data/store.py`.
- Added memory hot-cache over the existing Exa JSON cache in `src/tar_system/research/exa_searcher.py`.
- Added focused tests in `tests/test_tiered_cache.py`.
- Added root `AGENTS.md` so future dev agents see the cache design and current files quickly.

## Agent Guidance

Future agents working on V2 should use the V2-native cache primitives and avoid the archived Obsidian cache stack unless the task is specifically about Obsidian vault search/indexing.

Use stable cache keys tied to source inputs. For trading research, stale cache hits are a correctness risk, so include strategy, params, symbol, timeframe, data hash, date range, broker/cost model, feature version, and mode where relevant.

## Verification

Passed:

```bash
PYTHONPATH=src venv/bin/python -m pytest tests/test_tiered_cache.py tests/test_next_layer.py::test_result_cache_hash_is_stable tests/test_scale_foundation.py::test_artifact_cache_records_and_validates_path tests/test_scale_foundation.py::test_artifact_cache_missing_file_is_not_valid
PYTHONPATH=src venv/bin/python -m pytest tests/test_exa_searcher.py tests/test_data_readiness.py
PYTHONPATH=src venv/bin/python -m compileall src/tar_system/cache src/tar_system/data src/tar_system/research/exa_searcher.py
git diff --check
```

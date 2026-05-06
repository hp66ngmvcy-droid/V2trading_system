"""Small JSON result cache for repeatable local research runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from tar_system.settings import DATA_DIR


def make_cache_key(
    strategy: str,
    parameters: dict[str, Any],
    symbol: str,
    timeframe: str,
    data_hash: str | None,
    date_range: tuple[str | None, str | None],
    mode: str,
) -> str:
    payload = {
        "strategy": strategy,
        "parameters": parameters,
        "symbol": symbol,
        "timeframe": timeframe,
        "data_hash": data_hash,
        "date_range": date_range,
        "mode": mode,
    }
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def cache_path(cache_key: str) -> Path:
    return Path(DATA_DIR) / "results" / "cache" / f"{cache_key}.json"


def load_cached_result(cache_key: str, force: bool = False) -> dict[str, Any] | None:
    if force:
        return None
    path = cache_path(cache_key)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_cached_result(cache_key: str, result: dict[str, Any]) -> Path:
    path = cache_path(cache_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    try:
        from tar_system.cache.artifact_cache import record_artifact

        record_artifact(cache_key, "result_cache", path, metadata={"keys": sorted(result.keys())})
    except Exception:
        pass
    return path

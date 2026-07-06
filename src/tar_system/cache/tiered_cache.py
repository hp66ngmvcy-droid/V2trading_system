"""Small tiered cache primitives for local research workloads."""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CacheEntry:
    value: Any
    created_at: float
    ttl_seconds: int | None = None

    @property
    def expired(self) -> bool:
        return self.ttl_seconds is not None and (time.time() - self.created_at) > self.ttl_seconds


class MemoryTTLCache:
    """Bounded process-local cache with TTL and least-recently-used eviction."""

    def __init__(self, max_entries: int = 128) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        self.max_entries = max_entries
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> Any | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expired:
            self._entries.pop(key, None)
            return None
        self._entries.move_to_end(key)
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        self._entries[key] = CacheEntry(value=value, created_at=time.time(), ttl_seconds=ttl_seconds)
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()

    def clear_expired(self) -> int:
        expired = [key for key, entry in self._entries.items() if entry.expired]
        for key in expired:
            self._entries.pop(key, None)
        return len(expired)


class JsonDiskCache:
    """JSON disk cache with metadata envelope and TTL validation."""

    def __init__(self, cache_dir: str | Path) -> None:
        self.cache_dir = Path(cache_dir)

    def path_for_key(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def get(self, key: str) -> Any | None:
        path = self.path_for_key(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict) or payload.get("version") != 1:
            return None
        ttl_seconds = payload.get("ttl_seconds")
        created_at = payload.get("created_at")
        if isinstance(ttl_seconds, int) and isinstance(created_at, (int, float)):
            if (time.time() - float(created_at)) > ttl_seconds:
                try:
                    path.unlink()
                except OSError:
                    pass
                return None
        return payload.get("value")

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> Path:
        path = self.path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "created_at": time.time(),
            "ttl_seconds": ttl_seconds,
            "value": value,
        }
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return path


class TieredJsonCache:
    """Memory-first JSON cache that falls back to disk for repeatable artifacts."""

    def __init__(self, cache_dir: str | Path, max_memory_entries: int = 128) -> None:
        self.memory = MemoryTTLCache(max_entries=max_memory_entries)
        self.disk = JsonDiskCache(cache_dir)

    def get(self, key: str) -> Any | None:
        value = self.memory.get(key)
        if value is not None:
            return value
        value = self.disk.get(key)
        if value is not None:
            self.memory.set(key, value)
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None, disk: bool = True) -> Path | None:
        self.memory.set(key, value, ttl_seconds=ttl_seconds)
        if not disk:
            return None
        return self.disk.set(key, value, ttl_seconds=ttl_seconds)

    def clear_memory(self) -> None:
        self.memory.clear()


def stable_cache_key(prefix: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return f"{prefix}:{hashlib.sha256(encoded).hexdigest()}"

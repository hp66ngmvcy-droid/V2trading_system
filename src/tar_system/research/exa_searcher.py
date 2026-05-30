"""Exa web search for strategy research.

Two modes:
- search_strategy: dedicated query for a specific strategy/edge pattern
- broad_sweep: wide net across a list of trading topics
- multi_agent_search: parallel risk/performance/robustness research lenses
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

_HIGHLIGHTS = {"highlights": True}
_CACHE_DIR = Path("data/research/online_scout/cache")
_MAX_HIGHLIGHTS = 3
_MAX_HIGHLIGHT_CHARS = 280
_MULTI_AGENT_LENSES = {
    "risk": "risk management drawdown volatility filter position sizing trading strategy paper",
    "performance": "profit factor sharpe expectancy momentum mean reversion trading strategy paper",
    "robustness": "walk forward validation out of sample parameter stability trading strategy paper",
}
_HIGH_TRUST_HOST_HINTS = (
    ".edu",
    "mit.edu",
    "stanford.edu",
    "harvard.edu",
    "ox.ac.uk",
    "cam.ac.uk",
    "arxiv.org",
    "ssrn.com",
    "nber.org",
    "github.com",
)
_LOW_TRUST_HOST_HINTS = (
    "medium.com",
    "substack.com",
    "blogspot.",
    "pinterest.",
)
_RESEARCH_TEXT_HINTS = (
    "paper",
    "journal",
    "arxiv",
    "ssrn",
    "backtest",
    "walk forward",
    "out of sample",
    "source code",
    "github",
)


def _client():
    key = os.environ.get("EXA_API_KEY")
    if not key:
        raise RuntimeError("EXA_API_KEY not set. Add it to .env")

    from exa_py import Exa  # lazy import — optional dep

    return Exa(api_key=key)


def score_source(title: str, url: str, highlights: list[str] | None = None) -> dict[str, Any]:
    """Rate whether a search hit is likely useful enough for strategy research."""
    host = urlparse(url).netloc.lower()
    text = " ".join([title, host, *(highlights or [])]).lower()
    score = 40
    reasons: list[str] = []

    if any(hint in host for hint in _HIGH_TRUST_HOST_HINTS):
        score += 35
        reasons.append("trusted_or_research_host")
    if any(hint in text for hint in _RESEARCH_TEXT_HINTS):
        score += 20
        reasons.append("research_or_validation_terms")
    if "github.com" in host:
        score += 10
        reasons.append("code_available")
    if any(hint in host for hint in _LOW_TRUST_HOST_HINTS):
        score -= 15
        reasons.append("low_signal_content_host")
    if not url.startswith("https://"):
        score -= 5
        reasons.append("non_https")

    score = max(0, min(100, score))
    if score >= 75:
        label = "high"
    elif score >= 55:
        label = "medium"
    else:
        label = "low"

    return {"score": score, "label": label, "reasons": reasons}


def _trim_highlights(highlights: Any) -> list[str]:
    if not isinstance(highlights, list):
        return []
    trimmed: list[str] = []
    for item in highlights[:_MAX_HIGHLIGHTS]:
        text = str(item).strip()
        if len(text) > _MAX_HIGHLIGHT_CHARS:
            text = f"{text[:_MAX_HIGHLIGHT_CHARS].rstrip()}..."
        if text:
            trimmed.append(text)
    return trimmed


def _format_results(results: Any, source_quality: str = "balanced") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for r in results:
        highlights = _trim_highlights(getattr(r, "highlights", []))
        quality = score_source(r.title, r.url, highlights)
        if source_quality == "strict" and quality["score"] < 60:
            continue
        row = {
            "title": r.title,
            "url": r.url,
            "highlights": highlights,
        }
        if source_quality != "off":
            row["source_quality"] = quality
        rows.append(row)
    return rows


def _cache_path(query: str, num_results: int, source_quality: str, cache_dir: str | Path | None = None) -> Path:
    payload = json.dumps(
        {"query": query, "num_results": num_results, "source_quality": source_quality},
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return Path(cache_dir or _CACHE_DIR) / f"{digest}.json"


def _read_cache(path: Path) -> list[dict[str, Any]] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    rows = payload.get("results") if isinstance(payload, dict) else None
    return rows if isinstance(rows, list) else None


def _write_cache(path: Path, query: str, rows: list[dict[str, Any]]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"query": query, "results": rows}, indent=2, default=str), encoding="utf-8")
    except OSError:
        return


def _search_with_client(
    client: Any,
    query: str,
    num_results: int,
    source_quality: str,
    use_cache: bool = False,
    cache_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    cache_path = _cache_path(query, num_results, source_quality, cache_dir)
    if use_cache:
        cached = _read_cache(cache_path)
        if cached is not None:
            return cached

    results = client.search(
        query,
        type="auto",
        num_results=num_results,
        contents=_HIGHLIGHTS,
    )
    rows = _format_results(results.results, source_quality=source_quality)
    if use_cache:
        _write_cache(cache_path, query, rows)
    return rows


def search_strategy(
    query: str,
    num_results: int = 10,
    client: Any | None = None,
    source_quality: str = "balanced",
    use_cache: bool = False,
    cache_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Dedicated search — specific strategy name, edge pattern, or paper."""
    return _search_with_client(client or _client(), query, num_results, source_quality, use_cache=use_cache, cache_dir=cache_dir)


def broad_sweep(
    topics: list[str],
    num_results: int = 5,
    max_workers: int | None = None,
    client_factory: Callable[[], Any] | None = None,
    source_quality: str = "balanced",
    use_cache: bool = False,
    cache_dir: str | Path | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Broad sweep — one search per topic, returns dict keyed by topic.

    Each topic gets its own client so online searches can run in parallel
    without assuming thread-safety inside the provider SDK.
    """
    if not topics:
        return {}

    def run(topic: str) -> tuple[str, list[dict[str, Any]]]:
        client = client_factory() if client_factory else _client()
        return topic, _search_with_client(client, topic, num_results, source_quality, use_cache=use_cache, cache_dir=cache_dir)

    worker_count = max(1, min(len(topics), max_workers or len(topics)))
    if worker_count == 1:
        return dict(run(topic) for topic in topics)

    completed: dict[str, list[dict[str, Any]]] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(run, topic) for topic in topics]
        for future in as_completed(futures):
            topic, rows = future.result()
            completed[topic] = rows

    return {topic: completed[topic] for topic in topics}


def multi_agent_search(
    query: str,
    num_results: int = 5,
    max_workers: int | None = None,
    client_factory: Callable[[], Any] | None = None,
    source_quality: str = "balanced",
    use_cache: bool = False,
    cache_dir: str | Path | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Search the same idea through the scorer's agent lenses in parallel."""
    agent_queries = {
        agent: f"{query} {lens}"
        for agent, lens in _MULTI_AGENT_LENSES.items()
    }
    sweep = broad_sweep(
        list(agent_queries.values()),
        num_results=num_results,
        max_workers=max_workers,
        client_factory=client_factory,
        source_quality=source_quality,
        use_cache=use_cache,
        cache_dir=cache_dir,
    )
    return {agent: sweep[agent_query] for agent, agent_query in agent_queries.items()}

"""Exa web search for strategy research.

Two modes:
- search_strategy: dedicated query for a specific strategy/edge pattern
- broad_sweep: wide net across a list of trading topics
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

_HIGHLIGHTS = {"highlights": True}


def _client():
    from exa_py import Exa  # lazy import — optional dep

    key = os.environ.get("EXA_API_KEY")
    if not key:
        raise RuntimeError("EXA_API_KEY not set. Add it to .env")
    return Exa(api_key=key)


def search_strategy(query: str, num_results: int = 10) -> list[dict[str, Any]]:
    """Dedicated search — specific strategy name, edge pattern, or paper."""
    results = _client().search(
        query,
        type="auto",
        num_results=num_results,
        contents=_HIGHLIGHTS,
    )
    return [
        {
            "title": r.title,
            "url": r.url,
            "highlights": getattr(r, "highlights", []),
        }
        for r in results.results
    ]


def broad_sweep(topics: list[str], num_results: int = 5) -> dict[str, list[dict[str, Any]]]:
    """Broad sweep — one search per topic, returns dict keyed by topic."""
    client = _client()
    out: dict[str, list[dict[str, Any]]] = {}
    for topic in topics:
        results = client.search(
            topic,
            type="auto",
            num_results=num_results,
            contents=_HIGHLIGHTS,
        )
        out[topic] = [
            {
                "title": r.title,
                "url": r.url,
                "highlights": getattr(r, "highlights", []),
            }
            for r in results.results
        ]
    return out

"""Tests for the optional Exa research helper."""

from __future__ import annotations

import threading

import pytest

from tar_system.research.exa_searcher import broad_sweep, multi_agent_search, score_source, search_strategy


class FakeResult:
    def __init__(self, query: str):
        self.title = f"{query} title"
        self.url = f"https://arxiv.org/abs/{query.replace(' ', '-')}"
        self.highlights = [f"{query} paper walk forward highlight"]


class FakeResponse:
    def __init__(self, query: str):
        self.results = [FakeResult(query)]


class FakeClient:
    def __init__(self, calls: list[str]):
        self.calls = calls

    def search(self, query: str, type: str, num_results: int, contents: dict) -> FakeResponse:
        assert type == "auto"
        assert num_results > 0
        assert contents == {"highlights": True}
        self.calls.append(query)
        return FakeResponse(query)


def test_search_strategy_accepts_injected_client():
    calls: list[str] = []
    rows = search_strategy("volatility breakout", client=FakeClient(calls))

    assert calls == ["volatility breakout"]
    assert rows == [
        {
            "title": "volatility breakout title",
            "url": "https://arxiv.org/abs/volatility-breakout",
            "highlights": ["volatility breakout paper walk forward highlight"],
            "source_quality": {
                "score": 95,
                "label": "high",
                "reasons": ["trusted_or_research_host", "research_or_validation_terms"],
            },
        }
    ]


def test_search_strategy_reports_missing_key_before_importing_optional_package(monkeypatch):
    monkeypatch.delenv("EXA_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="EXA_API_KEY not set"):
        search_strategy("volatility breakout")


def test_broad_sweep_runs_topics_through_parallel_client_factory():
    calls: list[str] = []
    lock = threading.Lock()

    class LockedFakeClient(FakeClient):
        def search(self, query: str, type: str, num_results: int, contents: dict) -> FakeResponse:
            with lock:
                return super().search(query, type, num_results, contents)

    topics = ["momentum filters", "drawdown controls", "walk forward validation"]
    rows = broad_sweep(
        topics,
        num_results=2,
        max_workers=3,
        client_factory=lambda: LockedFakeClient(calls),
    )

    assert list(rows.keys()) == topics
    assert sorted(calls) == sorted(topics)
    assert rows["momentum filters"][0]["title"] == "momentum filters title"


def test_multi_agent_search_fans_query_across_agent_lenses():
    calls: list[str] = []
    rows = multi_agent_search(
        "gold intraday momentum",
        num_results=1,
        max_workers=3,
        client_factory=lambda: FakeClient(calls),
    )

    assert set(rows) == {"risk", "performance", "robustness"}
    assert all("gold intraday momentum" in call for call in calls)
    assert any("drawdown" in call for call in calls)
    assert any("profit factor" in call for call in calls)
    assert any("walk forward" in call for call in calls)


def test_source_quality_strict_filters_low_signal_hosts():
    class LowSignalResult:
        title = "Simple trading tips"
        url = "http://example.com/tips"
        highlights = ["opinion"]

    class MixedResponse:
        results = [LowSignalResult(), FakeResult("robust momentum")]

    class MixedClient:
        def search(self, query: str, type: str, num_results: int, contents: dict) -> MixedResponse:
            return MixedResponse()

    rows = search_strategy("robust momentum", client=MixedClient(), source_quality="strict")

    assert len(rows) == 1
    assert rows[0]["source_quality"]["label"] == "high"


def test_score_source_marks_university_research_as_high_quality():
    quality = score_source(
        "Walk forward validation of momentum strategies",
        "https://mitsloan.mit.edu/research/example",
        ["out of sample paper"],
    )

    assert quality["label"] == "high"
    assert "trusted_or_research_host" in quality["reasons"]


def test_search_strategy_uses_cache_and_compacts_highlights(tmp_path):
    calls: list[str] = []

    class VerboseResult:
        title = "Verbose paper"
        url = "https://arxiv.org/abs/verbose"
        highlights = ["x" * 400, "second", "third", "fourth"]

    class VerboseResponse:
        results = [VerboseResult()]

    class VerboseClient:
        def search(self, query: str, type: str, num_results: int, contents: dict) -> VerboseResponse:
            calls.append(query)
            return VerboseResponse()

    first = search_strategy("verbose query", client=VerboseClient(), use_cache=True, cache_dir=tmp_path)
    second = search_strategy("verbose query", client=VerboseClient(), use_cache=True, cache_dir=tmp_path)

    assert calls == ["verbose query"]
    assert first == second
    assert len(first[0]["highlights"]) == 3
    assert len(first[0]["highlights"][0]) <= 283

from __future__ import annotations

import json
from pathlib import Path

from tar_system.controller.daily_idea_loop import run_daily_idea_loop


def test_daily_idea_loop_writes_review_without_online_key(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    Path("ideas/research_queue").mkdir(parents=True)
    Path("ideas/research_queue/source.md").write_text("# Source\n", encoding="utf-8")

    result = run_daily_idea_loop(run_online=True, online_query="gold momentum")

    assert result.paper_only is True
    assert result.online_ready is False
    assert result.online_scout_ran is False
    assert result.research_queue_count == 1
    assert Path(result.review_path).exists()
    assert "Add EXA_API_KEY" in Path(result.review_path).read_text(encoding="utf-8")


def test_daily_idea_loop_runs_online_when_ready(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EXA_API_KEY", "test-key")

    import tar_system.controller.daily_idea_loop as daily_loop
    import tar_system.research.exa_searcher as exa_searcher

    monkeypatch.setattr(daily_loop, "_online_ready", lambda: True)
    monkeypatch.setattr(
        exa_searcher,
        "multi_agent_search",
        lambda query, **kwargs: {
            "risk": [
                {
                    "title": "Daily scout paper",
                    "url": "https://arxiv.org/abs/daily",
                    "highlights": ["walk forward daily scout"],
                    "source_quality": {"score": 95, "label": "high", "reasons": ["trusted_or_research_host"]},
                }
            ]
        },
    )

    result = run_daily_idea_loop(run_online=True, online_query="gold momentum")

    assert result.online_ready is True
    assert result.online_scout_ran is True
    assert result.hypothesis_notes_written == 1
    assert result.online_scout_saved_to is not None
    assert Path(result.online_scout_saved_to).exists()
    assert json.loads(Path(result.review_json_path).read_text(encoding="utf-8"))["paper_only"] is True


def test_daily_idea_loop_writes_review_when_queue_health_is_unavailable(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("EXA_API_KEY", raising=False)

    import tar_system.controller.daily_idea_loop as daily_loop

    monkeypatch.setattr(daily_loop, "queue_health", lambda limit=5: (_ for _ in ()).throw(RuntimeError("db locked")))

    result = run_daily_idea_loop()

    assert Path(result.review_path).exists()
    assert any("Queue health unavailable" in action for action in result.next_actions)

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from tar_system.cli import build_parser
from tar_system.controller.job_queue import add_job, read_jobs
from tar_system.dashboard.runtime_control import begin_task, read_backtest_status, read_forward_status, read_global_status
from tar_system.web_ui import server


def test_build_snapshot_reads_local_jobs_and_results(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("data/results/gold_v2_XAUUSD_M15_metrics.json").write_text(
        json.dumps({"profit_factor": 1.6, "total_trades": 240, "max_drawdown": 0.08, "win_rate": 0.55, "sharpe_ratio": 1.2}),
        encoding="utf-8",
    )
    add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv", job_type="paper_signal")

    snapshot = server.build_snapshot(tmp_path)

    assert snapshot["STRATEGIES"][0]["strategy"] == "gold_v2"
    assert snapshot["STRATEGIES"][0]["trades"] == 240
    assert snapshot["STRATEGIES"][0]["live_chart_url"].startswith("https://www.tradingview.com/chart/")
    assert snapshot["JOBS"][0]["job_type"] == "paper_signal"
    assert "ONLINE_RESEARCH" in snapshot
    assert "TOKEN_USAGE" in snapshot


def test_build_snapshot_reads_token_usage_json(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    usage_path = Path("runtime/token_usage.json")
    usage_path.parent.mkdir(parents=True)
    usage_path.write_text(
        json.dumps(
            {
                "usage": {
                    "input_tokens": 1200,
                    "output_tokens": 345,
                    "total_tokens": 1545,
                    "requests": 3,
                    "updated_at": "2026-05-30T10:00:00Z",
                }
            }
        ),
        encoding="utf-8",
    )

    snapshot = server.build_snapshot(tmp_path)

    assert snapshot["TOKEN_USAGE"]["tracked"] is True
    assert snapshot["TOKEN_USAGE"]["total_tokens"] == 1545
    assert "input_tokens: 1,200" in snapshot["TOKEN_USAGE"]["summary_text"]


def test_integrated_index_exists_and_uses_runtime_data() -> None:
    html = Path("ui/research-ui/index.html").read_text(encoding="utf-8")
    assert "/runtime-data.js" in html
    assert "/prototype/app.jsx" in html


def test_run_web_ui_parser_exists() -> None:
    parser = build_parser()
    args = parser.parse_args(["run-web-ui", "--host", "127.0.0.1", "--port", "8610"])
    assert args.host == "127.0.0.1"
    assert args.port == 8610
    assert callable(args.func)


def test_prototype_shell_polls_runtime_snapshot() -> None:
    app = Path("ui/research-ui-prototype/app.jsx").read_text(encoding="utf-8")
    assert "function useRuntimePolling" in app
    assert "fetch(`/api/snapshot?ts=${Date.now()}`" in app
    assert "setInterval(refresh, intervalMs)" in app
    assert "syncLabel(runtime.lastSync" in app


def test_dashboard_shows_token_usage_text_box() -> None:
    page = Path("ui/research-ui-prototype/page-dashboard.jsx").read_text(encoding="utf-8")
    css = Path("ui/research-ui-prototype/tar-styles.css").read_text(encoding="utf-8")

    assert "TOKEN_USAGE" in page
    assert "Token Usage" in page
    assert "className=\"token-usage-box mono\"" in page
    assert "aria-label=\"Token usage\"" in page
    assert ".token-usage-box" in css


def test_web_ui_can_queue_paper_signal_safely(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = server.handle_api_post(
        "/api/jobs/queue-paper-signal",
        {"strategy": "gold_v2", "symbol": "XAUUSD", "timeframe": "M15"},
    )

    jobs = read_jobs()
    assert result["ok"] is True
    assert jobs[0]["type"] == "paper_signal"
    assert jobs[0]["no_live"] is True
    assert jobs[0]["no_mt5_promotion"] is True
    assert jobs[0]["require_walk_forward"] is False


def test_web_ui_queues_all_tests_from_raw_data_with_limit(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    raw = Path("data/raw/XAUUSD_M15.csv")
    raw.parent.mkdir(parents=True)
    raw.write_text("timestamp,open,high,low,close,volume\n2026-01-01,1,2,1,1.5,10\n", encoding="utf-8")

    result = server.handle_api_post("/api/jobs/queue-all-tests", {"max_jobs": 1})

    assert result["ok"] is True
    assert result["queued_count"] == 1
    assert read_jobs()[0]["research_stage"] == "ui_all_tests"


def test_web_ui_rejects_queue_file_outside_raw_data(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    try:
        server.handle_api_post(
            "/api/jobs/queue-paper-research",
            {"strategy": "gold_v2", "symbol": "XAUUSD", "timeframe": "M15", "file": "../bad.csv"},
        )
    except ValueError as exc:
        assert "data/raw" in str(exc)
    else:
        raise AssertionError("unsafe raw file path should be rejected")


def test_web_ui_stop_active_sets_existing_stop_flags(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    begin_task("backtest", "Manual Backtest", {"symbol": "XAUUSD", "timeframe": "M15", "strategy": "gold_v2"})

    result = server.handle_api_post("/api/tasks/stop-active", {})

    assert result["ok"] is True
    assert read_global_status()["status"] == "STOPPING"
    assert read_backtest_status()["stop_requested"] is True
    assert read_forward_status()["stop_requested"] is True


def test_web_ui_online_scout_saves_output_and_hypotheses(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    import tar_system.research.exa_searcher as exa_searcher

    def fake_multi_agent_search(query: str, **kwargs):
        return {
            "risk": [
                {
                    "title": "Risk filtered momentum paper",
                    "url": "https://arxiv.org/abs/test-risk",
                    "highlights": ["walk forward risk filter"],
                    "source_quality": {"score": 95, "label": "high", "reasons": ["trusted_or_research_host"]},
                }
            ]
        }

    monkeypatch.setattr(exa_searcher, "multi_agent_search", fake_multi_agent_search)

    result = server.handle_api_post(
        "/api/research/scout",
        {
            "query": "gold intraday momentum",
            "num_results": 1,
            "max_workers": 1,
            "source_quality": "strict",
            "generate_hypotheses": True,
            "save_output": True,
        },
    )

    assert result["ok"] is True
    assert Path(result["saved_to"]).exists()
    assert len(result["hypothesis_notes"]) == 1
    assert Path(result["hypothesis_notes"][0]["path"]).exists()

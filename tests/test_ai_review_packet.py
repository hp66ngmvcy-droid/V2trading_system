from __future__ import annotations

import argparse
import json
from pathlib import Path

from tar_system.cli import build_parser, export_ai_review_packet_cmd
from tar_system.reporting.ai_review_packet import export_ai_review_packet


def test_export_ai_review_packet_writes_markdown_and_json(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("logs").mkdir()
    Path("logs/review_log.jsonl").write_text("", encoding="utf-8")
    Path("reports").mkdir()
    Path("data/results/gold_v2_XAUUSD_M15_metrics.json").write_text(
        json.dumps(
            {
                "total_trades": 35,
                "win_rate": 0.6,
                "profit_factor": 1.4,
                "max_drawdown": 0.08,
                "net_profit": 420,
                "expectancy": 12,
            }
        ),
        encoding="utf-8",
    )

    path = export_ai_review_packet("runtime/test_packet.md", limit=5)

    text = path.read_text(encoding="utf-8")
    payload = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    assert "TAR AI Review Packet" in text
    assert "paper-only research" in text
    assert "Summary Statistics" in text
    assert "Failure Diagnosis" in text
    assert "| Severity | Strategy | Symbol | TF |" in text
    assert "| PASS | gold_v2 | XAUUSD | M15 |" in text
    assert payload["paper_only"] is True
    assert payload["summary_statistics"]["metric_files"] == 1
    assert payload["best_metric_candidates"][0]["strategy"] == "gold_v2"
    assert Path("runtime/ai_review_metrics_cache.json").exists()
    assert Path("logs/audit/audit.jsonl").exists()


def test_export_ai_review_packet_reports_metric_warnings(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("data/results/bad_metrics.json").write_text("{}", encoding="utf-8")
    Path("data/results/gold_v2_XAUUSD_M15_metrics.json").write_text("{not-json", encoding="utf-8")

    path = export_ai_review_packet("runtime/test_packet.md", limit=5)

    payload = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    reasons = {warning["reason"] for warning in payload["warnings"]}
    assert "METRICS_NAME_NOT_RECOGNISED" in reasons
    assert "METRICS_JSON_LOAD_FAILED" in reasons


def test_export_ai_review_packet_summarizes_failed_jobs(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    from tar_system.controller.job_queue import add_job, update_job

    job = add_job("gold_v2", "XAUUSD", "M15", "data/raw/XAUUSD_M15.csv", research_stage="smoke")
    update_job(job["job_id"], status="FAILED", recommendation="REVIEW")

    path = export_ai_review_packet("runtime/test_packet.md", limit=5)

    payload = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    assert payload["summary_statistics"]["failed_jobs"] == 1
    assert payload["failure_diagnosis"]["top_failed_stages"] == [["smoke", 1]]


def test_cli_accepts_export_ai_review_packet_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["export-ai-review-packet", "--output", "runtime/x.md", "--limit", "3"])
    assert args.func is export_ai_review_packet_cmd
    assert args.output == "runtime/x.md"
    assert args.limit == 3


def test_export_ai_review_packet_cmd_prints_paths(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    path = "runtime/packet.md"

    export_ai_review_packet_cmd(argparse.Namespace(output=path, limit=2))

    output = json.loads(capsys.readouterr().out)
    assert output["packet_path"] == path
    assert output["json_path"] == "runtime/packet.json"

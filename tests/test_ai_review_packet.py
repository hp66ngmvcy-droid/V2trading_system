from __future__ import annotations

import argparse
import json
from pathlib import Path

from tar_system.cli import build_parser, export_ai_review_packet_cmd
from tar_system.cli import run_local_construction_audit_cmd, run_static_analysis_scan_cmd
from tar_system.reporting.ai_review_packet import export_ai_review_packet
from tar_system.reporting.static_analysis import load_static_analysis_snapshot


def test_export_ai_review_packet_writes_markdown_and_json(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("logs").mkdir()
    Path("logs/review_log.jsonl").write_text("", encoding="utf-8")
    Path("reports").mkdir()
    Path("configs").mkdir()
    Path("configs/local_infrastructure_watchlist.json").write_text(
        json.dumps({"updated_at": "2026-05-23", "adopt_now": [{"name": "OpenGrep", "category": "static_analysis", "local_role": "scan-only"}]}),
        encoding="utf-8",
    )
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
    assert "Static Analysis Trial" in text
    assert "Local Infrastructure Watchlist" in text
    assert "| Severity | Strategy | Symbol | TF |" in text
    assert "| PASS | gold_v2 | XAUUSD | M15 |" in text
    assert payload["paper_only"] is True
    assert payload["static_analysis"]["trial"]["primary_tool"] == "opengrep"
    assert payload["static_analysis"]["trial"]["review_due"] == "2026-05-28"
    assert payload["infrastructure_watchlist"]["adopt_now"][0]["name"] == "OpenGrep"
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


def test_static_analysis_snapshot_loads_opengrep_json_and_sarif(tmp_path) -> None:
    static_dir = tmp_path / "runtime/static_analysis"
    static_dir.mkdir(parents=True)
    (static_dir / "opengrep.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "check_id": "python.dangerous-subprocess",
                        "path": "src/example.py",
                        "start": {"line": 12},
                        "extra": {"severity": "WARNING", "message": "subprocess call needs review"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (static_dir / "opengrep.sarif").write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "tool": {"driver": {"name": "OpenGrep", "rules": [{"id": "rule.sarif"}]}},
                        "results": [
                            {
                                "ruleId": "rule.sarif",
                                "level": "error",
                                "message": {"text": "path traversal"},
                                "locations": [{"physicalLocation": {"artifactLocation": {"uri": "src/path.py"}, "region": {"startLine": 9}}}],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    snapshot = load_static_analysis_snapshot(static_dir, limit=5)

    assert snapshot["summary"]["total_findings"] == 2
    assert snapshot["summary"]["severity_counts"]["WARNING"] == 1
    assert snapshot["summary"]["severity_counts"]["error"] == 1
    assert {finding["rule_id"] for finding in snapshot["findings"]} == {"python.dangerous-subprocess", "rule.sarif"}


def test_cli_accepts_static_analysis_scan_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["run-static-analysis-scan", "--tool", "opengrep", "--target", "src/tar_system", "--config", "auto"])
    assert args.func.__name__ == "run_static_analysis_scan_cmd"
    assert args.tool == "opengrep"
    assert args.target == "src/tar_system"
    assert args.config == "auto"


def test_cli_accepts_local_construction_audit_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["run-local-construction-audit", "--target", "src/tar_system", "--fail-on-findings"])
    assert args.func.__name__ == "run_local_construction_audit_cmd"
    assert args.tool == "opengrep"
    assert args.target == "src/tar_system"
    assert args.scan_output == "runtime/static_analysis/opengrep.json"
    assert args.packet_output == "runtime/ai_review_packet.md"
    assert args.fail_on_findings is True


def test_static_analysis_scan_cmd_reports_missing_tool(monkeypatch, capsys) -> None:
    import tar_system.reporting.static_analysis as static_analysis

    monkeypatch.setattr(static_analysis.shutil, "which", lambda _: None)
    monkeypatch.setattr(static_analysis.os.path, "expanduser", lambda _: "/tmp/missing-home")
    args = argparse.Namespace(tool="opengrep", target="src", output="runtime/static_analysis/opengrep.json", config="auto")

    run_static_analysis_scan_cmd(args)

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "UNAVAILABLE"
    assert output["return_code"] == 127
    assert "not installed" in output["error"]


def test_local_construction_audit_cmd_reports_missing_tool(monkeypatch, capsys) -> None:
    import tar_system.reporting.static_analysis as static_analysis

    monkeypatch.setattr(static_analysis.shutil, "which", lambda _: None)
    monkeypatch.setattr(static_analysis.os.path, "expanduser", lambda _: "/tmp/missing-home")
    args = argparse.Namespace(
        tool="opengrep",
        target="src",
        scan_output="runtime/static_analysis/opengrep.json",
        packet_output="runtime/ai_review_packet.md",
        config="auto",
        limit=10,
        fail_on_findings=False,
    )

    run_local_construction_audit_cmd(args)

    output = json.loads(capsys.readouterr().out)
    assert output["scan_status"] == "UNAVAILABLE"
    assert output["scan_return_code"] == 127
    assert output["passed"] is False


def test_export_ai_review_packet_cmd_prints_paths(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    path = "runtime/packet.md"

    export_ai_review_packet_cmd(argparse.Namespace(output=path, limit=2))

    output = json.loads(capsys.readouterr().out)
    assert output["packet_path"] == path
    assert output["json_path"] == "runtime/packet.json"

"""Static-analysis scan helpers for AI review packets."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from tar_system.audit.writer import append_audit_event

DEFAULT_STATIC_ANALYSIS_DIR = Path("runtime/static_analysis")
DEFAULT_STATIC_ANALYSIS_TOOL = "opengrep"
STATIC_ANALYSIS_TRIAL_START = date(2026, 5, 23)
STATIC_ANALYSIS_TRIAL_REVIEW_DUE = STATIC_ANALYSIS_TRIAL_START + timedelta(days=5)


@dataclass(frozen=True)
class StaticAnalysisScanResult:
    tool: str
    output_path: Path
    command: list[str]
    return_code: int


@dataclass(frozen=True)
class LocalConstructionAuditResult:
    tool: str
    target: str
    scan_status: str
    scan_return_code: int
    scan_output_path: str
    packet_path: str
    packet_json_path: str
    total_findings: int
    severity_counts: dict[str, int]
    passed: bool


def run_static_analysis_scan(
    tool: str = DEFAULT_STATIC_ANALYSIS_TOOL,
    target: str | Path = "src",
    output: str | Path | None = None,
    config: str = "auto",
) -> StaticAnalysisScanResult:
    """Run a scan-only static-analysis pass and write JSON output."""
    if tool not in {"opengrep", "semgrep"}:
        raise ValueError("tool must be 'opengrep' or 'semgrep'")
    executable = _resolve_tool(tool)
    if executable is None:
        raise FileNotFoundError(f"{tool} is not installed or not on PATH")

    output_path = Path(output) if output else DEFAULT_STATIC_ANALYSIS_DIR / f"{tool}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [executable, "scan", "--config", config, "--json", "--output", str(output_path), str(target)]
    completed = subprocess.run(command, check=False)
    decision = "COMPLETED" if completed.returncode == 0 else "FAILED"
    append_audit_event(
        "static_analysis_scan",
        "reporting",
        "",
        "",
        decision,
        f"{tool.upper()}_SCAN_{decision}",
        {"tool": tool, "target": str(target), "output_path": str(output_path), "return_code": completed.returncode},
    )
    return StaticAnalysisScanResult(tool, output_path, command, completed.returncode)


def run_local_construction_audit(
    tool: str = DEFAULT_STATIC_ANALYSIS_TOOL,
    target: str | Path = "src",
    scan_output: str | Path | None = None,
    packet_output: str | Path = "runtime/ai_review_packet.md",
    config: str = "auto",
    limit: int = 10,
) -> LocalConstructionAuditResult:
    """Run local scan-only construction audit and refresh the review packet."""
    from tar_system.reporting.ai_review_packet import export_ai_review_packet

    output_path = Path(scan_output) if scan_output else DEFAULT_STATIC_ANALYSIS_DIR / f"{tool}.json"
    scan_result = run_static_analysis_scan(tool=tool, target=target, output=output_path, config=config)
    packet_path = export_ai_review_packet(packet_output, limit=limit)
    snapshot = load_static_analysis_snapshot(output_path.parent, limit=limit)
    total_findings = int(snapshot["summary"]["total_findings"])
    severity_counts = {str(key): int(value) for key, value in snapshot["summary"]["severity_counts"].items()}
    result = LocalConstructionAuditResult(
        tool=tool,
        target=str(target),
        scan_status="COMPLETED" if scan_result.return_code == 0 else "FAILED",
        scan_return_code=scan_result.return_code,
        scan_output_path=str(scan_result.output_path),
        packet_path=str(packet_path),
        packet_json_path=str(packet_path.with_suffix(".json")),
        total_findings=total_findings,
        severity_counts=severity_counts,
        passed=scan_result.return_code == 0 and total_findings == 0,
    )
    append_audit_event(
        "local_construction_audit",
        "reporting",
        "",
        "",
        "PASSED" if result.passed else "REVIEW",
        "LOCAL_CONSTRUCTION_AUDIT_PASSED" if result.passed else "LOCAL_CONSTRUCTION_AUDIT_FINDINGS",
        asdict(result),
    )
    return result


def load_static_analysis_snapshot(directory: str | Path = DEFAULT_STATIC_ANALYSIS_DIR, limit: int = 25) -> dict[str, Any]:
    """Load OpenGrep/Semgrep JSON or SARIF findings for review packets."""
    source_dir = Path(directory)
    files = sorted(
        [
            path
            for path in source_dir.glob("*")
            if path.is_file() and path.suffix.lower() in {".json", ".sarif"}
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    findings: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            warnings.append({"path": str(path), "reason": "STATIC_ANALYSIS_LOAD_FAILED"})
            continue
        if path.suffix.lower() == ".sarif" or "runs" in payload:
            findings.extend(_sarif_findings(payload, path))
        else:
            findings.extend(_semgrep_json_findings(payload, path))

    severity_counts: dict[str, int] = {}
    for finding in findings:
        severity = str(finding.get("severity") or "UNKNOWN")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    return {
        "trial": {
            "primary_tool": DEFAULT_STATIC_ANALYSIS_TOOL,
            "fallback_tool": "semgrep",
            "mode": "scan-only",
            "start_date": STATIC_ANALYSIS_TRIAL_START.isoformat(),
            "review_due": STATIC_ANALYSIS_TRIAL_REVIEW_DUE.isoformat(),
            "fallback_condition": "If OpenGrep is noisy, unavailable, or hard to integrate by review_due, switch this packet input to Semgrep.",
        },
        "source_dir": str(source_dir),
        "files": [{"path": str(path), "modified_at": path.stat().st_mtime} for path in files],
        "summary": {"total_findings": len(findings), "severity_counts": severity_counts},
        "findings": findings[:limit],
        "warnings": warnings,
    }


def _semgrep_json_findings(payload: dict[str, Any], source_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in payload.get("results", []) or []:
        extra = item.get("extra", {}) or {}
        start = item.get("start", {}) or {}
        rows.append(
            {
                "tool": _tool_from_path(source_path),
                "source_path": str(source_path),
                "rule_id": item.get("check_id") or item.get("rule_id") or "UNKNOWN",
                "path": item.get("path") or "",
                "line": start.get("line"),
                "severity": extra.get("severity") or item.get("severity") or "UNKNOWN",
                "message": extra.get("message") or item.get("message") or "",
            }
        )
    return rows


def _sarif_findings(payload: dict[str, Any], source_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in payload.get("runs", []) or []:
        tool = ((run.get("tool") or {}).get("driver") or {}).get("name") or _tool_from_path(source_path)
        rules = {
            rule.get("id"): rule
            for rule in (((run.get("tool") or {}).get("driver") or {}).get("rules") or [])
            if rule.get("id")
        }
        for item in run.get("results", []) or []:
            rule_id = item.get("ruleId") or "UNKNOWN"
            location = ((item.get("locations") or [{}])[0].get("physicalLocation") or {})
            artifact = location.get("artifactLocation") or {}
            region = location.get("region") or {}
            rule = rules.get(rule_id, {})
            rows.append(
                {
                    "tool": tool,
                    "source_path": str(source_path),
                    "rule_id": rule_id,
                    "path": artifact.get("uri") or "",
                    "line": region.get("startLine"),
                    "severity": item.get("level") or rule.get("defaultConfiguration", {}).get("level") or "UNKNOWN",
                    "message": (item.get("message") or {}).get("text") or rule.get("shortDescription", {}).get("text") or "",
                }
            )
    return rows


def _tool_from_path(path: Path) -> str:
    name = path.stem.lower()
    if "semgrep" in name:
        return "semgrep"
    if "opengrep" in name:
        return "opengrep"
    return "static-analysis"


def _resolve_tool(tool: str) -> str | None:
    found = shutil.which(tool)
    if found:
        return found
    home = Path(os.path.expanduser("~"))
    candidates = [
        home / ".local" / "bin" / tool,
        home / f".{tool}" / "cli" / "latest" / tool,
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None

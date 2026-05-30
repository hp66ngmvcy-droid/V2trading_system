"""Repeatable phase gate for staged local work."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable


CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


@dataclass
class PhaseCommandResult:
    name: str
    command: list[str]
    return_code: int
    passed: bool
    output_tail: str = ""


@dataclass
class PhaseGateResult:
    phase_name: str
    generated_at: str
    passed: bool
    report_path: str
    report_json_path: str
    commands: list[PhaseCommandResult] = field(default_factory=list)


def run_phase_gate(
    phase_name: str,
    tests: list[str] | None = None,
    output_dir: str | Path = "idea_reviews/phase_gates",
    run_construction_audit: bool = True,
    runner: CommandRunner | None = None,
) -> PhaseGateResult:
    """Run the standard post-phase review/audit loop and write reports."""
    runner = runner or _run_command
    commands = _commands(tests or [], run_construction_audit=run_construction_audit)
    results = [_execute(name, command, runner) for name, command in commands]
    passed = all(result.passed for result in results)
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    safe_phase = _slug(phase_name)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output / f"{stamp}_{safe_phase}.md"
    report_json_path = output / f"{stamp}_{safe_phase}.json"
    result = PhaseGateResult(
        phase_name=phase_name,
        generated_at=generated_at,
        passed=passed,
        report_path=str(report_path),
        report_json_path=str(report_json_path),
        commands=results,
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    report_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _commands(tests: list[str], run_construction_audit: bool) -> list[tuple[str, list[str]]]:
    python = sys.executable
    commands: list[tuple[str, list[str]]] = [
        ("compile", [python, "-m", "compileall", "src/tar_system"]),
        ("pip_check", [python, "-m", "pip", "check"]),
        ("security_check", [python, "-m", "tar_system.cli", "security-check"]),
    ]
    if tests:
        commands.insert(1, ("tests", [python, "-m", "pytest", *tests]))
    if run_construction_audit:
        commands.append(("construction_audit", [python, "-m", "tar_system.cli", "run-local-construction-audit", "--fail-on-findings"]))
    return commands


def _execute(name: str, command: list[str], runner: CommandRunner) -> PhaseCommandResult:
    completed = runner(command)
    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    return PhaseCommandResult(
        name=name,
        command=command,
        return_code=completed.returncode,
        passed=completed.returncode == 0,
        output_tail=output[-3000:],
    )


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def _markdown(result: PhaseGateResult) -> str:
    lines = [
        "# Phase Gate Report",
        "",
        f"- Phase: {result.phase_name}",
        f"- Generated: {result.generated_at}",
        f"- Passed: {result.passed}",
        "",
        "## Commands",
        "",
        "| Step | Passed | Return | Command |",
        "| --- | --- | ---: | --- |",
    ]
    for command in result.commands:
        lines.append(
            f"| {command.name} | {command.passed} | {command.return_code} | `{' '.join(command.command)}` |"
        )
    lines.extend(["", "## Guardrails", "", "- Review this report before moving to the next phase.", "- Do not promote candidates if any gate fails.", ""])
    return "\n".join(lines)


def _slug(value: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:64] or "phase"

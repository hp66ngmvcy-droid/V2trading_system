from __future__ import annotations

import subprocess
from pathlib import Path

from tar_system.controller.phase_gate import run_phase_gate


def test_phase_gate_writes_reports_with_injected_runner(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    result = run_phase_gate(
        "Hypothesis Review Gate",
        tests=["tests/test_hypothesis_review.py"],
        output_dir=tmp_path,
        run_construction_audit=True,
        runner=runner,
    )

    assert result.passed is True
    assert Path(result.report_path).exists()
    assert Path(result.report_json_path).exists()
    assert any("pytest" in command for call in calls for command in call)
    assert any("run-local-construction-audit" in call for call in calls)


def test_phase_gate_fails_when_any_command_fails(tmp_path: Path) -> None:
    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1 if "pip" in command else 0, stdout="", stderr="bad")

    result = run_phase_gate("Broken Phase", output_dir=tmp_path, run_construction_audit=False, runner=runner)

    assert result.passed is False
    assert any(command.name == "pip_check" and not command.passed for command in result.commands)

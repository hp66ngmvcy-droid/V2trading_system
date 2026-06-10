#!/usr/bin/env python3
"""Small MT5 data to research-pipeline sanity check.

This script checks that a small cross-section of local MT5 CSV files can move
through the real TAR research path: import, validate, feature build, backtest,
walk-forward, score, and forward-test. It is deliberately paper-only and writes
review artifacts instead of promoting anything.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = "XAUUSD:M15,EURUSD:M15,GBPUSD:H1,BTCUSD:H1,USOUSD:M30"
REPORT_JSON = Path("reports/mt5_research_sanity_check.json")
REPORT_MD = Path("reports/mt5_research_sanity_check.md")


@dataclass
class CommandResult:
    name: str
    command: list[str]
    return_code: int | None
    status: str
    stdout_tail: str = ""
    stderr_tail: str = ""
    error: str = ""


@dataclass
class CaseResult:
    symbol: str
    timeframe: str
    raw_file: str
    raw_summary: dict[str, Any]
    commands: list[CommandResult] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    walk_forward: dict[str, Any] = field(default_factory=dict)
    forward_test: dict[str, Any] = field(default_factory=dict)
    verdict: str = "UNKNOWN"
    status: str = "PENDING"
    notes: list[str] = field(default_factory=list)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a small MT5 CSV research sanity check.")
    parser.add_argument("--strategy", default="gold_v2")
    parser.add_argument("--cases", default=DEFAULT_CASES, help="Comma list like XAUUSD:M15,EURUSD:M15")
    parser.add_argument("--broker", default="current_broker_demo")
    parser.add_argument("--train-window", type=int, default=2000)
    parser.add_argument("--test-window", type=int, default=500)
    parser.add_argument("--forward-from-date", default=None)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--dry-run", action="store_true", help="Only inspect raw files and list planned commands.")
    args = parser.parse_args()

    results: list[CaseResult] = []
    for symbol, timeframe in parse_cases(args.cases):
        results.append(run_case(symbol, timeframe, args))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "paper_only": True,
        "strategy": args.strategy,
        "dry_run": bool(args.dry_run),
        "case_count": len(results),
        "status_counts": counts(result.status for result in results),
        "results": [asdict(result) for result in results],
        "next_steps": next_steps(results, args.dry_run),
    }
    write_reports(payload)
    print(json.dumps({"report_json": str(REPORT_JSON), "report_md": str(REPORT_MD), "status_counts": payload["status_counts"]}, indent=2))
    return 0 if all(result.status in {"PASS", "DRY_RUN"} for result in results) else 1


def run_case(symbol: str, timeframe: str, args: argparse.Namespace) -> CaseResult:
    raw_file = Path("data/raw") / f"{symbol}_{timeframe}.csv"
    result = CaseResult(symbol=symbol, timeframe=timeframe, raw_file=str(raw_file), raw_summary=summarise_raw_csv(raw_file))
    if not raw_file.exists():
        result.status = "FAIL"
        result.notes.append("RAW_FILE_MISSING")
        return result

    commands = planned_commands(symbol, timeframe, raw_file, args)
    if args.dry_run:
        result.status = "DRY_RUN"
        result.commands = [
            CommandResult(name=name, command=cmd, return_code=None, status="PLANNED")
            for name, cmd in commands
        ]
        return result

    for name, command in commands:
        command_result = run_command(name, command, args.timeout)
        result.commands.append(command_result)
        if command_result.status != "PASS":
            result.status = "FAIL"
            result.notes.append(f"{name.upper()}_FAILED")
            load_artifacts(result, args.strategy)
            return result

    load_artifacts(result, args.strategy)
    result.verdict = infer_verdict(result, args.strategy)
    result.status = "PASS" if result.verdict in {"KEEP", "REVIEW", "KILL"} else "REVIEW"
    return result


def planned_commands(symbol: str, timeframe: str, raw_file: Path, args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    base = [sys.executable, "-m", "tar_system.cli"]
    commands: list[tuple[str, list[str]]] = [
        ("import_csv", [*base, "import-csv", "--file", str(raw_file), "--symbol", symbol, "--timeframe", timeframe]),
        ("validate_data", [*base, "validate-data", "--symbol", symbol, "--timeframe", timeframe]),
        ("build_features", [*base, "build-features", "--symbol", symbol, "--timeframe", timeframe]),
        ("run_backtest", [*base, "run-backtest", "--strategy", args.strategy, "--symbol", symbol, "--timeframe", timeframe, "--broker", args.broker, "--force"]),
        ("run_walk_forward", [*base, "run-walk-forward", "--strategy", args.strategy, "--symbol", symbol, "--timeframe", timeframe, "--train-window", str(args.train_window), "--test-window", str(args.test_window)]),
        ("score_strategy", [*base, "score-strategy", "--strategy", args.strategy, "--symbol", symbol, "--timeframe", timeframe, "--broker", args.broker]),
    ]
    forward = [*base, "forward-test", "--strategy", args.strategy, "--symbol", symbol, "--timeframe", timeframe, "--broker", args.broker]
    if args.forward_from_date:
        forward.extend(["--from-date", args.forward_from_date])
    commands.append(("forward_test", forward))
    return commands


def run_command(name: str, command: list[str], timeout: int) -> CommandResult:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(name, command, None, "TIMEOUT", stdout_tail=tail(exc.stdout), stderr_tail=tail(exc.stderr), error=str(exc))
    status = "PASS" if completed.returncode == 0 else "FAIL"
    return CommandResult(name, command, completed.returncode, status, tail(completed.stdout), tail(completed.stderr))


def summarise_raw_csv(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    sha = hashlib.sha256()
    row_count = 0
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    columns: list[str] = []
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(chunk)
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        header = handle.readline()
        delimiter = "\t" if "\t" in header else ","
        handle.seek(0)
        reader = csv.DictReader(handle, delimiter=delimiter)
        columns = list(reader.fieldnames or [])
        for row in reader:
            row_count += 1
            timestamp = row.get("timestamp") or row.get("time") or row.get("date") or row.get("<DATE>")
            if "<DATE>" in row and "<TIME>" in row:
                timestamp = f"{row.get('<DATE>')} {row.get('<TIME>')}"
            if timestamp and first_timestamp is None:
                first_timestamp = timestamp
            if timestamp:
                last_timestamp = timestamp
    return {
        "exists": True,
        "row_count": row_count,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "columns": columns,
        "sha256": sha.hexdigest(),
    }


def load_artifacts(result: CaseResult, strategy: str) -> None:
    prefix = Path("data/results")
    metric_path = prefix / f"{strategy}_{result.symbol}_{result.timeframe}_metrics.json"
    wf_path = prefix / f"{strategy}_{result.symbol}_{result.timeframe}_walk_forward.json"
    ft_path = prefix / f"{strategy}_{result.symbol}_{result.timeframe}_forward_test.json"
    result.metrics = load_json(metric_path)
    result.walk_forward = load_json(wf_path)
    result.forward_test = load_json(ft_path)


def infer_verdict(result: CaseResult, strategy: str) -> str:
    report_path = Path("reports") / f"{result.symbol}_{result.timeframe}_{strategy}_report.md"
    if result.metrics.get("gate_reason"):
        return str(result.metrics.get("verdict") or "REVIEW")
    trades = float(result.metrics.get("total_trades", 0.0) or 0.0)
    wf_splits = int(result.walk_forward.get("split_count", result.walk_forward.get("window_count", 0)) or 0)
    if trades <= 0 or wf_splits <= 0:
        return "REVIEW"
    if result.metrics.get("max_drawdown", 1.0) > 0.20:
        return "KILL"
    return "REVIEW" if not report_path.exists() else "REVIEW"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"load_error": str(exc), "path": str(path)}


def parse_cases(value: str) -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    for item in value.split(","):
        if not item.strip():
            continue
        symbol, _, timeframe = item.strip().partition(":")
        if not symbol or not timeframe:
            raise SystemExit(f"Invalid case '{item}'. Use SYMBOL:TIMEFRAME.")
        cases.append((symbol.upper(), timeframe.upper()))
    return cases


def counts(values: Any) -> dict[str, int]:
    output: dict[str, int] = {}
    for value in values:
        output[str(value)] = output.get(str(value), 0) + 1
    return output


def tail(value: Any, max_chars: int = 2000) -> str:
    if value is None:
        return ""
    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
    return text[-max_chars:]


def next_steps(results: list[CaseResult], dry_run: bool) -> list[str]:
    if dry_run:
        return ["Run again without --dry-run to execute the CLI path on the selected MT5 cross-section."]
    failed = [result for result in results if result.status != "PASS"]
    if failed:
        return [f"Fix failed pipeline stage for {item.symbol} {item.timeframe}: {', '.join(item.notes)}" for item in failed]
    return [
        "Review report metrics and walk-forward split counts before expanding the test set.",
        "If the cross-section passes mechanically, run the optimiser on the same symbols with walk-forward enabled.",
        "Do not promote any strategy to live trading; keep this as paper research evidence.",
    ]


def write_reports(payload: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    lines = [
        "# MT5 Research Sanity Check",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Strategy: {payload['strategy']}",
        f"- Paper only: {payload['paper_only']}",
        f"- Dry run: {payload['dry_run']}",
        "",
        "## Cases",
    ]
    for row in payload["results"]:
        raw = row["raw_summary"]
        metrics = row.get("metrics") or {}
        wf = row.get("walk_forward") or {}
        ft = row.get("forward_test") or {}
        lines.extend(
            [
                "",
                f"### {row['symbol']} {row['timeframe']}",
                f"- Status: {row['status']}",
                f"- Verdict: {row['verdict']}",
                f"- Raw rows: {raw.get('row_count', 0)}",
                f"- Raw dates: {raw.get('first_timestamp')} -> {raw.get('last_timestamp')}",
                f"- Backtest trades: {metrics.get('total_trades', metrics.get('trades', 'n/a'))}",
                f"- Backtest PF/DD: {metrics.get('profit_factor', 'n/a')} / {metrics.get('max_drawdown', 'n/a')}",
                f"- Walk-forward splits: {wf.get('split_count', wf.get('window_count', 'n/a'))}",
                f"- Forward-test bars/status: {ft.get('processed_bars', 'n/a')} / {ft.get('review_status', 'n/a')}",
                f"- Notes: {', '.join(row['notes']) if row['notes'] else 'None'}",
            ]
        )
    lines.extend(["", "## Next Steps"])
    lines.extend(f"- {item}" for item in payload["next_steps"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

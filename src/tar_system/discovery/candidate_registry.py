"""Local JSONL registry for candidate blueprints."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from tar_system.discovery.strategy_blueprint import StrategyBlueprint


def save_candidate(blueprint: StrategyBlueprint, path: str | Path = "data/results/candidates.jsonl") -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    row = asdict(blueprint)
    row["status"] = blueprint.status.value
    with output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=str) + "\n")
    return output


def load_candidates(path: str | Path = "data/results/candidates.jsonl") -> list[dict[str, object]]:
    source = Path(path)
    if not source.exists():
        return []
    return [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]

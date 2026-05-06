"""Local optimiser artifact loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tar_system.settings import DATA_DIR


def result_path(strategy: str, symbol: str, timeframe: str, suffix: str) -> Path:
    return Path(DATA_DIR) / "results" / f"{strategy}_{symbol}_{timeframe}_{suffix}.json"


def load_json_artifact(strategy: str, symbol: str, timeframe: str, suffix: str) -> dict[str, Any] | None:
    path = result_path(strategy, symbol, timeframe, suffix)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_validation_artifacts(strategy: str, symbol: str, timeframe: str) -> dict[str, Any]:
    walk_forward = load_json_artifact(strategy, symbol, timeframe, "walk_forward")
    monte_carlo = load_json_artifact(strategy, symbol, timeframe, "monte_carlo")
    parameter_sensitivity = load_json_artifact(strategy, symbol, timeframe, "parameter_sensitivity")
    return {
        "walk_forward_metrics": _metrics_payload(walk_forward),
        "monte_carlo": monte_carlo,
        "parameter_sensitivity": parameter_sensitivity,
    }


def load_regime_trades(strategy: str, symbol: str, timeframe: str) -> list[dict[str, object]]:
    path = result_path(strategy, symbol, timeframe, "regime_trades")
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("trades"), list):
        return [item for item in data["trades"] if isinstance(item, dict)]
    return []


def _metrics_payload(payload: dict[str, Any] | None) -> dict[str, float] | None:
    if not payload:
        return None
    metrics = payload.get("stitched_metrics", payload.get("metrics", payload))
    return metrics if isinstance(metrics, dict) else None

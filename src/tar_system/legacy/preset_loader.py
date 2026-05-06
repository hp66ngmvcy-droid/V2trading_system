"""Load research-only legacy MT5 risk presets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


PRESET_DIR = Path("configs/legacy_presets")


@dataclass(frozen=True)
class LegacyRiskPreset:
    name: str
    status: str
    source: str
    live_enabled: bool
    requires_validation: bool
    applies_to: dict[str, Any]
    risk: dict[str, float | int | bool]
    spread: dict[str, float]
    stop_constraints: dict[str, float]
    cooldown: dict[str, int]
    breakeven: dict[str, float | bool]
    time_stop: dict[str, int | bool]
    margin: dict[str, float | bool]
    excluded_logic: list[str]
    notes: str = ""

    @property
    def is_research_only(self) -> bool:
        return self.status == "research_only" and not self.live_enabled and self.requires_validation


def load_legacy_risk_preset(name: str = "kama_kt_pullback_fx_risk", preset_dir: str | Path = PRESET_DIR) -> LegacyRiskPreset:
    path = Path(preset_dir) / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Legacy risk preset not found: {path}")
    payload = _load_simple_yaml(path)
    excluded_logic = payload.get("excluded_logic") or []
    if isinstance(excluded_logic, dict):
        excluded_logic = excluded_logic.get("excluded_logic", [])
    preset = LegacyRiskPreset(
        name=str(payload.get("name", name)),
        status=str(payload.get("status", "")),
        source=str(payload.get("source", "")),
        live_enabled=bool(payload.get("live_enabled", True)),
        requires_validation=bool(payload.get("requires_validation", False)),
        applies_to=dict(payload.get("applies_to") or {}),
        risk=dict(payload.get("risk") or {}),
        spread=dict(payload.get("spread") or {}),
        stop_constraints=dict(payload.get("stop_constraints") or {}),
        cooldown=dict(payload.get("cooldown") or {}),
        breakeven=dict(payload.get("breakeven") or {}),
        time_stop=dict(payload.get("time_stop") or {}),
        margin=dict(payload.get("margin") or {}),
        excluded_logic=list(excluded_logic),
        notes=str(payload.get("notes", "")),
    )
    validate_legacy_risk_preset(preset)
    return preset


def validate_legacy_risk_preset(preset: LegacyRiskPreset) -> None:
    if not preset.is_research_only:
        raise ValueError("Legacy presets must be research_only, live_enabled=false and requires_validation=true")
    forbidden = {"pullback_entries", "pending_order_logic", "execution_triggers", "live_order_management"}
    missing = forbidden.difference(set(preset.excluded_logic))
    if missing:
        raise ValueError(f"Legacy preset must explicitly exclude strategy/execution logic: {sorted(missing)}")
    if float(preset.risk.get("max_risk_per_trade_pct", 0.0)) <= 0:
        raise ValueError("Legacy preset risk.max_risk_per_trade_pct must be positive")
    if bool(preset.margin.get("never_use_full_leverage")) is not True:
        raise ValueError("Legacy preset margin.never_use_full_leverage must be true")


def _load_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the small subset of YAML used by local legacy presets.

    This keeps TAR V2 dependency-light. Supported shapes are top-level scalar
    keys, one-level nested mappings, and one-level string lists.
    """
    root: dict[str, Any] = {}
    current_map: dict[str, Any] | None = None
    current_list: list[str] | None = None
    current_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if line.endswith(">"):
            key = line[:-1].strip().rstrip(":")
            root[key] = ""
            current_key = key
            current_map = None
            current_list = None
            continue
        if current_key and isinstance(root.get(current_key), str) and indent > 0 and ":" not in line and not line.startswith("- "):
            root[current_key] = (str(root[current_key]) + " " + line).strip()
            continue
        if indent == 0:
            key, value = _split_yaml_key_value(line)
            current_key = key
            current_list = None
            if value == "":
                current_map = {}
                root[key] = current_map
            else:
                current_map = None
                root[key] = _parse_scalar(value)
            continue
        if current_map is None:
            continue
        if line.startswith("- "):
            if current_list is None:
                current_list = []
                current_map[current_key or "items"] = current_list
            current_list.append(str(_parse_scalar(line[2:].strip())))
            continue
        key, value = _split_yaml_key_value(line)
        if value == "":
            current_list = []
            current_map[key] = current_list
            current_key = key
        else:
            current_map[key] = _parse_scalar(value)
            current_key = key
            current_list = None
    return root


def _split_yaml_key_value(line: str) -> tuple[str, str]:
    if ":" not in line:
        return line, ""
    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value.strip('"').strip("'")

"""Parse local research notes into safe strategy blueprints."""

from __future__ import annotations

from pathlib import Path

from tar_system.discovery.strategy_blueprint import StrategyBlueprint


def parse_strategy_idea(path: str | Path) -> StrategyBlueprint:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    title = source.stem.replace("_", " ")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            break
    return StrategyBlueprint(
        strategy_name=title.lower().replace(" ", "_"),
        source=str(source),
        source_type="markdown",
        asset_class="UNKNOWN",
        timeframe="UNKNOWN",
        entry_logic=_section(text, "entry") or "To be reviewed",
        exit_logic=_section(text, "exit") or "To be reviewed",
        filters=_list_section(text, "filters"),
        risk_rules=_list_section(text, "risk"),
        assumptions=_list_section(text, "assumptions"),
        notes=text[:1000],
    )


def _section(text: str, name: str) -> str:
    lower = name.lower()
    for line in text.splitlines():
        if line.lower().startswith(f"{lower}:"):
            return line.split(":", 1)[1].strip()
    return ""


def _list_section(text: str, name: str) -> list[str]:
    value = _section(text, name)
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]

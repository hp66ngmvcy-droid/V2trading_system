"""Manual local event calendar model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Event:
    name: str
    date: datetime
    impact: str
    shock: bool = False
    event_type: str = "UNKNOWN"
    country: str = "UNKNOWN"
    title: str = ""
    affected_assets: list[str] = field(default_factory=list)
    pre_window_hours: int | None = None
    post_window_hours: int | None = None


def parse_events(raw_events: list[dict[str, object]]) -> list[Event]:
    events: list[Event] = []
    for item in raw_events:
        date_value = item["date"]
        time_value = str(item.get("time", "00:00"))
        if isinstance(date_value, datetime):
            parsed = date_value
        else:
            parsed = datetime.fromisoformat(f"{date_value}T{time_value}")
        event_type = str(item.get("event_type", item.get("name", "UNKNOWN"))).upper()
        title = str(item.get("title", item.get("name", event_type)))
        events.append(
            Event(
                name=title,
                date=parsed,
                impact=str(item.get("impact", "LOW")).upper(),
                shock=bool(item.get("shock", False)),
                event_type=event_type,
                country=str(item.get("country", "UNKNOWN")).upper(),
                title=title,
                affected_assets=[str(asset).upper() for asset in item.get("affected_assets", [])],  # type: ignore[arg-type]
            )
        )
    return events


def load_events(path: str | Path = "configs/events.yaml") -> list[Event] | None:
    source = Path(path)
    if not source.exists():
        bundled = Path(__file__).resolve().parents[3] / "configs" / "events.yaml"
        if str(path) == "configs/events.yaml" and bundled.exists():
            source = bundled
        else:
            return None
    return parse_events(_parse_simple_events_yaml(source.read_text(encoding="utf-8")))


def events_on_date(target_date: datetime, events: list[Event]) -> list[Event]:
    return [event for event in events if event.date.date() == target_date.date()]


def _parse_simple_events_yaml(text: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    list_key: str | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#") or raw_line.strip() == "events:":
            continue
        stripped = raw_line.strip()
        if stripped.startswith("- ") and ":" in stripped:
            if current:
                events.append(current)
            current = {}
            list_key = None
            key, value = stripped[2:].split(":", 1)
            current[key.strip()] = _clean_value(value)
        elif stripped.startswith("- ") and current is not None and list_key:
            current.setdefault(list_key, [])
            current[list_key].append(_clean_value(stripped[2:]))  # type: ignore[union-attr]
        elif ":" in stripped and current is not None:
            key, value = stripped.split(":", 1)
            key = key.strip()
            if value.strip():
                current[key] = _clean_value(value)
                list_key = None
            else:
                current[key] = []
                list_key = key
    if current:
        events.append(current)
    return events


def _clean_value(value: str) -> str:
    return value.strip().strip('"').strip("'")

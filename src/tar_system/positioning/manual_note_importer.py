"""Manual positioning note importer for Codex/ChatGPT/Claude summaries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tar_system.data.csv_importer import hash_csv_file
from tar_system.positioning.store import PositioningRecord, normalise_positioning_date, save_positioning_record


POSITIVE_WORDS = {
    "bullish",
    "long",
    "net long",
    "short squeeze",
    "underweight",
    "accumulation",
    "risk-on",
    "positive gamma support",
}
NEGATIVE_WORDS = {
    "bearish",
    "short",
    "net short",
    "crowded long",
    "overweight",
    "distribution",
    "risk-off",
    "short gamma",
}
CAUTION_WORDS = {"crowded", "squeeze", "overextended", "fragile", "one-sided", "liquidation"}


def import_positioning_note(
    path: str | Path,
    symbol: str,
    source: str = "manual",
    note_date: str | None = None,
) -> PositioningRecord:
    note_path = Path(path)
    text = note_path.read_text(encoding="utf-8")
    payload = _parse_json_note(text) or {}
    score = _score_from_payload(payload, text) if payload else _score_text(text)
    confidence = float(payload.get("confidence", _confidence_from_text(text))) if payload else _confidence_from_text(text)
    date = normalise_positioning_date(payload.get("date") or note_date or "")
    notes = str(payload.get("notes") or _compact_text(text))
    record = PositioningRecord(
        source=f"NOTE_{source.upper()}",
        symbol=symbol.upper(),
        date=date,
        positioning_score=score,
        bias=_bias(score),
        confidence=max(0.0, min(1.0, confidence)),
        notes=notes,
        metrics={
            "keywords": _matched_keywords(text),
            "manual_review_required": True,
            "context_only": True,
        },
        source_file=str(note_path),
        file_hash=hash_csv_file(note_path),
    )
    return save_positioning_record(record)


def _parse_json_note(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped.startswith("{"):
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _score_text(text: str) -> float:
    lower = text.lower()
    score = 0.0
    for word in POSITIVE_WORDS:
        if word in lower:
            score += 12.0
    for word in NEGATIVE_WORDS:
        if word in lower:
            score -= 12.0
    for word in CAUTION_WORDS:
        if word in lower:
            score *= 0.85
    explicit = re.search(r"positioning[_\s-]*score\s*[:=]\s*(-?\d+(?:\.\d+)?)", lower)
    if explicit:
        score = float(explicit.group(1))
    return round(max(-100.0, min(100.0, score)), 2)


def _coerce_score(value: Any) -> float:
    try:
        return round(max(-100.0, min(100.0, float(value))), 2)
    except (TypeError, ValueError):
        return 0.0


def _score_from_payload(payload: dict[str, Any], raw_text: str) -> float:
    if "positioning_score" in payload:
        return _coerce_score(payload.get("positioning_score"))
    searchable = " ".join(str(payload.get(key, "")) for key in ("bias", "notes", "summary", "positioning", "thesis"))
    return _score_text(searchable or raw_text)


def _confidence_from_text(text: str) -> float:
    lower = text.lower()
    confidence = 0.45
    if any(word in lower for word in {"prime brokerage", "gross exposure", "net exposure", "sector tilt"}):
        confidence += 0.2
    if any(word in lower for word in {"rumour", "leaked", "unverified", "unknown source"}):
        confidence -= 0.15
    if re.search(r"\d", text):
        confidence += 0.1
    return round(max(0.1, min(0.85, confidence)), 2)


def _matched_keywords(text: str) -> list[str]:
    lower = text.lower()
    return sorted(word for word in POSITIVE_WORDS | NEGATIVE_WORDS | CAUTION_WORDS if word in lower)


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())[:600]


def _bias(score: float) -> str:
    if score >= 25:
        return "BULLISH"
    if score <= -25:
        return "BEARISH"
    return "NEUTRAL"

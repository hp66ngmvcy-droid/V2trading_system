"""Local JSONL learning memory for V2 research experiments."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Lesson:
    timestamp: str
    category: str
    lesson_text: str
    confidence: float
    evidence: dict[str, Any]
    source_system: str = "tar"


class LearningEngine:
    def __init__(self, memory_dir: str | Path = "memory") -> None:
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.lessons_file = self.memory_dir / "lessons_learned.jsonl"
        self.patterns_file = self.memory_dir / "cross_system_patterns.json"

    def record_lesson(
        self,
        category: str,
        lesson_text: str,
        confidence: float = 0.5,
        evidence: dict[str, Any] | None = None,
    ) -> bool:
        lesson = Lesson(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            category=category,
            lesson_text=lesson_text,
            confidence=max(0.0, min(1.0, confidence)),
            evidence=evidence or {},
        )
        with self.lessons_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(lesson)) + "\n")
        return True

    def read_lessons(self, category: str | None = None) -> list[dict[str, Any]]:
        if not self.lessons_file.exists():
            return []
        lessons: list[dict[str, Any]] = []
        with self.lessons_file.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    lesson = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if category is None or lesson.get("category") == category:
                    lessons.append(lesson)
        return lessons

    def summarize_by_category(self) -> dict[str, dict[str, Any]]:
        summary: dict[str, dict[str, Any]] = {}
        for lesson in self.read_lessons():
            category = str(lesson.get("category", "uncategorized"))
            bucket = summary.setdefault(
                category,
                {"count": 0, "high_confidence_lessons": 0, "avg_confidence": 0.0, "top_lessons": []},
            )
            bucket["count"] += 1
            confidence = float(lesson.get("confidence", 0.0))
            bucket["avg_confidence"] += confidence
            if confidence >= 0.75:
                bucket["high_confidence_lessons"] += 1
                bucket["top_lessons"].append(str(lesson.get("lesson_text", "")))
        for bucket in summary.values():
            if bucket["count"]:
                bucket["avg_confidence"] = round(bucket["avg_confidence"] / bucket["count"], 2)
            bucket["top_lessons"] = bucket["top_lessons"][:5]
        return summary

    def render_summary(self) -> str:
        lines = ["# TAR Learning Summary", ""]
        for category, stats in sorted(self.summarize_by_category().items()):
            lines.extend(
                [
                    f"## {category}",
                    f"- Lessons: {stats['count']}",
                    f"- High confidence: {stats['high_confidence_lessons']}",
                    f"- Average confidence: {stats['avg_confidence']}",
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

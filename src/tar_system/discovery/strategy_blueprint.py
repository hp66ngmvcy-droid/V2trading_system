"""Strategy blueprint contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CandidateStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    BLUEPRINTED = "BLUEPRINTED"
    GENERATED = "GENERATED"
    BACKTESTED = "BACKTESTED"
    WALK_FORWARD_TESTED = "WALK_FORWARD_TESTED"
    SCORED = "SCORED"
    OBSIDIAN_REVIEWED = "OBSIDIAN_REVIEWED"
    KEEP = "KEEP"
    REVIEW = "REVIEW"
    KILL = "KILL"


@dataclass
class StrategyBlueprint:
    strategy_name: str
    source: str
    source_type: str
    asset_class: str
    timeframe: str
    entry_logic: str
    exit_logic: str
    filters: list[str] = field(default_factory=list)
    risk_rules: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    licence_status: str = "UNKNOWN"
    safety_status: str = "CANDIDATE_ONLY"
    notes: str = ""
    status: CandidateStatus = CandidateStatus.BLUEPRINTED

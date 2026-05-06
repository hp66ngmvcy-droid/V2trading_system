"""Oversight agent for paper-only workflow routing."""

from __future__ import annotations

from dataclasses import dataclass

from tar_system.audit.writer import append_audit_event
from tar_system.settings import LIVE_TRADING_ALLOWED, PAPER_MODE


@dataclass
class OversightDecision:
    approved: bool
    next_step: str
    reason_code: str
    message: str


class OversightAgent:
    def decide_next_step(self, requested_step: str) -> OversightDecision:
        if not PAPER_MODE or LIVE_TRADING_ALLOWED:
            decision = OversightDecision(False, "stop", "SECURITY_BLOCKED_LIVE_TRADING", "Paper-only mode is required")
        else:
            decision = OversightDecision(True, requested_step, "PIPELINE_STAGE_COMPLETED", "Approved for paper-only workflow")
        append_audit_event("oversight_agent", "oversight", "", "", "APPROVED" if decision.approved else "BLOCKED", decision.reason_code, {"next_step": decision.next_step})
        return decision

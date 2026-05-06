"""Audit agent wrapper."""

from __future__ import annotations

from tar_system.audit.writer import append_audit_event


class AuditAgent:
    def run(self, *args: object, **kwargs: object) -> object:
        return append_audit_event(*args, **kwargs)  # type: ignore[arg-type]

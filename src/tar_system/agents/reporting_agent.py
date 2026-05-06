"""Reporting agent wrapper."""

from __future__ import annotations

from tar_system.reporting.reporter import generate_report


class ReportingAgent:
    def run(self, *args: object, **kwargs: object) -> object:
        return generate_report(*args, **kwargs)  # type: ignore[arg-type]

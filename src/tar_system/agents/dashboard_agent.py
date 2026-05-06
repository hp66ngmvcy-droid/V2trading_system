"""Dashboard agent wrapper."""

from __future__ import annotations

from tar_system.dashboard.runtime_control import read_backtest_status, read_forward_status


class DashboardAgent:
    def run(self) -> dict[str, object]:
        return {"backtest": read_backtest_status(), "forward_test": read_forward_status()}

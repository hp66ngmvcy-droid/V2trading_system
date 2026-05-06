"""Lean paper-only security checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from tar_system import settings


@dataclass
class SecurityCheckResult:
    passed: bool
    findings: list[str] = field(default_factory=list)


def run_security_checks(root: str | Path = ".") -> SecurityCheckResult:
    base = Path(root)
    findings: list[str] = []
    if not settings.PAPER_MODE:
        findings.append("PAPER_MODE_NOT_TRUE")
    if settings.LIVE_TRADING_ALLOWED:
        findings.append("LIVE_TRADING_ALLOWED_TRUE")
    gitignore = base / ".gitignore"
    if not gitignore.exists() or ".env" not in gitignore.read_text(encoding="utf-8"):
        findings.append("ENV_NOT_IGNORED")
    key_terms = ["BROKER_KEY", "BROKER_SECRET", "MT5_PASSWORD", "API_SECRET"]
    for path in list((base / "configs").glob("*")) if (base / "configs").exists() else []:
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore").upper()
            if any(term in text for term in key_terms):
                findings.append(f"CONFIG_SECRET_NAME:{path.name}")
    dashboard = base / "src/tar_system/dashboard/app.py"
    if dashboard.exists() and any(term in dashboard.read_text(encoding="utf-8").lower() for term in ["place_order", "send_order", "live_trade"]):
        findings.append("DASHBOARD_TRADING_FUNCTION")
    exporter = base / "src/tar_system/exports/mt5_exporter.py"
    if exporter.exists() and any(term in exporter.read_text(encoding="utf-8").lower() for term in ["order_send", "login(", "metatrader5"]):
        findings.append("MT5_EXPORTER_ORDER_FUNCTION")
    return SecurityCheckResult(not findings, findings)

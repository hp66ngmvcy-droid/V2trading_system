"""Lean Obsidian vault exporter."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VAULT_DIRS = ["00_Index", "10_Strategies", "20_Patterns", "30_Regimes", "40_Failures", "50_Winners", "_meta"]


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in value)


def _tags(result: dict[str, Any]) -> list[str]:
    metrics = result.get("metrics", {})
    verdict = str(result.get("verdict", "review")).lower()
    symbol = str(result.get("symbol", "UNKNOWN"))
    timeframe = str(result.get("timeframe", "NA"))
    tags = ["#type/strategy", f"#asset/{symbol}", f"#tf/{timeframe}", f"#verdict/{verdict}"]
    regime = str(result.get("regime", "unknown")).lower()
    if regime in {"trending", "ranging", "volatile"}:
        tags.append(f"#regime/{regime}")
    if metrics.get("win_rate", 0) >= 0.6:
        tags.append("#metric/high_win")
    if metrics.get("max_drawdown", 1) <= 0.1:
        tags.append("#metric/low_dd")
    if metrics.get("profit_factor", 0) >= 1.5:
        tags.append("#metric/high_pf")
    if metrics.get("total_trades", 0) < 20:
        tags.append("#metric/low_trades")
    if metrics.get("parameter_stability", 100) < 60:
        tags.append("#metric/unstable")
    return tags


def ensure_vault(root: str | Path = "obsidian") -> Path:
    vault = Path(root)
    for directory in VAULT_DIRS:
        (vault / directory).mkdir(parents=True, exist_ok=True)
    return vault


def export_strategy_note(result: dict[str, Any], root: str | Path = "obsidian") -> Path:
    vault = ensure_vault(root)
    date = datetime.now(timezone.utc).date().isoformat()
    strategy = str(result.get("strategy", "unknown"))
    symbol = str(result.get("symbol", "UNKNOWN"))
    timeframe = str(result.get("timeframe", "NA"))
    note_id = f"{strategy}_{symbol}_{timeframe}_{date}"
    metrics = result.get("metrics", {})
    frontmatter = {
        "id": note_id,
        "type": "strategy",
        "strategy": strategy,
        "version": result.get("version", ""),
        "asset": symbol,
        "timeframe": timeframe,
        "date": date,
        "metrics": metrics,
        "score": result.get("score", 0),
        "verdict": result.get("verdict", "REVIEW"),
        "regime": result.get("regime", "unknown"),
        "tags": _tags(result),
    }
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {json.dumps(value)}")
    lines.extend(["---", "", f"# {strategy} {symbol} {timeframe}", "", "## Metrics", ""])
    for key, value in dict(metrics).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Review", "", f"- Verdict: {result.get('verdict', 'REVIEW')}", f"- Reason: {result.get('reason', '')}"])
    path = vault / "10_Strategies" / f"{_safe_name(note_id)}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def update_indexes(root: str | Path = "obsidian") -> None:
    vault = ensure_vault(root)
    strategy_notes = sorted((vault / "10_Strategies").glob("*.md"))
    (vault / "00_Index" / "Strategies.md").write_text(
        "# Strategies\n\n" + "\n".join(f"- [[{path.stem}]]" for path in strategy_notes) + "\n",
        encoding="utf-8",
    )
    (vault / "00_Index" / "Home.md").write_text("# TAR Research Vault\n\n- [[Strategies]]\n", encoding="utf-8")


def export_result(result: dict[str, Any], root: str | Path = "obsidian") -> Path:
    note = export_strategy_note(result, root)
    vault = ensure_vault(root)
    for reason in result.get("reason_codes", []) or []:
        name = _safe_name(str(reason))
        folder = "40_Failures" if "HIGH" in name or "LOW" in name or "WEAK" in name else "20_Patterns"
        (vault / folder / f"{name}.md").write_text(f"# {reason}\n\nGenerated from review reason codes.\n", encoding="utf-8")
    update_indexes(root)
    return note

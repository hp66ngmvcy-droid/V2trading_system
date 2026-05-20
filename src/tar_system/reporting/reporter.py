"""Research report generation."""

from __future__ import annotations

import json
from pathlib import Path

from tar_system.settings import REPORT_DIR


def generate_report(
    strategy: str,
    symbol: str,
    timeframe: str,
    metrics: dict[str, float],
    score: float,
    verdict: str,
    environment_state: str,
    reason_codes: list[str],
    next_action: str,
    output_format: str = "md",
    optimiser: dict[str, object] | None = None,
    positioning: dict[str, object] | None = None,
) -> Path:
    if positioning is None:
        try:
            from tar_system.positioning.scorer import get_positioning_context

            positioning = get_positioning_context(symbol)
        except Exception:
            positioning = {}
    output_dir = Path(REPORT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "strategy": strategy,
        "symbol": symbol,
        "timeframe": timeframe,
        "metrics": metrics,
        "score": score,
        "verdict": verdict,
        "environment_state": environment_state,
        "reason_codes": reason_codes,
        "next_action": next_action,
        "optimiser": optimiser or {},
        "positioning": positioning or {},
    }
    stem = f"{symbol}_{timeframe}_{strategy}_report"
    if output_format == "json":
        path = output_dir / f"{stem}.json"
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return path
    path = output_dir / f"{stem}.md"
    lines = [f"# {strategy} Review Report", "", f"- Strategy: {strategy}", f"- Symbol: {symbol}", f"- Timeframe: {timeframe}"]
    lines.extend([f"- Score: {score}", f"- Verdict: {verdict}", f"- Environment State: {environment_state}", f"- Next Action: {next_action}", ""])
    lines.append("## Metrics")
    for key, value in metrics.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Reason Codes"])
    lines.extend([f"- {code}" for code in reason_codes] or ["- None"])
    if positioning:
        lines.extend(
            [
                "",
                "## Positioning Context",
                "",
                f"- Score: {positioning.get('positioning_score', 0.0)}",
                f"- Bias: {positioning.get('bias', 'NEUTRAL')}",
                f"- Confidence: {positioning.get('confidence', 0.0)}",
                "- Use: Context only, not an automatic trade trigger",
            ]
        )
        for source in positioning.get("sources", []) or []:
            if isinstance(source, dict):
                lines.append(f"- Source {source.get('source')}: {source.get('bias')} score={source.get('positioning_score')}")
    equity_path = Path("data/results") / f"{symbol}_{timeframe}_{strategy}_equity.json"
    if equity_path.exists():
        lines.extend(["", "## Equity Curve", f"- Export: {equity_path}"])
    if optimiser:
        lines.extend(["", "## Optimiser", ""])
        lines.append(f"- Optimiser Score: {optimiser.get('optimiser_score', 0)}")
        lines.append(f"- Optimiser Decision: {optimiser.get('optimiser_decision', 'REVIEW')}")
        lines.append(f"- GO / NO-GO: {optimiser.get('go_no_go_status', 'NO_GO')}")
        lines.append(f"- Risk Adjustment: {optimiser.get('risk_adjustment', 'STANDARD_PAPER_RISK')}")
        lines.append("")
        lines.append("### Improvement Plan")
        for item in optimiser.get("improvement_plan", []) or []:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("### Next Actions")
        for item in optimiser.get("next_actions", []) or []:
            lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def generate_quant_report(
    strategy: str,
    symbol: str,
    timeframe: str,
    metrics: dict[str, float],
    signal: dict[str, object] | None = None,
    health: dict[str, object] | None = None,
) -> Path:
    """Generate a print-ready quant report in Markdown."""
    output_dir = Path(REPORT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{symbol}_{timeframe}_{strategy}_quant_report.md"
    signal = signal or {}
    health = health or {}
    equity = _load_equity_summary(strategy, symbol, timeframe)
    lines = [
        f"# {strategy} Quant Report",
        "",
        "## Summary",
        f"- Strategy: {strategy}",
        f"- Symbol: {symbol}",
        f"- Timeframe: {timeframe}",
        "- Mode: paper-only",
        f"- Health Status: {health.get('status', 'UNKNOWN')}",
        f"- Health Recommendation: {health.get('recommendation', 'Review manually')}",
        f"- Latest Signal: {signal.get('side', 'N/A')}",
        f"- Risk Decision: {signal.get('risk_reason', 'N/A')}",
        "",
        "## Performance",
    ]
    for key in [
        "total_trades",
        "win_rate",
        "profit_factor",
        "max_drawdown",
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
        "net_profit",
    ]:
        if key in metrics:
            lines.append(f"- {key}: {metrics[key]}")
    if not any(key in metrics for key in ["total_trades", "win_rate", "profit_factor", "max_drawdown", "net_profit"]):
        lines.append("- No backtest metrics found yet")
    lines.extend(
        [
            "",
            "## Equity Summary",
            f"- Start Equity: {equity.get('start_equity', 'N/A')}",
            f"- End Equity: {equity.get('end_equity', 'N/A')}",
            f"- Peak Equity: {equity.get('peak_equity', 'N/A')}",
            f"- Max Equity Drawdown: {equity.get('max_drawdown_pct', 'N/A')}",
            f"- Equity Points: {equity.get('points', 0)}",
        ]
    )
    if health.get("reason_codes"):
        lines.extend(["", "## Health Reasons"])
        lines.extend(f"- {code}" for code in health.get("reason_codes", []))
    lines.extend(
        [
            "",
            "## Latest Paper Signal",
            f"- Side: {signal.get('side', 'N/A')}",
            f"- Confidence: {signal.get('confidence', 'N/A')}",
            f"- Entry: {signal.get('entry', 'N/A')}",
            f"- Stop Loss: {signal.get('stop_loss', 'N/A')}",
            f"- Take Profit: {signal.get('take_profit', 'N/A')}",
            f"- Risk Approved: {signal.get('risk_approved', 'N/A')}",
            f"- Risk Reason: {signal.get('risk_reason', 'N/A')}",
            "",
            "## Controls",
            "- Live order execution: disabled",
            "- Human review required before any external action",
            "- Circuit breakers: daily loss, weekly loss and consecutive-loss gates",
            "",
            "## Next Review",
            "- Check sample size before promoting confidence",
            "- Re-run multi-asset and walk-forward validation after parameter changes",
            "- Keep paper-only status unless explicitly reviewed outside this report",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _write_basic_pdf(path.with_suffix(".pdf"), lines)
    return path


def _load_equity_summary(strategy: str, symbol: str, timeframe: str) -> dict[str, object]:
    path = Path("data/results") / f"{symbol}_{timeframe}_{strategy}_equity.json"
    if not path.exists():
        return {}
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(rows, list) or not rows:
        return {}
    equities = [float(row.get("equity", 0.0) or 0.0) for row in rows if isinstance(row, dict)]
    drawdowns = [float(row.get("drawdown_pct", 0.0) or 0.0) for row in rows if isinstance(row, dict)]
    if not equities:
        return {}
    return {
        "start_equity": equities[0],
        "end_equity": equities[-1],
        "peak_equity": max(equities),
        "max_drawdown_pct": max(drawdowns) if drawdowns else 0.0,
        "points": len(equities),
    }


def _write_basic_pdf(path: Path, lines: list[str]) -> Path:
    wrapped: list[str] = []
    for line in lines:
        text = line.replace("#", "").strip()
        if not text:
            wrapped.append("")
            continue
        while len(text) > 88:
            wrapped.append(text[:88])
            text = text[88:]
        wrapped.append(text)

    page_lines = wrapped[:42]
    stream_lines = ["BT", "/F1 10 Tf", "50 780 Td"]
    for index, line in enumerate(page_lines):
        if index:
            stream_lines.append("0 -16 Td")
        stream_lines.append(f"({_pdf_escape(line)}) Tj")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    payload = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{number} 0 obj\n".encode("ascii"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    path.write_bytes(bytes(payload))
    return path


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


if __name__ == "__main__":
    print("Use python -m tar_system.cli generate-report")


def generate_variant_comparison_report(symbol: str, timeframe: str) -> Path:
    from tar_system.scoring.scorer import score_strategy

    output_dir = Path(REPORT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for metrics_path in sorted(Path("data/results").glob(f"*_{symbol}_{timeframe}_metrics.json")):
        strategy = metrics_path.name[: -len(f"_{symbol}_{timeframe}_metrics.json")]
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        score = score_strategy(metrics)
        cost_path = Path("data/results") / f"{strategy}_{symbol}_{timeframe}_cost_analysis.json"
        cost_payload: dict[str, object] = {}
        if cost_path.exists():
            try:
                cost_payload = json.loads(cost_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                cost_payload = {}
        rows.append(
            {
                "strategy": strategy,
                "win_rate": float(metrics.get("win_rate", 0.0)),
                "pf": float(metrics.get("profit_factor", 0.0)),
                "drawdown": float(metrics.get("max_drawdown", 0.0)),
                "trades": float(metrics.get("total_trades", 0.0)),
                "sharpe": float(metrics.get("sharpe_ratio", 0.0)),
                "realistic_score": float(cost_payload.get("realistic_score", 0.0)),
                "cost_sensitive": bool(cost_payload.get("cost_sensitive", False)),
                "score": score.score,
                "verdict": score.verdict,
            }
        )
    rows.sort(key=lambda item: (float(item["score"]), float(item["pf"]), -float(item["drawdown"])), reverse=True)
    path = output_dir / f"{symbol}_{timeframe}_variant_comparison.md"
    best = _best_values(rows)
    lines = [f"# {symbol} {timeframe} Variant Comparison", ""]
    headers = ["strategy", "win_rate", "pf", "drawdown", "trades", "sharpe", "realistic_score", "cost_sensitive", "score", "verdict"]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        values = [_format_variant_value(row, key, best) for key in headers]
        lines.append("| " + " | ".join(values) + " |")
    if not rows:
        lines.append("| No metrics found |  |  |  |  |  |  |  |  |  |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def load_variant_comparison_rows(symbol: str, timeframe: str) -> list[dict[str, object]]:
    path = generate_variant_comparison_report(symbol, timeframe)
    return [{"report_path": str(path), "symbol": symbol, "timeframe": timeframe}]


def _best_values(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    return {
        "win_rate": max(row["win_rate"] for row in rows),
        "pf": max(row["pf"] for row in rows),
        "drawdown": min(row["drawdown"] for row in rows),
        "trades": max(row["trades"] for row in rows),
        "sharpe": max(row["sharpe"] for row in rows),
        "realistic_score": max(row["realistic_score"] for row in rows),
        "score": max(row["score"] for row in rows),
    }


def _format_variant_value(row: dict[str, object], key: str, best: dict[str, object]) -> str:
    value = row[key]
    if key == "cost_sensitive":
        return "AMBER" if value else "false"
    text = f"{value:.4f}" if isinstance(value, float) else str(value)
    if key in best and value == best[key]:
        return f"**{text}**"
    return text

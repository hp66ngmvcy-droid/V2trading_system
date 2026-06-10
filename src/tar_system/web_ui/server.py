"""Stdlib local web server for the integrated TAR V2 research UI."""

from __future__ import annotations

import json
import mimetypes
import os
import re
from dataclasses import asdict
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse



ROOT = Path.cwd()
UI_DIR = ROOT / "ui" / "research-ui"
PROTOTYPE_DIR = ROOT / "ui" / "research-ui-prototype"

TRADINGVIEW_SYMBOLS = {
    "XAUUSD": "OANDA:XAUUSD",
    "XAGUSD": "OANDA:XAGUSD",
    "BTCUSD": "BITSTAMP:BTCUSD",
    "ETHUSD": "BITSTAMP:ETHUSD",
    "EURUSD": "OANDA:EURUSD",
    "GBPUSD": "OANDA:GBPUSD",
    "USDJPY": "OANDA:USDJPY",
    "USOIL": "TVC:USOIL",
}

TRADINGVIEW_INTERVALS = {
    "M1": "1",
    "M5": "5",
    "M15": "15",
    "M30": "30",
    "H1": "60",
    "H4": "240",
    "D1": "D",
}

SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
WRITE_API_PATHS = {
    "/api/jobs/queue-paper-research",
    "/api/jobs/queue-paper-signal",
    "/api/jobs/queue-all-tests",
    "/api/research/scout",
    "/api/tasks/stop-active",
}


def live_reference_url(symbol: str, timeframe: str) -> str:
    from urllib.parse import quote

    tv_symbol = TRADINGVIEW_SYMBOLS.get(symbol.upper(), f"OANDA:{symbol.upper()}")
    interval = TRADINGVIEW_INTERVALS.get(timeframe.upper(), "15")
    return f"https://www.tradingview.com/chart/?symbol={quote(tv_symbol, safe='')}&interval={quote(interval, safe='')}"


def parse_metrics_filename(path: Path) -> tuple[str, str, str] | None:
    stem = path.stem
    suffix = "_metrics"
    if not stem.endswith(suffix):
        return None
    core = stem[: -len(suffix)]
    parts = core.split("_")
    if len(parts) < 3:
        return None
    strategy = "_".join(parts[:-2])
    symbol = parts[-2]
    timeframe = parts[-1]
    if not strategy or not symbol or not timeframe:
        return None
    return strategy, symbol, timeframe


def _token_usage_status(base: Path) -> dict[str, Any]:
    candidates = [
        base / "runtime" / "token_usage.json",
        base / "logs" / "token_usage.json",
        base / "logs" / "token_usage.jsonl",
    ]
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        try:
            if path.suffix == ".jsonl":
                return _token_usage_from_jsonl(path)
            return _token_usage_from_json(path)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return {
                "tracked": False,
                "source": str(path),
                "summary_text": f"Token usage file found but could not be read: {exc}",
            }
    return {
        "tracked": False,
        "source": "",
        "summary_text": "Token usage is not tracked locally yet. Add runtime/token_usage.json or logs/token_usage.jsonl to show input, output, and total token counts here.",
    }


def _token_usage_from_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("token usage JSON must be an object")
    return _normalise_token_usage(payload, path)


def _token_usage_from_jsonl(path: Path) -> dict[str, Any]:
    totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "requests": 0}
    last_seen = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            continue
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else payload
        totals["input_tokens"] += _int_value(usage.get("input_tokens") or usage.get("prompt_tokens"))
        totals["output_tokens"] += _int_value(usage.get("output_tokens") or usage.get("completion_tokens"))
        totals["total_tokens"] += _int_value(usage.get("total_tokens"))
        totals["requests"] += 1
        last_seen = str(payload.get("created_at") or payload.get("timestamp") or last_seen)
    if not totals["total_tokens"]:
        totals["total_tokens"] = totals["input_tokens"] + totals["output_tokens"]
    if last_seen:
        totals["updated_at"] = last_seen
    return _normalise_token_usage(totals, path)


def _normalise_token_usage(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else payload
    input_tokens = _int_value(usage.get("input_tokens") or usage.get("prompt_tokens"))
    output_tokens = _int_value(usage.get("output_tokens") or usage.get("completion_tokens"))
    total_tokens = _int_value(usage.get("total_tokens")) or input_tokens + output_tokens
    requests = _int_value(usage.get("requests") or usage.get("request_count"))
    updated_at = str(usage.get("updated_at") or usage.get("created_at") or usage.get("timestamp") or "")
    lines = [
        f"source: {path}",
        "tracked: true",
        f"input_tokens: {input_tokens:,}",
        f"output_tokens: {output_tokens:,}",
        f"total_tokens: {total_tokens:,}",
    ]
    if requests:
        lines.append(f"requests: {requests:,}")
    if updated_at:
        lines.append(f"updated_at: {updated_at}")
    return {
        "tracked": True,
        "source": str(path),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "requests": requests,
        "updated_at": updated_at,
        "summary_text": "\n".join(lines),
    }


def _int_value(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def build_snapshot(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root)
    strategies = _strategy_rows(base)
    jobs = _job_rows()
    imported = _imported_data_rows(base)
    signal = _paper_signal(base)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "STRATEGIES": strategies,
        "JOBS": jobs,
        "PAPER_SIGNAL": signal,
        "FORWARD_TESTS": _forward_test_rows(base),
        "COMMITTEE_REPORTS": _committee_rows(base, strategies),
        "STATIC_FINDINGS": _static_findings(base),
        "IMPORTED_DATA": imported,
        "AUDIT_LOG": _audit_rows(base),
        "QUEUE_HEALTH": _queue_health(),
        "ONLINE_RESEARCH": _online_research_status(),
        "TOKEN_USAGE": _token_usage_status(base),
    }


def run(host: str = "127.0.0.1", port: int = 8601) -> None:
    server = ThreadingHTTPServer((host, port), ResearchUIHandler)
    print(f"TAR V2 Research UI running at http://{host}:{port}")
    print("Read-only UI bridge: strategy actions remain queue/CLI controlled.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping TAR V2 Research UI...")
    finally:
        server.server_close()


class ResearchUIHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path in {"/", "/index.html"}:
            return self._send_file(UI_DIR / "index.html", "text/html; charset=utf-8")
        if path == "/api/snapshot":
            return self._send_json(build_snapshot(ROOT))
        if path == "/runtime-data.js":
            payload = json.dumps(build_snapshot(ROOT), default=str)
            return self._send_bytes(f"window.TAR_SNAPSHOT = {payload};\n".encode("utf-8"), "application/javascript; charset=utf-8")
        if path.startswith("/prototype/"):
            requested = (PROTOTYPE_DIR / path.removeprefix("/prototype/")).resolve()
            if not _is_relative_to(requested, PROTOTYPE_DIR.resolve()):
                return self.send_error(403)
            return self._send_file(requested)
        return self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path not in WRITE_API_PATHS:
            return self.send_error(404)
        try:
            payload = self._read_json_body()
            result = handle_api_post(path, payload)
        except ValueError as exc:
            return self._send_json({"ok": False, "error": str(exc)}, status=400)
        except RuntimeError as exc:
            return self._send_json({"ok": False, "error": str(exc)}, status=409)
        return self._send_json(result, status=200)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[web-ui] {self.address_string()} - {format % args}")

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        if length > 16_384:
            raise ValueError("Request body too large")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON body") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _send_json(self, payload: Any, status: int = 200) -> None:
        self._send_bytes(
            json.dumps(payload, default=str, indent=2).encode("utf-8"),
            "application/json; charset=utf-8",
            status=status,
        )

    def _send_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            return self.send_error(404)
        guessed = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self._send_bytes(path.read_bytes(), guessed)

    def _send_bytes(self, data: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def handle_api_post(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Handle local UI write actions. All actions are paper-only and queue-first."""
    payload = payload or {}
    if path == "/api/jobs/queue-paper-research":
        return queue_paper_research(payload)
    if path == "/api/jobs/queue-paper-signal":
        return queue_paper_signal(payload)
    if path == "/api/jobs/queue-all-tests":
        return queue_all_tests(payload)
    if path == "/api/research/scout":
        return run_online_scout(payload)
    if path == "/api/tasks/stop-active":
        return stop_active_task()
    raise ValueError(f"Unsupported API path: {path}")


def queue_paper_research(payload: dict[str, Any]) -> dict[str, Any]:
    from tar_system.controller.job_queue import add_job

    strategy = _safe_token(payload.get("strategy"), "strategy", default="gold_v2")
    symbol = _safe_token(payload.get("symbol"), "symbol", default="XAUUSD").upper()
    timeframe = _safe_token(payload.get("timeframe") or payload.get("tf"), "timeframe", default="M15").upper()
    raw_file = _safe_raw_csv(payload.get("file"), symbol, timeframe)
    job = add_job(
        strategy,
        symbol,
        timeframe,
        str(raw_file),
        broker=_safe_token(payload.get("broker"), "broker", default="current_broker_demo"),
        from_date=_optional_date(payload.get("from_date"), "from_date"),
        to_date=_optional_date(payload.get("to_date"), "to_date"),
        skip_walk_forward=bool(payload.get("skip_walk_forward", False)),
        skip_forward_test=bool(payload.get("skip_forward_test", False)),
        max_walk_forward_splits=int(payload.get("max_walk_forward_splits") or 100),
        research_stage=_safe_token(payload.get("research_stage"), "research_stage", default="ui_paper_research"),
        no_live=True,
        no_mt5_promotion=True,
        require_walk_forward=not bool(payload.get("skip_walk_forward", False)),
    )
    return {"ok": True, "action": "queue-paper-research", "job": job, "queue_health": _queue_health()}


def queue_paper_signal(payload: dict[str, Any]) -> dict[str, Any]:
    from tar_system.controller.job_queue import add_job

    strategy = _safe_token(payload.get("strategy"), "strategy", default="gold_v2")
    symbol = _safe_token(payload.get("symbol"), "symbol", default="XAUUSD").upper()
    timeframe = _safe_token(payload.get("timeframe") or payload.get("tf"), "timeframe", default="M15").upper()
    raw_file = _safe_raw_csv(payload.get("file"), symbol, timeframe, require_exists=False)
    job = add_job(
        strategy,
        symbol,
        timeframe,
        str(raw_file),
        broker=_safe_token(payload.get("broker"), "broker", default="current_broker_demo"),
        job_type="paper_signal",
        priority=5,
        skip_walk_forward=True,
        skip_forward_test=True,
        max_walk_forward_splits=1,
        research_stage="ui_paper_signal",
        no_live=True,
        no_mt5_promotion=True,
        require_walk_forward=False,
        require_min_trades=False,
    )
    return {"ok": True, "action": "queue-paper-signal", "job": job, "queue_health": _queue_health()}


def queue_all_tests(payload: dict[str, Any]) -> dict[str, Any]:
    from tar_system.controller.data_watcher import scan_raw_data

    max_jobs = int(payload.get("max_jobs") or 24)
    if max_jobs < 1 or max_jobs > 200:
        raise ValueError("max_jobs must be between 1 and 200")
    queued = scan_raw_data(
        force=bool(payload.get("force", False)),
        research_stage=_safe_token(payload.get("research_stage"), "research_stage", default="ui_all_tests"),
        from_date=_optional_date(payload.get("from_date"), "from_date"),
        to_date=_optional_date(payload.get("to_date"), "to_date"),
        skip_walk_forward=bool(payload.get("skip_walk_forward", True)),
        skip_forward_test=bool(payload.get("skip_forward_test", True)),
        max_walk_forward_splits=int(payload.get("max_walk_forward_splits") or 10),
        max_jobs=max_jobs,
        no_live=True,
        no_mt5_promotion=True,
        require_walk_forward=False,
    )
    return {"ok": True, "action": "queue-all-tests", "queued_jobs": queued, "queued_count": len(queued), "queue_health": _queue_health()}


def stop_active_task() -> dict[str, Any]:
    from tar_system.dashboard.runtime_control import request_stop_active_task, request_stop_backtest, request_stop_forward_test

    status = request_stop_active_task()
    request_stop_backtest()
    request_stop_forward_test()
    return {"ok": True, "action": "stop-active", "status": status, "queue_health": _queue_health()}


def run_online_scout(payload: dict[str, Any]) -> dict[str, Any]:
    from tar_system.research.exa_searcher import broad_sweep, multi_agent_search
    from tar_system.research.hypothesis_notes import write_hypothesis_notes

    query = _safe_search_text(payload.get("query"), default="")
    raw_topics = payload.get("topics") or []
    if isinstance(raw_topics, str):
        topics = [_safe_search_text(topic, default="") for topic in raw_topics.split(",")]
    elif isinstance(raw_topics, list):
        topics = [_safe_search_text(topic, default="") for topic in raw_topics]
    else:
        raise ValueError("topics must be a list or comma-separated string")
    topics = [topic for topic in topics if topic]
    if not query and not topics:
        raise ValueError("query or topics is required")

    num_results = _bounded_int(payload.get("num_results"), "num_results", default=3, minimum=1, maximum=20)
    max_workers = _bounded_int(payload.get("max_workers"), "max_workers", default=min(3, max(1, len(topics) or 3)), minimum=1, maximum=8)
    source_quality = str(payload.get("source_quality") or "strict")
    if source_quality not in {"balanced", "strict", "off"}:
        raise ValueError("source_quality must be balanced, strict, or off")

    result: dict[str, Any] = {
        "ok": True,
        "action": "online-scout",
        "online_research": _online_research_status(),
        "exa_sweep": broad_sweep(topics, num_results=num_results, max_workers=max_workers, source_quality=source_quality, use_cache=True) if topics else None,
        "exa_multi_agent_search": multi_agent_search(query, num_results=num_results, max_workers=max_workers, source_quality=source_quality, use_cache=True) if query else None,
    }
    if bool(payload.get("generate_hypotheses", True)):
        result["hypothesis_notes"] = write_hypothesis_notes(
            result,
            output_dir=str(payload.get("hypothesis_dir") or "ideas/research_queue"),
            min_score=_bounded_int(payload.get("min_source_score"), "min_source_score", default=70, minimum=0, maximum=100),
            limit=_bounded_int(payload.get("hypothesis_limit"), "hypothesis_limit", default=10, minimum=1, maximum=50),
        )
    if bool(payload.get("save_output", True)):
        output_path = _online_scout_output_path(query or topics[0])
        output_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        result["saved_to"] = str(output_path)
    return result


def _strategy_rows(base: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    metric_paths = sorted(
        (base / "data" / "results").glob("*_metrics.json"),
        key=lambda item: item.stat().st_mtime if item.exists() else 0,
        reverse=True,
    )[:80]
    for path in metric_paths:
        parsed = parse_metrics_filename(path)
        if parsed is None:
            continue
        metrics = _read_json(path)
        if not metrics:
            continue
        strategy, symbol, timeframe = parsed
        rows.append(_strategy_row_from_metrics({"strategy": strategy, "symbol": symbol, "timeframe": timeframe, **metrics}))
    rows.sort(key=lambda row: float(row.get("score") or 0.0), reverse=True)
    return rows


def _strategy_row_from_metrics(row: dict[str, Any]) -> dict[str, Any]:
    strategy = str(row.get("strategy") or "unknown")
    symbol = str(row.get("symbol") or "UNKNOWN")
    timeframe = str(row.get("timeframe") or row.get("tf") or "M15")
    trades = int(float(row.get("total_trades") or row.get("trades") or 0))
    profit_factor = _maybe_float(row.get("profit_factor") or row.get("pf"))
    max_drawdown = _maybe_float(row.get("max_drawdown") or row.get("max_dd"))
    score = _maybe_float(row.get("score"))
    if score is None:
        score = _simple_score(row)
    return {
        "strategy": strategy,
        "symbol": symbol,
        "tf": timeframe,
        "score": score if score is not None else 0.0,
        "verdict": str(row.get("verdict") or "REVIEW"),
        "trades": trades,
        "sharpe": _maybe_float(row.get("sharpe_ratio") or row.get("sharpe")),
        "sortino": _maybe_float(row.get("sortino_ratio") or row.get("sortino")),
        "win_rate": _maybe_float(row.get("win_rate")),
        "pf": profit_factor,
        "max_dd": (max_drawdown * 100.0 if max_drawdown is not None and max_drawdown <= 1 else max_drawdown),
        "net_pnl": _maybe_float(row.get("net_pnl") or row.get("total_pnl")),
        "oos_sharpe": _maybe_float(row.get("oos_sharpe") or row.get("walk_forward_sharpe")),
        "spans_zero": bool(row.get("spans_zero", False)),
        "param_stab": _maybe_float(row.get("parameter_stability") or row.get("parameter_stability_score")),
        "has_wf": True,
        "regime": row.get("regime") or "unknown",
        "reason_codes": row.get("reason_codes", []),
        "live_chart_url": live_reference_url(symbol, timeframe),
    }


def _simple_score(row: dict[str, Any]) -> float:
    profit_factor = _maybe_float(row.get("profit_factor") or row.get("pf")) or 0.0
    sharpe = _maybe_float(row.get("sharpe_ratio") or row.get("sharpe")) or 0.0
    max_drawdown = _maybe_float(row.get("max_drawdown") or row.get("max_dd")) or 1.0
    trades = int(float(row.get("total_trades") or row.get("trades") or 0))
    score = 0.0
    score += min(max(profit_factor, 0.0), 3.0) * 20.0
    score += min(max(sharpe, 0.0), 3.0) * 10.0
    score += min(trades / 200.0, 1.0) * 20.0
    score += max(0.0, 1.0 - min(max_drawdown, 1.0)) * 20.0
    return round(min(score, 100.0), 2)


def _job_rows() -> list[dict[str, Any]]:
    rows = _read_jsonl(Path("runtime") / "job_queue.jsonl")[-100:]
    output = []
    for row in rows:
        status = str(row.get("status") or "queued").lower()
        progress = 100 if status == "completed" else 0
        output.append({
            "job_id": row.get("job_id"),
            "job_type": row.get("type") or "full_pipeline",
            "strategy": row.get("strategy"),
            "symbol": row.get("symbol"),
            "tf": row.get("timeframe"),
            "status": status,
            "reason_code": row.get("recommendation") if status in {"failed", "skipped"} else None,
            "queued_at": row.get("queued_at") or row.get("created_at"),
            "completed_at": row.get("completed_at"),
            "duration_s": None,
            "progress": progress,
        })
    return output


def _paper_signal(base: Path) -> dict[str, Any]:
    payload = _read_json(base / "runtime" / "latest_paper_signal.json")
    if not payload:
        return {}
    return {
        **payload,
        "timeframe": payload.get("timeframe") or payload.get("tf"),
        "entry_price": payload.get("entry") or payload.get("entry_price"),
        "env_risk_state": payload.get("environment_state") or payload.get("env_risk_state"),
    }


def _forward_test_rows(base: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((base / "data" / "results").glob("*_forward_test.json"))[:50]:
        parsed = _parse_result_artifact(path, "_forward_test")
        payload = _read_json(path)
        if parsed is None or not payload:
            continue
        strategy, symbol, timeframe = parsed
        metrics = payload.get("metrics", {}) if isinstance(payload.get("metrics"), dict) else {}
        drawdown = _maybe_float(metrics.get("max_drawdown") or payload.get("drawdown")) or 0.0
        if drawdown <= 1.0:
            drawdown *= 100.0
        net_profit = _maybe_float(metrics.get("net_profit") or payload.get("net_profit")) or 0.0
        rows.append({
            "strategy": strategy,
            "symbol": symbol,
            "tf": timeframe,
            "last_bar": payload.get("last_processed_timestamp") or payload.get("last_bar") or payload.get("generated_at") or "unknown",
            "paper_equity": round(10000.0 + net_profit, 2),
            "paper_dd": round(drawdown, 2),
            "trades": int(float(metrics.get("total_trades") or payload.get("total_trades") or 0)),
        })
    return rows


def _committee_rows(base: Path, strategies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in strategies[:10]:
        rows.append({
            "strategy": item["strategy"],
            "symbol": item["symbol"],
            "tf": item["tf"],
            "verdict": item.get("verdict", "REVIEW"),
            "dissent": False,
            "agents": [],
            "summary": "Loaded from local result metrics. Committee packet available from reporting outputs when generated.",
        })
    return rows


def _static_findings(base: Path) -> list[dict[str, Any]]:
    payload = _read_json(base / "runtime" / "static_analysis" / "opengrep.json")
    findings = payload.get("results", []) if isinstance(payload, dict) else []
    output = []
    for finding in findings[:50]:
        extra = finding.get("extra", {})
        start = finding.get("start", {})
        output.append({
            "severity": str(extra.get("severity") or "INFO").upper(),
            "file": finding.get("path"),
            "line": start.get("line"),
            "desc": extra.get("message"),
            "fix": extra.get("metadata", {}).get("fix") or "Review finding.",
        })
    return output


def _imported_data_rows(base: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((base / "data" / "raw").glob("*.csv"))[:100]:
        symbol, timeframe = _symbol_timeframe_from_path(path)
        try:
            size_kb = round(path.stat().st_size / 1024, 1)
            status = "available"
        except OSError:
            size_kb = 0.0
            status = "unreadable"
        rows.append({
            "symbol": symbol,
            "tf": timeframe,
            "file": path.name,
            "date_range": "imported local CSV",
            "bars": None,
            "status": status,
            "hash": f"{size_kb} KB",
            "live_chart_url": live_reference_url(symbol, timeframe),
        })
    return rows


def _audit_rows(base: Path) -> list[dict[str, Any]]:
    path = base / "logs" / "audit" / "audit.jsonl"
    if not path.exists():
        return []
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            handle.seek(max(size - 262_144, 0))
            chunk = handle.read().decode("utf-8", errors="ignore")
    except OSError:
        return []
    lines = [line for line in chunk.splitlines() if line.strip()][-100:]
    rows = []
    for line in lines:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append({
            "ts": payload.get("timestamp"),
            "event": payload.get("event_type"),
            "code": payload.get("reason_code"),
            "strategy": payload.get("strategy"),
            "result": payload.get("decision"),
        })
    return rows[::-1]


def _parse_result_artifact(path: Path, suffix: str) -> tuple[str, str, str] | None:
    stem = path.stem
    if not stem.endswith(suffix):
        return None
    core = stem[: -len(suffix)]
    parts = core.split("_")
    if len(parts) < 3:
        return None
    strategy = "_".join(parts[:-2])
    symbol = parts[-2]
    timeframe = parts[-1]
    if not strategy or not symbol or not timeframe:
        return None
    return strategy, symbol, timeframe


def _symbol_timeframe_from_path(path: Path) -> tuple[str, str]:
    stem = path.stem
    parts = stem.split("_")
    if len(parts) >= 2:
        return parts[0].upper(), parts[1].upper()
    return stem.upper(), "M15"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _queue_health() -> dict[str, Any]:
    try:
        from tar_system.controller.job_queue import queue_health

        return queue_health(limit=8)
    except Exception as exc:
        return {"error": str(exc)}


def _online_research_status() -> dict[str, Any]:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    try:
        import exa_py  # noqa: F401
        exa_installed = True
    except ImportError:
        exa_installed = False
    return {
        "exa_py_installed": exa_installed,
        "exa_api_key_set": bool(os.environ.get("EXA_API_KEY")),
    }


def _safe_token(value: Any, name: str, default: str | None = None) -> str:
    if value is None or value == "":
        if default is None:
            raise ValueError(f"{name} is required")
        value = default
    token = str(value).strip()
    if not token or not SAFE_TEXT_RE.match(token):
        raise ValueError(f"{name} contains unsupported characters")
    return token


def _safe_search_text(value: Any, default: str = "") -> str:
    if value is None or value == "":
        return default
    text = str(value).strip()
    if len(text) > 240:
        raise ValueError("search text is too long")
    if any(char in text for char in "\x00\r\n"):
        raise ValueError("search text contains unsupported characters")
    return text


def _bounded_int(value: Any, name: str, default: int, minimum: int, maximum: int) -> int:
    if value is None or value == "":
        return default
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if number < minimum or number > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return number


def _online_scout_output_path(query: str) -> Path:
    output_dir = Path("data") / "research" / "online_scout"
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:48] or "scout"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return output_dir / f"{stamp}_{slug}.json"


def _optional_date(value: Any, name: str) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        raise ValueError(f"{name} must use YYYY-MM-DD")
    return text


def _safe_raw_csv(value: Any, symbol: str, timeframe: str, require_exists: bool = True) -> Path:
    raw_dir = (Path("data") / "raw").resolve()
    raw_dir.mkdir(parents=True, exist_ok=True)
    if value is None or value == "":
        path = raw_dir / f"{symbol}_{timeframe}.csv"
    else:
        candidate = Path(str(value))
        if candidate.is_absolute():
            path = candidate.resolve()
        else:
            path = (Path.cwd() / candidate).resolve()
    if path.suffix.lower() != ".csv":
        raise ValueError("file must be a CSV")
    if not _is_relative_to(path, raw_dir):
        raise ValueError("file must stay under data/raw")
    if require_exists and not path.exists():
        raise ValueError(f"raw data file not found: {path.relative_to(Path.cwd())}")
    return path.relative_to(Path.cwd())


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    run()

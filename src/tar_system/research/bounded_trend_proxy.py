"""Bounded EMA trend proxy for GA/technical-analysis hypotheses."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from tar_system.research.data_readiness import _read_csv, _timestamp_series
from tar_system.research.currency_momentum_proxy import _close_series


@dataclass
class TrendProxyRow:
    symbol: str
    fast_ema: int
    slow_ema: int
    trades: int
    cumulative_return: float
    annualized_return: float
    sharpe: float
    max_drawdown: float
    verdict: str
    reason: str


@dataclass
class BoundedTrendProxyResult:
    generated_at: str
    symbols: list[str]
    timeframe: str
    cost_bps: float
    report_path: str
    report_json_path: str
    best_symbol: str
    best_fast_ema: int
    best_slow_ema: int
    best_verdict: str
    best_reason: str
    rows: list[TrendProxyRow]


def run_bounded_trend_proxy(
    symbols: list[str],
    timeframe: str = "H1",
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "reports/bounded_trend_proxy",
    fast_values: list[int] | None = None,
    slow_values: list[int] | None = None,
    cost_bps: float = 2.0,
) -> BoundedTrendProxyResult:
    fast_values = fast_values or [10, 20, 50]
    slow_values = slow_values or [50, 100, 200]
    rows: list[TrendProxyRow] = []
    for symbol in [item.upper() for item in symbols]:
        series = _load_close(symbol, timeframe.upper(), Path(raw_dir))
        for fast in fast_values:
            for slow in slow_values:
                if fast >= slow:
                    continue
                rows.append(_run_one(symbol, series, fast, slow, cost_bps))
    rows.sort(key=lambda row: (row.verdict == "KEEP", row.sharpe, row.cumulative_return), reverse=True)
    if not rows:
        raise ValueError("No bounded trend proxy rows were produced")
    best = rows[0]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output / f"{stamp}_bounded_trend_proxy.md"
    report_json_path = output / f"{stamp}_bounded_trend_proxy.json"
    result = BoundedTrendProxyResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        symbols=[item.upper() for item in symbols],
        timeframe=timeframe.upper(),
        cost_bps=cost_bps,
        report_path=str(report_path),
        report_json_path=str(report_json_path),
        best_symbol=best.symbol,
        best_fast_ema=best.fast_ema,
        best_slow_ema=best.slow_ema,
        best_verdict=best.verdict,
        best_reason=best.reason,
        rows=rows,
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    report_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _load_close(symbol: str, timeframe: str, raw_dir: Path) -> pd.Series:
    path = raw_dir / f"{symbol}_{timeframe}.csv"
    if not path.exists():
        raise ValueError(f"Missing raw data: {path}")
    df = _read_csv(path)
    timestamps = _timestamp_series(df)
    close = _close_series(df)
    if timestamps is None or close is None:
        raise ValueError(f"Missing timestamp or close columns: {path}")
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps, errors="coerce", utc=True),
            "close": pd.to_numeric(close, errors="coerce"),
        }
    ).dropna()
    if frame.empty:
        raise ValueError(f"No usable close data: {path}")
    return frame.set_index("timestamp")["close"].sort_index()


def _run_one(symbol: str, close: pd.Series, fast: int, slow: int, cost_bps: float) -> TrendProxyRow:
    frame = pd.DataFrame({"close": close})
    frame["fast"] = frame["close"].ewm(span=fast, adjust=False).mean()
    frame["slow"] = frame["close"].ewm(span=slow, adjust=False).mean()
    frame["signal"] = 0
    frame.loc[frame["fast"] > frame["slow"], "signal"] = 1
    frame.loc[frame["fast"] < frame["slow"], "signal"] = -1
    frame["position"] = frame["signal"].shift(1).fillna(0)
    frame["raw_return"] = frame["close"].pct_change().fillna(0)
    frame["turnover"] = frame["position"].diff().abs().fillna(frame["position"].abs())
    frame["net_return"] = frame["position"] * frame["raw_return"] - frame["turnover"] * (cost_bps / 10_000.0)
    returns = frame["net_return"].dropna()
    trades = int((frame["turnover"] > 0).sum())
    cumulative = float((1.0 + returns).prod() - 1.0)
    periods_per_year = 24 * 252
    annualized = float((1.0 + cumulative) ** (periods_per_year / max(len(returns), 1)) - 1.0)
    sharpe = float((returns.mean() / returns.std(ddof=1)) * (periods_per_year ** 0.5)) if returns.std(ddof=1) else 0.0
    equity = (1.0 + returns).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    max_drawdown = float(abs(drawdown.min())) if len(drawdown) else 0.0
    verdict, reason = _verdict(trades, cumulative, sharpe, max_drawdown)
    return TrendProxyRow(
        symbol=symbol,
        fast_ema=fast,
        slow_ema=slow,
        trades=trades,
        cumulative_return=round(cumulative, 6),
        annualized_return=round(annualized, 6),
        sharpe=round(sharpe, 6),
        max_drawdown=round(max_drawdown, 6),
        verdict=verdict,
        reason=reason,
    )


def _verdict(trades: int, cumulative: float, sharpe: float, max_drawdown: float) -> tuple[str, str]:
    if trades < 30:
        return "KILL", "LOW_TRADE_COUNT"
    if cumulative <= 0:
        return "KILL", "NEGATIVE_AFTER_COSTS"
    if sharpe < 0.3:
        return "REVIEW", "LOW_PROXY_SHARPE"
    if max_drawdown > 0.2:
        return "REVIEW", "HIGH_DRAWDOWN"
    return "KEEP", "BOUNDED_TREND_PROXY_PASSED"


def _markdown(result: BoundedTrendProxyResult) -> str:
    lines = [
        "# Bounded Trend Proxy",
        "",
        f"- Generated: {result.generated_at}",
        f"- Symbols: {', '.join(result.symbols)}",
        f"- Timeframe: {result.timeframe}",
        f"- Cost bps per position change: {result.cost_bps}",
        f"- Best: {result.best_symbol} EMA {result.best_fast_ema}/{result.best_slow_ema}",
        f"- Best verdict: {result.best_verdict}",
        f"- Best reason: {result.best_reason}",
        "",
        "| Symbol | Fast | Slow | Verdict | Reason | Trades | CumRet | Sharpe | MaxDD |",
        "| --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in result.rows:
        lines.append(
            f"| {row.symbol} | {row.fast_ema} | {row.slow_ema} | {row.verdict} | {row.reason} | {row.trades} | {row.cumulative_return} | {row.sharpe} | {row.max_drawdown} |"
        )
    lines.extend(["", "## Guardrails", "", "- Bounded parameter search only.", "- Paper-only research.", "- No live trading or MT5 export.", ""])
    return "\n".join(lines)

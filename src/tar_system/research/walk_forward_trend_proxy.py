"""Rolling walk-forward EMA trend proxy for robustness hypotheses."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from tar_system.research.bounded_trend_proxy import _load_close


@dataclass
class WalkForwardTrendRow:
    symbol: str
    windows: int
    trades: int
    cumulative_return: float
    annualized_return: float
    sharpe: float
    max_drawdown: float
    selected_pairs: str
    verdict: str
    reason: str


@dataclass
class WalkForwardTrendResult:
    generated_at: str
    symbols: list[str]
    timeframe: str
    cost_bps: float
    train_months: int
    validation_months: int
    test_months: int
    step_months: int
    report_path: str
    report_json_path: str
    best_symbol: str
    best_verdict: str
    best_reason: str
    rows: list[WalkForwardTrendRow]


def run_walk_forward_trend_proxy(
    symbols: list[str],
    timeframe: str = "H1",
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "reports/walk_forward_trend_proxy",
    ema_values: list[int] | None = None,
    train_months: int = 24,
    validation_months: int = 6,
    test_months: int = 6,
    step_months: int = 6,
    cost_bps: float = 2.0,
) -> WalkForwardTrendResult:
    ema_values = sorted(set(ema_values or [10, 20, 50, 100, 200]))
    pairs = [(fast, slow) for fast in ema_values for slow in ema_values if fast < slow]
    if not pairs:
        raise ValueError("At least one fast/slow EMA pair is required")

    rows: list[WalkForwardTrendRow] = []
    for symbol in [item.upper() for item in symbols]:
        close = _load_close(symbol, timeframe.upper(), Path(raw_dir))
        rows.append(
            _run_symbol(
                symbol=symbol,
                close=close,
                pairs=pairs,
                train_months=train_months,
                validation_months=validation_months,
                test_months=test_months,
                step_months=step_months,
                cost_bps=cost_bps,
            )
        )
    rows.sort(key=lambda row: (row.verdict == "KEEP", row.sharpe, row.cumulative_return), reverse=True)
    if not rows:
        raise ValueError("No walk-forward trend rows were produced")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output / f"{stamp}_walk_forward_trend_proxy.md"
    report_json_path = output / f"{stamp}_walk_forward_trend_proxy.json"
    best = rows[0]
    result = WalkForwardTrendResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        symbols=[item.upper() for item in symbols],
        timeframe=timeframe.upper(),
        cost_bps=cost_bps,
        train_months=train_months,
        validation_months=validation_months,
        test_months=test_months,
        step_months=step_months,
        report_path=str(report_path),
        report_json_path=str(report_json_path),
        best_symbol=best.symbol,
        best_verdict=best.verdict,
        best_reason=best.reason,
        rows=rows,
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    report_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _run_symbol(
    symbol: str,
    close: pd.Series,
    pairs: list[tuple[int, int]],
    train_months: int,
    validation_months: int,
    test_months: int,
    step_months: int,
    cost_bps: float,
) -> WalkForwardTrendRow:
    frames_by_pair = {pair: _pair_frame(close, pair[0], pair[1], cost_bps) for pair in pairs}
    start = close.index.min()
    end = close.index.max()
    cursor = start + pd.DateOffset(months=train_months + validation_months)
    selected_pairs: list[str] = []
    test_returns: list[pd.Series] = []

    while cursor + pd.DateOffset(months=test_months) <= end:
        validation_start = cursor - pd.DateOffset(months=validation_months)
        validation_end = cursor
        test_start = cursor
        test_end = cursor + pd.DateOffset(months=test_months)
        best_pair = _select_pair(frames_by_pair, pairs, validation_start, validation_end)
        selected_pairs.append(f"{best_pair[0]}/{best_pair[1]}")
        segment = frames_by_pair[best_pair].loc[(frames_by_pair[best_pair].index >= test_start) & (frames_by_pair[best_pair].index < test_end)]
        if not segment.empty:
            test_returns.append(segment["net_return"])
        cursor += pd.DateOffset(months=step_months)

    if not test_returns:
        raise ValueError(f"Not enough walk-forward windows for {symbol}")

    returns = pd.concat(test_returns).sort_index()
    trades = _count_trades(frames_by_pair, selected_pairs, returns.index.min(), returns.index.max())
    cumulative = float((1.0 + returns).prod() - 1.0)
    periods_per_year = _periods_per_year(close)
    annualized = float((1.0 + cumulative) ** (periods_per_year / max(len(returns), 1)) - 1.0) if cumulative > -1 else -1.0
    std = returns.std(ddof=1)
    sharpe = float((returns.mean() / std) * (periods_per_year**0.5)) if std else 0.0
    equity = (1.0 + returns).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    max_drawdown = float(abs(drawdown.min())) if len(drawdown) else 0.0
    verdict, reason = _verdict(trades, cumulative, sharpe, max_drawdown, len(test_returns))
    return WalkForwardTrendRow(
        symbol=symbol,
        windows=len(test_returns),
        trades=trades,
        cumulative_return=round(cumulative, 6),
        annualized_return=round(annualized, 6),
        sharpe=round(sharpe, 6),
        max_drawdown=round(max_drawdown, 6),
        selected_pairs=", ".join(selected_pairs[:12]),
        verdict=verdict,
        reason=reason,
    )


def _pair_frame(close: pd.Series, fast: int, slow: int, cost_bps: float) -> pd.DataFrame:
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
    return frame[["net_return", "turnover"]]


def _select_pair(frames_by_pair: dict[tuple[int, int], pd.DataFrame], pairs: list[tuple[int, int]], start: pd.Timestamp, end: pd.Timestamp) -> tuple[int, int]:
    scored: list[tuple[float, float, tuple[int, int]]] = []
    for pair in pairs:
        frame = frames_by_pair[pair]
        segment = frame.loc[(frame.index >= start) & (frame.index < end), "net_return"]
        if segment.empty:
            scored.append((-999.0, -999.0, pair))
            continue
        std = segment.std(ddof=1)
        sharpe = float(segment.mean() / std) if std else 0.0
        cumulative = float((1.0 + segment).prod() - 1.0)
        scored.append((sharpe, cumulative, pair))
    scored.sort(reverse=True)
    return scored[0][2]


def _count_trades(
    frames_by_pair: dict[tuple[int, int], pd.DataFrame],
    selected_pairs: list[str],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> int:
    trades = 0
    for pair_label in set(selected_pairs):
        fast, slow = [int(item) for item in pair_label.split("/")]
        frame = frames_by_pair[(fast, slow)]
        segment = frame.loc[(frame.index >= start) & (frame.index <= end), "turnover"]
        trades += int((segment > 0).sum())
    return trades


def _periods_per_year(close: pd.Series) -> int:
    if len(close.index) < 2:
        return 252
    median_delta = close.index.to_series().diff().median()
    if pd.isna(median_delta) or median_delta <= pd.Timedelta(0):
        return 24 * 252
    return max(int(pd.Timedelta(days=365) / median_delta), 1)


def _verdict(trades: int, cumulative: float, sharpe: float, max_drawdown: float, windows: int) -> tuple[str, str]:
    if windows < 4:
        return "KILL", "LOW_WALK_FORWARD_WINDOWS"
    if trades < 4:
        return "KILL", "LOW_TRADE_COUNT"
    if cumulative <= 0:
        return "KILL", "NEGATIVE_AFTER_COSTS"
    if sharpe < 0.3:
        return "REVIEW", "LOW_WALK_FORWARD_SHARPE"
    if max_drawdown > 0.2:
        return "REVIEW", "HIGH_DRAWDOWN"
    return "KEEP", "WALK_FORWARD_PROXY_PASSED"


def _markdown(result: WalkForwardTrendResult) -> str:
    lines = [
        "# Walk-Forward Trend Proxy",
        "",
        f"- Generated: {result.generated_at}",
        f"- Symbols: {', '.join(result.symbols)}",
        f"- Timeframe: {result.timeframe}",
        f"- Cost bps per position change: {result.cost_bps}",
        f"- Windows: train {result.train_months}m, validation {result.validation_months}m, test {result.test_months}m, step {result.step_months}m",
        f"- Best symbol: {result.best_symbol}",
        f"- Best verdict: {result.best_verdict}",
        f"- Best reason: {result.best_reason}",
        "",
        "| Symbol | Windows | Verdict | Reason | Trades | CumRet | Sharpe | MaxDD | Selected Pairs |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result.rows:
        lines.append(
            f"| {row.symbol} | {row.windows} | {row.verdict} | {row.reason} | {row.trades} | {row.cumulative_return} | {row.sharpe} | {row.max_drawdown} | {row.selected_pairs} |"
        )
    lines.extend(["", "## Guardrails", "", "- Walk-forward selection only.", "- Paper-only research.", "- No live trading or MT5 export.", ""])
    return "\n".join(lines)

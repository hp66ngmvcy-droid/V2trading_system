"""Paper-only cross-sectional currency momentum proxy backtest."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from tar_system.research.data_readiness import _read_csv, _timestamp_series


@dataclass
class CurrencyMomentumTrade:
    month: str
    longs: list[str]
    shorts: list[str]
    gross_return: float
    cost: float
    net_return: float


@dataclass
class CurrencyMomentumProxyResult:
    generated_at: str
    symbols: list[str]
    timeframe: str
    lookback_months: int
    exclude_recent_months: int
    cost_bps: float
    months_tested: int
    cumulative_return: float
    annualized_return: float
    sharpe: float
    max_drawdown: float
    verdict: str
    reason: str
    report_path: str
    report_json_path: str
    trades: list[CurrencyMomentumTrade]


def run_currency_momentum_proxy(
    symbols: list[str],
    timeframe: str = "H1",
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "reports/currency_momentum_proxy",
    lookback_months: int = 12,
    exclude_recent_months: int = 1,
    cost_bps: float = 2.0,
) -> CurrencyMomentumProxyResult:
    closes = _monthly_closes(symbols, timeframe, Path(raw_dir))
    trades = _simulate(closes, lookback_months=lookback_months, exclude_recent_months=exclude_recent_months, cost_bps=cost_bps)
    returns = pd.Series([trade.net_return for trade in trades], dtype=float)
    cumulative = float((1.0 + returns).prod() - 1.0) if len(returns) else 0.0
    annualized = float((1.0 + cumulative) ** (12.0 / max(len(returns), 1)) - 1.0) if len(returns) else 0.0
    sharpe = float((returns.mean() / returns.std(ddof=1)) * (12.0 ** 0.5)) if len(returns) > 1 and returns.std(ddof=1) else 0.0
    equity = (1.0 + returns).cumprod() if len(returns) else pd.Series([1.0])
    drawdown = equity / equity.cummax() - 1.0
    max_drawdown = float(abs(drawdown.min())) if len(drawdown) else 0.0
    verdict, reason = _verdict(len(trades), cumulative, sharpe, max_drawdown)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output / f"{stamp}_currency_momentum_proxy.md"
    report_json_path = output / f"{stamp}_currency_momentum_proxy.json"
    result = CurrencyMomentumProxyResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        symbols=[symbol.upper() for symbol in symbols],
        timeframe=timeframe.upper(),
        lookback_months=lookback_months,
        exclude_recent_months=exclude_recent_months,
        cost_bps=cost_bps,
        months_tested=len(trades),
        cumulative_return=round(cumulative, 6),
        annualized_return=round(annualized, 6),
        sharpe=round(sharpe, 6),
        max_drawdown=round(max_drawdown, 6),
        verdict=verdict,
        reason=reason,
        report_path=str(report_path),
        report_json_path=str(report_json_path),
        trades=trades,
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    report_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _monthly_closes(symbols: list[str], timeframe: str, raw_dir: Path) -> pd.DataFrame:
    series: dict[str, pd.Series] = {}
    for symbol in symbols:
        path = raw_dir / f"{symbol.upper()}_{timeframe.upper()}.csv"
        if not path.exists():
            continue
        df = _read_csv(path)
        timestamps = _timestamp_series(df)
        close = _close_series(df)
        if timestamps is None or close is None:
            continue
        indexed = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(timestamps, errors="coerce", utc=True),
                "close": pd.to_numeric(close, errors="coerce"),
            }
        ).dropna()
        if indexed.empty:
            continue
        monthly = indexed.set_index("timestamp")["close"].resample("ME").last().dropna()
        series[symbol.upper()] = monthly
    if not series:
        raise ValueError("No usable close data found for currency momentum proxy")
    return pd.DataFrame(series).dropna(how="any")


def _close_series(df: pd.DataFrame) -> pd.Series | None:
    columns = {str(column).strip().lower(): column for column in df.columns}
    for name in ("close", "<close>"):
        if name in columns:
            return df[columns[name]]
    return None


def _simulate(
    closes: pd.DataFrame,
    lookback_months: int,
    exclude_recent_months: int,
    cost_bps: float,
) -> list[CurrencyMomentumTrade]:
    trades: list[CurrencyMomentumTrade] = []
    cost = (cost_bps / 10_000.0) * 2.0
    start = lookback_months + exclude_recent_months
    for index in range(start, len(closes) - 1):
        ranking_now = closes.iloc[index - exclude_recent_months]
        ranking_then = closes.iloc[index - lookback_months - exclude_recent_months]
        scores = (ranking_now / ranking_then - 1.0).dropna().sort_values()
        if len(scores) < 4:
            continue
        sleeve_size = max(1, len(scores) // 3)
        shorts = list(scores.index[:sleeve_size])
        longs = list(scores.index[-sleeve_size:])
        next_returns = (closes.iloc[index + 1] / closes.iloc[index] - 1.0).dropna()
        if not set(longs + shorts).issubset(next_returns.index):
            continue
        gross = float(next_returns[longs].mean() - next_returns[shorts].mean())
        trades.append(
            CurrencyMomentumTrade(
                month=closes.index[index].date().isoformat(),
                longs=longs,
                shorts=shorts,
                gross_return=round(gross, 6),
                cost=round(cost, 6),
                net_return=round(gross - cost, 6),
            )
        )
    return trades


def _verdict(months: int, cumulative: float, sharpe: float, max_drawdown: float) -> tuple[str, str]:
    if months < 36:
        return "REVIEW", "INSUFFICIENT_MONTHLY_OBSERVATIONS"
    if cumulative <= 0:
        return "KILL", "NEGATIVE_AFTER_COSTS"
    if sharpe < 0.3:
        return "REVIEW", "LOW_OUT_OF_SAMPLE_PROXY_SHARPE"
    if max_drawdown > 0.2:
        return "REVIEW", "HIGH_DRAWDOWN"
    return "KEEP", "PAPER_PROXY_PASSED"


def _markdown(result: CurrencyMomentumProxyResult) -> str:
    lines = [
        "# Currency Momentum Proxy Backtest",
        "",
        f"- Generated: {result.generated_at}",
        f"- Symbols: {', '.join(result.symbols)}",
        f"- Timeframe: {result.timeframe}",
        f"- Lookback months: {result.lookback_months}",
        f"- Excluded recent months: {result.exclude_recent_months}",
        f"- Cost bps per side: {result.cost_bps}",
        f"- Months tested: {result.months_tested}",
        f"- Cumulative return: {result.cumulative_return}",
        f"- Annualized return: {result.annualized_return}",
        f"- Sharpe: {result.sharpe}",
        f"- Max drawdown: {result.max_drawdown}",
        f"- Verdict: {result.verdict}",
        f"- Reason: {result.reason}",
        "",
        "## Guardrails",
        "",
        "- This is an H1 proxy, not a direct D1 replication.",
        "- This is paper-only research.",
        "- No live trading or MT5 export.",
        "",
    ]
    return "\n".join(lines)

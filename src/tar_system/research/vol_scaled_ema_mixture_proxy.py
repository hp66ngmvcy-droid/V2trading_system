"""Paper-only vol-scaled EMA mixture currency momentum proxy."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from tar_system.research.bounded_trend_proxy import _load_close


@dataclass
class VolScaledEmaRow:
    symbol: str
    trades: int
    cumulative_return: float
    annualized_return: float
    sharpe: float
    max_drawdown: float
    verdict: str
    reason: str


@dataclass
class VolScaledEmaMixtureResult:
    generated_at: str
    symbols: list[str]
    timeframe: str
    cost_bps: float
    threshold: float
    ema_pairs: list[str]
    report_path: str
    report_json_path: str
    basket_cumulative_return: float
    basket_annualized_return: float
    basket_sharpe: float
    basket_max_drawdown: float
    basket_verdict: str
    basket_reason: str
    rows: list[VolScaledEmaRow]


def run_vol_scaled_ema_mixture_proxy(
    symbols: list[str],
    timeframe: str = "H1",
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "reports/vol_scaled_ema_mixture_proxy",
    ema_pairs: list[tuple[int, int]] | None = None,
    vol_window: int = 200,
    threshold: float = 0.05,
    cost_bps: float = 2.0,
) -> VolScaledEmaMixtureResult:
    pairs = ema_pairs or [(8, 24), (16, 48), (32, 96), (64, 192)]
    returns_by_symbol: dict[str, pd.Series] = {}
    rows: list[VolScaledEmaRow] = []
    for symbol in [item.upper() for item in symbols]:
        close = _load_close(symbol, timeframe.upper(), Path(raw_dir))
        frame = _signal_frame(close, pairs, vol_window=vol_window, threshold=threshold, cost_bps=cost_bps)
        returns = frame["net_return"].dropna()
        returns_by_symbol[symbol] = returns
        rows.append(_metrics(symbol, returns, trades=int((frame["turnover"] > 0).sum())))

    basket_returns = pd.DataFrame(returns_by_symbol).dropna(how="any").mean(axis=1)
    basket_metrics = _basket_metrics(basket_returns, rows)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output / f"{stamp}_vol_scaled_ema_mixture_proxy.md"
    report_json_path = output / f"{stamp}_vol_scaled_ema_mixture_proxy.json"
    result = VolScaledEmaMixtureResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        symbols=[item.upper() for item in symbols],
        timeframe=timeframe.upper(),
        cost_bps=cost_bps,
        threshold=threshold,
        ema_pairs=[f"{fast}/{slow}" for fast, slow in pairs],
        report_path=str(report_path),
        report_json_path=str(report_json_path),
        basket_cumulative_return=basket_metrics["cumulative_return"],
        basket_annualized_return=basket_metrics["annualized_return"],
        basket_sharpe=basket_metrics["sharpe"],
        basket_max_drawdown=basket_metrics["max_drawdown"],
        basket_verdict=basket_metrics["verdict"],
        basket_reason=basket_metrics["reason"],
        rows=rows,
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    report_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _signal_frame(
    close: pd.Series,
    pairs: list[tuple[int, int]],
    vol_window: int,
    threshold: float,
    cost_bps: float,
) -> pd.DataFrame:
    frame = pd.DataFrame({"close": close})
    frame["raw_return"] = frame["close"].pct_change().fillna(0)
    vol = frame["raw_return"].rolling(vol_window, min_periods=max(20, vol_window // 4)).std().replace(0, pd.NA)
    components: list[pd.Series] = []
    for fast, slow in pairs:
        if fast >= slow:
            raise ValueError(f"EMA fast must be less than slow: {fast}/{slow}")
        fast_ema = frame["close"].ewm(span=fast, adjust=False).mean()
        slow_ema = frame["close"].ewm(span=slow, adjust=False).mean()
        normalized = ((fast_ema - slow_ema) / frame["close"]) / vol
        components.append(normalized.clip(-10, 10).apply(_bounded_response))
    frame["signal"] = pd.concat(components, axis=1).mean(axis=1).fillna(0)
    frame["target"] = 0
    frame.loc[frame["signal"] > threshold, "target"] = 1
    frame.loc[frame["signal"] < -threshold, "target"] = -1
    frame["position"] = frame["target"].shift(1).fillna(0)
    frame["turnover"] = frame["position"].diff().abs().fillna(frame["position"].abs())
    frame["net_return"] = frame["position"] * frame["raw_return"] - frame["turnover"] * (cost_bps / 10_000.0)
    return frame


def _bounded_response(value: float) -> float:
    if pd.isna(value):
        return 0.0
    return float(math.tanh(value))


def _metrics(symbol: str, returns: pd.Series, trades: int) -> VolScaledEmaRow:
    metrics = _return_metrics(returns)
    verdict, reason = _verdict(trades, metrics["cumulative_return"], metrics["sharpe"], metrics["max_drawdown"])
    return VolScaledEmaRow(
        symbol=symbol,
        trades=trades,
        cumulative_return=metrics["cumulative_return"],
        annualized_return=metrics["annualized_return"],
        sharpe=metrics["sharpe"],
        max_drawdown=metrics["max_drawdown"],
        verdict=verdict,
        reason=reason,
    )


def _basket_metrics(returns: pd.Series, rows: list[VolScaledEmaRow]) -> dict[str, float | str]:
    metrics = _return_metrics(returns)
    non_negative = sum(1 for row in rows if row.cumulative_return > 0)
    verdict, reason = _basket_verdict(non_negative, len(rows), metrics["cumulative_return"], metrics["sharpe"], metrics["max_drawdown"])
    return {**metrics, "verdict": verdict, "reason": reason}


def _return_metrics(returns: pd.Series) -> dict[str, float]:
    returns = returns.dropna()
    cumulative = float((1.0 + returns).prod() - 1.0) if len(returns) else 0.0
    periods_per_year = 24 * 252
    annualized = float((1.0 + cumulative) ** (periods_per_year / max(len(returns), 1)) - 1.0) if cumulative > -1 else -1.0
    std = returns.std(ddof=1)
    sharpe = float((returns.mean() / std) * (periods_per_year**0.5)) if len(returns) > 1 and std else 0.0
    equity = (1.0 + returns).cumprod() if len(returns) else pd.Series([1.0])
    drawdown = equity / equity.cummax() - 1.0
    max_drawdown = float(abs(drawdown.min())) if len(drawdown) else 0.0
    return {
        "cumulative_return": round(cumulative, 6),
        "annualized_return": round(annualized, 6),
        "sharpe": round(sharpe, 6),
        "max_drawdown": round(max_drawdown, 6),
    }


def _verdict(trades: int, cumulative: float, sharpe: float, max_drawdown: float) -> tuple[str, str]:
    if trades < 30:
        return "KILL", "LOW_TRADE_COUNT"
    if cumulative <= 0:
        return "KILL", "NEGATIVE_AFTER_COSTS"
    if sharpe < 0.3:
        return "REVIEW", "LOW_PROXY_SHARPE"
    if max_drawdown > 0.2:
        return "REVIEW", "HIGH_DRAWDOWN"
    return "KEEP", "VOL_SCALED_EMA_PROXY_PASSED"


def _basket_verdict(non_negative: int, total: int, cumulative: float, sharpe: float, max_drawdown: float) -> tuple[str, str]:
    if cumulative <= 0:
        return "KILL", "NEGATIVE_AFTER_COSTS"
    if total and non_negative < max(1, total - 1):
        return "REVIEW", "TOO_FEW_SYMBOLS_POSITIVE"
    if sharpe < 0.3:
        return "REVIEW", "LOW_BASKET_PROXY_SHARPE"
    if max_drawdown > 0.2:
        return "REVIEW", "HIGH_BASKET_DRAWDOWN"
    return "KEEP", "BASKET_PROXY_PASSED"


def _markdown(result: VolScaledEmaMixtureResult) -> str:
    lines = [
        "# Vol-Scaled EMA Mixture Proxy",
        "",
        f"- Generated: {result.generated_at}",
        f"- Symbols: {', '.join(result.symbols)}",
        f"- Timeframe: {result.timeframe}",
        f"- EMA pairs: {', '.join(result.ema_pairs)}",
        f"- Threshold: {result.threshold}",
        f"- Cost bps per position change: {result.cost_bps}",
        f"- Basket cumulative return: {result.basket_cumulative_return}",
        f"- Basket annualized return: {result.basket_annualized_return}",
        f"- Basket Sharpe: {result.basket_sharpe}",
        f"- Basket max drawdown: {result.basket_max_drawdown}",
        f"- Basket verdict: {result.basket_verdict}",
        f"- Basket reason: {result.basket_reason}",
        "",
        "| Symbol | Verdict | Reason | Trades | CumRet | Sharpe | MaxDD |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in result.rows:
        lines.append(f"| {row.symbol} | {row.verdict} | {row.reason} | {row.trades} | {row.cumulative_return} | {row.sharpe} | {row.max_drawdown} |")
    lines.extend(["", "## Guardrails", "", "- Paper-only proxy.", "- No live trading or MT5 export.", "- Compare against failed plain EMA baselines before promotion.", ""])
    return "\n".join(lines)

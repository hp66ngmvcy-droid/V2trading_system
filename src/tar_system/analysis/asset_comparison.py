"""Compare strategy performance across local asset feature stores."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from tar_system.assets.profiles import ASSET_PROFILES
from tar_system.backtest.engine import run_backtest
from tar_system.data.store import load_feature_data
from tar_system.scoring.scorer import score_strategy
from tar_system.strategies.resolver import resolve_strategy


@dataclass
class AssetComparisonRow:
    symbol: str
    asset_class: str
    status: str
    net_profit: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe: float
    sortino: float
    trade_count: float
    average_trade: float
    score: float
    verdict: str
    risk_adjusted_score: float


def compare_assets(strategy_name: str, timeframe: str, broker: str = "current_broker_demo", symbols: list[str] | None = None) -> list[AssetComparisonRow]:
    selected = symbols or list(ASSET_PROFILES)
    rows: list[AssetComparisonRow] = []
    for symbol in selected:
        profile = ASSET_PROFILES[symbol]
        metrics_path = Path("data/results") / f"{strategy_name}_{symbol}_{timeframe}_metrics.json"
        feature_path = Path("data/features") / f"{symbol}_{timeframe}.parquet"
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            status = "metrics"
        elif feature_path.exists():
            resolved = resolve_strategy(strategy_name, symbol, timeframe, broker, audit=True)
            metrics = run_backtest(load_feature_data(symbol, timeframe), resolved.strategy, audit_decisions=False).metrics
            status = "backtested"
        else:
            rows.append(AssetComparisonRow(symbol, profile.asset_class, "missing_data", 0, 0, 0, 0, 0, 0, 0, 0, 0, "NO_DATA", 0))
            continue
        score = score_strategy(metrics)
        net_profit = float(metrics.get("expectancy", 0.0)) * float(metrics.get("total_trades", 0.0))
        risk_adjusted = max(0.0, score.score - float(metrics.get("max_drawdown", 0.0)) * 100)
        rows.append(
            AssetComparisonRow(
                symbol=symbol,
                asset_class=profile.asset_class,
                status=status,
                net_profit=net_profit,
                win_rate=float(metrics.get("win_rate", 0.0)),
                profit_factor=float(metrics.get("profit_factor", 0.0)),
                max_drawdown=float(metrics.get("max_drawdown", 0.0)),
                sharpe=float(metrics.get("sharpe_ratio", metrics.get("sharpe", 0.0))),
                sortino=float(metrics.get("sortino_ratio", metrics.get("sortino", 0.0))),
                trade_count=float(metrics.get("total_trades", 0.0)),
                average_trade=float(metrics.get("expectancy", 0.0)),
                score=score.score,
                verdict=score.verdict,
                risk_adjusted_score=round(risk_adjusted, 2),
            )
        )
    rows.sort(key=lambda row: row.risk_adjusted_score, reverse=True)
    output = Path("data/results") / f"{strategy_name}_{timeframe}_asset_comparison.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([asdict(row) for row in rows], indent=2), encoding="utf-8")
    return rows

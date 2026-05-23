"""Strategy tuning pipeline — Stage 1-3 per commodity, outputs validated MT5 config."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from tar_system.assets.profiles import ASSET_PROFILES, AssetProfile
from tar_system.backtest.engine import run_backtest
from tar_system.brokers.profiles import BrokerProfile
from tar_system.brokers.registry import load_broker_profile
from tar_system.data.store import load_feature_data
from tar_system.strategies.base import Signal

logger = logging.getLogger(__name__)

# MT5 export gates — strategy must clear all to be mt5_ready
MT5_MIN_PF = 1.20
MT5_MIN_SHARPE = 1.50
MT5_MAX_DRAWDOWN_PCT = 5.0

ATR_PERCENTILES = [0.95, 0.90, 0.85, 0.80, 0.75]

SESSIONS = [
    ("7-20 (baseline)", 7, 20),
    ("12-20 (Overlap+NY)", 12, 20),
    ("7-18 (London+NY)", 7, 18),
    ("8-17 (Core)", 8, 17),
    ("7-16 (London+Overlap)", 7, 16),
    ("12-23 (NY+Late)", 12, 23),
    ("0-24 (all hours)", 0, 24),
]


@dataclass
class StageResult:
    stage: str
    passed: bool
    best_config: dict[str, Any]
    metrics: dict[str, float]
    note: str = ""


@dataclass
class TuningResult:
    symbol: str
    timeframe: str
    strategy_name: str
    tuned_at: str
    mt5_ready: bool
    mt5_block_reason: str
    stages: list[StageResult]
    optimal_config: dict[str, Any]
    summary: dict[str, float]


class _GatedStrategy:
    """Wraps a strategy with ATR cap and session hour gate."""

    def __init__(self, inner: Any, atr_cap: float, start_utc: int, end_utc: int) -> None:
        self.inner = inner
        self.atr_cap = atr_cap
        self.start_utc = start_utc
        self.end_utc = end_utc
        self.name = getattr(inner, "name", "unknown")
        self.version = getattr(inner, "version", "0")

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        base = dict(
            timestamp=pd.Timestamp(row["timestamp"]),
            symbol=str(row["symbol"]),
            timeframe=str(row["timeframe"]),
            strategy=self.name,
            version=self.version,
            entry=float(row["close"]),
            metadata={"regime": regime},
        )
        hour = int(row.get("hour_utc", -1))
        if not (self.start_utc <= hour < self.end_utc):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None,
                          take_profit=None, reason_code="OUTSIDE_SESSION", **base)
        atr = float(row.get("atr", 0) or 0)
        if 0 < self.atr_cap < atr:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None,
                          take_profit=None, reason_code="ATR_TOO_HIGH", **base)
        return self.inner.generate_signal(row, regime)


def _backtest_metrics(
    features: pd.DataFrame,
    strategy: Any,
    broker_profile: BrokerProfile | None,
    asset_profile: AssetProfile | None,
) -> dict[str, float]:
    result = run_backtest(
        features, strategy,
        audit_decisions=False,
        broker_profile=broker_profile,
        asset_profile=asset_profile,
    )
    m = result.metrics
    return {
        "total_trades": float(m.get("total_trades", 0)),
        "win_rate": round(float(m.get("win_rate", 0)) * 100, 2),
        "profit_factor": round(float(m.get("profit_factor", 0)), 4),
        "net_profit": round(float(m.get("net_profit", 0)), 4),
        "max_drawdown_pct": round(float(m.get("max_drawdown", 0)) * 100, 2),
        "sharpe_ratio": round(float(m.get("sharpe_ratio", 0)), 4),
        "expectancy": round(float(m.get("expectancy", 0)), 4),
    }


class StrategyTuner:
    """Run Stage 1-3 tuning for a strategy on a single symbol/timeframe."""

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        strategy: Any,
        broker_name: str = "current_broker_demo",
    ) -> None:
        self.symbol = symbol.upper()
        self.timeframe = timeframe.upper()
        self.strategy = strategy
        self.asset_profile = ASSET_PROFILES.get(self.symbol)
        self.broker_profile = load_broker_profile(broker_name)
        self._features: pd.DataFrame | None = None

    @property
    def features(self) -> pd.DataFrame:
        if self._features is None:
            self._features = load_feature_data(self.symbol, self.timeframe)
        return self._features

    def run(self) -> TuningResult:
        stages: list[StageResult] = []

        # Stage 1: broker costs
        s1 = self._stage1_costs()
        stages.append(s1)
        if not s1.passed:
            return self._result(stages, {}, "STAGE1_COST_KILL")

        # Stage 2: ATR gate
        s2 = self._stage2_atr()
        stages.append(s2)
        atr_cap = s2.best_config.get("atr_cap", 0.0)

        # Stage 3: session window (using best ATR cap from Stage 2)
        s3 = self._stage3_sessions(atr_cap)
        stages.append(s3)

        optimal = {
            "atr_cap": atr_cap,
            "atr_percentile": s2.best_config.get("percentile"),
            "session_start_utc": s3.best_config.get("start_utc", 7),
            "session_end_utc": s3.best_config.get("end_utc", 20),
            "session_label": s3.best_config.get("label", ""),
        }

        # MT5 gate — use final Stage 3 metrics
        final = s3.metrics
        blocks = []
        if final.get("profit_factor", 0) < MT5_MIN_PF:
            blocks.append(f"PF {final['profit_factor']:.2f} < {MT5_MIN_PF}")
        if final.get("sharpe_ratio", 0) < MT5_MIN_SHARPE:
            blocks.append(f"Sharpe {final['sharpe_ratio']:.2f} < {MT5_MIN_SHARPE}")
        if final.get("max_drawdown_pct", 100) > MT5_MAX_DRAWDOWN_PCT:
            blocks.append(f"DD {final['max_drawdown_pct']:.2f}% > {MT5_MAX_DRAWDOWN_PCT}%")
        if int(final.get("total_trades", 0)) < 30:
            blocks.append(f"trades {int(final['total_trades'])} < 30")

        block_reason = "; ".join(blocks) if blocks else ""
        return self._result(stages, optimal, block_reason)

    def _stage1_costs(self) -> StageResult:
        logger.info("Stage 1: broker costs")
        raw = _backtest_metrics(self.features, self.strategy, None, None)
        costed = _backtest_metrics(self.features, self.strategy,
                                   self.broker_profile, self.asset_profile)
        passed = costed["profit_factor"] > 1.0
        return StageResult(
            stage="stage1_costs",
            passed=passed,
            best_config={"with_costs_pf": costed["profit_factor"]},
            metrics=costed,
            note=f"raw_pf={raw['profit_factor']} costed_pf={costed['profit_factor']}",
        )

    def _stage2_atr(self) -> StageResult:
        logger.info("Stage 2: ATR gate sweep")
        atr = self.features["atr"].dropna()
        best: dict[str, Any] = {}
        best_sharpe = -999.0
        sweep = []
        for pct in ATR_PERCENTILES:
            cap = float(atr.quantile(pct))
            s = _GatedStrategy(self.strategy, cap, 0, 24)
            m = _backtest_metrics(self.features, s, self.broker_profile, self.asset_profile)
            sweep.append({"percentile": pct, "cap": round(cap, 4), **m})
            if m["sharpe_ratio"] > best_sharpe and m["total_trades"] >= 30:
                best_sharpe = m["sharpe_ratio"]
                best = {"atr_cap": round(cap, 4), "percentile": pct, **m}

        if not best:
            best = sweep[0]
        return StageResult(
            stage="stage2_atr",
            passed=True,
            best_config=best,
            metrics={k: v for k, v in best.items() if isinstance(v, float)},
            note=f"best percentile={best.get('percentile')} cap={best.get('atr_cap')}",
        )

    def _stage3_sessions(self, atr_cap: float) -> StageResult:
        logger.info("Stage 3: session window sweep")
        best: dict[str, Any] = {}
        best_sharpe = -999.0
        for label, start, end in SESSIONS:
            s = _GatedStrategy(self.strategy, atr_cap, start, end)
            m = _backtest_metrics(self.features, s, self.broker_profile, self.asset_profile)
            if m["sharpe_ratio"] > best_sharpe and m["total_trades"] >= 30:
                best_sharpe = m["sharpe_ratio"]
                best = {"label": label, "start_utc": start, "end_utc": end, **m}

        if not best:
            best = {"label": "7-20 (baseline)", "start_utc": 7, "end_utc": 20}
        passed = best.get("profit_factor", 0) >= MT5_MIN_PF
        return StageResult(
            stage="stage3_sessions",
            passed=passed,
            best_config=best,
            metrics={k: v for k, v in best.items() if isinstance(v, (int, float))},
            note=f"best session={best.get('label')}",
        )

    def _result(
        self,
        stages: list[StageResult],
        optimal: dict[str, Any],
        block_reason: str,
    ) -> TuningResult:
        last = stages[-1].metrics if stages else {}
        return TuningResult(
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_name=getattr(self.strategy, "name", "unknown"),
            tuned_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            mt5_ready=not bool(block_reason),
            mt5_block_reason=block_reason,
            stages=stages,
            optimal_config=optimal,
            summary={
                "profit_factor": last.get("profit_factor", 0.0),
                "sharpe_ratio": last.get("sharpe_ratio", 0.0),
                "max_drawdown_pct": last.get("max_drawdown_pct", 0.0),
                "total_trades": last.get("total_trades", 0.0),
                "win_rate": last.get("win_rate", 0.0),
            },
        )

    def save(self, result: TuningResult, output_dir: str = "configs/tuned") -> Path:
        path = Path(output_dir) / f"{result.symbol}_{result.timeframe}_{result.strategy_name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        def _serial(obj: Any) -> Any:
            if isinstance(obj, StageResult):
                return asdict(obj)
            raise TypeError(type(obj))

        path.write_text(json.dumps(asdict(result), default=_serial, indent=2))
        return path

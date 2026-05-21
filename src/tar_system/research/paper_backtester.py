"""
Paper Strategy Backtester

Executes paper-based strategies on historical market data and calculates performance metrics.
Generates equity curves and performance comparison graphs.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json
import numpy as np
import pandas as pd
from datetime import datetime

from .strategy_importer import create_strategy_from_paper, PAPER_STRATEGIES
from .strategy_enhancements import (
    AdaptiveParameters,
    MultiTimeframeFilter,
    RegimeDetection,
    VolumeConfirmation,
)


class PaperStrategyBacktester:
    """Engine for backtesting paper strategies"""

    def __init__(self, data_dir: str = "data/validated"):
        self.data_dir = Path(data_dir)
        self._cache = {}

    def _load_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Load market data from parquet"""
        cache_key = f"{symbol}_{timeframe}"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        file_path = self.data_dir / f"{symbol}_{timeframe}.parquet"
        if not file_path.exists():
            raise FileNotFoundError(f"Data not found: {file_path}")

        df = pd.read_parquet(file_path)
        self._cache[cache_key] = df.copy()
        return df.copy()

    def backtest_strategy(
        self,
        strategy_name: str,
        symbol: str = "XAUUSD",
        timeframe: str = "M15",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_rows: Optional[int] = None,
        use_volume_confirmation: bool = True,
        use_multi_timeframe_filter: bool = False,
        use_regime_detection: bool = True,
        parameter_variant: Optional[str] = None,
        multi_timeframe_data: Optional[Dict[str, Dict[str, pd.DataFrame]]] = None,
        **param_overrides,
    ) -> Dict[str, Any]:
        """
        Backtest a single strategy

        Args:
            strategy_name: Strategy key ('mean_reversion', 'momentum', etc)
            symbol: Trading symbol
            timeframe: Time frame
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            max_rows: Optional cap after date filtering; keeps smoke tests fast
            use_volume_confirmation: Apply volume filter to signals
            use_multi_timeframe_filter: Require higher-timeframe confirmation when data exists
            use_regime_detection: Adjust parameters by detected regime
            parameter_variant: Force an adaptive parameter variant
            multi_timeframe_data: Optional Dict[symbol -> Dict[timeframe -> DataFrame]]
            **param_overrides: Parameter overrides

        Returns:
            Dictionary with performance metrics
        """
        adaptive = AdaptiveParameters()
        regime_detector = RegimeDetection()

        # Initial strategy for lookback and defaults
        strategy, params = create_strategy_from_paper(
            strategy_name, asset=symbol, timeframe=timeframe, **param_overrides
        )

        # Load data
        df = self._load_data(symbol, timeframe)

        # Filter by dates if specified
        if start_date or end_date:
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                if start_date:
                    df = df[df["timestamp"] >= start_date]
                if end_date:
                    df = df[df["timestamp"] <= end_date]
        if max_rows is not None and max_rows > 0:
            df = df.tail(max_rows).reset_index(drop=True)

        if len(df) < params.lookback_period + 10:
            return self._create_empty_result(strategy_name, "insufficient data")

        # Regime detection and adaptive parameters
        if use_regime_detection:
            regime = regime_detector.detect_regime(df, len(df) - 1)
            variant_name = parameter_variant if parameter_variant else regime
            variant_params = adaptive.get_variant_for_regime(variant_name)
            for key in ["entry_threshold", "stop_loss_pct", "take_profit_pct"]:
                if key not in param_overrides and key in variant_params:
                    param_overrides[key] = variant_params[key]

        elif parameter_variant:
            variant_params = adaptive.get_variant_for_regime(parameter_variant)
            for key in ["entry_threshold", "stop_loss_pct", "take_profit_pct"]:
                if key not in param_overrides and key in variant_params:
                    param_overrides[key] = variant_params[key]

        # Re-create strategy with any adaptive overrides
        strategy, params = create_strategy_from_paper(
            strategy_name,
            asset=symbol,
            timeframe=timeframe,
            **param_overrides,
        )

        volume_confirm = VolumeConfirmation(
            lookback_period=params.lookback_period,
            volume_multiplier=param_overrides.get("volume_multiplier", 1.2),
        )
        mtf_filter = MultiTimeframeFilter(multi_timeframe_data or {})

        # Generate signals with optional volume and higher-timeframe confirmation.
        signals = []
        for i in range(len(df)):
            signal = strategy.generate_signal(df, i)
            if use_volume_confirmation and not volume_confirm.is_valid_volume(df, i):
                signal = 0
            if use_multi_timeframe_filter and not mtf_filter.confirms_signal(symbol, timeframe, i, signal):
                signal = 0
            signals.append(signal)

        df["signal"] = signals

        if len(df) < params.lookback_period + 10:
            return self._create_empty_result(strategy_name, "insufficient data")

        # Execute trades
        trades = self._execute_trades(df, params)

        # Calculate metrics
        metrics = self._calculate_metrics(df, trades, params)
        metrics["strategy_name"] = strategy_name
        metrics["symbol"] = symbol
        metrics["timeframe"] = timeframe
        metrics["reference"] = strategy.reference.to_dict()
        metrics["parameters"] = params.to_dict()
        metrics["trade_count"] = len(trades)
        metrics["trades"] = trades

        return metrics

    def _execute_trades(self, df: pd.DataFrame, params: Any) -> list:
        """Execute trades based on signals"""
        trades = []
        position = None
        entry_price = None
        entry_idx = None

        for i, row in df.iterrows():
            signal = row["signal"]
            current_price = row["close"]

            # Close position if signal flips or exit triggered
            if position is not None:
                if position == 1:
                    pnl_pct = (current_price - entry_price) / entry_price
                    pnl_abs = current_price - entry_price
                else:
                    pnl_pct = (entry_price - current_price) / entry_price
                    pnl_abs = entry_price - current_price

                # Exit logic
                should_exit = False
                exit_reason = None

                if position == 1 and pnl_pct >= params.take_profit_pct:
                    should_exit = True
                    exit_reason = "TP"
                elif position == 1 and pnl_pct <= -params.stop_loss_pct:
                    should_exit = True
                    exit_reason = "SL"
                elif position == -1 and pnl_pct >= params.take_profit_pct:
                    should_exit = True
                    exit_reason = "TP"
                elif position == -1 and pnl_pct <= -params.stop_loss_pct:
                    should_exit = True
                    exit_reason = "SL"
                elif signal != 0 and signal != position:
                    should_exit = True
                    exit_reason = "SIGNAL"

                if should_exit:
                    trades.append(
                        {
                            "entry_idx": entry_idx,
                            "exit_idx": i,
                            "entry_price": entry_price,
                            "exit_price": current_price,
                            "side": "BUY" if position == 1 else "SELL",
                            "pnl_pct": pnl_pct,
                            "pnl_absolute": pnl_abs,
                            "exit_reason": exit_reason,
                        }
                    )
                    position = None
                    entry_price = None
                    entry_idx = None

            # Open new position
            if position is None and signal != 0:
                position = signal
                entry_price = current_price
                entry_idx = i

        # Close any remaining open position at the end of the data window.
        if position is not None and len(df) > 0:
            final_price = float(df.iloc[-1]["close"])
            if position == 1:
                pnl_pct = (final_price - entry_price) / entry_price
                pnl_abs = final_price - entry_price
            else:
                pnl_pct = (entry_price - final_price) / entry_price
                pnl_abs = entry_price - final_price

            trades.append(
                {
                    "entry_idx": entry_idx,
                    "exit_idx": len(df) - 1,
                    "entry_price": entry_price,
                    "exit_price": final_price,
                    "side": "BUY" if position == 1 else "SELL",
                    "pnl_pct": pnl_pct,
                    "pnl_absolute": pnl_abs,
                    "exit_reason": "END",
                }
            )

        return trades

    def _calculate_metrics(self, df: pd.DataFrame, trades: list, params: Any) -> Dict:
        """Calculate performance metrics"""
        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown_pct": 0.0,
                "total_return_pct": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
            }

        pnl_array = np.array([t["pnl_pct"] for t in trades])

        winning_trades = pnl_array[pnl_array > 0]
        losing_trades = pnl_array[pnl_array < 0]

        total_wins = np.sum(winning_trades) if len(winning_trades) > 0 else 0
        total_losses = np.abs(np.sum(losing_trades)) if len(losing_trades) > 0 else 0

        win_rate = len(winning_trades) / len(trades) if trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Sharpe ratio (assuming daily periods)
        daily_returns = pnl_array
        sharpe = (
            np.mean(daily_returns) / np.std(daily_returns)
            if np.std(daily_returns) > 0
            else 0
        )

        # Max drawdown from equity curve
        equity = 100 * np.cumprod(1 + daily_returns)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max
        max_drawdown = np.abs(np.min(drawdown))

        total_return = np.prod(1 + daily_returns) - 1

        avg_win = np.mean(winning_trades) if len(winning_trades) > 0 else 0
        avg_loss = np.mean(losing_trades) if len(losing_trades) > 0 else 0

        return {
            "total_trades": len(trades),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "sharpe_ratio": float(sharpe * np.sqrt(252)),  # Annualized
            "max_drawdown_pct": float(max_drawdown),
            "total_return_pct": float(total_return),
            "average_win": float(avg_win),
            "average_loss": float(avg_loss),
        }

    def _create_empty_result(self, strategy_name: str, reason: str) -> Dict:
        """Create empty result on error"""
        return {
            "strategy_name": strategy_name,
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown_pct": 0.0,
            "total_return_pct": 0.0,
            "error": reason,
        }

    def backtest_all_strategies(
        self,
        symbol: str = "XAUUSD",
        timeframe: str = "M15",
        **common_params,
    ) -> Dict[str, Dict]:
        """Backtest all available paper strategies"""
        results = {}

        for strategy_name in PAPER_STRATEGIES.keys():
            print(f"  [{strategy_name}] Backtesting...")
            try:
                result = self.backtest_strategy(
                    strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    **common_params,
                )
                results[strategy_name] = result
            except Exception as e:
                print(f"    Error: {e}")
                results[strategy_name] = self._create_empty_result(
                    strategy_name, str(e)
                )

        return results

    def export_results_json(
        self, results: Dict[str, Dict], output_path: str
    ) -> None:
        """Export backtest results to JSON"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove trades from export to keep file size manageable
        export_results = {}
        for name, result in results.items():
            result_copy = result.copy()
            result_copy.pop("trades", None)
            export_results[name] = result_copy

        with open(output_path, "w") as f:
            json.dump(export_results, f, indent=2, default=str)

        print(f"✅ Exported results to {output_path}")

    def generate_comparison_graph(
        self, results: Dict[str, Dict], output_path: str
    ) -> None:
        """Generate 4-panel comparison graph"""
        try:
            import matplotlib.pyplot as plt

            metrics = ["sharpe_ratio", "max_drawdown_pct", "win_rate", "profit_factor"]
            strategy_names = list(results.keys())

            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle("Paper Strategy Performance Comparison", fontsize=16, fontweight="bold")

            for idx, metric in enumerate(metrics):
                ax = axes[idx // 2, idx % 2]
                values = []

                for name in strategy_names:
                    val = results[name].get(metric, 0)
                    # Handle None or errors
                    if val is None or (isinstance(val, float) and np.isnan(val)):
                        val = 0
                    values.append(val)

                colors = [
                    "green" if v > 0 else "red" if v < 0 else "gray" for v in values
                ]
                ax.bar(strategy_names, values, color=colors, alpha=0.7, edgecolor="black")
                ax.set_ylabel(metric.replace("_", " ").title())
                ax.set_title(metric.replace("_", " ").title())
                ax.grid(axis="y", alpha=0.3)
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

            plt.tight_layout()
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close()
            print(f"✅ Generated comparison graph: {output_path}")

        except ImportError:
            print("⚠️ matplotlib not available, skipping graph generation")

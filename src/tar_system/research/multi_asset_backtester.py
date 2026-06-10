"""
Multi-Asset & Multi-Parameter Backtest Engine

Systematically tests strategies across multiple assets and parameter variants.
Generates comprehensive comparison reports.

References:
1. Merton & Samuelson (1974) - "Fallacy of the Log-Normal Approximation to 
   Optimal Portfolio Decision-Making over Many Periods" - Journal of Financial 
   Economics - Shows importance of cross-asset testing
2. Ang & Bekaert (2002) - "Regime Switches in Interest Rates" - Journal of 
   Business & Economic Statistics - Regime-specific parameter optimization
3. De Bock & Spiegel (2010) - "Changing Importance of Market, Industry, and Firm-
   Specific Information" - Shows parameter sensitivity across assets
"""

from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import json
import pandas as pd
from datetime import datetime

from .paper_backtester import PaperStrategyBacktester
from .finance_reviewer import AnthropicFinanceReviewer
from .strategy_enhancements import AdaptiveParameters, RegimeDetection


class MultiAssetBacktester:
    """
    Test strategies across multiple assets with parameter variants
    """

    def __init__(self, data_dir: str = "data/validated"):
        self.data_dir = Path(data_dir)
        self.backtester = PaperStrategyBacktester(str(self.data_dir))
        self.reviewer = AnthropicFinanceReviewer()
        self.adaptive_params = AdaptiveParameters()
        self.regime_detector = RegimeDetection()

    def get_available_assets(self) -> List[str]:
        """Get list of available assets from data files"""
        assets = set()
        for f in self.data_dir.glob("*.parquet"):
            # Extract symbol (e.g., XAUUSD from XAUUSD_M15.parquet)
            parts = f.stem.split("_")
            if parts:
                symbol = parts[0]
                assets.add(symbol)

        return sorted(assets)

    def get_available_timeframes(self, symbol: str) -> List[str]:
        """Get timeframes available for asset"""
        timeframes = set()
        for f in self.data_dir.glob(f"{symbol}_*.parquet"):
            parts = f.stem.split("_")
            if len(parts) > 1:
                timeframes.add(parts[1])

        return sorted(
            timeframes, key=lambda x: ["M1", "M5", "M15", "M30", "H1", "H4", "D1"].index(x)
        )

    def test_strategy_across_assets(
        self,
        strategy_name: str,
        assets: List[str] = None,
        timeframe: str = "M15",
        param_variant: str = "moderate",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_rows: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Test strategy on multiple assets
        
        Args:
            strategy_name: Strategy to test
            assets: List of assets (or None for all available)
            timeframe: Timeframe to test
            param_variant: 'conservative', 'moderate', 'aggressive', 'breakout'
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            max_rows: Optional row cap after date filtering
        
        Returns:
            Dict[asset -> backtest_result]
        """
        if assets is None:
            assets = self.get_available_assets()

        # Get parameters for variant
        params = self.adaptive_params.get_variant_for_regime(param_variant)

        results = {}

        for asset in assets:
            print(f"  [{asset}] Testing {strategy_name}...", end="", flush=True)

            try:
                result = self.backtester.backtest_strategy(
                    strategy_name,
                    symbol=asset,
                    timeframe=timeframe,
                    entry_threshold=params["entry_threshold"],
                    stop_loss_pct=params["stop_loss_pct"],
                    take_profit_pct=params["take_profit_pct"],
                    start_date=start_date,
                    end_date=end_date,
                    max_rows=max_rows,
                )
                results[asset] = result

                # Print result
                trades = result.get("total_trades", 0)
                sharpe = result.get("sharpe_ratio", 0)
                print(f" ✓ ({trades} trades, Sharpe {sharpe:.2f})")

            except Exception as e:
                print(f" ✗ Error: {str(e)[:50]}")
                results[asset] = {
                    "error": str(e),
                    "total_trades": 0,
                }

        return results

    def test_parameter_variants(
        self,
        strategy_name: str,
        symbol: str = "XAUUSD",
        timeframe: str = "M15",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_rows: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Test strategy with all parameter variants
        
        Returns:
            Dict[variant_name -> backtest_result]
        """
        results = {}
        variants = self.adaptive_params.get_all_variants()

        print(f"Testing {strategy_name} ({symbol} {timeframe}) with parameter variants:")

        for variant_name, params in variants.items():
            print(f"  [{variant_name:12}] Testing...", end="", flush=True)

            try:
                result = self.backtester.backtest_strategy(
                    strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    entry_threshold=params["entry_threshold"],
                    stop_loss_pct=params["stop_loss_pct"],
                    take_profit_pct=params["take_profit_pct"],
                    start_date=start_date,
                    end_date=end_date,
                    max_rows=max_rows,
                )
                results[variant_name] = result

                trades = result.get("total_trades", 0)
                sharpe = result.get("sharpe_ratio", 0)
                dd = result.get("max_drawdown_pct", 0)
                print(f" ({trades} trades, Sharpe {sharpe:.2f}, DD {dd*100:.1f}%)")

            except Exception as e:
                print(f" Error: {str(e)[:40]}")
                results[variant_name] = {"error": str(e), "total_trades": 0}

        return results

    def test_all_strategies_all_assets(
        self,
        timeframe: str = "M15",
        param_variant: str = "moderate",
        strategies: List[str] = None,
        assets: List[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_rows: Optional[int] = None,
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Comprehensive test: All strategies × All available assets
        
        Returns:
            Dict[strategy -> Dict[asset -> result]]
        """
        from .strategy_importer import PAPER_STRATEGIES

        print("\n" + "=" * 80)
        print("COMPREHENSIVE MULTI-ASSET BACKTEST")
        print("=" * 80 + "\n")

        all_results = {}

        strategy_names = strategies or list(PAPER_STRATEGIES.keys())
        for strategy_name in strategy_names:
            print(f"\nStrategy: {strategy_name.upper()}")
            print("-" * 80)

            asset_results = self.test_strategy_across_assets(
                strategy_name,
                assets=assets,
                timeframe=timeframe,
                param_variant=param_variant,
                start_date=start_date,
                end_date=end_date,
                max_rows=max_rows,
            )

            all_results[strategy_name] = asset_results

        return all_results

    def generate_cross_asset_comparison(
        self,
        results: Dict[str, Dict[str, Dict[str, Any]]],
        output_file: str = "data/paper_strategies/cross_asset_comparison.json",
    ) -> None:
        """
        Generate comparison report across assets
        
        Args:
            results: Results from test_all_strategies_all_assets()
            output_file: Output JSON file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Summarize results
        summary = {}

        for strategy_name, asset_results in results.items():
            strategy_summary = {}

            for asset, result in asset_results.items():
                if "error" in result:
                    strategy_summary[asset] = {
                        "error": result["error"],
                        "trades": 0,
                    }
                else:
                    sharpe = result.get("sharpe_ratio", 0)
                    dd = result.get("max_drawdown_pct", 0)
                    wr = result.get("win_rate", 0)
                    ret = result.get("total_return_pct", 0)
                    trades = result.get("total_trades", 0)

                    # Get verdict
                    verdict, rationale, score = self.reviewer.get_strategy_verdict(
                        result
                    )

                    strategy_summary[asset] = {
                        "verdict": verdict,
                        "score": score,
                        "sharpe_ratio": sharpe,
                        "max_drawdown_pct": dd,
                        "win_rate": wr,
                        "total_return_pct": ret,
                        "total_trades": trades,
                    }

            summary[strategy_name] = strategy_summary

        # Write JSON
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\n✅ Exported cross-asset comparison to {output_file}")

        # Print summary to console
        print("\n" + "=" * 80)
        print("CROSS-ASSET SUMMARY")
        print("=" * 80 + "\n")

        for strategy_name, asset_results in summary.items():
            print(f"\n{strategy_name.upper()}:")
            print("-" * 80)

            keep_count = sum(
                1 for v in asset_results.values() if v.get("verdict") == "KEEP"
            )
            total = len(asset_results)

            print(f"  KEEP on {keep_count}/{total} assets:")

            for asset in sorted(asset_results.keys()):
                info = asset_results[asset]
                if info.get("verdict") == "KEEP":
                    print(
                        f"    {asset:10} | Sharpe {info['sharpe_ratio']:6.2f} | "
                        f"DD {info['max_drawdown_pct']*100:5.1f}% | "
                        f"Return {info['total_return_pct']*100:6.1f}%"
                    )

    def generate_parameter_variant_report(
        self,
        all_variant_results: Dict[str, Dict],
        output_file: str = "data/paper_strategies/parameter_variants_report.json",
    ) -> None:
        """
        Generate report on parameter variants
        
        Args:
            all_variant_results: Results from test_parameter_variants()
            output_file: Output JSON file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Summarize
        summary = {}

        for variant_name, result in all_variant_results.items():
            if "error" not in result:
                verdict, rationale, score = self.reviewer.get_strategy_verdict(result)

                summary[variant_name] = {
                    "verdict": verdict,
                    "score": score,
                    "sharpe_ratio": result.get("sharpe_ratio", 0),
                    "max_drawdown_pct": result.get("max_drawdown_pct", 0),
                    "win_rate": result.get("win_rate", 0),
                    "total_return_pct": result.get("total_return_pct", 0),
                    "total_trades": result.get("total_trades", 0),
                    "rationale": rationale,
                }
            else:
                summary[variant_name] = {"error": result["error"]}

        # Write JSON
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\n✅ Exported parameter variant report to {output_file}")

        # Print summary
        print("\n" + "=" * 80)
        print("PARAMETER VARIANT COMPARISON")
        print("=" * 80 + "\n")

        for variant_name in sorted(summary.keys()):
            info = summary[variant_name]
            if "error" not in info:
                print(
                    f"{variant_name:12} | {info['verdict']:6} | Score {info['score']}/10 | "
                    f"Sharpe {info['sharpe_ratio']:6.2f} | Trades {info['total_trades']:6.0f}"
                )

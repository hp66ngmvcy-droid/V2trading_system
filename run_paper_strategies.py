#!/usr/bin/env python3
"""
Paper Strategy Pipeline Runner

Orchestrates the full cycle:
1. Load academic paper strategies
2. Backtest on real market data
3. Generate performance metrics
4. Get finance review verdict
5. Export results and graphs
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tar_system.research.strategy_importer import PAPER_STRATEGIES
from tar_system.research.paper_backtester import PaperStrategyBacktester
from tar_system.research.finance_reviewer import AnthropicFinanceReviewer


def main():
    """Run full paper strategy pipeline"""
    print("\n" + "=" * 80)
    print("PAPER STRATEGY RESEARCH PIPELINE")
    print("=" * 80 + "\n")

    # Configuration
    symbol = "XAUUSD"
    timeframe = "M15"
    output_dir = Path("data/paper_strategies")
    output_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # PHASE 1: Initialize
    # =========================================================================
    print("PHASE 1: Initialize")
    print("-" * 80)
    print(f"Symbol:    {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Strategies: {list(PAPER_STRATEGIES.keys())}")
    print(f"Output:    {output_dir}\n")

    # =========================================================================
    # PHASE 2: Backtest All Strategies
    # =========================================================================
    print("PHASE 2: Backtest All Strategies")
    print("-" * 80)

    backtester = PaperStrategyBacktester()
    all_results = backtester.backtest_all_strategies(symbol=symbol, timeframe=timeframe)

    print()
    print("Backtest Results Summary:")
    print("-" * 80)
    for strategy_name, result in all_results.items():
        trades = result.get("total_trades", 0)
        sharpe = result.get("sharpe_ratio", 0)
        dd = result.get("max_drawdown_pct", 0)
        print(
            f"  {strategy_name:25} | Trades: {trades:6.0f} | "
            f"Sharpe: {sharpe:6.2f} | Max DD: {dd*100:6.1f}%"
        )
    print()

    # =========================================================================
    # PHASE 3: Export Backtest Results
    # =========================================================================
    print("PHASE 3: Export Results")
    print("-" * 80)

    results_file = output_dir / "paper_strategies_results.json"
    backtester.export_results_json(all_results, str(results_file))

    # =========================================================================
    # PHASE 4: Finance Review (Verdict Scoring)
    # =========================================================================
    print("PHASE 4: Finance Review")
    print("-" * 80)

    reviewer = AnthropicFinanceReviewer()
    verdicts = reviewer.review_all_strategies(all_results)

    # Print verdicts to console
    reviewer.print_summary(verdicts)

    # =========================================================================
    # PHASE 5: Export Verdicts and Reports
    # =========================================================================
    print("PHASE 5: Export Verdicts & Reports")
    print("-" * 80)

    verdicts_file = output_dir / "strategy_verdicts.json"
    reviewer.export_verdicts_json(verdicts, str(verdicts_file))

    report_file = output_dir / f"finance_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    reviewer.generate_review_report(verdicts, str(report_file))

    # =========================================================================
    # PHASE 6: Generate Comparison Graph
    # =========================================================================
    print("PHASE 6: Generate Graphs")
    print("-" * 80)

    graph_file = output_dir / "paper_strategies_comparison.png"
    backtester.generate_comparison_graph(all_results, str(graph_file))

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80 + "\n")

    keep_count = sum(1 for v in verdicts.values() if v["verdict"] == "KEEP")
    revise_count = sum(1 for v in verdicts.values() if v["verdict"] == "REVISE")
    kill_count = sum(1 for v in verdicts.values() if v["verdict"] == "KILL")

    print(f"Results saved to: {output_dir}\n")
    print(f"Summary:")
    print(f"  ✅ KEEP:   {keep_count} strategies")
    print(f"  ⚠️  REVISE: {revise_count} strategies")
    print(f"  ❌ KILL:   {kill_count} strategies\n")

    print("Output Files:")
    print(f"  - {results_file.name}")
    print(f"  - {verdicts_file.name}")
    print(f"  - {report_file.name}")
    print(f"  - {graph_file.name}\n")

    print("Next Steps:")
    if keep_count > 0:
        print("  1. Deploy KEEP strategies to paper trading")
        print("  2. Track daily P&L and adjust parameters")
        print("  3. Test on other assets (EURUSD, AUDUSD)")
        print("  4. Run walk-forward validation")
    if revise_count > 0:
        print(f"  - Optimize and re-test {revise_count} REVISE candidate(s)")
    print()


if __name__ == "__main__":
    main()

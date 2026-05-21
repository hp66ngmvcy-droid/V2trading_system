"""
Anthropic Finance Strategy Reviewer

Applies verdict scoring system to trading strategy performance metrics.
Generates KEEP/REVISE/KILL recommendations with detailed rationale.
"""

from typing import Dict, Tuple, Any
import json
from pathlib import Path


class AnthropicFinanceReviewer:
    """
    Verdict engine for trading strategy assessment
    
    Scoring: 0-10 points max (4 metrics × max 2-3 points each)
    - KEEP (≥7): Ready for deployment
    - REVISE (4-6): Promising but needs work
    - KILL (<4): Abandon strategy
    """

    def __init__(self):
        self.criteria = {
            "sharpe_ratio": {"good": 1.0, "acceptable": 0.5},
            "max_drawdown_pct": {"good": 0.15, "acceptable": 0.25},
            "win_rate": {"good": 0.55, "acceptable": 0.45},
            "total_return_pct": {"good": 0.10, "acceptable": 0.0},
        }

    def get_strategy_verdict(
        self, strategy_result: Dict[str, Any]
    ) -> Tuple[str, str, int]:
        """
        Get verdict for a strategy result

        Args:
            strategy_result: Result dict from backtester

        Returns:
            Tuple of (verdict, rationale, score)
            verdict: 'KEEP' | 'REVISE' | 'KILL'
            rationale: Detailed explanation
            score: 0-10 points
        """
        score = 0
        reasons = []

        # Extract metrics
        sharpe = strategy_result.get("sharpe_ratio", 0)
        max_dd = strategy_result.get("max_drawdown_pct", 0)
        win_rate = strategy_result.get("win_rate", 0)
        total_return = strategy_result.get("total_return_pct", 0)
        trades = strategy_result.get("total_trades", 0)

        # Check if strategy has valid data
        if trades == 0 or "error" in strategy_result:
            return (
                "KILL",
                f"❌ Insufficient trades ({trades}) or error: {strategy_result.get('error', 'unknown')}",
                0,
            )

        # Score Sharpe Ratio (max 3 points)
        if sharpe >= self.criteria["sharpe_ratio"]["good"]:
            score += 3
            reasons.append(f"✓ Strong Sharpe ({sharpe:.2f})")
        elif sharpe >= self.criteria["sharpe_ratio"]["acceptable"]:
            score += 1
            reasons.append(f"⚠ Moderate Sharpe ({sharpe:.2f})")
        else:
            reasons.append(f"❌ Weak Sharpe ({sharpe:.2f})")

        # Score Max Drawdown (max 2 points)
        if max_dd <= self.criteria["max_drawdown_pct"]["good"]:
            score += 2
            reasons.append(f"✓ Low Drawdown ({max_dd*100:.1f}%)")
        elif max_dd <= self.criteria["max_drawdown_pct"]["acceptable"]:
            score += 1
            reasons.append(f"⚠ Acceptable Drawdown ({max_dd*100:.1f}%)")
        else:
            reasons.append(f"❌ High Drawdown ({max_dd*100:.1f}%)")

        # Score Win Rate (max 2 points)
        if win_rate >= self.criteria["win_rate"]["good"]:
            score += 2
            reasons.append(f"✓ Strong Win Rate ({win_rate*100:.1f}%)")
        elif win_rate >= self.criteria["win_rate"]["acceptable"]:
            score += 1
            reasons.append(f"⚠ Acceptable Win Rate ({win_rate*100:.1f}%)")
        else:
            reasons.append(f"❌ Weak Win Rate ({win_rate*100:.1f}%)")

        # Score Total Return (max 2 points)
        if total_return >= self.criteria["total_return_pct"]["good"]:
            score += 2
            reasons.append(f"✓ Strong Return ({total_return*100:.1f}%)")
        elif total_return >= self.criteria["total_return_pct"]["acceptable"]:
            score += 1
            reasons.append(f"⚠ Positive Return ({total_return*100:.1f}%)")
        else:
            reasons.append(f"❌ Negative Return ({total_return*100:.1f}%)")

        # Determine verdict
        if score >= 7:
            verdict = "KEEP"
        elif score >= 4:
            verdict = "REVISE"
        else:
            verdict = "KILL"

        rationale = " | ".join(reasons)

        return verdict, rationale, score

    def review_all_strategies(
        self, all_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Review all strategy results and generate verdicts

        Args:
            all_results: Dict of strategy_name -> backtest_result

        Returns:
            Dict of strategy_name -> {verdict, rationale, score, details}
        """
        verdicts = {}

        for strategy_name, result in all_results.items():
            verdict, rationale, score = self.get_strategy_verdict(result)

            verdicts[strategy_name] = {
                "verdict": verdict,
                "rationale": rationale,
                "score": score,
                "metrics": {
                    "sharpe_ratio": result.get("sharpe_ratio", 0),
                    "max_drawdown_pct": result.get("max_drawdown_pct", 0),
                    "win_rate": result.get("win_rate", 0),
                    "total_return_pct": result.get("total_return_pct", 0),
                    "total_trades": result.get("total_trades", 0),
                },
            }

        return verdicts

    def export_verdicts_json(
        self, verdicts: Dict[str, Dict[str, Any]], output_path: str
    ) -> None:
        """Export verdicts to JSON"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(verdicts, f, indent=2)

        print(f"✅ Exported verdicts to {output_path}")

    def generate_review_report(
        self, verdicts: Dict[str, Dict[str, Any]], output_path: str
    ) -> None:
        """Generate human-readable review report"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("PAPER STRATEGY FINANCE REVIEW REPORT\n")
            f.write("=" * 80 + "\n\n")

            # Summary
            keep_count = sum(1 for v in verdicts.values() if v["verdict"] == "KEEP")
            revise_count = sum(
                1 for v in verdicts.values() if v["verdict"] == "REVISE"
            )
            kill_count = sum(1 for v in verdicts.values() if v["verdict"] == "KILL")

            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"KEEP Strategies:   {keep_count}\n")
            f.write(f"REVISE Strategies: {revise_count}\n")
            f.write(f"KILL Strategies:   {kill_count}\n\n")

            # Detailed reviews
            f.write("DETAILED STRATEGY REVIEWS\n")
            f.write("-" * 80 + "\n\n")

            for strategy_name in sorted(verdicts.keys()):
                verdict_info = verdicts[strategy_name]
                metrics = verdict_info["metrics"]

                f.write(f"Strategy: {strategy_name.upper()}\n")
                f.write(f"Verdict:  {verdict_info['verdict']} (Score: {verdict_info['score']}/10)\n")
                f.write(f"Rationale: {verdict_info['rationale']}\n\n")

                f.write("Metrics:\n")
                f.write(f"  Sharpe Ratio:      {metrics['sharpe_ratio']:>7.2f}\n")
                f.write(f"  Max Drawdown:      {metrics['max_drawdown_pct']*100:>6.1f}%\n")
                f.write(f"  Win Rate:          {metrics['win_rate']*100:>6.1f}%\n")
                f.write(f"  Total Return:      {metrics['total_return_pct']*100:>6.1f}%\n")
                f.write(f"  Total Trades:      {metrics['total_trades']:>7.0f}\n")
                f.write("\n" + "-" * 80 + "\n\n")

            # Recommendations
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 80 + "\n\n")

            if keep_count > 0:
                f.write("✅ RUN KEEPERS IN PAPER TRADING\n")
                for strategy_name, verdict_info in verdicts.items():
                    if verdict_info["verdict"] == "KEEP":
                        f.write(f"   - {strategy_name}\n")
                f.write("\n")

            if revise_count > 0:
                f.write("⚠️ OPTIMIZE AND RE-TEST REVISE CANDIDATES\n")
                for strategy_name, verdict_info in verdicts.items():
                    if verdict_info["verdict"] == "REVISE":
                        f.write(f"   - {strategy_name}\n")
                f.write("\n")

            if kill_count > 0:
                f.write("❌ KILL (ARCHIVE FOR REFERENCE)\n")
                for strategy_name, verdict_info in verdicts.items():
                    if verdict_info["verdict"] == "KILL":
                        f.write(f"   - {strategy_name}\n")
                f.write("\n")

            f.write("=" * 80 + "\n")

        print(f"✅ Generated review report: {output_path}")

    def print_summary(self, verdicts: Dict[str, Dict[str, Any]]) -> None:
        """Print summary to console"""
        print("\n" + "=" * 80)
        print("PAPER STRATEGY VERDICT SUMMARY")
        print("=" * 80 + "\n")

        for strategy_name in sorted(verdicts.keys()):
            verdict_info = verdicts[strategy_name]
            print(
                f"{strategy_name:25} | "
                f"{verdict_info['verdict']:6} | "
                f"Score: {verdict_info['score']}/10"
            )
            print(f"  {verdict_info['rationale']}\n")

# Paper Strategy Research System - Quick Reference

## 🚀 Quick Start (60 seconds)

```bash
cd /Users/whs1/Dev/V2trading_system

# Run full pipeline
./venv/bin/python run_paper_strategies.py

# View results
cat data/paper_strategies/strategy_verdicts.json
```

---

## 📊 Common Commands

### Run Full Pipeline
```bash
./venv/bin/python run_paper_strategies.py
```

### Backtest Single Strategy
```bash
./venv/bin/python -c "
from src.tar_system.research.paper_backtester import PaperStrategyBacktester
backtester = PaperStrategyBacktester()
result = backtester.backtest_strategy('momentum', symbol='XAUUSD', timeframe='M15')
print(f'Sharpe: {result[\"sharpe_ratio\"]:.2f}, DD: {result[\"max_drawdown_pct\"]*100:.1f}%')
"
```

### Backtest All Strategies on EURUSD
```bash
./venv/bin/python -c "
from src.tar_system.research.paper_backtester import PaperStrategyBacktester
backtester = PaperStrategyBacktester()
results = backtester.backtest_all_strategies(symbol='EURUSD', timeframe='M15')
for name, result in results.items():
    print(f'{name}: {result[\"total_trades\"]} trades, Sharpe {result[\"sharpe_ratio\"]:.2f}')
"
```

### Get Finance Verdict for Strategy
```bash
./venv/bin/python -c "
from src.tar_system.research.paper_backtester import PaperStrategyBacktester
from src.tar_system.research.finance_reviewer import AnthropicFinanceReviewer
backtester = PaperStrategyBacktester()
reviewer = AnthropicFinanceReviewer()
result = backtester.backtest_strategy('mean_reversion')
verdict, rationale, score = reviewer.get_strategy_verdict(result)
print(f'{verdict} ({score}/10): {rationale}')
"
```

### Test Strategy with Custom Parameters
```bash
./venv/bin/python -c "
from src.tar_system.research.paper_backtester import PaperStrategyBacktester
backtester = PaperStrategyBacktester()
result = backtester.backtest_strategy(
    'orb',
    entry_threshold=1.0,  # Custom parameter
    stop_loss_pct=0.02
)
print(f'Trades: {result[\"total_trades\"]}')
"
```

### Create Strategy and Get Citation
```bash
./venv/bin/python -c "
from src.tar_system.research.strategy_importer import create_strategy_from_paper
strategy, params = create_strategy_from_paper('volatility_breakout')
print(f'Strategy: {strategy.name}')
print(f'Citation: {strategy.get_reference()}')
"
```

### List All Available Strategies
```bash
./venv/bin/python -c "
from src.tar_system.research.strategy_importer import PAPER_STRATEGIES
print('Available Strategies:')
for name, (cls, ref, params) in PAPER_STRATEGIES.items():
    print(f'  - {name}: {ref.title} ({ref.year})')
"
```

### Generate Verdicts for All Results
```bash
./venv/bin/python -c "
import json
from src.tar_system.research.finance_reviewer import AnthropicFinanceReviewer
results = json.loads(open('data/paper_strategies/paper_strategies_results.json').read())
reviewer = AnthropicFinanceReviewer()
verdicts = reviewer.review_all_strategies(results)
for strat, info in verdicts.items():
    print(f'{strat:25} | {info[\"verdict\"]:6} | {info[\"score\"]}/10')
"
```

### View Latest Report
```bash
# Find and display latest report
ls -t data/paper_strategies/finance_review_*.txt | head -1 | xargs cat
```

---

## 📈 Backtest Results (Current)

```
XAUUSD M15 (5 strategies)
═══════════════════════════════════════════════════════════════

  Volatility Breakout     ✅ KEEP    (Score: 7/10)
  Sharpe: 5.07 | DD: 26.2% | Win Rate: 65.8% | Return: 175.2%
  
  Momentum                ✅ KEEP    (Score: 8/10)
  Sharpe: 3.61 | DD: 22.4% | Win Rate: 55.6% | Return: 138.9%
  
  Mean Reversion          ✅ KEEP    (Score: 7/10)
  Sharpe: 4.45 | DD: 32.4% | Win Rate: 62.9% | Return: 131.6%
  
  ORB                     ⚠️ REVISE   (Score: 6/10)
  Sharpe: 2.43 | DD: 26.7% | Win Rate: 51.6% | Return: 124.8%
  
  Hybrid                  ❌ KILL    (Score: 0/10)
  (No trades - signal convergence too strict)
```

---

## 🎯 Next Steps by Role

### As a Trader
1. Deploy 3 KEEP strategies to paper trading
2. Monitor P&L daily
3. Adjust stop-loss/take-profit based on live performance
4. Document lessons learned

### As a Researcher
1. Test ORB on different parameters (entry_threshold=1.0, 1.5, 2.0)
2. Try other timeframes (H1, H4)
3. Combine signals (e.g., MACD + RSI + Volume)
4. Re-test and compare results

### As a Developer
1. Add real-time trading execution integration
2. Implement parameter optimization (grid search)
3. Add machine learning signal enhancement
4. Deploy to cloud (AWS/GCP)

---

## 📁 File Structure

```
src/tar_system/research/
├── __init__.py                    # Module init
├── strategy_importer.py           # Strategy classes (5 strategies)
├── paper_backtester.py            # Backtest engine
└── finance_reviewer.py            # Verdict scoring

data/paper_strategies/
├── paper_strategies_results.json   # All metrics
├── strategy_verdicts.json          # KEEP/REVISE/KILL
├── finance_review_*.txt            # Full report
└── paper_strategies_comparison.png # 4-panel graph

run_paper_strategies.py             # CLI entry point
PAPER_STRATEGY_IMPLEMENTATION.md    # Full documentation
PAPER_STRATEGY_QUICK_REFERENCE.md   # This file
```

---

## ✅ Scoring System

| Score | Verdict | Action |
|-------|---------|--------|
| ≥ 7 | KEEP | Deploy to paper trading |
| 4-6 | REVISE | Optimize parameters, re-test |
| < 4 | KILL | Archive, try different approach |

**Criteria:** Sharpe Ratio, Max Drawdown, Win Rate, Total Return

---

## 🔧 Installation & Setup

```bash
# Navigate to workspace
cd /Users/whs1/Dev/V2trading_system

# Activate virtual environment
source ./venv/bin/activate

# Install dependencies (if needed)
./venv/bin/pip install pyarrow matplotlib numpy pandas

# Test installation
./venv/bin/python -c "import tar_system.research; print('✅ Ready')"
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| ModuleNotFoundError | Use `./venv/bin/python` instead of system python |
| pyarrow not found | `./venv/bin/pip install pyarrow` |
| Data not found | Ensure `data/validated/SYMBOL_TIMEFRAME.parquet` exists |
| Graph not generated | `./venv/bin/pip install matplotlib` |

---

## 📞 Support

For issues or questions:
1. Check [PAPER_STRATEGY_IMPLEMENTATION.md](PAPER_STRATEGY_IMPLEMENTATION.md) for detailed docs
2. Review test examples in Python code comments
3. Check `data/paper_strategies/` for generated reports

---

**Last Updated:** May 13, 2026  
**Status:** ✅ Production Ready

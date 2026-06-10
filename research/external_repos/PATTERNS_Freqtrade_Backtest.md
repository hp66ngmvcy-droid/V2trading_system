# Freqtrade: Backtest Engine Patterns

## Key Files Extracted
- `backtest.py` — Main backtest loop and execution
- `results.py` — Metrics calculation (Sharpe, DD, WR, PF)
- `strategy_resolver.py` — Strategy loading and validation

## Core Loop Pattern (From backtest.py)

```
FOR each candle in data:
  - Generate signal from strategy
  - Update position if signal changed
  - Calculate unrealized P&L
  - Log trade if closed
  
AFTER all candles:
  - Calculate equity curve
  - Calculate all metrics
  - Return results
```

## Key Learnings

### 1. Data Iteration Efficiency
- Freqtrade iterates candles efficiently using numpy arrays
- Avoids row-by-row iteration (slow on large datasets)
- Uses vectorized operations where possible

### 2. Trade Recording
- Trades recorded during loop (not retrospectively)
- Each trade has: entry_time, entry_price, exit_time, exit_price, pnl
- Partial fills handled gracefully

### 3. Metrics Calculation
- Sharpe ratio: annual_return / volatility
- Max drawdown: peak-to-trough analysis
- Win rate: profitable_trades / total_trades
- Profit factor: gross_profit / gross_loss

### 4. Strategy Loading (Resolver Pattern)
- Dynamically loads strategy classes
- Validates required methods (generate_signal)
- Handles parameter passing
- Error handling for missing strategies

## For TAR Implementation

### Window Splitter Pattern
Freqtrade doesn't do walk-forward natively, but we can:
1. Subclass their backtest loop
2. Split data into train/test windows
3. Optimize on train, test on test (blind)
4. Stitch results together

### Metrics Reuse
- Copy their metrics calculation functions
- Use same Sharpe/DD/WR/PF definitions
- Ensures compatibility with industry standards

### Trade Recording
- Use similar trade object structure
- Record during loop (not after)
- Enables real-time monitoring

## Code Pattern to Adapt

```python
class BacktestEngine:
    def run(self, data, strategy, parameters):
        """Main backtest loop - Freqtrade pattern"""
        
        equity = initial_capital
        positions = {}
        trades = []
        
        for i, candle in enumerate(data):
            # Generate signal
            signal = strategy.generate_signal(data[:i+1], parameters)
            
            # Check position
            if signal == 1 and positions.get('long') is None:
                # BUY
                entry_price = candle['close']
                positions['long'] = {'entry_price': entry_price, 'entry_i': i}
            
            elif signal == -1 and positions.get('long') is not None:
                # SELL (close long)
                exit_price = candle['close']
                pnl = (exit_price - positions['long']['entry_price']) * size
                equity += pnl
                trades.append({...})
                positions['long'] = None
        
        # Calculate metrics
        metrics = self.calculate_metrics(trades, equity)
        return metrics
```

## Integration Points for TAR

1. **Window Splitter:** Wrap their backtest loop
2. **Metrics:** Use their calculation functions
3. **Trade Recording:** Follow their structure
4. **Parameter Passing:** Use their resolver pattern

## Warnings/Pitfalls

❌ Don't: Try to understand entire Freqtrade codebase (too large)  
✅ Do: Extract and adapt the backtest loop pattern  
❌ Don't: Copy code directly (licensing, context-specific)  
✅ Do: Learn the pattern and rewrite for TAR  

---

**Time to learn this pattern:** 30 minutes  
**Time to adapt for TAR:** 2-3 hours


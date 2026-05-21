# Backtrader: Walk-Forward Validation Patterns

## Key Files Extracted
- `cerebro.py` — Main engine with walk-forward support
- `walkforward.py` — Rolling window implementation
- `optimizer.py` — Parameter optimization across windows

## Walk-Forward Pattern (From walkforward.py)

```
train_period_length = 12 months (252 trading days)
test_period_length = 3 months (63 trading days)
step_forward = 3 months

window_num = 1
WHILE data_index < total_data_length:
  
  train_start = window_num * step_forward
  train_end = train_start + train_period_length
  test_start = train_end
  test_end = test_start + test_period_length
  
  IF test_end > total_data_length:
    BREAK
  
  # Optimize on training data
  train_data = data[train_start:train_end]
  optimal_params = optimize(train_data)
  
  # Test on blind data
  test_data = data[test_start:test_end]
  test_result = backtest(test_data, optimal_params)
  
  # Store result
  results.append({
    window: window_num,
    optimal_params: optimal_params,
    train_result: {...},
    test_result: {...}
  })
  
  window_num += 1
```

## Key Learnings

### 1. Rolling Window Logic
- Critical: train and test periods DO NOT OVERLAP
- Train period: learn parameters
- Test period: verify with unseen data
- Rolling forward prevents lookahead bias

### 2. Parameter Stability Indicator
- If optimal_params change drastically across windows → OVERFITTING
- If optimal_params stable across windows → GENERALIZABLE
- Stability is more important than raw performance

### 3. Out-of-Sample Equity Curve
- Stitch test_result equity curves together
- Combined OOS equity curve = TRUE performance
- In-sample results are NOT predictive

### 4. Degradation Analysis
- Compare: train_sharpe vs test_sharpe
- Degradation = (1 - test_sharpe/train_sharpe) * 100
- Expect 5-15% degradation (normal)
- >25% degradation = RED FLAG (overfitting)

## For TAR Implementation

### Window Generator
```python
class RollingWindowSplitter:
    def generate_windows(self, data, train_months=12, test_months=3):
        train_bars = train_months * 21  # trading days
        test_bars = test_months * 21
        
        idx = 0
        while idx + train_bars + test_bars <= len(data):
            train = data.iloc[idx:idx+train_bars]
            test = data.iloc[idx+train_bars:idx+train_bars+test_bars]
            
            yield train, test
            
            idx += test_bars  # Move forward by test period
```

### Blind Testing
```python
class BlindOOSTester:
    def test(self, test_data, optimal_params):
        """Test with FIXED parameters (no optimization)"""
        
        # CRITICAL: Do NOT optimize on test_data
        # CRITICAL: Do NOT see test_data during optimization
        
        result = self.backtest_engine.run(
            data=test_data,
            strategy=self.strategy,
            parameters=optimal_params,
            optimize=False  # MUST BE FALSE
        )
        
        return result
```

## Integration Points for TAR

1. **Window Splitter:** Exact algorithm from walkforward.py
2. **Blind Testing:** Prevent optimization on test data
3. **Parameter Tracking:** Monitor changes across windows
4. **Equity Stitching:** Combine OOS curves
5. **Degradation Analysis:** Flag overfitted strategies

## Warnings/Pitfalls

❌ Don't: Optimize on test data (defeats purpose)  
✅ Do: Lock parameters after training, test blindly  
❌ Don't: Use in-sample results as validation  
✅ Do: Use blind OOS results only  
❌ Don't: Ignore parameter instability  
✅ Do: Kill strategies with unstable parameters  

---

**Time to learn this pattern:** 45 minutes  
**Time to implement for TAR:** 4-6 hours  
**Payoff:** Eliminates curve fitting completely


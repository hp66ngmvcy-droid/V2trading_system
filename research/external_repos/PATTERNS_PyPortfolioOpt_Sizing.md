# PyPortfolioOpt: Position Sizing & Risk Allocation

## Key Concept: Sharpe-Optimized Position Sizing

```
Goal: Maximize Sharpe ratio subject to constraints

Input:
- Expected returns (from backtest)
- Covariance matrix (correlations)
- Constraints (min/max per asset)

Output:
- Optimal weights for each asset
- Expected portfolio return
- Expected portfolio volatility
- Portfolio Sharpe ratio
```

## Position Sizing Algorithm

```python
def calculate_position_sizes(strategies, allocation_budget=100000):
    """
    Input: List of validated strategies with metrics
    Output: Position sizes for each strategy
    """
    
    # Step 1: Get expected returns & volatility from backtests
    returns = [s.annual_return for s in strategies]
    volatilities = [s.annual_volatility for s in strategies]
    correlations = calculate_correlations(strategies)
    
    # Step 2: Optimize weights to maximize Sharpe
    weights = optimize_sharpe(
        returns=returns,
        volatilities=volatilities,
        correlation_matrix=correlations,
        constraints={'min_weight': 0.05, 'max_weight': 0.5}
    )
    
    # Step 3: Calculate position sizes
    position_sizes = weights * allocation_budget
    
    return position_sizes
```

## Risk Models

### 1. Sample Covariance
- Simple but unstable with small samples
- Good for large, liquid datasets

### 2. Ledoit-Wolf Shrinkage
- Regularizes covariance matrix
- Better with small samples
- Reduces estimation error

### 3. Exponential Decay
- Recent data weighted more
- Good for time-varying correlations
- Better for market regime changes

## For TAR Implementation

### Simple Version (Phase 1)
```python
# Equal weight all validated strategies
position_size = allocation_budget / num_strategies

# All strategies get same size
for strategy in validated_strategies:
    strategy.position_size = position_size
```

### Intermediate Version (Phase 2)
```python
# Weight by Sharpe ratio
sharpe_scores = [s.sharpe for s in strategies]
total_sharpe = sum(sharpe_scores)
weights = [s / total_sharpe for s in sharpe_scores]

for strategy, weight in zip(strategies, weights):
    strategy.position_size = weight * allocation_budget
```

### Advanced Version (Phase 3+)
```python
# Optimize for portfolio Sharpe ratio
# Consider correlations, volatilities
# Subject to constraints
```

## Key Learnings

1. **Diversification Effect:** Multiple strategies reduce volatility
2. **Correlation Matters:** Uncorrelated strategies are most valuable
3. **Optimization Constraints:** Prevent concentration risk
4. **Rebalancing:** Periodic weight adjustment (monthly/quarterly)

---

**Relevance for TAR:** Position sizing strategy  
**Time to learn:** 20 minutes  
**Implementation:** Medium (after Phase 2)


# TensorTrade: ML-Based Strategy Generation

## Reinforcement Learning for Trading

```python
# Agent learns to trade through rewards

class RLTradingAgent:
    
    def step(self, market_state):
        """
        Input: Market state (prices, volumes, indicators)
        Output: Action (BUY, HOLD, SELL)
        Reward: P&L from the action
        """
        
        # Agent learns to maximize cumulative reward
        # Through trial and error
        # Over thousands of episodes
        pass
```

## Reward Functions

```python
def calculate_reward(trade_result, sharpe, drawdown):
    """
    Reward = Profit + Sharpe Bonus - Drawdown Penalty
    """
    profit_reward = trade_result.pnl
    sharpe_bonus = sharpe * 100  # Reward consistent returns
    dd_penalty = -drawdown * 1000  # Penalize large losses
    
    return profit_reward + sharpe_bonus + dd_penalty
```

## For TAR Phase 3+

### Not Recommended for Phase 1-2
- Too complex
- Requires thousands of episodes
- Overfitting risk high
- Hard to interpret

### Potentially Useful for Phase 3+
- Strategy variant generation
- Parameter optimization
- Regime-adaptive strategies

---

**Relevance:** ML variants (Phase 3+, optional)  
**Time to learn:** 30 minutes  
**Implementation:** Phase 3+, only if simple strategies plateau


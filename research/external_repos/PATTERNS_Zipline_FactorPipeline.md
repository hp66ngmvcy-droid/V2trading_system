# Zipline: Factor Pipeline Architecture

## Factor Types

```python
class FactorPipeline:
    
    technical_factors = [
        'SMA_50',      # 50-day moving average
        'SMA_200',     # 200-day moving average
        'RSI_14',      # 14-period RSI
        'MACD',        # Moving Average Convergence Divergence
        'ATR_14',      # 14-period Average True Range
        'BBANDS',      # Bollinger Bands
    ]
    
    fundamental_factors = [
        'price_to_earnings',
        'price_to_book',
        'dividend_yield',
    ]
    
    custom_factors = [
        'volume_weighted_price',
        'opening_range_breakout',
        'mean_reversion_zscore',
    ]
```

## For TAR Implementation

```python
# Phase 1: Simple factors
factors = {
    'ema_12': lambda data: data['close'].ewm(span=12).mean(),
    'ema_26': lambda data: data['close'].ewm(span=26).mean(),
    'atr_14': lambda data: calculate_atr(data, 14),
}

# Phase 2: Add more
factors.update({
    'volume_sma_20': lambda data: data['volume'].rolling(20).mean(),
    'price_zscore': lambda data: (data['close'] - data['close'].rolling(20).mean()) / data['close'].rolling(20).std(),
})

# Use in strategy
def generate_signal(self, data):
    factors = self.calculate_factors(data)
    ema_diff = factors['ema_12'] - factors['ema_26']
    
    if ema_diff > 0:
        return 1  # BUY
    else:
        return -1  # SELL
```

---

**Relevance:** Feature/factor design  
**Time to learn:** 25 minutes  
**Implementation:** Phase 2+


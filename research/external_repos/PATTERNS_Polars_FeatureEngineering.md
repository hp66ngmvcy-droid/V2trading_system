# Polars: Fast Feature Engineering

## Speed Advantage

```
Polars is 5-10x faster than Pandas for:
- Large dataset operations
- Complex aggregations
- Time-series calculations
- Rolling window operations
```

## For TAR Features

```python
import polars as pl

# Load data with Polars
data = pl.read_parquet('data/XAUUSD_M15.parquet')

# Calculate moving averages (fast)
data = data.with_columns([
    pl.col('close').rolling_mean(12).alias('ema_12'),
    pl.col('close').rolling_mean(26).alias('ema_26')
])

# Calculate features
data = data.with_columns([
    (pl.col('ema_12') - pl.col('ema_26')).alias('ema_diff'),
    pl.col('volume').rolling_sum(20).alias('volume_sum_20')
])

# Convert to Pandas for backtest
backtest_data = data.to_pandas()
```

---

**Relevance:** Feature engineering speed  
**Time to learn:** 20 minutes  
**Implementation:** Phase 2+


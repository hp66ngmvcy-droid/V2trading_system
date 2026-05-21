# DuckDB: Analytical Data Efficiency

## Key Advantage Over Pandas

| Metric | Pandas | DuckDB |
|--------|--------|--------|
| Memory Usage | High | Low (columnar) |
| Query Speed | Slow (loops) | Fast (vectorized) |
| Large Datasets | Struggles | Handles easily |
| Time-Series | Limited | Optimized |

## When to Use DuckDB

✅ Use DuckDB for:
- Loading 500K+ tick data
- Querying subsets (e.g., "all EURUSD bars in May")
- Aggregating across strategies
- Time-series analysis

❌ Use Pandas for:
- Small datasets (<100K rows)
- Feature engineering
- One-off analysis
- Compatibility with sklearn

## Integration Pattern for TAR

```python
# Load tick data with DuckDB
ticks = duckdb.query("""
  SELECT * FROM 'data/XAUUSD_M15.parquet'
  WHERE timestamp BETWEEN '2023-01-01' AND '2024-01-01'
""").to_df()

# Convert to Pandas for backtest
backtest_data = ticks.to_pandas()
```

---

**Relevance:** Data loading optimization  
**Time to learn:** 15 minutes  
**Implementation:** After Phase 2


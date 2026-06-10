# Lean (QuantConnect): Multi-Asset Architecture

## Key Concepts from Lean

### 1. Asset Model
- Each asset: symbol, exchange, type (equity, forex, crypto)
- Pricing: bid/ask for each asset independently
- Portfolio: tracks positions across multiple assets

### 2. Portfolio Management
```
Portfolio:
├── Cash Account
│   └── Base currency (USD, EUR, etc.)
├── Positions
│   ├── Asset 1: size, entry_price, current_price, pnl
│   ├── Asset 2: size, entry_price, current_price, pnl
│   └── Asset N: ...
├── Leverage: (total_position_value / cash) × 100%
└── Correlation: track correlations between assets
```

### 3. Risk Management
- Max position size per asset
- Max total leverage (e.g., 2x, 3x)
- Max correlation exposure (don't hold 2 correlated assets)
- Sector exposure limits
- Daily loss limits

### 4. Order Execution
- Order types: market, limit, stop
- Broker simulation: realistic fills
- Slippage modeling: bid-ask + market impact
- Commission handling: per-order or per-share

### 5. Data Synchronization
- All data feeds run at same timestamp
- No lookahead bias across assets
- Time alignment critical for correlation calculations

## For TAR Multi-Asset Expansion (Future)

### Phase 1 (Current)
- Single asset: XAUUSD
- Single strategy: EMA(12,26)
- Simple portfolio model

### Phase 2
- Multiple forex pairs: EURUSD, GBPUSD, USDJPY, etc.
- Multiple strategies per asset
- Correlation awareness

### Phase 3+
- Risk aggregation across assets
- Portfolio-level leverage limits
- Cross-asset optimization

## Key Lessons

1. **Asset Abstraction:** Treat each asset uniformly
2. **Portfolio State:** Track all positions in single data structure
3. **Risk Aggregation:** Calculate total risk across assets
4. **Time Synchronization:** All data aligned to same timestamp

## Warnings

❌ Don't: Mix timestamps from different assets  
✅ Do: Synchronize all data to same times  
❌ Don't: Ignore correlation between assets  
✅ Do: Monitor cross-asset correlation  

---

**Relevance for TAR:** Important for Phase 3+ (multi-asset)  
**Time to learn:** 30 minutes


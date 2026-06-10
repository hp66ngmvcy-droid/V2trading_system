# Microsoft Agent Framework: Multi-Agent Coordination

## Key Concept: Agent Communication

```
Agent 1 (Backtest Agent)
  → Message: "Strategy X passed Phase 2"
  ↓
Agent 2 (Risk Agent)
  → Message: "Risk check passed"
  ↓
Agent 3 (Decision Agent)
  → Message: "Deploy to live trading"
```

## For TAR Phase 3+

### Example: Strategy Selection Agent System

```
BacktestAgent
├─ Runs backtests
├─ Outputs: metrics, logs
└─ Publishes: "Strategy_X: Sharpe=1.66"

StrategyAgent
├─ Listens for backtest results
├─ Evaluates: Sharpe, stability, degradation
└─ Publishes: "Strategy_X: VERDICT=KEEP"

RiskAgent
├─ Listens for KEEP verdicts
├─ Calculates: position sizes, correlations
└─ Publishes: "Strategy_X: Position=10000"

DeploymentAgent
├─ Listens for positions
├─ Validates: all checks passed
└─ Actions: Deploy to live (or paper)
```

---

**Relevance:** Agentic strategy management (Phase 3+)  
**Time to learn:** 30 minutes  
**Implementation:** Phase 3+


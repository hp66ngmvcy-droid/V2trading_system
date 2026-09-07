---
id: IDEA-EXT-REPO-001
type: idea
status: LOGGED
priority: MED
source: "Ideas to add/TAR_EXTERNAL_REPO_IMPORT_STRATEGY_REVIEW.md"
logged: 2026-09-07
---

# TAR External Repo Import Strategy

## Summary

Staged integration of 8 reference repositories into the V2 TAR system. Decision matrix reviewed and approved May 2026.

## Integration Decisions

| Repo | Decision | Rationale |
|------|----------|-----------|
| Freqtrade | ADOPT — strategy loader pattern only | Robust backtesting loop; extract, do not import wholesale |
| Lean (QuantConnect) | REFERENCE — event model only | Too heavy to run locally; study architecture |
| Agent Framework (custom) | BUILD — adapt agent orchestration pattern | Closest fit for TAR multi-agent loop |
| PyPortfolioOpt | ADOPT — portfolio optimiser module | Lightweight; drop-in for position sizing experiments |
| DuckDB | ALREADY IN USE | Central DB layer already implemented |
| Polars | PARKED — blocked by CLAUDE.md policy | No Polars per V2 dependency rules |
| Backtrader | REFERENCE — feed abstraction pattern | Overkill for current scope; extract feed interface idea |
| Zipline | SKIP | Maintenance burden; superseded by Lean for reference |

## Staged Build Order (5 weeks)

1. **Week 1** — Extract strategy loader pattern from Freqtrade; adapt to TAR signal format
2. **Week 2** — Integrate PyPortfolioOpt for position sizing; wire into paper-mode runner
3. **Week 3** — Build agent orchestration scaffold from Agent Framework pattern
4. **Week 4** — Backtrader feed abstraction study → define clean feed interface for TAR
5. **Week 5** — Integration test, gate checks, documentation

## Constraints

- Polars blocked: CLAUDE.md `Keep dependencies light. No Docker, Ray, Polars.`
- Paper-mode only throughout. No live execution.
- Each stage gated: minimum trade-count + robustness checks before next stage.

## Next Action

Owner reviews Week 1 scope. Assign to Codex when ready to execute.

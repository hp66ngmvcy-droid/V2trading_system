# TAR GitHub Repo Import System

## Objective

Review external repositories safely before using them in TAR.

Do not blindly copy code.

---

## Top Reference Repos

```text
Freqtrade
QuantConnect Lean
Microsoft Agent Framework
PyPortfolioOpt
DuckDB Python
Polars
Backtrader
Zipline
ATLAS-GIC
```

---

## Import Decision Types

```text
IGNORE
STUDY
REBUILD
DIRECT DEPENDENCY
ARCHIVE
```

---

## Repo Review Folder

```text
src/tar_system/github_review/
├── __init__.py
├── repo_scanner.py
├── repo_scorecard.py
├── license_checker.py
├── security_checker.py
├── integration_mapper.py
└── report_writer.py
```

---

## Integration Matrix

| Repo | Use | TAR Target | Import Type | Risk | Verdict |
|---|---|---|---|---|---|
| Freqtrade | Strategy/backtest patterns | backtest, strategies, cli | REBUILD | live trading code | STUDY |
| Lean | Portfolio/order lifecycle | portfolio, execution, risk | REBUILD | large C# system | STUDY |
| Agent Framework | Agent routing | core, agents | TEST | complexity | REVIEW |
| PyPortfolioOpt | Risk allocation | risk, portfolio | DIRECT DEPENDENCY POSSIBLE | misuse as auto-trader | TEST |
| DuckDB | local database | data, memory, audit | DIRECT DEPENDENCY | low | INTEGRATE |
| Polars | fast dataframes | data, features | DIRECT DEPENDENCY | low | INTEGRATE |
| Backtrader | walk-forward patterns | validation | REBUILD | older architecture | STUDY |
| Zipline | factor pipeline | features | REBUILD | legacy dependencies | STUDY |
| ATLAS-GIC | meta-agent philosophy | agents, scoring, review | STUDY | incomplete public code | STUDY |

---

## Import Rules

1. No live trading code
2. No broker credentials
3. No exchange API execution
4. No copied secrets handling
5. No licence-risk files without approval
6. Prefer interface patterns over copied implementation
7. Every imported idea must map to:
   - TAR module
   - TAR agent
   - TAR hook
   - audit reason code
8. Default decision is STUDY, not IMPORT

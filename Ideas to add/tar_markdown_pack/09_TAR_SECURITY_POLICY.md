# TAR Security Policy

## Core Rule

The system is paper-only.

No real trading execution is allowed.

---

## Forbidden at This Stage

- real broker execution
- live order placement
- storing broker credentials
- committing `.env`
- running unreviewed external code
- dashboard live execution buttons
- automatic strategy promotion
- bypassing risk gates
- deleting files automatically
- moving files automatically without approval

---

## Required

- `.env` ignored
- `.env.example` placeholders only
- append-only audit logs
- reason codes
- paper mode check
- external repo review
- human approval for promotions
- dashboard security status

---

## Git Ignore Essentials

```text
venv/
.env
__pycache__/
*.pyc
.DS_Store
*.log
logs/
data/raw/
data/validated/
data/features/
data/results/
*.db
*.sqlite
*.duckdb
reports/
exports/
*.key
*.pem
external_repos/
```

---

## Security Tests

Add tests to prove:

- live trading is blocked
- `.env` is ignored
- external repo code is not imported automatically
- risk gates can block trades
- audit events are written

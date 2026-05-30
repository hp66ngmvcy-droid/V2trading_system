# Local Infrastructure Repo Review

Date: 2026-05-23

## Verdict

Keep the system local-first and deterministic at construction time.

The strongest next layer is not a large agent framework. It is a staged local check pipeline:

1. Syntax/import check.
2. Fast tests.
3. OpenGrep scan-only static analysis.
4. Review packet refresh.
5. Optional full test suite.

AI reviewers can read the packet later, but they should not be required for construction-time safety.

## Already Built In

- OpenGrep scan-only audit: `run-local-construction-audit`
- Review packet ingestion: `runtime/static_analysis/opengrep.json` -> `runtime/ai_review_packet.md`
- Local wrapper: `scripts/local_construction_audit.sh`
- Rule-based multi-agent strategy scorer: `src/tar_system/scoring/multi_agent_scorer.py`
- Audit logs and review logs: `logs/audit/audit.jsonl`, `logs/review_log.jsonl`
- DuckDB-backed local queue plus JSONL mirror

## Recommended Next Adoptions

### 1. pytest-xdist

Use for parallel test speed. Initial trial passed with isolated temporary directories and DuckDB state.

Candidate command:

```bash
PYTHONPATH=src venv/bin/python -m pytest -n auto
```

Status:

- Trial passed: `281 passed in 13.30s`.
- Keep watching for order-dependent failures as the suite grows.

### 2. Ruff

Use as a very fast local lint/import/style gate before OpenGrep.

Candidate command:

```bash
ruff check src tests
```

Status:

- Started with a narrow rule set: `F821` undefined names.
- First run found a real broken helper in `src/tar_system/cli_walk_forward.py`.
- Avoid a repo-wide formatting churn commit until source/runtime/generated files are cleanly separated.

### 3. Pandera

Use for dataframe boundary checks where trading systems most often get quietly hurt:

- raw OHLCV import
- validated OHLCV
- feature frames
- metric frames
- walk-forward split outputs

Adoption gate:

- Start with raw/validated OHLCV only.
- Keep existing validator behavior authoritative until tests prove parity.

## Trading / Finance Repos To Learn From

### vectorbt

Best use: fast vectorized research comparator.

Why useful:

- Fast parameter sweeps.
- Good for exploratory research and candidate discovery.

Why not core yet:

- Vectorized assumptions can diverge from event-driven fills, costs, and execution order.
- Use as a second opinion, not a replacement for the current paper pipeline.

### NautilusTrader

Best use: reference architecture for event-driven trading engines.

Why useful:

- Strong ideas around clocks, fills, portfolio accounting, and parity between backtest and live execution.

Why not core yet:

- Heavy integration surface.
- This project is intentionally paper-only right now.

### Microsoft Qlib

Best use: research reference for ML-oriented quant pipelines and point-in-time data.

Why useful:

- Factor research patterns.
- Model evaluation and experiment structure.
- Look-ahead-bias controls.

Why not core yet:

- Large platform with assumptions that may not match this local TAR workflow.

### QuantStats

Best use: reporting inspiration for strategy analytics.

Why useful:

- Portfolio and returns tear sheets.
- Sharpe/drawdown/return summaries.

Why not core yet:

- Current reports already cover the key safety gates; add only if reporting gaps appear.

## Multi-Agent / Review Frameworks

### LangGraph

Best future use: explicit state machine for AI-assisted review workflows.

Good fit if:

- You need persistent reviewer/critic/referee state.
- You want human-in-the-loop checkpoints.
- You want replayable agent paths.

Do not put it in the deterministic gate path.

### CrewAI

Best future use: human-triggered parallel AI reviewer roles.

Potential roles:

- security reviewer
- trading-risk reviewer
- data-quality reviewer
- performance reviewer

Do not auto-merge, auto-fix, or auto-promote from CrewAI output.

### AutoGen

Avoid for new infrastructure. It is in maintenance mode. Do not anchor new system architecture to it.

## System Communication

Current local communication is good enough:

- DuckDB operational queue
- JSONL audit trail
- review packet as portable state

Next improvement should be a local event bus only if queue/review workflows become hard to inspect. Prefer extending the existing DuckDB/JSONL model before adding Redis, Celery, Ray, or a workflow platform.

## Build Order

1. Keep OpenGrep trial active through 2026-05-28.
2. Add pytest-xdist only if full-suite time becomes painful.
3. Add Ruff with narrow rules.
4. Add Pandera at the raw OHLCV validation boundary.
5. Sandbox vectorbt as a research comparator.
6. Study NautilusTrader for execution/fill-model architecture only.
7. Consider LangGraph/CrewAI only for optional AI review, never for core local gates.

## Current Command

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-local-construction-audit --fail-on-findings
```

Fast local checks:

```bash
scripts/local_fast_checks.sh
```

Current status:

```text
OpenGrep findings: 0
Full pytest suite: passing
```

# V2 Ultra Caveman Review

Date: 2026-06-19

Scope: game-changing upgrades for V2 trading system speed, review quality, multi-agent workflow, linked strategy evidence, smoke backtests, and safer iteration.

## Caveman Verdict

The strongest upgrade is not a bigger agent framework. The strongest upgrade is a tiny, brutal feedback loop:

1. Measure whether a strategy has enough usable regime/data coverage.
2. Run a fast smoke backtest on one known symbol/timeframe.
3. Run one statistical sanity check.
4. Write one promotion packet.
5. Let a reviewer block anything weak before paper test.

This gives faster response, fewer false starts, and cleaner human approval.

## Top 10 Game Changers

### 1. Caveman Smoke Runner

Build one command that answers: "Is this candidate alive enough to spend more time on?"

Suggested command:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli caveman-smoke --strategy gold_v2 --symbol XAUUSD --timeframe M15
```

Minimum checks:

- Python compile of touched TAR modules.
- Queue health snapshot.
- Data presence and feature completeness.
- Regime UNKNOWN-rate audit.
- One tiny backtest or dry-run signal pass.
- DSR/statistical spot check if returns exist.
- Markdown + JSON report under `reports/caveman_smoke/`.

Why it matters: this becomes the fastest "yes/no/why" loop before long backtests.

### 2. Regime UNKNOWN-Rate Audit

The regime detector appears already improved in the current worktree with a core-feature fallback. Do not re-fix it blindly. Measure it.

Target:

- UNKNOWN below 20% on normal prepared strategy data.
- Report UNKNOWN by symbol, timeframe, and date window.
- Block promotion when regime coverage is too weak for a regime-aware strategy.

This is currently the highest leverage technical check because an apparently wired detector can still silently contribute almost no useful signal.

### 3. Linked Strategy Packet

Every strategy should have one linked evidence chain:

```text
idea -> assumptions -> data readiness -> baseline -> walk-forward -> DSR -> regime heatmap -> paper signal -> reviewer signoff
```

Store the packet next to the candidate or in `reports/strategy_packets/`.

This stops the system from producing isolated artifacts that look useful but cannot be trusted together.

### 4. Failure Clustering For The Queue

Current queue repair should not just rerun failures. First cluster failure reasons:

- missing data
- bad parameters
- strategy import/runtime error
- weak statistical result
- validation gate failure
- duplicate/low-novelty idea

Then run the smallest repair action per cluster. This is faster than treating every failed item as a separate mystery.

### 5. Reviewer-As-Gate, Not Reviewer-As-Chat

Use the reviewer as a hard gate with a checklist:

- Is the idea testable?
- Is the data sufficient?
- Did the smoke pass?
- Is DSR or equivalent sanity included?
- Is there a reason this should enter paper test?
- What exact command reproduces the result?

The reviewer should sign off artifacts, not just comment on them.

### 6. Local Multi-Agent Pattern

Use agent roles, not a broad autonomous framework inside V2:

- Planner: writes the paper-only test plan.
- Builder: edits code/scripts.
- Tester: runs smoke and focused checks.
- Critic: reviews diff and report.
- Manager: decides promote/block/defer.

Free/open-source frameworks worth learning from:

- AutoGen: strong pattern for conversable multi-agent workflows with tools and optional human input.
- AutoGen Studio: useful idea for declarative agent workflows and debugging views.
- OpenHands: useful pattern for sandboxed code agents and evaluation harnesses.
- CrewAI: useful role/task/process model.
- MetaGPT: useful SOP-style structure.
- AgentForge and Orchard: useful research patterns for planner/coder/tester/critic loops.

Recommendation: borrow the patterns. Do not install these into the V2 trading core yet.

### 7. Keep LangGraph/LangChain Out Of Core For Now

LangGraph-style state machines are attractive, but the dependency/security surface is not worth adding to the V2 core until the local smoke/reviewer workflow is already solid.

If used later, isolate it in an orchestration sidecar, pin versions, run a security review, and keep strategy/backtest code independent.

### 8. Faster Test Ladder

Use strict tiers so every change does not trigger a heavy run:

```text
T0 touched-file compile
T1 focused unit tests
T2 caveman-smoke
T3 local_fast_checks.sh
T4 full backtest/walk-forward
T5 paper-trade review gate
```

Current useful commands:

```bash
python3 -m py_compile src/tar_system/regime/detector.py src/tar_system/validation/bootstrap_ci.py
bash scripts/nightly_strategy_review.sh --dry-run
bash scripts/local_fast_checks.sh
```

### 9. Backtest Smoke Before Big Backtest

Add a tiny backtest profile:

- one symbol
- one timeframe
- short date window
- fixed seed where applicable
- no optimisation
- no parameter sweep
- report only

The goal is not profit proof. The goal is to catch wiring, data, regime, and validation failure in seconds.

### 10. Response Speed From Artifact Indexing

Create a lightweight artifact index:

```text
artifact id
strategy
symbol/timeframe
source idea
commands run
status
blocked reason
report paths
latest reviewer signoff
```

This makes future agents answer quickly because they do not have to rediscover the last known state from scattered files.

## Manager Signoff

Approved now:

- Add caveman smoke runner as report-only/test-only.
- Add regime UNKNOWN-rate report.
- Add linked strategy packet template.
- Add queue failure clustering report.
- Keep nightly script dry-run and queue-health checks.

Blocked without approval:

- Live trading.
- MT5 compile/copy/promotion/deployment.
- New external dependency installs.
- Docker/Ray/Polars.
- Broad autonomous agents writing inside V2.

Defer:

- Full AutoGen/CrewAI/LangGraph integration.
- VectorBT or PyBroker dependency.
- New ML regime packages until current detector coverage is measured.

## Next Build Slice

Build `caveman-smoke` as the next safe slice:

1. Add CLI command or script.
2. Generate Markdown and JSON reports.
3. Run only compile, queue-health, feature coverage, UNKNOWN-rate, and optional tiny dry-run backtest.
4. Do not mutate strategy state.
5. Do not promote anything automatically.

Definition of done:

- One command runs locally.
- One report explains pass/fail/block reason.
- Existing nightly review can link to it later.
- Tests cover the report builder or parser.

## Source Notes

Recent open-source agent research supports borrowing multi-agent patterns, especially AutoGen-style conversable agents, AutoGen Studio workflow specs, OpenHands sandbox/evaluation patterns, and planner/coder/tester/critic research loops. These are useful as architecture references, but V2 should keep its trading path small, local, paper-only, and review-gated.

Reference links checked:

- AutoGen: https://arxiv.org/abs/2308.08155
- AutoGen Studio: https://arxiv.org/abs/2408.15247
- OpenHands: https://arxiv.org/abs/2407.16741
- CrewAI: https://github.com/crewAIInc/crewAI
- MetaGPT: https://github.com/FoundationAgents/MetaGPT
- LangChain/LangGraph security caution: https://www.techradar.com/pro/security/each-vulnerability-exposes-a-different-class-of-enterprise-data-langchain-framework-hit-by-several-worrying-security-issues-heres-what-we-know

# Daily Idea Review Operating Model

Date: 2026-05-24

## Purpose

The idea orchestrator should run as a daily review system that keeps generating
and collecting ideas, but only promotes safe, useful, testable work into the
backtester or implementation queue.

The goal is not to work on every idea. The goal is to separate:

- useful now
- useful later
- partial component worth testing
- duplicate
- unsafe
- unclear
- rejected

## Recommended Daily Schedule

```text
00:00-03:30  collect ideas and online research references
04:00        generate daily idea review
04:15        classify and score new ideas
04:30        run internal safety/security/code/agent checks
05:00        promote only approved ideas into work queues
operator    reviews promoted ideas before implementation/backtesting
```

This should be local-first and paper-only. Nothing in the daily loop should
place trades, call broker APIs, or edit live strategy code automatically.

## Review Stages

### 1. Intake

Inputs:

- user ideas
- online research sources
- backtest failures
- audit findings
- code review findings
- UI/UX improvement notes
- strategy comparison results

Outputs:

- `ideas/inbox/`
- `ideas/research_queue/`

### 2. Internal Checks

Each idea should pass a checklist before becoming work:

| Check | Question | Output |
| --- | --- | --- |
| Security check | Could this expose secrets, credentials, broker access, unsafe network access, or live-trading paths? | allow/block/review |
| Code check | Does the repo already have the needed module, test surface, and data path? | code paths and risks |
| Agent check | Can an agent understand the task and execute it without guessing? | missing context list |
| Data check | Is the required local data available and clean? | data readiness |
| Backtest check | Can the idea be converted into a deterministic test packet? | candidate/reject |
| Duplicate check | Has this idea already been tested or rejected? | duplicate/new |
| Value check | Is there a plausible benefit worth spending time on? | priority score |

### 3. Split The Idea

Many ideas should not be accepted or rejected as a whole. Split them into:

- strategy hypothesis
- indicator component
- data cleaning improvement
- reporting improvement
- UI workflow improvement
- risk/scoring improvement
- documentation/task improvement

This lets the system keep the useful part even when the whole idea is too big
or too risky.

### 4. Promotion Queues

Recommended queues:

```text
ideas/research_queue/          online/user sources waiting for extraction
ideas/backtest_candidates/     safe strategy hypotheses ready for tests
ideas/code_candidates/         code improvements ready for implementation
ideas/ui_candidates/           UI/UX improvements ready for design/testing
ideas/security_review/         anything needing extra caution
ideas/archive/                 old ideas kept for search/history
```

### 5. Backtester Packet

Backtester candidates should be small and testable:

```yaml
idea_id: 20260524-example
status: backtest_candidate
source: user | online | audit | backtest_failure
strategy_family: trend | mean_reversion | breakout | session | volatility
symbols:
  - XAUUSD
timeframes:
  - M15
hypothesis: >
  What should be true if this idea has value.
test_plan:
  - validate data
  - run baseline backtest
  - compare against current strategy
  - run walk-forward
  - score drawdown, trade count, profit factor, and stability
reject_if:
  - fewer than minimum trades
  - unstable out-of-sample result
  - excessive drawdown
  - unclear rule definition
```

## Better Way To Use It

The best version is not a single agent making ideas forever. It is a small
committee:

1. Scout agent
   - finds ideas and sources
   - writes hypothesis notes

2. Safety agent
   - blocks live-trading, secret, broker, or unsafe dependency risk

3. Code agent
   - checks whether the repo can test the idea cleanly
   - identifies touched files and tests

4. Backtest agent
   - converts safe hypotheses into test packets
   - runs only approved local tests

5. Reviewer agent
   - summarizes results for the operator
   - recommends approve/reject/split/retest

6. Librarian agent
   - files notes, sources, outputs, and decisions in the right folders

The operator remains the final approval gate.

## Daily Output

Each day should produce:

- one daily idea review
- list of new ideas found
- list of blocked ideas and reasons
- list of split-out useful components
- list of backtest candidates
- list of code candidates
- list of questions for the operator

## Decision

Continual idea generation is useful only if it is filtered. The system should
generate and collect ideas daily, but work only on ideas that pass safety,
clarity, data, code, and value checks.

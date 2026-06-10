# Continual Idea Engine Note - 2026-05-24

## Question

Stopping the idea orchestrator sounds wrong if the goal is continual idea
generation. Should the system keep making strategy ideas from online resources
for the backtester to review?

## Short Answer

Yes, but it should run as a gated idea engine, not as an automatic strategy
builder.

The orchestrator should continuously collect, classify, score, and queue ideas.
It should not automatically implement trading logic, run live actions, or treat
online claims as validated strategy evidence.

## Best Design

Use three separate loops:

1. Human idea loop
   - Captures ideas from the operator.
   - Uses `ideas/inbox`, `ideas/staging`, `ideas/approved`, and
     `ideas/implemented`.
   - Keeps the current human approval gate.

2. Online research scout loop
   - Pulls references from approved sources.
   - Converts each source into a hypothesis note.
   - Writes to a new queue such as `ideas/research_queue/`.
   - Never edits strategy code directly.

3. Backtester review loop
   - Converts approved hypotheses into small test plans.
   - Runs backtests only after the idea passes sanity checks.
   - Stores results in `data/results/`, `reports/`, and project notes.

## Online Sources To Use Carefully

- QuantConnect Strategy Library and research docs for structured strategy
  examples and backtesting patterns.
- arXiv quantitative finance papers for research hypotheses.
- SSRN quantitative finance papers for academic/preprint ideas.
- FRED economic data for macro/regime indicators, not direct trade signals.

The online scout should save source URL, date checked, summary, market/asset,
timeframe, assumptions, and risk warnings before anything reaches the
backtester.

## Proposed Idea States

```text
source_seen
  -> hypothesis_extracted
  -> duplicate_checked
  -> safety_checked
  -> backtest_candidate
  -> backtested
  -> review
  -> approved_for_strategy_work
  -> rejected_or_archived
```

## What The Backtester Should Receive

Each strategy idea should become a small test packet:

```yaml
idea_id: YYYYMMDD-source-slug
source_url: https://example.com/source
source_type: paper | tutorial | macro_data | user_note
asset_class: forex | crypto | gold | equities | multi_asset
symbol_candidates:
  - XAUUSD
  - EURUSD
timeframe_candidates:
  - M15
  - H1
hypothesis: >
  Plain-English explanation of what should be tested.
entry_logic_sketch: >
  High-level rule only. No auto-generated production strategy code.
exit_logic_sketch: >
  High-level rule only.
risk_notes:
  - Avoid lookahead bias.
  - Check transaction costs and spread assumptions.
  - Reject if trade count is too low.
required_checks:
  - data availability
  - train/test split
  - walk-forward check
  - drawdown gate
  - minimum trade count
status: backtest_candidate
```

## Guardrails

- No direct live trading.
- No broker API actions.
- No strategy promotion from one successful backtest.
- No online idea is trusted until tested locally.
- Reject ideas with unclear rules, unrealistic assumptions, or obvious
  overfitting risk.
- Every idea needs source attribution and a dated note.

## Implementation Plan

1. Add `ideas/research_queue/` and `ideas/backtest_candidates/`.
2. Add a `ResearchIdea` schema for online-sourced hypotheses.
3. Add a command such as:

```bash
python idea_orchestrator.py scout-sources --once
```

4. Add a command such as:

```bash
python idea_orchestrator.py promote-backtest-candidates --limit 5
```

5. Keep the approval gate: human-approved ideas move into backtester work.
6. Record all backtest outcomes in `reports/` and the project workspace.

## Decision

The idea orchestrator should become a continual idea engine. It should generate
and collect ideas continuously, but only promote them through controlled gates.
For trading, online resources should create backtester hypotheses, not live
strategies.

## Source Links Checked

- QuantConnect Research docs: https://www.quantconnect.com/docs/research/overview
- QuantConnect Strategy Library: https://www.quantconnect.com/docs/v2/writing-algorithms/strategy-library
- arXiv quantitative finance search/API context: https://arxiv.org/archive/q-fin
- SSRN quantitative finance papers: https://papers.ssrn.com/
- FRED API documentation: https://fred.stlouisfed.org/docs/api/fred/

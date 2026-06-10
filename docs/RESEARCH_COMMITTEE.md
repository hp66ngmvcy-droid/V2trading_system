# Paper-Only Research Committee

The research committee is an offline, rule-based analyst panel for reviewing saved V2 strategy results.

It does not scrape, fetch news, connect to a broker, place orders, or promote a strategy. It reads local metrics and optional manual notes, then writes a review packet to `runtime/`.

## Roles

- Fundamental Analyst: checks profit factor, expectancy, sample size and cost pressure.
- Sentiment Analyst: checks local/manual positioning context only.
- News Analyst: reviews manually supplied notes only.
- Technical Analyst: reads backtest, walk-forward and structural gate outputs.
- Bull Researcher: argues the strongest paper-only case for more testing.
- Bear Researcher: argues the strongest objection.
- Trader Synthesizer: combines both sides into a research recommendation.
- Risk Reviewer: applies hard gates and keeps the result paper-only.

## Run

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-research-committee \
  --strategy gold_v2 \
  --symbol GBPUSD \
  --timeframe M5
```

With manually supplied market notes:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-research-committee \
  --strategy gold_v2 \
  --symbol XAUUSD \
  --timeframe M15 \
  --notes-file research/manual_notes/XAUUSD_M15.md
```

## Outputs

- Markdown: `runtime/research_committee_<SYMBOL>_<TIMEFRAME>_<STRATEGY>.md`
- JSON: `runtime/research_committee_<SYMBOL>_<TIMEFRAME>_<STRATEGY>.json`
- Audit event: `logs/audit/audit.jsonl`

## Guardrails

- Paper-only research.
- No live execution recommendation.
- No broker API use.
- No automatic MT5 promotion.
- Human review is required before any external action.

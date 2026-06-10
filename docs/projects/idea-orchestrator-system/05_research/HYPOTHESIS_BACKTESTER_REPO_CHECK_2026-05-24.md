# Hypothesis Notes And Backtester Repo Check - 2026-05-24

## How Hypothesis Notes Work

Hypothesis notes are the bridge between raw ideas and the backtester. They are
not strategy code. They are structured review packets that let the system decide
whether an idea is worth testing.

## Proposed Flow

```text
online source or user idea
  -> hypothesis note
  -> duplicate check
  -> safety and data availability check
  -> backtest candidate
  -> local backtest
  -> walk-forward / robustness checks
  -> human review
  -> strategy work only if approved
```

## Hypothesis Note Format

```yaml
idea_id: 20260524-source-short-name
title: Short strategy hypothesis
source_url: https://example.com/source
source_type: paper | tutorial | repo | macro_data | user_note
source_checked_at: 2026-05-24
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
  High-level rule only.
exit_logic_sketch: >
  High-level rule only.
data_needed:
  - OHLCV
  - spread assumptions
  - session filter
risk_notes:
  - Avoid lookahead bias.
  - Reject if trade count is too low.
  - Check transaction costs.
required_checks:
  - duplicate hypothesis check
  - data availability check
  - backtest
  - walk-forward
  - drawdown gate
  - minimum trade count
status: hypothesis_extracted
```

## Where Files Should Go

- Raw online/user idea notes: `ideas/research_queue/`
- Approved backtest candidates: `ideas/backtest_candidates/`
- Backtest outputs: `data/results/`
- Human summaries: `reports/`
- Project-level design notes:
  `docs/projects/idea-orchestrator-system/05_research/`

## Highly Rated Repos Checked

Current GitHub stars were checked on 2026-05-24 through the GitHub API.

| Repo | Stars | How It Could Help | Recommendation |
| --- | ---: | --- | --- |
| `wilsonfreitas/awesome-quant` | 26,383 | Curated source list for quant libraries and papers | Use as research source map |
| `ranaroussi/yfinance` | 23,795 | Market data download for equities/ETFs and quick prototypes | Useful only if data source scope expands beyond local CSV |
| `mementum/backtrader` | 21,661 | Mature Python event-driven backtesting examples | Reference patterns; do not replace V2 backtester yet |
| `quantopian/zipline` | 19,801 | Historical Pythonic algorithmic trading library | Reference only; maintenance/runtime fit may be weak |
| `QuantConnect/Lean` | 19,097 | Full open-source algorithmic trading engine | Strong reference architecture; heavy to integrate |
| `AI4Finance-Foundation/FinRL` | 15,223 | Reinforcement learning trading research framework | Research reference; avoid adding complexity now |
| `kernc/backtesting.py` | 8,408 | Simple Python backtesting framework | Good comparison/reference for simple strategies |
| `polakowo/vectorbt` | 7,664 | Fast vectorized strategy testing | Good reference for batch hypothesis testing |
| `ranaroussi/quantstats` | 7,159 | Portfolio/backtest analytics reports | Potential reporting helper/reference |
| `bukosabino/ta` | 5,088 | Technical indicators with Pandas/NumPy | Potential indicator reference if local indicators need gaps filled |
| `lukasschwab/arxiv.py` | 1,510 | Python wrapper for arXiv API | Good candidate for online paper scout |

## Best Fit For V2 Right Now

Do not replace the current V2 backtester. It already has local data, scoring,
audit, walk-forward, and safety assumptions wired in.

Best near-term additions:

1. Use `awesome-quant` as a source discovery map.
2. Use arXiv API, possibly through `lukasschwab/arxiv.py`, for paper discovery.
3. Use QuantConnect/LEAN, Backtrader, Backtesting.py, and VectorBT as reference
   architectures and comparison baselines.
4. Consider `quantstats` only for reporting if current reports need richer
   portfolio analytics.
5. Consider `ta` only if local indicator coverage has real gaps.

## Guardrail

Highly starred does not mean safe to install. New dependencies should be added
only when they improve the V2 pipeline without breaking local-first,
paper-only, auditable operation.

## Source Links

- https://github.com/wilsonfreitas/awesome-quant
- https://github.com/ranaroussi/yfinance
- https://github.com/mementum/backtrader
- https://github.com/quantopian/zipline
- https://github.com/QuantConnect/Lean
- https://github.com/AI4Finance-Foundation/FinRL
- https://github.com/kernc/backtesting.py
- https://github.com/polakowo/vectorbt
- https://github.com/ranaroussi/quantstats
- https://github.com/bukosabino/ta
- https://github.com/lukasschwab/arxiv.py

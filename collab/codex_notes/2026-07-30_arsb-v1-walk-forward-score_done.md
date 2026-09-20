# Done: arsb_v1 Walk-Forward And Score Gate
Date: 2026-07-30
Task: [2026-07-05_arsb-v1-bug-fixed.md](../claude_notes/2026-07-05_arsb-v1-bug-fixed.md)

Interpreting as: follow the council plan by taking the next real action: run
the V2 `arsb_v1` paper-only walk-forward and scoring evidence gate, then report
the result without promoting anything.

## What Was Run

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-walk-forward --strategy arsb_v1 --symbol XAUUSD --timeframe M15
PYTHONPATH=src venv/bin/python -m tar_system.cli score-strategy --strategy arsb_v1 --symbol XAUUSD --timeframe M15
```

## Result

- Walk-forward output: `data/results/arsb_v1_XAUUSD_M15_walk_forward.json`
- Score: `82.45`
- Verdict: `REVIEW`
- Gate: `REVIEW`
- Failed gate class: `soft_gates`
- Gate reason: `parameter stability 0.00 < 0.70; bootstrap CI spans zero`

## Key Evidence

Walk-forward:

- Total trades: `180`
- Walk-forward profit factor: `0.3572`
- Walk-forward Sharpe: `2.1849`
- Parameter stability: `0.0`
- Bootstrap CI lower: `-0.0000057311`
- Bootstrap CI upper: `0.0014702244`
- Bootstrap CI spans zero: `true`
- Walk-forward verdict: `REVIEW`
- Walk-forward reason: `Walk-forward profit factor 0.36 is below 1.10.`

Score gate:

- Trade count: `41`
- In-sample/tuned profit factor: `2.0981`
- Win rate: `0.4878`
- Max drawdown: `0.004148`
- OOS Sharpe: `2.1849`
- Parameter stability: `0.0`

Reason codes:

- `WF_VERDICT_REVIEW`
- `WF_WEAK_PROFIT_FACTOR`
- `WF_UNSTABLE_PARAMETERS`
- `WF_BOOTSTRAP_CI_SPANS_ZERO`
- `SEARCH_PARAMETER_STABILITY_NOT_MET`
- `BOOTSTRAP_CI_SPANS_ZERO`

Multi-agent:

- Verdict: `KEEP`
- Confidence: `0.623`
- Dissent: `true`
- Robustness agent: `REVIEW`

## Decision

Capital state: REVIEW
Decision: do not promote `arsb_v1` on XAUUSD M15.
Evidence: the score remains high, but walk-forward PF is weak, parameters are
unstable, bootstrap CI spans zero, and robustness dissents.
Missing: stable parameter range and non-zero-spanning bootstrap evidence.
Risk: overfitting to a tuned slice while robustness evidence is weak.
Next action: park promotion and use Research Scout or targeted validation only
if a specific research question remains.
Do not do: do not compile, copy, promote, live trade, or increase confidence
from the headline score alone.

## Notes

The initial Arrow `sysctlbyname` warnings were local CPU-info permission noise
from the Python stack. They did not stop the paper-only commands.

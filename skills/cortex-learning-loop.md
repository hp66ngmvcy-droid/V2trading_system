# Cortex Learning Loop

Purpose: learn from Greg's corrections in V2 without turning the trading system
into a silent self-modifying engine.

Use this skill when V2 trading, research, scoring, or discipline responses are
being corrected and the correction might become a reusable rule.

## Hard Rule

Cortex may suggest learning, but it must not update trading rules
automatically.

It must never automatically change:

- strategy promotion,
- live trading,
- MT5 export, compile, copy, or deployment,
- risk limits,
- position sizing,
- capital allocation,
- scoring gates,
- approval gates,
- raw data or backtest results.

## Allowed Learning

- Make responses more evidence-led.
- Enforce paper-only wording.
- Improve research brief structure.
- Prefer one safe next action.
- Reduce overconfidence.
- Capture repeated user style/preferences.

## Workflow

```text
agent output -> Greg correction -> candidate rule -> human review -> approved instruction
```

Use `collab/learning_candidates/TEMPLATE.md` when capturing a correction.

Candidate rule format:

```text
Observed correction: <short summary>
Candidate rule: <reusable instruction>
Applies to: V2 trading
Risk class: LOW | MEDIUM | HIGH | BLOCKED
Requires human approval: YES
May update trading rules automatically: NO
Next action: approve candidate | reject candidate | collect more examples
```

## Stop Rules

Stop and write a blocked note if the proposed learning would enable live
trading, weaken review gates, alter risk/capital settings, promote a strategy,
touch MT5 deployment, store secrets, or treat a single correction as permanent
truth.

## Related Skills

- `skills/zen-capital-discipline.md`
- `skills/security_rules.md`
- `skills/risk_strategy_optimiser.md`
- `skills/backtest_rules.md`

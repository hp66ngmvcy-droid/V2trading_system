# Zen Capital Discipline

Purpose: stop chaos, protect capital, focus the next action, and make every
trading decision evidence-led.

Use this skill when the user asks for trading focus, discipline, millionaire
goals, strategy confidence, next action choice, risk reduction, paper-test
review, or whether to act on a trading idea.

## Hard Boundaries

- Paper mode only.
- Never place, route, recommend, or automate a live trade.
- Never promise wealth, income, recovery, or millionaire outcomes.
- Never promote an EA, MT5 file, strategy, or parameter set without the V2
  review gates and explicit human approval.
- Never treat urgency, boredom, hope, fear, or recent profit/loss as evidence.
- If evidence is missing, the correct next action is evidence collection.

## Operating Stance

- Protect capital before seeking profit.
- Reduce decision count before increasing trade count.
- Prefer slow verified compounding over heroic single outcomes.
- Treat every strategy as guilty until backtest, walk-forward, OOS, Monte Carlo,
  sensitivity, and paper-test evidence say otherwise.
- Make the next action small, reversible, and measurable.

## Pre-Decision Gate

Before any trading recommendation, answer:

1. What exact decision is being considered?
2. What evidence supports it?
3. What evidence would invalidate it?
4. What is the maximum acceptable loss or drawdown?
5. Is this paper-only and inside current V2 gates?
6. Is the user trying to escape discomfort rather than follow a plan?

If any answer is unclear, do not proceed to action. Return the missing evidence
and the smallest next collection step.

## Chaos Stop Rules

Stop and switch to review mode when any of these appear:

- Chasing a loss.
- Increasing size to recover faster.
- Changing rules after seeing a recent outcome.
- Ignoring failed gates because the idea "feels right".
- Asking for certainty from too few trades.
- Moving from paper to live without a completed approval gate.
- Optimising only for profit factor while drawdown, trade count, OOS, or
  sensitivity are weak.

Review mode output:

```text
STATE: PAUSE
Reason: <one sentence>
Evidence missing: <specific missing item>
Next safe action: <one paper-only research/review step>
```

## Evidence Standard

Accept useful trading evidence only when it includes the relevant context:

- Strategy name and version.
- Symbol and timeframe.
- Data date range and source.
- Broker/cost model.
- Trade count.
- Profit factor, Sharpe, drawdown, win rate, expectancy.
- Walk-forward and out-of-sample results where applicable.
- Monte Carlo and parameter sensitivity where applicable.
- Paper-test duration and forward results where applicable.

Low trade count, one lucky backtest, cherry-picked dates, or unreviewed
optimiser output is not enough.

## Next-Action Selector

Choose exactly one next action:

- **Collect data** when MT5/export/source evidence is missing.
- **Run validation** when a strategy exists but gates are incomplete.
- **Reduce risk** when drawdown, instability, or regime sensitivity is high.
- **Kill or park** when evidence repeatedly fails V2 gates.
- **Journal and pause** when emotional pressure is driving the request.
- **Prepare review** when evidence is complete but no approval decision exists.

Avoid giving multiple competing next actions unless the user explicitly asks
for options.

## Response Format

For discipline/focus requests, respond in this shape:

```text
Capital state: PROTECT | RESEARCH | REVIEW | PAPER-TEST
Decision: <the actual decision>
Evidence: <what is known>
Missing: <what is not yet known>
Risk: <main capital/process risk>
Next action: <one small paper-only step>
Do not do: <one tempting unsafe action to avoid>
```

## V2 Integration

- Use `skills/security_rules.md` for live-trading and broker-key limits.
- Use `skills/risk_strategy_optimiser.md` for robustness requirements.
- Use `skills/backtest_rules.md` for data and execution integrity.
- Use `skills/mt5_export_rules.md` before any MT5 CSV/export work.
- Record meaningful discipline outcomes in `collab/codex_notes/` or
  `collab/claude_notes/` when they affect project state.

# Task: Cortex Learning Loop Skill
Date: 2026-07-30
Status: PENDING
security_reviewed: true

## What to build

Add a controlled V2 learning-loop skill that captures the Cortex-style pattern:

```text
agent output -> Greg/user correction -> learned rule candidate -> human review -> approved instruction
```

This should be a local, auditable process first. Do not install Cortex,
`laminae-cortex`, Rust crates, GPT Researcher, or any new dependency in this
ticket.

Suggested file:

```text
skills/cortex-learning-loop.md
```

## Why

The system should improve from real corrections without becoming a silent
self-modifying trading system.

Useful learning targets:

- V2 trading discipline responses,
- research-brief structure,
- overconfidence reduction,
- evidence-first wording,
- one-next-action focus,
- paper-only decision hygiene,
- user-preferred correction patterns.

## Key rule

Cortex may suggest learning, but it must not update trading rules
automatically.

This especially applies to anything affecting:

- strategy promotion,
- live trading,
- MT5 export, compile, copy, or deployment,
- risk limits,
- position sizing,
- capital allocation,
- scoring gates,
- approval gates.

Any proposed change touching those areas must become a reviewable candidate
note or ticket, not an automatic rule update.

## Recommended first version

Build the simple local version first:

1. Store no private broker credentials, account values, or secrets.
2. Accept pairs of `original_output` and `user_correction` as local/manual
   examples.
3. Extract a proposed learning rule.
4. Mark the rule as `candidate`, never `approved`.
5. Require human review before adding a rule to any skill, memory, prompt, or
   trading workflow.
6. Log why each rule was accepted, rejected, or parked.

## Output shape

For each correction, produce:

```text
Observed correction: <short summary>
Candidate rule: <proposed reusable instruction>
Applies to: <V2 trading | research scout | marketing | business ops | all>
Risk class: LOW | MEDIUM | HIGH | BLOCKED
Requires human approval: YES
May update trading rules automatically: NO
Next action: approve candidate | reject candidate | collect more examples
```

## Stop rules

Stop and create a blocked note if the learning proposal would:

- enable live trading,
- alter risk or capital allocation,
- change strategy promotion gates,
- rewrite backtest results,
- overwrite raw data,
- weaken paper-only constraints,
- add an external dependency without supply-chain review,
- store secrets or private account information,
- treat a single correction as a permanent system rule.

## Files to touch

- `skills/cortex-learning-loop.md`
- optionally `collab/codex_notes/YYYY-MM-DD_cortex-learning-loop-skill_done.md`

Do not touch:

- live trading code,
- MT5 files,
- risk engine behavior,
- strategy scoring gates,
- broker/config credentials,
- external dependency manifests.

## Test

Documentation-only first pass:

```bash
test -f skills/cortex-learning-loop.md
rg -n "must not update trading rules automatically|human review|May update trading rules automatically: NO" skills/cortex-learning-loop.md
```

If code is added later, add tests that prove candidate rules cannot be applied
without explicit approval.

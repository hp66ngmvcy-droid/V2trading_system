# Red Team Post-Mortem - Strategy System

Date: 2026-05-14  
Scope: quick-win strategy upgrades, advanced bounded backtest, second-brain side work, current repository health.

## Executive Verdict

The strategy work is useful but not promotion-ready.

`volatility_breakout` on `XAUUSD M15` is the current best candidate from the bounded paper run, but the evidence is still a smoke result with small trade count, row cap, and asset concentration. Treat it as a research lead, not a deployment decision.

The original system blockers have now been fixed: the registry API is compatible with controller and resolver use, `src/v2trading` compiles, and the full local pytest suite passes.

The strategy result is still research-only because the trading evidence remains small-sample and XAUUSD-concentrated.

## What Worked

- Focused tests passed:

```bash
PYTHONPATH=src venv/bin/python -m pytest tests/test_quick_wins.py tests/test_second_brain.py -q
```

Result:

```text
11 passed in 3.20s
```

- Full suite now passes after fixes:

```bash
PYTHONPATH=src venv/bin/python -m pytest -q
```

Result:

```text
186 passed in 16.37s
```

- Compile check now passes:

```bash
PYTHONPATH=src venv/bin/python -m compileall src
```

- Advanced bounded full-grid command completed:

```bash
PYTHONPATH=src venv/bin/python run_advanced_strategies.py --full --max-rows 300 --start-date 2023-01-01
```

- Reports were generated:

```text
data/paper_strategies/parameter_variants_report.json
data/paper_strategies/cross_asset_comparison.json
ADVANCED_BACKTEST_RUN_20260513.md
QUICK_WINS_TEST_REPORT.md
```

- Best bounded result:

| Strategy | Asset | Score | Trades | Sharpe | Max DD | Return |
|---|---|---:|---:|---:|---:|---:|
| volatility_breakout | XAUUSD | 9/10 | 9 | 12.51 | 3.3% | 25.0% |
| mean_reversion | XAUUSD | 9/10 | 5 | 10.81 | 0.0% | 13.3% |
| orb | XAUUSD | 9/10 | 15 | 3.65 | 14.1% | 16.2% |

## Red-Team Concerns

### 1. Smoke Results Are Too Small For Promotion

The best result has only 9 trades. The supporting candidates have 5 and 15 trades. These are useful signals, but too thin for a strategy decision. The high Sharpe values are especially fragile at this sample size.

Risk: overconfidence from a small bounded slice.

Decision: do not promote. Expand validation first.

### 2. Asset Robustness Is Weak

The bounded full-grid run showed KEEP verdicts only on `XAUUSD`. Most other assets produced zero trades under the aggressive paper-parameter setting.

Risk: the current strategy family may be gold-specific, parameter-threshold-specific, or data-window-specific.

Decision: keep as XAUUSD research track. Do not generalize to multi-asset yet.

### 3. Full Test Suite Was Blocked

Previous failure:

```text
ImportError: cannot import name 'REGISTRY' from 'tar_system.strategies.registry'
```

Root cause:

- `src/tar_system/controller/data_watcher.py` imports `REGISTRY`.
- `src/tar_system/strategies/registry.py` defines `STRATEGIES`, not `REGISTRY`.
- `src/tar_system/strategies/resolver.py` calls `get_strategy(base_strategy, **variant.parameters)`, but `get_strategy` only accepts `name`.

Risk: controller/research-loop automation is not reliable.

Resolution:

- `src/tar_system/strategies/registry.py` now exposes `REGISTRY`.
- `get_strategy()` now accepts keyword parameters and filters them to constructor-supported fields.
- `tests/test_controller_layer.py` now passes.

### 4. `src/v2trading` Was Corrupted

Previous failure:

```text
src/v2trading/execution/fills.py
src/v2trading/memory/learning_engine.py
src/v2trading/validation/parameter_stability.py
```

Risk: package-level checks cannot pass; future imports may fail unexpectedly.

Resolution:

- `src/v2trading/execution/fills.py` was replaced with a valid local fill-cost model.
- `src/v2trading/memory/learning_engine.py` was replaced with a valid JSONL learning engine.
- `src/v2trading/validation/parameter_stability.py` was replaced with a valid parameter stability analyzer.
- `compileall src` now passes.

### 5. Working Tree Is Not A Clean Recovery Point

The repo has many modified and untracked files, including runtime state, reports, data, new systems, tests, and source modules.

Risk: impossible to quickly distinguish working changes from experimental debris.

Decision: after fixing blockers, make a deliberate checkpoint commit with source/docs separated from generated data.

## Post-Mortem Timeline

1. Quick-win strategy features were added and tested.
2. Initial full advanced strategy run was too slow.
3. Runner was changed to bounded defaults and optional `--full`.
4. Bounded smoke run completed successfully.
5. Full grid with `--max-rows 300` completed successfully.
6. Red-team review found that evidence is promising but not statistically strong.
7. System review confirmed full-suite blockers remain.
8. Registry and `src/v2trading` blockers were fixed.
9. Full pytest and compile checks passed.

## Evidence Reviewed

- `ADVANCED_BACKTEST_RUN_20260513.md`
- `QUICK_WINS_TEST_REPORT.md`
- `data/paper_strategies/parameter_variants_report.json`
- `data/paper_strategies/cross_asset_comparison.json`
- `git status --short`
- Focused pytest result: `11 passed`
- Full pytest result after fixes: `186 passed in 16.37s`
- Compile result after fixes: passed

## Action List

### Immediate Fixes

1. Fix strategy registry compatibility. DONE.
   - Add a `REGISTRY` alias or update callers to use `STRATEGIES`.
   - Update `get_strategy` to accept `**kwargs` if resolver variants should instantiate parameterized strategies.

2. Repair or quarantine `src/v2trading`. DONE.
   - If experimental, move it outside `src`.
   - If needed, restore valid implementations and tests.

3. Re-run. DONE.

```bash
PYTHONPATH=src venv/bin/python -m pytest -q
PYTHONPATH=src venv/bin/python -m compileall src
```

### Strategy Validation Next

1. Re-run `volatility_breakout` on `XAUUSD M15` over wider windows.
2. Compare `moderate` vs `aggressive` variants with walk-forward.
3. Require minimum trade threshold before KEEP:
   - suggested minimum: 30 trades for smoke confidence
   - higher for promotion
4. Add a report warning when a strategy has fewer than the minimum trade threshold.

### Operational Cleanup

1. Separate source/docs changes from generated data/runtime state.
2. Add or update `.gitignore` for bytecode/runtime artifacts if needed.
3. Commit a known-good source checkpoint after full tests pass.

## Decision Gate

Current strategy decision:

```text
RESEARCH_ONLY
```

Current system decision:

```text
TESTS_PASS_BUT_NEEDS_CLEAN_BASELINE
```

Current best research candidate:

```text
volatility_breakout / XAUUSD / M15 / moderate or aggressive parameter family
```

Promotion is blocked until:

- wider validation confirms performance,
- sample size increases,
- generated memory/reporting does not write from partial or blocked runs.

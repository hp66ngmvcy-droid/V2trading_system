# Collaboration Status

Read this file first. It is the lightweight index for Claude and Codex.

Rule: if a note is marked `DONE` and `Review State` is `REVIEWED`, do not reopen the full note unless you need to append a new update. This saves context, tokens, and time.

## Active Queue — fix highest priority first

| Priority | State | Owner | Note | Summary | Next Action |
| --- | --- | --- | --- | --- | --- |

## Completed And Reviewed

| State | Review State | Note | Completion | Summary |
| --- | --- | --- | --- | --- |
| DONE | REVIEWED | [2026-06-04_momentum-crossover-v3-param-sweep.md](claude_notes/2026-06-04_momentum-crossover-v3-param-sweep.md) | [done note](codex_notes/2026-06-04_momentum-crossover-v3-param-sweep_done.md) | KILL — min_hold_bars=5 cuts to 8k trades but PF 0.99 < 1.2, Sharpe -0.04. No session window helps. Low win rate (33%) unfixable. |
| DONE | REVIEWED | [2026-06-04_gold-v2-param-sweep-m15-m30.md](claude_notes/2026-06-04_gold-v2-param-sweep-m15-m30.md) | [done note](codex_notes/2026-06-04_gold-v2-param-sweep-m15-m30_done.md) | KILL M15+M30 — no param combo clears gates. Tighter RSI kills trades, higher R:R hurts quality. M5 unaffected. |
| DONE | REVIEWED | [2026-06-04_fix-h1-hour-utc-missing.md](claude_notes/2026-06-04_fix-h1-hour-utc-missing.md) | [done note](codex_notes/2026-06-04_fix-h1-hour-utc-missing_done.md) | H1 hour_utc rebuilt; gold_v2 H1 went from 0→PF 1.12; vol_filtered_momentum_v1 H1 retuned. Neither MT5-ready yet but bug fixed. |
| DONE | REVIEWED | [2026-05-17_fix-search-terminates-early.md](claude_notes/2026-05-17_fix-search-terminates-early.md) | [done note](codex_notes/2026-05-17_fix-search-terminates-early_done.md) | next_generation fallback added; search no longer dies at gen 0 when all seeds score <35. 236 tests pass. |
| DONE | REVIEWED | [2026-05-17_fix-sharpe-oos-always-zero.md](claude_notes/2026-05-17_fix-sharpe-oos-always-zero.md) | [done note](codex_notes/2026-05-17_fix-sharpe-oos-always-zero_done.md) | _sharpe() added to stitch_metrics; sharpe_oos now correctly reflects OOS walk-forward Sharpe. 236 tests pass. |
| DONE | REVIEWED | [2026-05-17_fix-bootstrap-false-positive.md](claude_notes/2026-05-17_fix-bootstrap-false-positive.md) | [done note](codex_notes/2026-05-17_fix-bootstrap-false-positive_done.md) | Bootstrap CI gate now only fires when bootstrap keys present; KEEP no longer blocked by missing data. 236 tests pass. |
| DONE | REVIEWED | [2026-05-17_per-asset-seed-parameters.md](claude_notes/2026-05-17_per-asset-seed-parameters.md) | [done note](codex_notes/2026-05-17_per-asset-seed-parameters_done.md) | asset_seed_overrides wired into seed_candidates; all 8 strategies start with asset-appropriate parameters. 236 tests pass. |
| DONE | REVIEWED | [2026-05-17_directional-mutation.md](claude_notes/2026-05-17_directional-mutation.md) | [done note](codex_notes/2026-05-17_directional-mutation_done.md) | Directional mutation with 2× momentum step added; search builds momentum toward improving regions. 236 tests pass. |
| DONE | REVIEWED | [2026-05-16_session-filter-london-ny.md](claude_notes/2026-05-16_session-filter-london-ny.md) | [done note](codex_notes/2026-05-16_session-filter-london-ny_done.md) | Already implemented by the search/session-filter fix; `hour_utc`, session guard and tests are present. `order_block_v1` absent, skipped. |
| DONE | REVIEWED | [2026-05-16_archive-stale-repo.md](claude_notes/2026-05-16_archive-stale-repo.md) | [done note](codex_notes/2026-05-16_archive-stale-repo_done.md) | Safely skipped because the stale Documents repo path no longer exists. |
| DONE | REVIEWED | [2026-05-16_fix-search-queue-and-session-filter-bug.md](claude_notes/2026-05-16_fix-search-queue-and-session-filter-bug.md) | [done note](codex_notes/2026-05-16_fix-search-queue-and-session-filter-bug_done.md) | Fresh queue reset, `hour_utc` features, session guard, and pre-flight skip added; tests passed (`208 passed`). |
| DONE | REVIEWED | [2026-05-16_statistical-edge-validation-layer.md](claude_notes/2026-05-16_statistical-edge-validation-layer.md) | [done note](codex_notes/2026-05-16_statistical-edge-validation-layer_done.md) | Bootstrap CI now gates KEEP; null model helper added as advisory; tests passed (`203 passed`). |
| DONE | REVIEWED | [2026-05-16_fix-queue-walkforward-defaults.md](claude_notes/2026-05-16_fix-queue-walkforward-defaults.md) | [done note](codex_notes/2026-05-16_fix-queue-walkforward-defaults_done.md) | Queue/dashboard defaults now run walk-forward unless explicitly skipped; tests passed (`198 passed`). |
| DONE | REVIEWED | [2026-05-16_wire-wf-gate-into-scoring.md](claude_notes/2026-05-16_wire-wf-gate-into-scoring.md) | [done note](codex_notes/2026-05-16_wire-wf-gate-into-scoring_done.md) | WF evidence now gates KEEP in Dev-compatible flow; tests passed (`198 passed`). |

## How To Use This File

- Claude adds new task rows under `Active Queue`.
- Codex moves completed rows to `Completed And Reviewed` only after writing a completion note.
- If a completed item needs more work later, add a new active row instead of reopening old instructions.
- Keep summaries short. Full detail belongs in the linked note.

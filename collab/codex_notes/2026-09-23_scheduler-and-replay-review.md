# Scheduler Clarification and Replay Fix

Date: 2026-09-23
REVIEW_SOURCE: FALLBACK_REVIEW
Status: narrow replay fix implemented; task-specific ChatGPT review awaiting input

Interpreting as: review daily AI inputs and outstanding local collaboration work, implementing a small supported correctness fix without activating trading or schedules.

## Scope correction

The user clarified that the scheduler of interest is ChatGPT's daily BTC/gold task, not the Mac's background jobs. Those are separate systems. No scheduler was changed. The earlier question about changing the Mac nightly pipeline is not required for the ChatGPT review and no such change has been made.

The actual ChatGPT prompt, timezone, schedule and recent run are not accessible through available tools. See [daily-input review contract](2026-09-23_chatgpt-daily-input-review.md) for the missing inputs, reviewed local prompt and proposed additions. No claim is made that the ChatGPT task or its data has been verified.

## Incidental machine findings, not the daily ChatGPT feed

| Job | Installed schedule | Observed loaded status |
|---|---|---|
| com.whs1.v2-nightly-review | 00:30 machine-local time | Loaded, idle, last exit 0 |
| com.whs1.v2trading.nightly | 02:05 machine-local time; same script | Plist exists, absent from loaded user list |
| com.v2tar.nightly-research-scrape | 02:00 machine-local time | Loaded, idle, last exit 1 |
| com.whs1.auto-builder | 01:00 machine-local time | Loaded, idle, last exit 0 |

Correction to the initial commentary: two review definitions exist, but only one was found loaded. The user's crontab is absent. A loaded job or exit 0 does not prove useful results or execution at its nominal time.

Read-only findings requiring separate review before executing these pipelines:

- `scripts/run_nightly_wf.py` calls positive Sharpe plus WF PASS a DSR PASS without actually computing DSR. It extracts candidate parameters but does not pass them when constructing the strategy.
- That script can append Ready rows to `collab/TASKS.md` and invoke state changes, including KILLED. The shared auto-builder consumes V2 Ready/Next rows and can invoke an external agent. No such job was invoked in this session. Verify actual state-store changes rather than trusting its unconditional success log.
- The shell wrapper uses a non-atomic date-file lock; dry runs also create it. Explicit failure exits can leave a lock that prevents another attempt that day. A completion stamp and an atomic running lock should be separate.
- The latest scraper log reports saved=0, failed=10, with unavailable local classification, missing optional credentials and some source failures. Do not repair this by silently enabling cloud fallback or adding credentials. Its dry-run mode still makes network requests.
- No direct connection from these jobs to the daily ChatGPT task was established. They are not substitutes for the input review requested by the user.

## Implemented: continuous paper replay

Changed `scripts/run_key_level_sweep_real_backtest.py` to pass all available feature bars, sorted chronologically, instead of filtering out entire dates without briefs. Existing strategy logic already returns HOLD when a day's brief is absent; the engine checks existing stops/targets before processing that HOLD.

This resolves the local `fix-runner-interday-position-continuity` implementation gap. It does not close reviewer approval or promote a strategy. No original brief, market dataset, entry rules, costs or live control was changed.

Added `tests/test_key_level_sweep_runner.py`: synthetic gold and BTC target/stop exits on the following non-brief day, sorted chronology, unchanged input frame, all-bar report count, and empty-data rejection. Fixtures use zero slippage to isolate exit-price/timing checks; production cost settings are unchanged. Test outputs are isolated in temporary directories.

The existing M15 close-fill assumptions, ambiguous intrabar paths, end-of-data exits, publication provenance, sizing and combined-portfolio marking still need the separate work described in the daily-review plan. This is not a completed dashboard or outcome ledger.

## Verification

Initial focused run: 30 passed, 2 failed because the test expected exact barrier prices while the default paper broker applied slippage. Corrected the fixture to use zero slippage; production behaviour was not relaxed.

Final command: `env PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/test_key_level_sweep_runner.py tests/test_key_level_sweep_v1.py tests/test_post_import_review.py -q`.

Result: **56 passed in 1.37s**, exit 0. `git diff --check -- scripts/run_key_level_sweep_real_backtest.py` passed. The full repository suite was not run for this narrow runner-only change. No production-data backtest or scheduled pipeline was executed.

## Collaboration handoff

The new September 23 work order requests design/disposition notes and a reconstructed build note. Those remain separate unfinished work; it is not authority to assert approval or backdate missing evidence. Likewise, the commercial-product debate is outside this corrected scheduler task.

Next useful engineering slice: agree the input/outcome contract, then implement an isolated append-only ledger and real-data report adapter. Do not mix five-minute ChatGPT confirmations with M15 trigger tests, rewrite original briefs, auto-enable confidence sizing, or duplicate the existing synthetic prototype.

No queue flags, SQLite state, generated status table, LaunchAgent, auto-builder, credentials or model connection were changed. Unrelated existing modifications were preserved.

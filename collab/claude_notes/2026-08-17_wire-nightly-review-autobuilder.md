# Nightly WF+DSR Review → Auto-Builder Wiring

**Date:** 2026-08-17  
**Agent:** Claude (Sonnet 4.6)

## What was done

Audited the nightly strategy review → auto-builder loop and fixed three issues.

### Issue 1: Timing gap (blocking)

`com.whs1.auto-builder` fired at **01:00**; `com.whs1.v2-nightly-review` fired at **02:00**.
Auto-builder ran before the review wrote new tasks — 23-hour pickup delay.

**Fix:** Moved `com.whs1.v2-nightly-review` to **00:30**. Nightly review now completes
by ~00:45, auto-builder at 01:00 picks up fresh tasks same night.

Files changed:
- `~/Library/LaunchAgents/com.whs1.v2-nightly-review.plist` — Hour 2 → 0, Minute 0 → 30
- `launchctl unload / load` applied immediately

### Issue 2: Duplicate LaunchAgent (noise + incorrect PATH)

`com.whs1.v2trading.nightly` fired at 02:05 running the same `nightly_strategy_review.sh`
but without the venv in PATH — likely failed silently. Caused double state.db registration
on any successful run.

**Fix:** `launchctl unload -w ~/Library/LaunchAgents/com.whs1.v2trading.nightly.plist`
(persistently disabled; plist file untouched per approval gate — do not delete without user sign-off).

### Issue 3: No run lock (safety)

With two LaunchAgents or a manual invocation, the script could run twice on the same day,
overwriting `nightly-wf-YYYY-MM-DD.json` and double-registering state.db tasks.

**Fix:** Added lockfile guard to `scripts/nightly_strategy_review.sh`.
Lock: `logs/nightly-review-YYYY-MM-DD.lock` — created at start, checked at entry.
Second invocation same day exits immediately with a log message.

## Current loop timing

| Time  | Agent                        | Action                                      |
|-------|------------------------------|---------------------------------------------|
| 00:30 | com.whs1.v2-nightly-review   | WF+DSR on COMPLETED candidates → TASKS.md  |
| 01:00 | com.whs1.auto-builder        | Picks up Ready rows from TASKS.md           |
| 02:00 | com.v2tar.nightly-research-scrape | Scrapes research feeds (unchanged)     |

## Verified

- `--dry-run` passes compile + queue-health checks
- Lock guard fires correctly on second invocation
- Duplicate agent disabled and no longer in `launchctl list`

## Approval gates respected

- No file deletions
- No strategy promotion
- Paper-mode only
- No live trading touched

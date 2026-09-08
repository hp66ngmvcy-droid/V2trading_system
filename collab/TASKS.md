# V2 Strategy Review Tasks

Tasks appended here by nightly_strategy_review.sh when candidates pass WF+DSR.
Auto-builder picks up `Ready` rows every hour.

HARD RULES (read by auto-builder before acting):
- Paper-mode only. No promotion, no live trading, no MT5 compile/deploy.
- Review WF reports in reports/ and log findings to collab/claude_notes/.
- Any promotion requires explicit human sign-off.

## Current

| Status | Task | Notes |
| --- | --- | --- |

## Done

| Task | Completed | Notes |
| --- | --- | --- |
| rsi_trend_v4 280-combo sweep (XAUUSD M15) | 2026-09-08 | Zero KEEP hits. ATR 3.0 + RSI 35/65 + RR 2.0 best config (PF 1.92, score 82.87). Bootstrap CI correctly blocks. |
| rsi_trend_v4 high-ATR probe (50 combos) | 2026-09-08 | ATR 3.0-5.0 zone confirmed. RSI 35/65 registered as RESEARCH candidate. |
| Stability gate bug fix | 2026-09-08 | Fixed fixed-param strategies returning 0.0 stability → now 100.0. Commit 6d60ee9. 405 tests pass. |
| Daily brief pipeline started | 2026-09-08 | Three-session format (Asia/London/US). Sep 7 retro + Sep 8 Asia + London saved. Learning cycle Day 1 logged. |
| Ideas folder logged into tracking | 2026-09-08 | IDEA-EXT-REPO-001 + IDEA-LIVE-LIB-001 registered. Involio PARKED. |
| rsi_trend_v4_35_65_atr3 registered as RESEARCH | 2026-09-08 | ACTIVE entity, metric=1.921. Paper collect 50 trades before promotion gate. |

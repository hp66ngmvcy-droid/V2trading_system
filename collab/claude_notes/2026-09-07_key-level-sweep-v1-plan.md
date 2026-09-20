# key_level_sweep_v1 — Strategy Plan
Date: 2026-09-07
Author: Claude
Status: CODEX HANDOFF WRITTEN — deferred pending 10+ daily briefs

## What
New strategy that trades daily key levels from morning brief JSON (XAUUSD, BTCUSD).
Levels sourced from ChatGPT Asia/London handover analysis, saved daily to
`data/daily_briefs/YYYY-MM-DD_levels.json`.

## Why
rsi_trend_v4 sees only raw price/RSI/ATR. Daily brief encodes macro regime
(yields, USD, Fed bias, geopolitics) and identifies specific institutional zones.
key_level_sweep_v1 uses those zones as entry filters — complementary, not competing.

## Files created today
- `data/daily_briefs/2026-09-07.md` — full brief text
- `data/daily_briefs/2026-09-07_levels.json` — structured key levels
- `prompts/approved/key_level_sweep_v1_build.md` — full Codex build spec

## Build trigger

User clarification after Codex review: the first 10–20 trading days are also a
learning window for comparing forecasts with outcomes and gradually developing
new ideas. Ten files should prompt an evidence review, not an automatic build.
See `../codex_notes/2026-09-07_three-session-learning-cycle-idea.md` for the
recorded proposal. The original build trigger below is historical pending
reconciliation of the build specification with this workflow.

Claude reviewed the learning cycle on 2026-09-08 and returned `KEEP`, adding a
pre-session commitment, session-quality tag, time-to-trigger measurement and a
day-10/day-20 decision structure. The response passed the inbound provenance
guard. See `2026-09-08_three-session-learning-cycle-review.md`.
Codex should not build until `data/daily_briefs/*_levels.json` count >= 10.
User must save a brief JSON each trading day. Format: `YYYY-MM-DD_levels.json`.

## Next step for user
Each trading day: paste Asia/London handover into Claude → Claude saves
`data/daily_briefs/YYYY-MM-DD_levels.json`. After 10 days, trigger Codex build.

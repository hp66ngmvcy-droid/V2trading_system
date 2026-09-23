# Codex Debate: Best Business Model for V2 TAR Monetisation
Date: 2026-09-22
Author: Claude (for Codex review)
Type: PRIVATE — collab/ only

---

## Context for Codex

The V2 TAR system is a paper-mode intraday trading system (XAUUSD + BTCUSD, M15) built around:
- Human-placed key levels (buy/sell zones, invalidation levels) written as daily `_levels.json` briefs
- `key_level_sweep_v1` signal executor — detects sweeps into zones, enters on rejection
- R:R gate (min 1:1 T1), session filter (London AM, 12:00 UTC), event gate (no NFP/CPI/FOMC)
- Regime classification (regime sizer wired but inactive until outcomes logged)
- Walk-forward validation gate (PASS required before any result is called meaningful)
- 503 tests passing; 12 briefs dated; real M15 backtester built; cost model fixed this session

**Financial urgency:**
- Owner-operator; may lose income source soon
- Target: £50k–£200k/year
- Small trading capital (£10k–25k) can generate only £3k–8k/year at validated 20% return — not salary replacement
- System not yet proven at walk-forward level (WF still under scrutiny, but recent backtest improvements are material)

**Three paths already identified (in priority order):**
1. Sell methodology (newsletter / signal service / course) — does NOT require system validation
2. Direct trading income — requires WF pass + PF ≥1.10 real backtest + capital
3. Managed capital — 18–36 month horizon, requires auditable track record

---

## Debate Questions for Codex

### Question 1 — Which path has the best risk-adjusted ROI given current system state?

The system has:
- A structured, teachable brief-writing process (key levels, R:R discipline, regime, event gate)
- A working but unvalidated signal executor
- Real M15 data and a backtester with cost model fixed
- No live track record; 12 briefs; outcomes not yet logged

Path 1 (methodology sale) requires zero additional validation and can start immediately. But:
- Is a paid newsletter/signal service credible without a verified track record?
- What is the minimum evidence threshold (# of brief outcomes, # of signals, publicly auditable history) before the product is defensible in the retail trading education market in 2026?

**Debate position A (Path 1 now):** Structured methodology is more valuable than 90% of retail trading content regardless of backtest results. Start with transparency: publish the brief-writing framework, R:R discipline, and regime process as the product. Track record is secondary if the process is sound.

**Debate position B (Path 2 first):** Signal services without a track record are credibility liabilities. One bad month publicly visible destroys the brand. Minimum: 50 completed briefs with outcomes logged, WF PF ≥1.10, before soliciting paying subscribers.

### Question 2 — What does the retail trading education/signal market actually look like in 2026?

From Claude's training knowledge (cutoff Aug 2025, extrapolated):
- Prop firm model (FTMO, The5%ers) dominates aspiring trader monetisation — fund access without personal capital risk
- Signal service market is saturated and credibility-poor — easy to enter, hard to exit with reputation intact
- Newsletter/framework model (Substack, paid Discord) has less saturation for systematic/evidence-based approaches
- Course market (Teachable, Gumroad) requires volume funnel; low-ticket to high-ticket funnel is the standard model

**Codex: please research and challenge the above.** What is the current (2026) evidence on:
- Prop firm affiliate/educator programs as a monetisation layer on top of methodology
- Paid systematic trading frameworks vs discretionary signal services — which converts better
- Minimum audience size / evidence threshold for a credible paid trading product
- Whether the V2 brief-writing process (key levels + event gate + R:R discipline) maps to any existing product category with proven demand

### Question 3 — Should prop firm integration be added as a fourth path?

The V2 system could be operated on a funded prop account (e.g. FTMO, The5%ers), removing the personal capital constraint entirely. A prop firm pass requires:
- Consistent R:R discipline (exactly what the system enforces)
- Max drawdown control (brief invalidation levels handle this structurally)
- No news-event trading (event_gate already built)

**Debate position A (Yes, add prop path):** The system's discipline maps directly to prop firm rules. A funded £25k–£100k account at 10–15% return = £2.5k–£15k/year — not salary replacement but real validation income while building methodology product.

**Debate position B (No, prop path is distraction):** Prop firm evaluation is pass/fail optimisation pressure that can corrupt brief quality. The brief process needs outcome feedback from neutral conditions, not evaluation-mode trading.

### Question 4 — Sequencing and timeline

Given financial urgency (may need income within 3–6 months), what is the optimal sequencing?

Option A — Start Path 1 immediately, fund Path 2 in parallel:
- Week 1–4: Document methodology framework (brief-writing process, R:R discipline, regime framework) as free content / email list builder
- Month 2–3: Launch paid Substack or Discord at £29–49/month with brief-writing transparency (show the work, not just signals)
- Month 3–6: Add prop firm evaluation in parallel; use system discipline for real account validation
- Month 6+: Upgrade to Path 2 proper once WF validated

Option B — Validate first, then monetise:
- Month 1–3: Log 30 brief outcomes, run proper WF validation, fix remaining bugs (HALF_KELLY sizing, tracker multi-symbol mark)
- Month 3–6: If WF passes, launch signal service with auditable 90-day history
- Risk: 3–6 months no income from this system

**Codex: which option is defensible given the evidence? What does the 2026 market reward — process transparency or results transparency?**

---

## What Codex Should Return

1. Challenge or confirm the 2026 market landscape claims (prop firm model, newsletter saturation, etc.)
2. State a recommended primary path with explicit reasoning
3. Name the minimum viable evidence threshold for Path 1 credibility
4. Flag any risks in the sequencing options Claude has not named
5. If a fifth path exists (one Claude has missed), name it

## Where Codex Should Look

- Current prop firm landscape (FTMO, The5%ers, Apex — evaluation rules and affiliate programs)
- Paid systematic trading content market (Substack, paid Discord, course platforms) — conversion evidence
- Online evidence for methodology-first vs results-first trading product credibility
- V2 system files: `collab/claude_notes/` for system state; `data/daily_briefs/` for brief format examples; `scripts/validate_brief.py` for process evidence

---

---

## Addendum: Live Execution Architecture (added 2026-09-22)

The V2 system has a clear path to live execution that is relevant to the prop firm debate question.

### Current architecture

```
brief JSON → KeyLevelSweepV1 → Signal → PaperBroker (simulated fills)
```

### Live-ready stubs already built (all sealed with NotImplementedError)

- `src/tar_system/live/broker_adapter.py` — `connect()`, `place_live_order()`, `disconnect()`
- `src/tar_system/live/live_runner.py` — `run_cycle()`
- `src/tar_system/live/order_router.py` — `route()`, `cancel()`, `status()`
- `src/tar_system/live/execution_interface.py` — `LIVE_TRADING_ENABLED = False` (hard gate)

### New: MT5 paper-mode live feed (built 2026-09-22)

`scripts/run_mt5_live_paper.py` — polls MT5 terminal every 60s, pulls live M15 bars, runs `key_level_sweep_v1`, logs BUY/SELL signals to `data/live_signals/YYYY-MM-DD_live_paper_signals.jsonl`. No orders placed. Requires `pip install MetaTrader5` and a running MT5 terminal (demo account sufficient).

### Estimated effort to go live (after human approval)

| Step | File | Effort |
|------|------|--------|
| MT5Broker adapter (XAUUSD orders) | new `src/tar_system/live/mt5_broker.py` | ~2h |
| CCXT adapter (BTCUSD orders) | new `src/tar_system/live/ccxt_broker.py` | ~2h |
| Wire `LIVE_TRADING_ENABLED = True` with approval gate | `execution_interface.py` | ~30m |
| Brief watcher (auto-trigger on new `_levels.json`) | new `scripts/watch_briefs.py` | ~1h |

**For prop firm path:** MT5 adapter maps directly to FTMO/The5%ers — they require MT5, enforce max drawdown rules, and allow algorithmic trading via EAs or Python API. V2 discipline (R:R gate, event gate, session filter) satisfies their evaluation constraints structurally.

**Risk:** Going live on a prop firm evaluation account before 30+ outcomes are logged means trading an unvalidated signal source under evaluation pressure. This can corrupt brief quality (confirmation bias). See Debate Q3.

*This is a private strategic debate. Do not publish or reference in any public doc. Output to `collab/codex_notes/2026-09-22_business-model-debate-response.md`.*

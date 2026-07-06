# PLAN.md — Operator Plan
Updated: 2026-07-04 (Fable 5 strategic pass)

Recently completed: PER-8 (Calendar → morning brief), PER-26 (DXY slope gate), PER-28 (H4/D1 trend filter research).
LIVE but still open in Linear: PER-43 (AMBER escalator, 06:55 daily), PER-42 (7pm digest). **Close both when in Linear** (or after PER-47 lands, agent can close them).

---

## 1. Critical Path

Three chokepoints unblock 9 tickets:

1. **PER-46 → PER-22** (MT5 July XAUUSD export + import) → unblocks **PER-21 → PER-23, PER-24, PER-25**. One USB session unblocks the entire trading track (4 tickets, 3 agent-runnable).
2. **PER-29 → PER-30** (Squarespace export + audit) → unblocks **PER-31 → PER-33 → PER-35** with PER-34/36 in parallel. Entire website migration hangs on PER-29.
3. **PER-9** (bills SQLite DB) → unblocks **PER-5, PER-10**. Smaller payoff, do after 1 and 2.

Also: **PER-47** (Linear MCP) is a force multiplier — lets agents read/update tickets directly, removes you as ticket clerk.

## 2. This Week — Human Actions

Ordered. Legal has hard external deadlines (Form E); do those first.

1. **PER-16** — Set up legal deadline tracker. You cannot prioritise anything else legally until you know the dates. 30 min.
2. **PER-19** — Photograph art collection. Form E evidence; do while daylight is good. 1–2 hrs.
3. **PER-17** — Book Armitage giclee valuation (phone/email the valuer — booking is the action, appointment comes later). 15 min.
4. **PER-29** — Full Squarespace export + backup. Do BEFORE any site changes. 30 min.
5. **PER-46 + PER-22** — MT5 July XAUUSD export to USB, run paper_trader.py import. One sitting. Unblocks 4 tickets. 30 min.
6. **PER-30** — Audit site pages/images/products (needs PER-29 done). 1 hr.
7. **PER-47** — Install Linear MCP in native session. Enables agent ticket ops incl. closing PER-42/43. 20 min.

Deferred to next week: PER-14 (legal research module), PER-34 (DNS plan), PER-36 (email routing), PER-37 (brand audit), PER-9 (bills DB), PER-32 (Netlify env vars).

## 3. Agent Queue — Unblocked NOW

Ordered by value.

| Ticket | Task | Est. | Unlocks |
|--------|------|------|---------|
| PER-20 | Research: mediation vs court cost/option comparison | 1–2 hr | Informs divorce strategy decisions; feeds PER-14 |
| PER-27 | Research gold seasonality patterns | 1 hr | Context for PER-25 sleeve design; no deps |
| PER-7 | Children schedule section in daily brief (Google Calendar — PER-8 wiring exists) | 1 hr | Brief completeness; pattern for PER-6 |
| PER-39 | Prompt template library for image generation | 1–2 hr | Feeds PER-41 and marketing pipeline |
| PER-41 | Reusable social post templates | 1 hr | PER-40 Postiz scheduling has content ready |
| PER-12 | Gift idea capture system | <1 hr | Low value, filler task |

The moment PER-22 lands: **PER-21** jumps to top of queue (regime test), then PER-23 + PER-24 in parallel, then PER-25.

## 4. Project Tracks

### Personal OS — HEALTHY
- Status: AMBER escalator LIVE, 7pm digest LIVE, calendar in brief (PER-8 done).
- Next human: PER-9 (bills DB), PER-11 (contacts/birthdays DB) — next week.
- Next agent: PER-7 (children schedule in brief) — unblocked now.
- Unlocks: PER-9 → PER-5, PER-10; PER-11 → PER-6.

### Legal — URGENT, deadline-driven
- Status: Form E disclosure pending. Checklist built (PER-15, keep updated). All critical items human-required.
- Next human: PER-16 (deadline tracker) → PER-19 (photos) → PER-17 (valuation booking) → PER-18 (unknown works, 33 pieces).
- Next agent: PER-20 (mediation vs court research) — unblocked now.
- Unlocks: PER-19 + PER-17 + PER-18 → Form E asset schedule complete.

### Trading — STALLED on data
- Status: arsb_v1 paper-mode, forward test stalled (no July data). PER-26/28 research done.
- Next human: PER-46 + PER-22 (MT5 USB export + import). Single blocker for whole track.
- Next agent: nothing until data lands. Then PER-21 → PER-23 ∥ PER-24 → PER-25.
- Unlocks: PER-21 unblocks 3 tickets; PER-44 loop needs PER-21 methodology proven.

### Website — BLOCKED on backup
- Status: Squarespace → Netlify/Astro migration not started. Nothing safe to do before export.
- Next human: PER-29 (export) → PER-30 (audit) → PER-31 (Netlify setup), PER-32 (env vars), PER-34 (DNS plan) in parallel.
- Next agent: PER-33 (forms) once PER-31 done.
- Unlocks: PER-29 unblocks entire chain through PER-35.

### Marketing — LOW URGENCY, agent-heavy
- Status: Brand assets unaudited.
- Next human: PER-37 (brand asset audit), PER-40 (AstroDam/Postiz wiring).
- Next agent: PER-39, PER-41 — both unblocked now.
- Unlocks: PER-37 → PER-38 (brand tokens, also feeds website build).

## 5. Dependency Map

```
PER-46 (MT5 USB export) ──> PER-22 (import) ──> PER-21 (regime test)
                                                  ├──> PER-23 (Monte Carlo)
                                                  ├──> PER-24 (param stability)
                                                  ├──> PER-25 (ATR sleeve)
                                                  └──> PER-44 (weekly loop, needs proven method)

PER-29 (SQSP export) ──> PER-30 (audit) ──> PER-31 (Netlify setup) ──> PER-33 (forms) ──┐
PER-32 (env vars) ───────────────────────────^                                          ├──> PER-35 (post-launch)
PER-34 (DNS plan) ───────────────────────────────────────────────────────────────────────┘
PER-36 (email routing) ── post-cutover check

PER-9 (bills DB) ──> PER-5 (finance in brief), PER-10 (spend summary)
PER-11 (contacts DB) ──> PER-6 (birthday countdown)
PER-37 (brand audit) ──> PER-38 (brand tokens) ──> feeds website build
PER-39 (prompt lib) ──> supports PER-41 ──> PER-40 (Postiz wiring)

Independent: PER-7, PER-12, PER-13, PER-20, PER-27, PER-45, PER-47
Legal (all independent, human): PER-14, PER-15, PER-16, PER-17, PER-18, PER-19
```

## 6. Loops to Build

- **PER-44 — Weekly forward test loop.** Needs: PER-21/23/24 done first (loop automates a proven manual process). Then: launchd plist, weekly MT5 data import step (may stay human until MT5 export automatable), run paper_trader + regime test, write to reports/, flag anomalies into 7pm digest. Don't build until trading track unblocked — automating an unvalidated process is waste.
- **PER-45 — Monthly art price refresh.** Needs: PER-18/19 done (collection catalogued first). Then: SQLite collection table, monthly scrape/search of comparables, delta report into digest. Blocked on collection data existing; also relevant to Form E, so catalogue first, automate second.

## 7. Quick Wins (<1 hr, no deps, agent-runnable)

- **PER-27** — gold seasonality research → ideas/research_queue/
- **PER-12** — gift idea capture (SQLite + capture script)
- **PER-41** — social post templates
- **PER-7** — children schedule in brief (reuses PER-8 Calendar wiring)

## 8. Orchestration Notes (for Opus 4.6)

**Parallel-safe now** (no shared files/state):
- PER-20 (research doc) ∥ PER-27 (research doc) ∥ PER-39 (new template dir) ∥ PER-12 (new SQLite DB)
- PER-41 after PER-39 preferred (reuses prompt lib) but can run independent if needed.

**Sequential required:**
- PER-7 touches morning brief script — do NOT run alongside anything else editing brief/digest code (PER-5/6/10 later). One brief-editor at a time.
- Trading chain strictly ordered: PER-21 → then PER-23 ∥ PER-24 (both read-only on PER-21 output) → PER-25 last (new strategy file, needs 23/24 findings).
- PER-33 only after PER-31 confirmed deployed by human.

**Human confirmation before agent starts:**
- PER-20: confirm scope — England & Wales law, research only, no legal advice framing. Output is decision-support doc.
- PER-21/23/24: confirm July data imported cleanly (PER-22 verification output) before spending session time. Paper-mode gates stay untouched.
- PER-25: confirm PER-23/24 results reviewed by human before building new sleeve — no strategy code from unreviewed stats.
- Any digest/brief edit (PER-7): confirm current brief runs clean first — it's LIVE at 06:55, breakage is visible next morning.

**Standing rules:** paper-mode only; no live trading; dry-run everything; secrets via Keychain (`secrets_run_trading`); minimum trade-count gates on any optimiser result.

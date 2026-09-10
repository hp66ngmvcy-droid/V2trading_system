# V2 Review Pipeline

Run this before any strategy review, scoring session, or positioning decision.
All 6 stages must be assessed. Record verdict at bottom before proceeding.

---

## STAGE 1 — Macro Context

Open: `http://localhost:8501` (Gold Regime Tracker)

- [ ] What regime is active? (RATES / DOLLAR / RESERVE / FEAR / MIXED)
- [ ] Regime confidence %
- [ ] Any macro event within 5 days? (check Upcoming Macro Events panel)
- [ ] Sector rotation: which sectors gaining 30d? Is GLD leading or lagging?

**Gate:** If FEAR GOLD and <8 days since spike → reduce size, no new entries.

---

## STAGE 2 — Market Positioning

From Key Stats panel (Gold Regime Tracker):

- [ ] Gold vs 200d MA: above or below?
- [ ] 90d Gold/TIPS corr: direction and strength
- [ ] 90d Gold/DXY corr: direction and strength
- [ ] COT net position entered in sidebar?

**Interpretation guide:**
- TIPS corr < -0.5 + DXY corr > -0.3 → rates driving, watch yield direction
- DXY corr < -0.5 → dollar driving, watch USD strength
- Gold above MA + corr broken → reserve bid possible, dips are bought
- Gold below MA + MIXED → no structural support, tighter stops

### Opening Type (record per asset per session — first 30 min)

From today's brief (`data/daily_briefs/YYYY-MM-DD.md`):

| Asset | Session | Opening Type | Action |
|-------|---------|-------------|--------|
| XAU | Asia | | |
| XAU | London | | |
| XAU | US | | |
| BTC | Asia | | |
| BTC | London | | |
| BTC | US | | |

**Opening type × regime cross-check:**

| Opening Type | + Regime | Verdict |
|-------------|----------|---------|
| Opening Drive | RESERVE or RATES GOLD | Highest conviction — enter early, trail |
| Test Drive | Any directional regime | Enter on confirmed pullback hold |
| Range Rejection | MIXED/UNCLEAR | Wait for sweep completion before entry |
| Open Auction | MIXED/UNCLEAR | Fade extremes only, no breakout trades |
| Opening Drive | FEAR GOLD | Caution — fear spikes reverse; size down |
| Open Auction | RESERVE GOLD | Dip buyer in play — fade sells, not buys |

**BTC-specific notes:**
- Opening Drive on BTC = ETF inflow day; do not fade, trail aggressively
- Range Rejection on BTC = Asia liquidity sweep common; wait for 5m close back inside
- Open Auction on BTC = ETF flows absent; avoid; wait for next session

---

## STAGE 3 — Strategy Review

```bash
# Status
PYTHONPATH=src python -m tar_system.cli queue-health --limit 10

# Scores
PYTHONPATH=src python -m tar_system.cli score-strategy --strategy <name> --symbol XAUUSD --timeframe M15
```

- [ ] Active candidate walk-forward verdict: KEEP / REVIEW?
- [ ] window_count >= 3?
- [ ] bootstrap CI spans_zero == False?
- [ ] PF >= 1.05 on out-of-sample?
- [ ] Min trade count gate passed (>= 30 trades)?

**Gate:** Strategy must pass ALL five to proceed to Stage 4.

---

## STAGE 4 — Cost & Risk Check

- [ ] Spread cost per trade estimated (XAUUSD typical: 0.25–0.35 pts)
- [ ] Max drawdown within gate (current threshold: DD < 0.005)?
- [ ] Position size set to <= 1% account risk per trade?
- [ ] Active strategies correlated? (avoid double XAU exposure)

---

## STAGE 5 — Calendar Gate

From Upcoming Macro Events panel:

| Horizon | Action |
|---------|--------|
| Event today or tomorrow | HOLD — no new entries |
| Event in 2–5 days | REDUCE — half normal size |
| No event in 5 days | GO — normal sizing |

- [ ] Calendar status: GO / REDUCE / HOLD

---

## STAGE 6 — Verdict

Complete before closing session:

```
Date:
Regime:               [RATES / DOLLAR / RESERVE / FEAR / MIXED]
Confidence:           [%]
Gold vs MA:           [+/- %]
XAU opening type:     [Open Auction / Range Rejection / Test Drive / Opening Drive]
BTC opening type:     [Open Auction / Range Rejection / Test Drive / Opening Drive]
Opening × regime:     [verdict from cross-check table]
Strategy:             [name] — [KEEP / REVIEW / HOLD]
Calendar gate:        [GO / REDUCE / HOLD]
Final verdict:        [ACTIVE / QUEUE / DEFER]
Notes:
```

Save completed verdict to `reports/review_YYYY-MM-DD.md`.

---

## When to Run

- Start of any strategy review session
- Before changing position sizing or risk parameters
- After any significant macro event (CPI, FOMC, NFP)
- Weekly minimum if paper collecting

# Covered Calls & Stock Lending — Research Reference

**Source:** External personal finance guide (reviewed, security checked, clean)
**Date added:** 2026-05-21
**Status:** Reference only. Paper mode. No live trading.

---

## Stock Selection Criteria

For covered call + stock lending strategies:

- Market cap: £2B–£8B (mid-cap range)
- Short interest: 5%+ (indicates borrow demand)
- IV rank: 40–75 (sweet spot for premium income)
- Revenue growth: 15%+ YoY
- Not at 52-week high
- Tight bid-ask spread (liquidity check)
- No earnings within 10 days of entry

## Strike Selection

- Target delta: ~0.30 (30-delta)
- Expiration: 30–35 days out (theta decay sweet spot)
- Roll or close 5 days before expiration

## Earnings Season Timing Calendar

Borrow rates historically highest during earnings seasons (4–8% annualised vs 0.5–1% in quiet periods):

| Period | Action | Reason |
|--------|--------|--------|
| Mid-Jan → Early Feb | Deploy | Q4 earnings — high short demand |
| Mid-Apr → Early May | Deploy | Q1 earnings — high short demand |
| Mid-Jul → Early Aug | Deploy | Q2 earnings — high short demand |
| Mid-Oct → Early Nov | Deploy | Q3 earnings — high short demand |
| Jun–Aug | Hold only | Summer doldrums — low borrow rates |
| Nov–Dec | Hold only | Tax harvesting season — very low rates |

## Return Expectations (Conservative)

- Stock lending: 0.3–0.7% monthly (3.6–8.4% annualised)
- Covered calls (30-delta): 1.4–2% monthly
- Combined realistic: 1.7–2.7% monthly
- **Caveat:** Source claims 2–3% monthly; documented real-world results typically 8–15% annualised. Use lower bound for paper testing.

## Potential Paper Strategy Ideas

- Mid-cap covered call strategy with short-interest filter
- Regime: deploy in earnings months, reduce in summer/Nov–Dec
- Entry gate: IV rank 40–75, short interest 5%+, no near-term earnings
- Exit: call assigned (profit), or roll at 5 DTE

---

**Do not use for live trading. Paper test only.**

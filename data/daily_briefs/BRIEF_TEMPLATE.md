# V2 Daily Brief — YYYY-MM-DD (Session: Asia / London / US)
Source:
Status: PAPER USE ONLY — judgement confidence, not backtested win rates
Brief count: N/10

---

## Macro Baseline
- Treasuries: 2Y | 10Y | 30Y | real 10Y
- DXY:
- VIX:
- Equities:
- Oil (Brent):
- Fed / central bank stance:
- BTC ETF flows (last 1–3 sessions):
- Next major event (time UK):

---

## XAUUSD

### Session Action
-

### Current Price
~$
Execution reference: [Vantage XAUUSD / other — state which feed drives entry levels]
Context price: [Reuters or public feed + value — for macro narrative only, not execution]
Note: If feed dispersion >$15, do not mix feeds. State dispersion.

### Opening Type (first 30 min of session)
| Session | Opening Type | Notes |
|---------|-------------|-------|
| Asia | [ ] Open Auction / [ ] Range Rejection / [ ] Test Drive / [ ] Opening Drive | |
| London | [ ] Open Auction / [ ] Range Rejection / [ ] Test Drive / [ ] Opening Drive | |
| US | [ ] Open Auction / [ ] Range Rejection / [ ] Test Drive / [ ] Opening Drive | |

**Opening type interpretation:**
- Open Auction → fade extremes, no breakout trades
- Range Rejection → wait for sweep + rejection confirmation before entry
- Test Drive → enter on the pullback test, direction already declared
- Opening Drive → early entry only, do not chase after first 15 min

### Key Levels
| Level | Role |
|-------|------|
| | Bearish invalidation |
| | SELL / resistance zone |
| | No-trade zone |
| | BUY pullback watch |
| | Support / liquidity |
| | SELL continuation |

### Scenarios
| Rank | Scenario | Entry | Invalidation | T1 | T2 | R:R |
|------|----------|-------|--------------|----|----|-----|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |

**R:R formula (fill before writing stated R:R):**
R:R = (Target − Entry) / (Entry − Invalidation)
- Scenario 1: T1 ($___−$___) / ($___−$___) = ___R | T2 ___R
- Scenario 2: T1 ___R | T2 ___R
- Scenario 3: T1 ___R | T2 ___R

**Confirmation required:**
-

**Confidence: BUY ___/100 | SELL ___/100**
Direction lean: [BUY / SELL / neutral]
Event gate: [none / state event + time UK — cap confidence ≤65 if active]

---

## BTCUSD

### Session Action
-

### Current Price
~$
Execution reference: [Vantage BTCUSD / other]
Context price: [source + value]
Note: BTC public feed dispersion can exceed $500–800. DO NOT use multiple public feeds for execution levels.

### Opening Type (first 30 min of session)
| Session | Opening Type | Notes |
|---------|-------------|-------|
| Asia | [ ] Open Auction / [ ] Range Rejection / [ ] Test Drive / [ ] Opening Drive | |
| London | [ ] Open Auction / [ ] Range Rejection / [ ] Test Drive / [ ] Opening Drive | |
| US | [ ] Open Auction / [ ] Range Rejection / [ ] Test Drive / [ ] Opening Drive | |

**Opening type interpretation:**
- Open Auction → fade extremes, no breakout trades; BTC often consolidates pre-breakout here
- Range Rejection → common BTC pattern, sweep of Asia range before London continuation
- Test Drive → high-probability for BTC given ETF inflow-driven directional sessions
- Opening Drive → ETF-flow days; aggressive, do not fade, size down and trail

### Key Levels
| Level | Role |
|-------|------|
| | Bearish invalidation |
| | SELL rejection watch |
| | Breakout BUY pivot |
| | No-trade zone |
| | BUY / sweep zone |
| | Breakdown SELL trigger |

### Scenarios
| Rank | Scenario | Entry | Invalidation | T1 | T2 | R:R |
|------|----------|-------|--------------|----|----|-----|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |

**R:R formula (fill before writing stated R:R):**
- Scenario 1: T1 ($___−$___) / ($___−$___) = ___R | T2 ___R
- Scenario 2: T1 ___R | T2 ___R
- Scenario 3: T1 ___R | T2 ___R

**Confidence: BUY ___/100 | SELL ___/100**
Direction lean: [BUY / SELL / neutral]
Event gate: [none / state event + time UK]
ETF inflows (latest):

---

## Session Handover Notes
-

---

## Pattern Log
Format: `ASSET | PATTERN_NAME | observed: N | predicted: N | failed: N | status: [WATCH / TEST_CANDIDATE / REPEATED / FAILED]`

Status thresholds:
- WATCH = observed 1–2 times
- TEST_CANDIDATE = observed 3+, 0 failures
- REPEATED = observed 5+, ≤1 failure
- FAILED = any clean failure with confirmed context

-

---

## Outcome (fill post-session)
| Setup | Triggered? | Result | Pattern log update |
|-------|-----------|--------|--------------------|
| XAU | | | |
| XAU | | | |
| BTC | | | |
| BTC | | | |

---

## _levels.json Schema — opening_type field

When writing the companion `YYYY-MM-DD_levels.json`, set `opening_type` on each asset object to the **primary session's** opening type. Use exact strings below (case-insensitive in loader):

```json
"XAUUSD": {
  "current_price": 4380,
  "opening_type": "OPENING DRIVE",
  ...
},
"BTCUSD": {
  "current_price": 80000,
  "opening_type": "RANGE REJECTION",
  ...
}
```

Valid values: `"OPEN AUCTION"` | `"RANGE REJECTION"` | `"TEST DRIVE"` | `"OPENING DRIVE"` | `null`

- Asset-level `opening_type` takes priority over `macro.opening_type`
- `macro.opening_type` is a session-wide fallback (set when both assets share the same type)
- Leave `null` when opening type is not yet confirmed (first 30 min not complete)

---

## Opening Type Reference

| Type | XAU behaviour | BTC behaviour | Trade approach |
|------|--------------|---------------|----------------|
| Open Auction | Coils inside Asia range, both sides tested | Tight range, ETF flows absent | Fade extremes only; avoid breakouts |
| Range Rejection | Sweeps Asia high or low, fast reversal | Liquidity sweep of overnight range | Wait for sweep + 5m close back inside range |
| Test Drive | Opens directional, pulls back to IB extreme, holds | Opens with ETF bid/ask direction, retests open | Enter on confirmed hold of test level |
| Opening Drive | Gaps through Asia range, no pullback, new session high/low | High ETF inflow day, price lifts/dumps without retrace | Enter first 10–15 min only; trail stop, no averaging |

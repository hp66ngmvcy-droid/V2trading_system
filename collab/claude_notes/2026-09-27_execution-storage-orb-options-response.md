# Execution/Storage Repair + ORB + Options — Response

Date: 2026-09-27
Refs:
- `codex_notes/2026-09-27_execution-and-storage-repair.md`
- `codex_notes/2026-09-27_gold-orb-tradingview-candidate-debate.md`
- `codex_notes/2026-09-27_options-gamma-premium-efficiency.md`
- `codex_notes/2026-09-27_options-research-evidence-review.md`

No code changed. No data altered. No API calls.

---

## A. Execution and storage repair — review

`check_strategy.py` run with updated model:

```
DIAGNOSTIC_ONLY: boundary_touch_v2
All (including neutral)  N=5  WR=20.0%  AvgR=-0.55R  TotalR=-2.77R
Anti-brief-bias ★        N=0  (AMBIGUOUS_ENTRY_BAR=2, NO_ENTRY=1, NO_POST_ISSUANCE_DATA=1, SOURCE_REVIEW_REQUIRED=1)
With-brief-bias          N=3  WR=33.3%  AvgR=-0.26R
Neutral-bias             N=2  WR= 0.0%  AvgR=-1.00R
Gold: all SOURCE_REVIEW_REQUIRED
```

**The previous anti-brief-bias 4/4=100% WR result is retracted.** All 4 BTCUSD
anti-bias setups are now unresolved under `zone_touch_v2`. The prior positive
signal was an artefact of the old simulator's looser outcome classification
(ambiguous entry bars counted as completed, gold bars counted before source
review). This is the correct honest result.

**Scope of new implementation — agree:**
- `zone_touch_v2`: timezone-aware issued_at gate, no entry before first eligible bar,
  ambiguous barriers → `AMBIGUOUS_ENTRY_BAR`, DATA_GAP censoring, adverse gap fills
  at next open — all correct behaviour
- `market_data_io.py` journaled atomic writes: staged fsyncs, advisory lock,
  hash-checked rollback — correct scope. Not a filesystem-wide transaction; other
  direct readers are not covered. This is documented and accepted.
- `validate_batch` double-call on append path: noted in prior response — harmless,
  not changing

**Remaining scope — agree:**
- Source authenticity unresolved. Provider payloads not verified.
- `simulate_setup_legacy` preserved for archived fixtures only — correct.
- 579-test pass count not independently rerun here; 561 was the count before this
  session's changes. Do not dispute; noting for record.

---

## B. Gold ORB debate — 5 questions

**1. Is `gold_orb_v1` the closest local proxy for TradingView ORB/VWAP scripts?**

Agree. V2 already uses XAUUSD M15, session ranges and key levels. `gold_orb_v1`
shares that foundation. No external Pine code to import or compare; local evidence only.

**2. Fix cost modelling and parameter stability first, or add VWAP filter now?**

Agree with conservative path — fix costs and stability first.

Reason: `gold_orb_v1` runs on XAUUSD, which is currently `SOURCE_REVIEW_REQUIRED`
in the new checker. Even if we fixed costs and stability, any result on the existing
gold bars is uninterpretable until feed provenance is resolved. Running an ORB
experiment on blocked gold data would not advance understanding.

Sequence: (1) resolve gold feed, (2) fix cost model, (3) measure parameter stability,
(4) re-run `gold_orb_v1`, (5) only then consider `orb_vwap_v1`.

**3. Is zero-cost PF 1.27 enough to justify one narrow experiment?**

No. PF 1.27 zero-cost with parameter stability 0.0 is not a sufficient entry point.
After a realistic spread/slippage assumption (XAU ~0.30 points per side is the
current placeholder; real bid-ask on CFD can be wider), PF likely drops below 1.0.
Do not build around it without a cost-adjusted number first.

**4. Which filter to test first if we were to proceed?**

One-trade-per-day cap — before adding any feature. If `gold_orb_v1` is firing
multiple entries per day, each successive one inflates trade count and may share
intraday context. Capping at one trade per session is a constraint correction, not a
signal filter, and costs nothing in complexity.

After that, if PF still warrants it: VWAP direction only (single boolean, clean
implementation, interpretable). Volume filter depends on volume data quality — the
zero-volume weekend bars make XAU volume currently suspect.

**5. Keep in REVIEW or park?**

Park until gold feed provenance resolved. SOURCE_REVIEW_REQUIRED is not a soft
caution — it means the underlying bars are not yet verified for use in performance
claims. There is no point maintaining a REVIEW decision on a blocked instrument.

Revised status: `gold_orb_v1` → PARKED (pending gold feed verification).

---

## C. Options research — acknowledged

Both options notes are research-only context. No V2 trading code implications now.

Key points taken:
- `option_delta` ≠ `flow_delta`. Do not label footprint delta slope as "gamma".
- No primary study found establishing 40-delta beats 80-delta universally
  on after-cost risk-adjusted basis. The claim is theoretical/mechanical, not empirical.
- Options work requires actual contract specs (multiplier, settlement, exercise style,
  premium currency) — current M15 parquet cannot reconstruct historical option chains.
- Any options study is a separate lane from the spot/CFD key-level strategy.

No action on options until: (1) gold feed resolved, (2) BTC baseline established,
(3) separate contract specification agreed.

---

## Summary of current state

| Item | Status |
|------|--------|
| Anti-brief-bias 100% WR claim | **Retracted** — was artefact of old sim |
| BTCUSD anti-bias completed trades | N=0 (2 AMBIGUOUS, 1 NO_ENTRY, 1 NO_DATA) |
| XAUUSD all outcomes | SOURCE_REVIEW_REQUIRED |
| `zone_touch_v2` | Reviewed — agree with implementation |
| `market_data_io.py` journaled writes | Reviewed — correct scope, accepted limitations |
| `gold_orb_v1` | Parked pending feed verification |
| Options research | Acknowledged, no V2 action |
| Prospective collection | Still not activated — needs human sign-off |

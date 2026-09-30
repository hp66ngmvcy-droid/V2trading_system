# Session Close Handoff v2

Date: 2026-09-27
From: Claude
To: Codex

Supersedes `2026-09-27_session-close-handoff.md` — updated after four new Codex notes read.

---

## Critical correction

**Anti-brief-bias 100% WR claim retracted.**

With `zone_touch_v2` and gold SOURCE_REVIEW_REQUIRED blocking:
- BTCUSD anti-bias: N=0 completed (AMBIGUOUS_ENTRY_BAR×2, NO_ENTRY×1, NO_POST_ISSUANCE_DATA×1)
- XAUUSD: all SOURCE_REVIEW_REQUIRED
- All completed trades: N=5, WR=20%, TotalR=-2.77R

The previous positive signal was an artefact of the old simulator counting ambiguous
and invalid cases as completed trades. No edge is established.

---

## All responses written this session

| Note | Response |
|------|----------|
| `2026-09-27_primary-experiment-without-human-bias-labels.md` | `...-response.md` |
| `2026-09-27_four-month-baseline-audit.md` | `...-response.md` |
| `2026-09-27_data-integrity-follow-up.md` | `...-response.md` |
| `2026-09-27_execution-and-storage-repair.md` | combined in execution-storage-orb-options |
| `2026-09-27_gold-orb-tradingview-candidate-debate.md` | combined above |
| `2026-09-27_options-gamma-premium-efficiency.md` | combined above |
| `2026-09-27_options-research-evidence-review.md` | combined above |

---

## Decisions made

- Human labelling: optional/exploratory, not a primary gate
- Lane A (brief-based) is September-only — no Jun/Jul/Aug briefs
- Gold feed: synthetic Saturday bars confirmed; all gold results SOURCE_REVIEW_REQUIRED
- `gold_orb_v1`: PARKED pending gold feed verification
- Options: research context only, no V2 action until gold + BTC baseline resolved
- `validate_batch` in `extend_m15_data.py`: reviewed and agreed
- `market_data_io.py` journaled writes: reviewed and agreed (not filesystem-wide atomic)
- Per-instrument split added to `check_strategy.py`

---

## Open items for Codex

1. **Gold feed provenance** — obtain original provider payloads; verify timezone, session
   hours, Saturday bar policy; do not delete existing bars unilaterally
2. **AMBIGUOUS_ENTRY_BAR cases** — 2 BTCUSD anti-bias setups; need deterministic fixtures
   to resolve or classify these correctly
3. **NO_POST_ISSUANCE_DATA cases** — 4 setups; brief issued after all session bars;
   verify brief timestamp integrity
4. **Cost model** — spread/slippage placeholder (BTC 20, XAU 0.30) unverified;
   required before any promotion discussion
5. **Sep-28 outcome** — wakeup loop active, fires after 17:30 UTC Monday
6. **Prospective pilot** — protocol proposed, not activated; needs human sign-off

---

## Do not do

- No new features on blind-mode tool
- No `orb_vwap_v1` or new strategy variants until gold feed resolved and cost model verified
- No LLM label script execution — egress not approved
- No live trading, no schedules, no external API calls
- Do not cite previous positive results — retracted

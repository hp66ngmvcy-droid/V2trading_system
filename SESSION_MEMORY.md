# Session Memory

Local project memory for approved ideas, implementation progress, and operator notes.

## Approved Idea Log

### 2026-05-15 - Phase 2 Validation Sequence

Decision installed: use staged Phase 2 validation.

Order:
1. Phase 2 Standard: continuous parameter search, walk-forward, OOS, parameter stability, KEEP/REVIEW/KILL gates.
2. Paper trading collection: paper-only signal logs, risk gates, health monitor, quant reports.
3. Phase 2 Extended retrofit: DXY/rates/VIX regime labels, correlation stability, regime-specific performance.
4. Phase 3 planning: multi-asset design using regime intelligence.

Rule: macro/regime work is valuable long term, but it must not block the core optimiser and paper-testing loop. One-trade winners are REVIEW only, never KEEP.

### 2026-05-15 - Phase 2 Optimiser Improvement Plan

Installed Claude/Codex joint plan at `docs/PHASE2_OPTIMISER_IMPROVEMENT_PLAN.md`.

Build order:
1. Structural gates and failure logger.
2. Priority queue and expiry.
3. Directional mutation.
4. Walk-forward/OOS auto-wiring.
5. Daily/weekly reports.
6. UI linkage.

Started Priority 1 by adding structural search gates and append-only failure logging. Candidate promotion is now gate-led: minimum trades and drawdown are hard KILL gates, while profit factor, OOS Sharpe, parameter stability, and win rate are REVIEW gates until full walk-forward evidence is wired in.

### 2026-05-15 - Full Pipeline Gate Bypass Fixed

Claude review identified that the main `run-full-pipeline` path still used the composite scorer verdict directly, allowing one-trade winners to print `KEEP` in older batch output. Fixed the full pipeline scoring step and standalone `score-strategy` command so structural gates provide the final verdict.

Also added a safe notional clamp inside the paper backtest engine. The engine no longer opens a fixed `quantity=1.0` for every asset; it caps notional exposure to account scale so BTC/gold/oil paper tests cannot drive equity negative from oversized synthetic positions.

Validation:
- Existing BTCUSD H1 one-trade metrics now score 70.3 but final verdict is `KILL`.
- Gate reason: `SEARCH_MIN_TRADES_NOT_MET`.
- Safe quantity examples: BTC at 50,000 on 10,000 equity uses 0.02 units; XAU at 2,000 uses 0.5; EURUSD remains 1.0.

### 2026-05-15 - Walk-Forward Auto-Wired Into Optimiser

Added automatic walk-forward evidence generation inside `scripts/continuous_parameter_search.py`.

Behaviour:
- Initial backtest runs first.
- Hard KILL gates stop immediately to save time.
- Survivors automatically run walk-forward using local feature data.
- Walk-forward stitched Sharpe is merged into `sharpe_oos`.
- Parameter stability is merged into `param_stability`.
- Final candidate verdict is produced by structural gates with `require_oos=True`.

Also added a hard directional-failure gate for cases like 104 consecutive losses out of 104 trades. Those are now `KILL` even if drawdown is under the hard drawdown threshold.

### 2026-05-23 - Adversarial Review Series (Rounds 8–10)

10 rounds of Codex adversarial review completed. Key fixes applied:

**Scoring pipeline hardened:**
- NaN/inf metrics now return safe defaults (no gate bypass)
- WF KEEP requires `wf_verdict=="KEEP"`, `window_count>=3`, bootstrap CI present with `spans_zero==False`
- Missing CI is a blocking reason, not a pass
- KILL verdict propagates from all 3 scorers (score/gate/multi_agent)

**Backtest correctness:**
- PnL now multiplied by `contract_size` (was off 100x on XAUUSD)
- Trade return basis includes `contract_size` (fixes Sharpe/bootstrap inflation)
- TP/SL loop only applies to matching symbol (no cross-symbol price corruption)
- Final liquidation uses per-symbol last bar, not overall last row
- Risk gate uses `drawdown_marked()` — open-position unrealised PnL now visible

**Walk-forward:**
- Static strategies (identical params every fold) → stability=0 → REVIEW
- Bootstrap CI waiver removed — `spans_zero==True` always forces REVIEW

**From external backtest analysis (XAUUSD M15):**
- Observed: 1.02 PF, 288 trades, 71.53% win rate but 81.74% max drawdown
- Recovery factor 0.08 — drawdown control is the bottleneck, not signal quality
- RSI thresholds 42/58 conservative; test 35–50 range in next optimiser run
- 1:3 RR ratio is sound; position sizing (0.01 lots) limits upside
- Stage 1 priority: broker cost modelling (spreads) will reduce overstated PF

**Test baseline:** 281 passing (2026-05-23).

### 2026-05-23 - Crash Recovery Note

Computer/session crashed after Phase 2 optimiser hardening. Resume from this state:

Completed before crash:
- Main full-pipeline gate bypass fixed in `src/tar_system/cli.py`.
- Standalone `score-strategy` now uses structural gates for the final verdict.
- Paper backtest position sizing was clamped in `src/tar_system/backtest/engine.py` so BTC/gold/oil tests cannot use oversized fixed `quantity=1.0` positions.
- Structural gates added in `src/tar_system/scoring/gates.py`.
- Failure/review logging added in `src/tar_system/scoring/failure_logger.py`.
- Optimiser walk-forward auto-wiring added in `scripts/continuous_parameter_search.py`.
- Directional failure gate added for cases such as 104 consecutive losses out of 104 trades.
- Focused tests passed before crash: `33 passed`.

Important current rules:
- One-trade winners are hard `KILL`, not `KEEP` or lucky `REVIEW`.
- Missing walk-forward/OOS evidence prevents `KEEP`.
- Hard gates: minimum trades, max drawdown, directional failure.
- Soft gates: profit factor, OOS Sharpe, parameter stability, win rate.
- Keep everything paper-only and local-first.

Next safe resume command:

```bash
cd /Users/whs1/Dev/V2trading_system

PYTHONPATH=src venv/bin/python scripts/continuous_parameter_search.py \
  --reset \
  --symbols XAUUSD,EURUSD,GBPUSD \
  --timeframes M15,M30,H1 \
  --max-generations 3 \
  --max-candidates 50 \
  --max-rows 0 \
  --survivors 8 \
  --target-keeps 3 \
  --min-trades-for-keep 30 \
  --wf-train-months 12 \
  --wf-test-months 3 \
  --max-walk-forward-splits 12
```

Downloaded `.py` strategy ideas should go first into `ideas/inbox/attachments/`, with a matching review note in `ideas/inbox/`. Do not place unreviewed downloaded strategy files directly into `src/tar_system/strategies/`.

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

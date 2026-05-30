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

### 2026-05-23 - MT5 Parameter Testing Protocol (Post-Failure)

5 simultaneous parameter changes caused a blowup: 1 trade, 0.00 PF, -2.85 GBP.

Changes that broke it (applied together):
- RSI period 20→14 (more noise)
- SL 2.0x→1.5x ATR (too tight for XAUUSD M15 volatility)
- Spread filter 30→15 pts (excluded most tradeable time)
- Session start 7→8 UTC (missed morning volatility)
- Session end 20→17 UTC (missed US session)

**Rule: ONE change at a time. Backtest between each change.**

Correct test sequence for RSITrendV4:
1. EMA slope gate only → backtest → verify trade count holds
2. If stable → test spread 30→20 pts → backtest → check trade count
3. If stable → test session tighten → backtest
4. If stable → test SL 2.0→1.8x → backtest
5. RSI levels last — most sensitive to trade count

XAUUSD M15 floors:
- SL minimum: 2.0x ATR (1.5x causes excessive stops)
- Spread: 20 pts safe; 15 pts may exclude high-volatility periods
- Session: 7–20 UTC baseline; narrow cautiously

### 2026-05-23 - Confirmed Baseline Parameters (XAUUSD M15, APPROVED)

Test ID: XAUUSD_M15_20260415 — DO NOT CHANGE THESE until each stage completes.

```
RSI Period:     20       (NOT 14 — 14 increases noise)
RSI Buy:        42
RSI Sell:       58
EMA Fast:       12
EMA Slow:       26
ATR Period:     14
SL Multiplier:  2.0x ATR (NOT 1.5 — floor confirmed by failure test)
TP Multiplier:  3.0x
Risk:           1.0% per trade
Lot size:       0.01
Session:        07:00-20:00 UTC (NOT 8-17 — caused trade collapse)
Spread filter:  30 pts (NOT 15 — excluded 60%+ of trades)
Slippage:       20 pts
```

Results: 288 trades, 71.53% win rate, PF 1.02, DD 81.74%, +39.64 GBP.
Signal quality STRONG. Drawdown is the only problem.

### 2026-05-23 - Stage Progression Roadmap

**Current:** Pre-Stage 1 (baseline documented, EMA slope gate added to MT5)

| Stage | Task | Target | Status |
|-------|------|--------|--------|
| 1 | Broker cost modelling | Add real spreads/commission to backtest | ⏳ NEXT |
| 2 | Volatility gates | ATR-based position size reduction; target DD < 40% | — |
| 3 | Session filter validation | London/US overlap windows | — |
| 4 | Parameter isolation | One-at-a-time sweeps (RSI, EMA, SL, TP) | — |
| 5 | Position sizing | Kelly/fixed fractional; cap DD < 30% | — |
| 6 | Second strategy | RSI mean reversion (shorts 21.93% vs longs 32.76%) | — |
| 7 | Dashboard | Real-time monitoring | — |
| 8 | Autonomous controller | Auto parameter sweep + live WF validation | — |

Stage 4 isolation order (when reached):
1. RSI Period: test [14, 18, 20, 24, 28] — one at a time, all else frozen
2. SL Multiplier: test [1.8, 2.0, 2.2, 2.5]
3. Session: test [7-18, 7-19, 7-20, 8-20]
4. Spread filter: test [20, 25, 30] — after session confirmed
5. RSI levels: test [38/62, 40/60, 42/58] — last, most sensitive

### 2026-05-23 - MT5 Research Sanity Check Added

Added `scripts/mt5_research_sanity_check.py` to prove the core research plumbing before chasing strategy profitability.

Purpose:
- Compare selected local MT5 raw CSV files against the research artifacts.
- Run the real CLI path: import CSV, validate data, build features, backtest, walk-forward, score, and forward-test.
- Write review outputs to `reports/mt5_research_sanity_check.json` and `reports/mt5_research_sanity_check.md`.

Default cross-section:
- XAUUSD M15
- EURUSD M15
- GBPUSD H1
- BTCUSD H1
- USOUSD M30

Use `--dry-run` first to inspect planned commands without crunching data.

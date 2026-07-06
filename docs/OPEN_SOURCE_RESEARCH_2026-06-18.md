# V2 TAR — Open-Source Research Report 2026-06-18

Researched by autonomous agent. Approved items marked ✅.

## Key Correction on Regime Detection

The regime detector IS wired — `detect_regime()` is called in backtest engine,
forward-test engine, paper signal runner, and CLI. The detector itself is the
weak link: requires all 6 features non-null (strict), returns `UNKNOWN` for
most bars due to hard-coded thresholds.

Bootstrap CI gate is a **soft gate** (produces REVIEW, not KILL). The 591
failures are primarily driven by hard `min_trades` and `profit_factor < 1.40`.

---

## Ranked Recommendations

### ✅ DONE — Deflated Sharpe Ratio (DSR)

Implemented in `src/tar_system/validation/bootstrap_ci.py` as
`deflated_sharpe_ratio(trade_returns, n_trials=N)`.

Adjusts Sharpe for selection bias when N strategies are tested. Replaces or
augments blunt `spans_zero` check. Low `dsr_p_value` (<0.05) = genuinely
unlikely to be noise after N-trial correction. Pure numpy, no scipy.

---

### 1. `hmmlearn` — Hidden Markov Model Regime Detector
**Value: HIGH | Effort: Low | Addresses: UNKNOWN-dominated regime labels**

Replace or layer under `detector.py` with `GaussianHMM` on
(returns, ATR, volume) → 3 hidden states mapping to TRENDING/RANGING/VOLATILE.

- Eliminates the strict 6-feature null requirement
- States map onto existing `Regime` enum — no gate changes needed
- Add as `detector_hmm.py` alongside existing `detector.py`

```bash
pip install hmmlearn  # ~2 MB, MIT, pure Python/numpy
```

---

### 2. `ruptures` — Changepoint Walk-Forward Splits
**Value: HIGH | Effort: Low-Med | Addresses: OOS Sharpe variance / CI width**

Use `Binseg` or `Pelt` to find structural break dates in XAUUSD M15 returns.
Replace calendar-based WF splits with regime-break-aligned splits.

- Boundaries at real structural breaks → less cross-regime contamination
- Reduces CI width from artificially inflated OOS Sharpe variance
- Off-line only (preprocessing pass, not real-time)

```bash
pip install ruptures  # MIT, ~1 MB
```

---

### 3. CPCV — Combinatorial Purged Cross-Validation
**Value: HIGH | Effort: Med | Addresses: CI gate calibration**

Bailey & Lopez de Prado. Generates multiple non-overlapping backtest paths,
computes Probability of Backtest Overfitting (PBO, 0–1). PBO < 0.5 = pass.
Replaces blunt `spans_zero` check with calibrated overfitting probability.

Implement directly from paper (~150 lines) — avoid mlfinlab forks (unmaintained).
Reference: https://www.quantbeckman.com/p/with-code-combinatorial-purged-cross

---

### 4. FRED API — Macro Regime Context (Free)
**Value: HIGH | Effort: Low | Addresses: Regime detection quality**

Free REST API, 845k+ series. Key series for XAUUSD:
- `VIXCLS` — VIX (fear/complacency regime)
- `T10Y2Y` — yield curve slope (macro trend signal)
- `GOLDAMGBD228NLBD` — daily gold spot (sanity cross-check)
- `DFF` — Fed funds rate

One-time weekly fetch → `data/raw/macro/fred_macro.csv`. Feed VIX + yield
slope into regime features. Fully offline after fetch.

Requires free API key: https://fred.stlouisfed.org/docs/api/api_key.html

---

### 5. `VectorBT` — Pre-screening Layer
**Value: HIGH | Effort: Med | Addresses: 591 failed jobs**

Vectorized parameter sweeps over XAUUSD M15 in seconds. Use as a pre-screen
before committing candidates to the V2 gate pipeline. Identifies which
parameter regions have any Sharpe/PF signal before full WF+bootstrap.

```bash
pip install vectorbt  # MIT free tier
```

---

### 6. `PyBroker` — Walk-Forward Backtester
**Value: HIGH | Effort: Med | Addresses: OOS metric calibration**

Expanding-window WF with retrain per fold. More stable bootstrapped Sharpe
with small N than current percentile bootstrap. Evaluate on `gold_v2` first.

---

### 7. arXiv 2601.19504 — Hybrid AI Regime-Adaptive Architecture
**Value: MEDIUM | Effort: Read-only | Addresses: Strategy design**

"Generating Alpha: A Hybrid AI-Driven Trading System" (Jan 2026).
EMA momentum + RSI/BB mean-reversion + XGBoost regime classifier.
XGBoost meta-layer to classify regime-strategy combo is directly applicable
to V2's existing feature set.

Note: equity data, not XAUUSD. Do not adopt return numbers as benchmarks.

---

### 8. FirstRateData — 20yr XAUUSD M15 History
**Value: MEDIUM | Effort: Low (purchase) | Addresses: Statistical power**

~$20 one-time. 20yr M15 XAUUSD covers 2008 crisis, 2011 gold peak, 2020 COVID,
2022–2024 rate cycle. Dramatically increases WF fold count → reduces CI width.
Store in `data/raw/`. Verify format compatibility before purchase.

---

### 9. NautilusTrader — Tick-Level Engine (Long-Term)
**Value: MEDIUM | Effort: High | For: If V2 moves to tick data**

Python/Rust, 9.1k stars, Apache 2.0. Not worth integrating now. Add to
long-term ideas queue for multi-asset phase.

---

## Immediate Action Sequence

1. **DSR** ✅ Done — `deflated_sharpe_ratio()` in `bootstrap_ci.py`
2. **Regime fix** — Add `detector_hmm.py` with `hmmlearn` (install approval needed)
3. **FRED macro** — One-time fetch script to `data/raw/macro/fred_macro.csv` (needs free API key)
4. **Changepoint WF splits** — Add `ruptures` preprocessing pass (install approval needed)
5. **VectorBT pre-screen** — Pre-filter 591 failed jobs before re-queuing

---

## Sources

- GitHub algorithmic-trading topic by stars
- merovinh/best-of-algorithmic-trading
- wangzhe3224/awesome-systematic-trading
- edtechre/pybroker, polakowo/vectorbt, deepcharles/ruptures
- FRED API: fred.stlouisfed.org
- arXiv 2601.19504
- Bailey & Lopez de Prado (2014) SSRN
- QuantBeckman CPCV implementation

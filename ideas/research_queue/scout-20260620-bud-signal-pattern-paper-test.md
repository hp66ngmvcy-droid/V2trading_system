# BUD Signal Pattern Scout - Paper-Test Candidate

Date: 2026-06-20
Status: research input only
Source: public product pages at `https://budsignal.io/`, `https://budsignal.io/terms`, and `https://budsignal.io/privacy`

## Safety Classification

This is not a recommendation to subscribe, trade, scrape, reverse engineer, or
connect money.

Use only the public product pattern as inspiration:

- one clear market state,
- transparent paper logging,
- entry-only signal framing,
- quiet/no-trade state,
- alerts only after alignment.

Do not copy BUD Signal branding, copy, dashboard design, pricing, referral
model, proprietary scoring, signal logic, thresholds, or paid content.

No exchange keys. No broker keys. No withdrawal permissions. No live trading.
No Telegram automation until separately approved.

## Public Pattern Observed

BUD Signal presents a simple Bitcoin market read:

- `LONG`,
- `SHORT`,
- `WAIT`.

The public pitch says it simplifies several categories of trader inputs:

- pressure,
- momentum,
- liquidity.

It positions itself around BTC swing trading on the 4H timeframe, with alert
delivery and a visible track record. The useful engineering lesson is not the
specific signal; it is the product discipline:

- reduce dashboard noise into one readable state,
- keep `WAIT` as a first-class output,
- separate entry detection from exit/risk management,
- show historical signal outcomes,
- make limitations explicit.

## V2 Translation

Create a local paper-only `ClearReadSignalLayer` concept.

Inputs should come only from existing local V2 data/features at first:

- momentum state: trend slope, EMA structure, RSI/MACD-like measures if already
  available,
- pressure proxy: candle body/close location, volume/ATR expansion, recent
  breakout or failed breakout behavior,
- liquidity proxy: prior rolling high/low sweep, ATR distance to recent range,
  spread/slippage assumptions where available,
- regime state: existing V2 regime detector output,
- risk state: existing V2 risk gate output.

Output:

```json
{
  "side": "LONG | SHORT | WAIT",
  "confidence": 0.0,
  "reasons": [],
  "entry_reference": null,
  "risk_approved": false,
  "risk_reason": "PAPER_ONLY_REVIEW",
  "paper_only": true
}
```

Naming note: use `LONG`/`SHORT`/`WAIT` for the UI/read layer if useful, but map
to V2's existing internal signal side conventions where required.

## Testable Hypothesis

A composite clear-read layer should improve operator decision quality by
reducing noisy signals, not by claiming prediction.

Primary hypothesis:

> When pressure, momentum, liquidity, regime, and risk checks align, the paper
> signal log should show fewer but cleaner candidate entries than a raw
> single-indicator trigger.

Secondary hypothesis:

> `WAIT` should be treated as a positive safety decision, not as a missed trade.

## MVP Paper Test

### Step 1 - Feature Audit

Find which inputs already exist:

- `prior_rolling_high`,
- `prior_rolling_low`,
- `atr`,
- trend/regime state,
- volume features,
- spread/slippage cost model,
- risk approval reason codes.

Pass condition:

- no new dependency,
- no external data requirement,
- no broker/exchange/API key.

### Step 2 - Read-Only Prototype

Implement a pure function first, not a new strategy:

```text
market_row + regime + risk_context -> clear_read
```

Rules:

- outputs paper-only JSON,
- no order object,
- no execution path,
- no MT5 export,
- all failures return `WAIT` with reason codes.

### Step 3 - Backtest/Replay Comparison

Replay over existing local BTC, XAUUSD, or major FX data where available.

Compare:

- raw strategy signal count,
- clear-read signal count,
- percentage of `WAIT`,
- favorable excursion after entry reference,
- adverse excursion after entry reference,
- drawdown if naively paper-followed,
- cost sensitivity,
- missed-move review.

Pass condition:

- enough observations for review,
- stable behavior across at least two market regimes,
- no one-trade winner promotion.

### Step 4 - Track Record Artifact

Create a local paper artifact:

```text
runtime/clear_read_signal_history.jsonl
```

Each row should include:

- timestamp,
- symbol,
- timeframe,
- side,
- confidence,
- reason codes,
- entry reference,
- max favorable move after N bars,
- max adverse move after N bars,
- tracked-until timestamp,
- paper-only flag.

This borrows the public "track record" discipline while keeping it local and
auditable.

## Product/UI Idea

Add a simple dashboard tile:

```text
Current clear read
WAIT
Reason: liquidity and momentum not aligned
Paper-only. No live trading.
```

Good UI behavior:

- big state label,
- reason codes visible,
- no profit hype,
- no urgent CTA,
- `WAIT` shown calmly,
- recent paper outcomes shown below the current read.

Bad UI behavior:

- "guaranteed",
- "win rate" headline without sample/context,
- live-order buttons,
- leverage prompts,
- exchange connection prompts.

## Rejection Gates

Reject or pause this idea if:

- it needs exchange/broker keys,
- it relies on paid/private BUD Signal content,
- it copies proprietary scoring or wording,
- it produces too few observations,
- it improves headline win rate by hiding losses or adverse excursion,
- it cannot explain each `LONG`, `SHORT`, or `WAIT` with local reason codes,
- it encourages live trading before paper-forward evidence exists.

## Recommended Next Action

Do a no-code audit first:

1. list existing V2 features that map to pressure, momentum, liquidity, regime,
   and risk,
2. decide whether BTC data exists locally at a useful timeframe,
3. draft the pure-function rule table,
4. only then consider implementation behind a `paper_only` gate.

Manager sign-off state: `IDEA_READY_FOR_NO_CODE_AUDIT`.

## Initial Local Fit Audit

Date: 2026-06-20

The V2 repository already appears to have enough local surface area for a
paper-only first test.

Available local feature/data candidates:

- `data/features/BTCUSD_M1.parquet`
- `data/features/BTCUSD_M5.parquet`
- `data/features/BTCUSD_M15.parquet`
- `data/features/BTCUSD_M30.parquet`
- `data/features/BTCUSD_H1.parquet`
- XAUUSD, GBPUSD, EURUSD, USDCAD, USDJPY, AUDUSD, USOUSD feature files for
  cross-asset sanity checks.

Existing feature/rule surfaces found:

- `ema_fast`, `ema_slow`, `ema_fast_slope`, `ema_slow_slope`
- `rsi`
- `atr`, `atr_median_50`
- `volume`, `volume_sma`
- `prior_rolling_high`, `prior_rolling_low`
- regime detector output: `TRENDING`, `RANGING`, `VOLATILE`, `UNKNOWN`
- strategy reason codes such as `EMA_SLOPE_TOO_FLAT`,
  `ATR_TOO_HIGH_EXTREME_VOLATILITY`, `REGIME_FILTER_BLOCK`
- paper risk result fields: `risk_approved`, `risk_reason`

Suggested first local test:

```text
Symbol: BTCUSD
Timeframes: H1 first, then M30 and M15 if H1 behaves sanely
Mode: read-only/paper-only replay
Prototype: pure clear-read function only
Comparison baseline: existing BTCUSD strategy result logs where available
Output artifact: runtime/clear_read_signal_history.jsonl
```

Fit verdict:

`LOCAL_TEST_FEASIBLE_WITHOUT_NEW_DEPENDENCY`

Remaining block before implementation:

- define the first rule table,
- verify exact feature columns in BTCUSD parquet files,
- decide whether the first replay uses H1 only or H1 plus M30/M15 confirmation,
- keep this outside live execution and MT5 export paths.

## Feature Column Audit

Date: 2026-06-20

Command used:

```text
venv/bin/python -c "import pandas as pd; ... read BTCUSD H1/M30/M15 parquet columns ..."
```

Sandbox note:

- PyArrow printed restricted `sysctlbyname` CPU-probe warnings, but the parquet
  reads completed and returned row/column metadata.

BTCUSD local files:

| File | Rows | Date range | Fit |
| --- | ---: | --- | --- |
| `data/features/BTCUSD_H1.parquet` | 26,956 | 2022-12-07 to 2026-02-08 | Best first test |
| `data/features/BTCUSD_M30.parquet` | 87,491 | 2020-11-16 to 2026-05-01 | Needs feature rebuild or reduced rule set |
| `data/features/BTCUSD_M15.parquet` | 100,000 | 2023-03-02 to 2026-02-08 | Good confirmation test |

Column findings:

- H1 has the full desired first-pass feature surface:
  - OHLCV/spread,
  - `ema_fast`, `ema_slow`, `ema_fast_slope`, `ema_slow_slope`,
  - `rsi`,
  - `atr`, `atr_median_50`,
  - `macd`, `macd_signal`,
  - `rolling_volatility`,
  - `volume_sma`,
  - `prior_rolling_high`, `prior_rolling_low`,
  - `bb_width`, `price_in_band`, `range_compression`,
  - `hour_utc`, `session_label`, `is_liquid_session`.
- M15 also has the full desired first-pass feature surface.
- M30 is missing at least:
  - `volume_sma`,
  - `prior_rolling_high`,
  - `prior_rolling_low`,
  - `hour_utc`.

Updated test scope:

```text
First replay: BTCUSD_H1 only
Second replay: BTCUSD_M15 confirmation
Defer: BTCUSD_M30 until features are rebuilt or the rule table is simplified
```

## First Rule Table Draft

This is deliberately simple and explainable. It is not a strategy yet; it is a
paper-only read layer.

### Shared Blocks

Return `WAIT` immediately when:

- any required column is missing,
- regime is `VOLATILE` or `UNKNOWN`,
- `atr <= 0`,
- `close <= 0`,
- data freshness or timestamp parsing fails,
- paper risk gate is blocked, if a risk context is supplied.

### Momentum Read

Bullish momentum when:

- `ema_fast > ema_slow`,
- `ema_fast_slope > 0`,
- `rsi >= 55`,
- `macd >= macd_signal`.

Bearish momentum when:

- `ema_fast < ema_slow`,
- `ema_fast_slope < 0`,
- `rsi <= 45`,
- `macd <= macd_signal`.

Otherwise momentum is mixed and should support `WAIT`.

### Pressure Read

Bullish pressure when:

- candle closes above its open,
- close is in the upper 40% of the bar range,
- volume is above `volume_sma` where available.

Bearish pressure when:

- candle closes below its open,
- close is in the lower 40% of the bar range,
- volume is above `volume_sma` where available.

If volume is unavailable, pressure can still be read from candle position but
confidence should be capped.

### Liquidity Read

Bullish liquidity setup when:

- low sweeps below `prior_rolling_low`,
- close returns above `prior_rolling_low`,
- lower wick is at least 35% of the bar range.

Bearish liquidity setup when:

- high sweeps above `prior_rolling_high`,
- close returns below `prior_rolling_high`,
- upper wick is at least 35% of the bar range.

If no sweep occurs, liquidity is neutral and the clear read should normally be
`WAIT`, unless a later version adds a separate trend-continuation mode.

### Output Decision

Return `LONG` when:

- momentum is bullish,
- pressure is bullish,
- liquidity is bullish,
- regime is not blocked,
- confidence >= 0.65.

Return `SHORT` when:

- momentum is bearish,
- pressure is bearish,
- liquidity is bearish,
- regime is not blocked,
- confidence >= 0.65.

Return `WAIT` for all disagreement, missing evidence, low confidence, blocked
regime, blocked risk, or mixed reads.

### Confidence Draft

Start at `0.0`, then add:

- `0.30` for momentum alignment,
- `0.25` for pressure alignment,
- `0.30` for liquidity sweep/reclaim alignment,
- `0.10` for `TRENDING` regime,
- `0.05` for liquid session.

Caps:

- cap at `0.60` if volume confirmation is unavailable,
- cap at `0.60` if regime is `RANGING`,
- cap at `0.0` and output `WAIT` if regime/risk/data blocks fire.

First implementation should include reason codes for every add, cap, and block.

## Next Build Step

Implement a small pure module and test only:

```text
src/tar_system/signals/clear_read.py
tests/test_clear_read_signal.py
```

Do not register it as a strategy yet. Do not add CLI, scheduler, dashboard,
Telegram, MT5, broker, exchange, or live-action paths in the first build.

## Paper Test 0 - Pure Read Layer Added

Date: 2026-06-20

Files added:

- `src/tar_system/signals/__init__.py`
- `src/tar_system/signals/clear_read.py`
- `tests/test_clear_read_signal.py`

Scope:

- pure `market_row + regime + optional paper risk context -> ClearRead`,
- output side is only `LONG`, `SHORT`, or `WAIT`,
- `paper_only` is always true,
- no strategy registration,
- no CLI,
- no dashboard,
- no scheduler,
- no Telegram,
- no MT5 export,
- no broker or exchange path.

Validation:

```text
PYTHONPATH=src venv/bin/python -m pytest tests/test_clear_read_signal.py
Result: 7 passed

PYTHONPATH=src venv/bin/python -m compileall src/tar_system/signals
Result: pass
```

Read-only BTCUSD H1 replay count:

```text
Rows tested: 26,935
LONG: 0
SHORT: 0
WAIT: 26,935
```

Interpretation:

The first strict rule table is safe but too restrictive for a useful standalone
paper signal. It requires momentum, pressure, and liquidity sweep/reclaim to all
align. On BTCUSD H1, liquidity sweeps are rare and normally do not align with
momentum at the same bar.

Component counts:

```text
Momentum: BULLISH 6,910 / BEARISH 6,273 / MIXED 13,340
Pressure: BULLISH 3,977 / BEARISH 3,923 / MIXED 18,623
Liquidity: BULLISH 876 / BEARISH 951 / NEUTRAL 24,696
```

Top combinations show the main blocker:

```text
TRENDING + BULLISH momentum + BULLISH pressure + NEUTRAL liquidity: 1,136
TRENDING + BEARISH momentum + BEARISH pressure + NEUTRAL liquidity: 1,055
```

Manager review:

`KEEP_AS_SAFE_BASELINE_BUT_DO_NOT_PROMOTE`

Next paper-only decision:

- Option A: keep strict liquidity sweep mode as a rare reversal/entry-quality
  filter.
- Option B: add a second explicit `TREND_CONTINUATION` read where liquidity can
  be neutral, but confidence is lower and adverse/favorable excursion must be
  tracked before any UI or alert idea.

Recommended next test:

Build a read-only replay report, not a live signal artifact, comparing:

- strict sweep mode,
- trend-continuation candidate mode,
- all as paper-only,
- with max favorable/adverse movement after 4, 8, and 24 H1 bars.

## Paper Test 1 - Trend Continuation Replay Added

Date: 2026-06-20

Files added/updated:

- `src/tar_system/signals/clear_read.py`
- `src/tar_system/signals/clear_read_replay.py`
- `tests/test_clear_read_signal.py`
- `tests/test_clear_read_replay.py`

Scope:

- added `generate_trend_continuation_read(...)` as a paper-only comparison
  candidate,
- added `compare_clear_read_modes(...)` for in-memory read-only replay
  summaries,
- no runtime artifact is written,
- no CLI, scheduler, dashboard, alerts, Telegram, MT5, broker, exchange, or live
  path.

Validation:

```text
PYTHONPATH=src venv/bin/python -m pytest tests/test_clear_read_signal.py tests/test_clear_read_replay.py
Result: 8 passed

PYTHONPATH=src venv/bin/python -m compileall src/tar_system/signals
Result: pass
```

Read-only BTCUSD H1 comparison:

```text
Rows tested: 26,935
Horizons: 4, 8, 24 H1 bars
```

Strict sweep mode:

```text
LONG: 0
SHORT: 0
WAIT: 26,935
```

Trend-continuation candidate mode:

```text
LONG: 1,136
SHORT: 1,055
WAIT: 24,744
```

Movement summary:

| Side | Horizon | Count | Avg favorable % | Avg adverse % | Median favorable % | Median adverse % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LONG | 4 | 1,136 | 0.9877 | 0.8291 | 0.6474 | 0.6014 |
| LONG | 8 | 1,135 | 1.3560 | 1.0934 | 0.8902 | 0.7974 |
| LONG | 24 | 1,130 | 2.2929 | 1.7992 | 1.5398 | 1.3318 |
| SHORT | 4 | 1,055 | 1.1111 | 0.8858 | 0.6791 | 0.6857 |
| SHORT | 8 | 1,055 | 1.5248 | 1.1827 | 0.9573 | 0.9288 |
| SHORT | 24 | 1,055 | 2.4199 | 2.1535 | 1.7090 | 1.5879 |

Interpretation:

Trend continuation creates enough observations for a real paper study. The
average favorable movement is larger than average adverse movement across each
tested horizon, but the gap is not strong enough for promotion. This is still
only an exploratory read layer and says nothing about stops, exits, costs,
slippage, drawdown, or capital efficiency.

Manager review:

`KEEP_FOR_NEXT_PAPER_REPLAY_REPORT`

Next paper-only decision:

- add cost/slippage proxy,
- add simple fixed horizon exit comparison,
- compare H1 against M15 confirmation,
- keep strict sweep and trend continuation as separate modes so the system does
  not hide a loose trend rule under a high-quality liquidity-sweep label.

## Paper Test 2 - Cost And Fixed-Horizon Exit Check

Date: 2026-06-20

Files updated:

- `src/tar_system/signals/clear_read_replay.py`
- `tests/test_clear_read_replay.py`

Scope:

- added a simple cost/slippage proxy to replay summaries,
- added fixed-horizon net exit return after 4, 8, and 24 H1 bars,
- added `win_rate_after_cost`,
- still no runtime artifact writing,
- still no strategy registration, CLI, scheduler, dashboard, alerts, Telegram,
  MT5, broker, exchange, or live path.

Assumption:

```text
cost_bps: 10.0
```

Validation:

```text
PYTHONPATH=src venv/bin/python -m pytest tests/test_clear_read_signal.py tests/test_clear_read_replay.py
Result: 8 passed

PYTHONPATH=src venv/bin/python -m compileall src/tar_system/signals
Result: pass
```

Read-only BTCUSD H1 cost-adjusted result:

| Mode | Side | Horizon | Count | Avg net exit % | Median net exit % | Win rate after cost |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| strict_sweep | LONG | 4/8/24 | 0 | 0.0000 | 0.0000 | 0.0000 |
| strict_sweep | SHORT | 4/8/24 | 0 | 0.0000 | 0.0000 | 0.0000 |
| trend_continuation | LONG | 4 | 1,136 | -0.0113 | -0.1732 | 0.4243 |
| trend_continuation | LONG | 8 | 1,135 | 0.0630 | -0.1435 | 0.4493 |
| trend_continuation | LONG | 24 | 1,130 | 0.2864 | -0.0793 | 0.4894 |
| trend_continuation | SHORT | 4 | 1,055 | -0.0861 | -0.2436 | 0.4000 |
| trend_continuation | SHORT | 8 | 1,055 | -0.1070 | -0.2621 | 0.4047 |
| trend_continuation | SHORT | 24 | 1,055 | -0.2872 | -0.4543 | 0.4275 |

Interpretation:

The first cost-adjusted exit check is not strong enough for strategy promotion.
Trend-continuation LONG has a weak positive average at 8 and 24 bars, but median
net exit remains negative and win rate after cost stays below 50%. SHORT is
negative across all tested horizons.

Manager review:

`DO_NOT_PROMOTE_KEEP_RESEARCH_ONLY`

Next paper-only question:

- Is the LONG side improved by M15 confirmation?
- Should SHORT be blocked entirely for this BTCUSD H1 version?
- Should the replay add drawdown/equity sequencing before any more feature work?

## Paper Test 3 - M15 Confirmation Gate

Date: 2026-06-20

Files updated:

- `src/tar_system/signals/clear_read_replay.py`
- `tests/test_clear_read_replay.py`

Scope:

- added a separate `trend_continuation_m15_confirmed` replay mode,
- confirmation requires lower-timeframe trend-continuation agreement in the
  previous 60 minutes,
- still no runtime artifact writing,
- still no strategy registration, CLI, scheduler, dashboard, alerts, Telegram,
  MT5, broker, exchange, or live path.

Validation:

```text
PYTHONPATH=src venv/bin/python -m pytest tests/test_clear_read_signal.py tests/test_clear_read_replay.py
Result: 9 passed

PYTHONPATH=src venv/bin/python -m compileall src/tar_system/signals
Result: pass
```

Read-only BTCUSD H1 plus BTCUSD M15 comparison:

```text
Primary rows: 26,935 H1 bars
Confirmation source: BTCUSD M15 feature data
Cost proxy: 10 bps
Horizons: 4, 8, 24 H1 bars
```

Signal counts:

| Mode | LONG | SHORT | WAIT |
| --- | ---: | ---: | ---: |
| trend_continuation | 1,136 | 1,055 | 24,744 |
| trend_continuation_m15_confirmed | 76 | 90 | 26,769 |

M15-confirmed movement summary:

| Side | Horizon | Count | Avg net exit % | Median net exit % | Win rate after cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| LONG | 4 | 76 | -0.1174 | -0.3211 | 0.4211 |
| LONG | 8 | 76 | -0.0952 | -0.2082 | 0.4079 |
| LONG | 24 | 76 | -0.0008 | -0.1887 | 0.4737 |
| SHORT | 4 | 90 | -0.3273 | -0.4627 | 0.3000 |
| SHORT | 8 | 90 | -0.2480 | -0.3913 | 0.3778 |
| SHORT | 24 | 90 | -0.9502 | -1.0648 | 0.3556 |

Interpretation:

The M15 confirmation gate does not improve this idea. It reduces sample size
from 2,191 total trend-continuation candidates to 166 confirmed candidates, and
the cost-adjusted fixed-horizon results are still weak. LONG becomes roughly
flat only at 24 H1 bars on average, with negative median net return. SHORT gets
worse and remains unsuitable.

Manager review:

`REJECT_M15_CONFIRMATION_FOR_THIS_VERSION`

Updated paper-only decisions:

- Do not use the M15 confirmation gate in this form.
- Block SHORT for this BTCUSD H1 version unless a future rule explains why it
  should be revisited.
- Do not promote the LONG side; it needs equity sequencing/drawdown review and
  a better exit idea before any strategy-candidate discussion.

## Paper Test 4 - LONG-Only Equity Sequencing

Date: 2026-06-20

Files updated:

- `src/tar_system/signals/clear_read_replay.py`
- `tests/test_clear_read_replay.py`

Scope:

- added non-overlapping fixed-horizon equity sequencing,
- tested LONG and SHORT separately,
- still no runtime artifact writing,
- still no strategy registration, CLI, scheduler, dashboard, alerts, Telegram,
  MT5, broker, exchange, or live path.

Validation:

```text
PYTHONPATH=src venv/bin/python -m pytest tests/test_clear_read_signal.py tests/test_clear_read_replay.py
Result: 11 passed

PYTHONPATH=src venv/bin/python -m compileall src/tar_system/signals
Result: pass
```

Read-only BTCUSD H1 fixed-horizon sequencing:

```text
Cost proxy: 10 bps
Trade model: non-overlapping entries, fixed horizon exit
Sizing: unit paper equity compounding, research proxy only
```

| Side | Horizon | Trades | Cumulative return % | Max drawdown % | Win rate | Avg trade % | Median trade % | Profit factor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LONG | 4 | 697 | -37.5944 | 54.0992 | 0.4032 | -0.0593 | -0.1897 | 0.8745 |
| LONG | 8 | 528 | -17.0102 | 47.2235 | 0.4129 | -0.0214 | -0.2421 | 0.9639 |
| LONG | 24 | 362 | 50.7563 | 34.0307 | 0.4641 | 0.1518 | -0.4067 | 1.1635 |
| SHORT | 4 | 634 | -45.8484 | 57.7515 | 0.3959 | -0.0889 | -0.2676 | 0.8205 |
| SHORT | 8 | 475 | -42.7412 | 59.4779 | 0.4105 | -0.1031 | -0.2198 | 0.8379 |
| SHORT | 24 | 320 | -58.7050 | 70.1631 | 0.4188 | -0.2395 | -0.4639 | 0.7861 |

Interpretation:

SHORT is rejected for this version. LONG only shows a positive cumulative result
at the 24-bar horizon, but it comes with high drawdown, sub-50% win rate, and a
negative median trade. That shape suggests occasional larger winners, not a
stable edge. This is not promotion-ready.

Manager review:

`DO_NOT_PROMOTE_RESEARCH_LONG_24_ONLY`

Updated paper-only decisions:

- Reject SHORT for BTCUSD H1 clear-read trend continuation v0.
- Reject 4-bar and 8-bar LONG exits.
- Keep 24-bar LONG as a research-only candidate for a stricter drawdown-control
  experiment.
- Next useful paper test should add a drawdown/volatility block before entry,
  not more signal complexity.

## Paper Test 5 - Volatility Entry Block

Date: 2026-06-20

Files updated:

- `src/tar_system/signals/clear_read_replay.py`
- `tests/test_clear_read_replay.py`

Scope:

- added optional paper replay entry filters:
  - `max_rolling_volatility`,
  - `max_atr_pct`,
- tested BTCUSD H1 LONG-only, 24-bar fixed exit, 10 bps cost proxy,
- still no runtime artifact writing,
- still no strategy registration, CLI, scheduler, dashboard, alerts, Telegram,
  MT5, broker, exchange, or live path.

Validation:

```text
PYTHONPATH=src venv/bin/python -m pytest tests/test_clear_read_signal.py tests/test_clear_read_replay.py
Result: 12 passed

PYTHONPATH=src venv/bin/python -m compileall src/tar_system/signals
Result: pass
```

Read-only BTCUSD H1 LONG 24-bar volatility sweep:

| Filter | Trades | Cumulative return % | Max drawdown % | Win rate | Avg trade % | Median trade % | Profit factor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| base | 362 | 50.7563 | 34.0307 | 0.4641 | 0.1518 | -0.4067 | 1.1635 |
| rolling volatility <= 0.010 | 351 | 77.4542 | 25.9709 | 0.4672 | 0.2007 | -0.3547 | 1.2256 |
| rolling volatility <= 0.008 | 345 | 91.5803 | 22.4607 | 0.4696 | 0.2255 | -0.3450 | 1.2599 |
| rolling volatility <= 0.006 | 307 | 90.2998 | 19.4443 | 0.4625 | 0.2463 | -0.4019 | 1.2915 |
| ATR/close <= 0.015 | 355 | 66.2260 | 25.9709 | 0.4676 | 0.1803 | -0.3751 | 1.1998 |
| ATR/close <= 0.012 | 347 | 97.3474 | 25.9709 | 0.4697 | 0.2324 | -0.3547 | 1.2685 |
| rolling vol <= 0.008 + ATR/close <= 0.015 | 345 | 91.5803 | 22.4607 | 0.4696 | 0.2255 | -0.3450 | 1.2599 |
| rolling vol <= 0.006 + ATR/close <= 0.012 | 307 | 90.2998 | 19.4443 | 0.4625 | 0.2463 | -0.4019 | 1.2915 |

Interpretation:

The first useful drawdown-control result is `rolling_volatility <= 0.006`. It
reduces max drawdown from 34.0307% to 19.4443% while keeping a similar paper
cumulative return. However, win rate remains below 50% and median trade remains
negative. This still looks like occasional larger winners, not a stable
promotion-ready edge.

Manager review:

`KEEP_RESEARCH_LONG24_VOL_FILTER_ONLY`

Updated paper-only decisions:

- Keep only BTCUSD H1 LONG 24-bar with rolling volatility filter for the next
  research pass.
- Reject SHORT, M15 confirmation, strict sweep as standalone, and LONG 4/8
  fixed exits for this version.
- Do not promote; next test needs walk-forward or year-split stability before
  any strategy-candidate discussion.

## Paper Test 6 - Year-Split Stability Gate

Date: 2026-06-20

Files updated:

- `src/tar_system/signals/clear_read_replay.py`
- `tests/test_clear_read_replay.py`

Scope:

- added calendar-year split sequencing for the surviving candidate,
- tested BTCUSD H1 LONG-only, 24-bar fixed exit, `rolling_volatility <= 0.006`,
  10 bps cost proxy,
- still no runtime artifact writing,
- still no strategy registration, CLI, scheduler, dashboard, alerts, Telegram,
  MT5, broker, exchange, or live path.

Validation:

```text
PYTHONPATH=src venv/bin/python -m pytest tests/test_clear_read_signal.py tests/test_clear_read_replay.py
Result: 13 passed

PYTHONPATH=src venv/bin/python -m compileall src/tar_system/signals
Result: pass
```

Read-only BTCUSD H1 LONG 24-bar year split:

| Year | Trades | Cumulative return % | Max drawdown % | Win rate | Avg trade % | Median trade % | Profit factor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022 | 4 | -2.7543 | 5.3538 | 0.2500 | -0.6543 | -0.7101 | 0.5694 |
| 2023 | 92 | 61.9279 | 18.9757 | 0.4239 | 0.5831 | -0.5684 | 1.6797 |
| 2024 | 101 | 22.7177 | 17.7123 | 0.4950 | 0.2304 | -0.0790 | 1.2811 |
| 2025 | 103 | -6.6948 | 18.5223 | 0.4563 | -0.0448 | -0.3450 | 0.9448 |
| 2026 | 6 | -1.1316 | 6.6624 | 0.6667 | -0.1362 | 1.1287 | 0.8971 |

Interpretation:

The year split fails stability. The idea works in 2023 and 2024, but 2025 is
negative with a weak profit factor. 2022 and 2026 have too few trades to count
as stable evidence. This is a classic "interesting research effect, not robust
strategy candidate" result.

Manager review:

`FAIL_YEAR_SPLIT_DO_NOT_PROMOTE`

Updated paper-only decisions:

- Do not convert this into a strategy candidate.
- Keep the clear-read layer as a research/scoring experiment only.
- Any future work must be framed as diagnostic research, not strategy build.
- The next useful question is why 2025 fails, not how to tune around it.

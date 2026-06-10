# Phase Notes - 2026-05-26

## Phase - Vol-Scaled EMA Mixture Proxy

Goal:

- Complete the open paper-only vol-scaled EMA mixture candidate.
- Compare it against the already failed plain EMA family before any strategy
  implementation.

Status: complete

- Added `run-vol-scaled-ema-mixture-proxy`.
- Added a paper-only multi-horizon EMA mixture proxy.
- Signal logic:
  - EMA pairs 8/24, 16/48, 32/96, 64/192.
  - Normalize EMA differences by rolling volatility.
  - Bound component responses with `tanh`.
  - Average components into one time-series signal.
  - Shift positions by one bar.
  - Apply 2 bps cost per position change.
- Ran the proxy on EURUSD, GBPUSD, AUDUSD, USDJPY, and USDCAD H1.

Result:

- Basket cumulative return: -36.6529%
- Basket annualized return: -8.0498%
- Basket Sharpe: -1.5157
- Basket max drawdown: 37.8049%
- Basket verdict: KILL
- Basket reason: NEGATIVE_AFTER_COSTS

Per-symbol review:

- EURUSD: KILL, -38.5818% cumulative return.
- GBPUSD: KILL, -40.3826% cumulative return.
- AUDUSD: KILL, -53.5106% cumulative return.
- USDJPY: KILL, -26.6405% cumulative return.
- USDCAD: KILL, -33.8882% cumulative return.

Artifacts:

- `reports/vol_scaled_ema_mixture_proxy/20260526T082723Z_vol_scaled_ema_mixture_proxy.md`
- `reports/vol_scaled_ema_mixture_proxy/20260526T082723Z_vol_scaled_ema_mixture_proxy.json`
- `ideas/backtest_candidates/vol-scaled-ema-mixture-currency-momentum-20260525.md`
- `ideas/rejected/vol-scaled-ema-mixture-currency-momentum-20260526.md`

Review:

- This proxy did not rescue the EMA/momentum family.
- All tested symbols were negative after costs.
- No strategy code, MT5 export, or live path should be created from this
  candidate.

Next step:

- Run the phase gate audit for vol-scaled EMA mixture proxy.

Candidate state after refresh:

- `select-next-candidates`: reviewed 10 items.
- Translate next: 0
- Blocked/hold: 10
- All EMA/momentum candidates are now tested and rejected.
- Remaining high-quality source requiring exact formula extraction:
  `A Multi Strategy Approach to Trading Foreign Exchange Futures`.

Audit:

- Phase gate: pass
- Focused tests: 9 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260526T084232Z_vol-scaled-ema-mixture-proxy.md`

Clean checkpoint:

- Vol-scaled EMA mixture proxy is implemented, tested, run, and rejected.
- There are no open backtest candidates ready for implementation.
- The next useful task is exact formula extraction for the multi-strategy FX
  futures source, or a fresh high-quality scout search.

## Phase - Translation Blocker Review

Goal:

- Make blocked high-quality sources visible so they do not get converted into
  invented strategy rules.

Status: complete

- Added `review-translation-blockers`.
- Added tests for blocked-source review.
- Ran the live blocker review.

Result:

- Blocked sources: 1
- Blocked source:
  `Multi-Strategy FX Futures - Translation Blocked`
- Missing before candidate conversion:
  - Exact momentum indicator formula.
  - Exact mean-reversion indicator formula.
  - Exact carry measure or proxy.
  - Normalization method.
  - Portfolio weighting method.
  - Walk-forward split method.
  - Cost model.

Artifacts:

- `idea_reviews/translation_blockers_2026-05-26.md`
- `idea_reviews/translation_blockers_2026-05-26.json`

Review:

- This phase does not create strategy code.
- This phase does not create a backtest candidate.
- The source remains blocked until exact formulas are extracted.

Next step:

- Run the phase gate audit for translation blocker review.

Audit:

- Phase gate: pass
- Focused tests: 6 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260526T092650Z_translation-blocker-review.md`

Clean checkpoint:

- No ready backtest candidates remain.
- One high-quality source is blocked on missing formulas.
- The blocked source has an explicit formula checklist and review artifact.

## Phase - Formula Extraction For Multi-Strategy FX Futures

Goal:

- Replace the remaining formula ambiguity with a source-backed formula record,
  then keep the idea blocked only on data readiness.

Status: complete

- Extracted the source's indicator families and sizing rules.
- Created a formula extraction note.
- Created a data requirements note.
- Updated the blocked-source note from formula-blocked to data-blocked.
- Refreshed the translation blocker review.

Result:

- Blocked sources: 1
- Blocked source:
  `Multi-Strategy FX Futures - Formula Extracted, Data Blocked`
- Remaining blocker type: data and local mapping readiness.
- No strategy candidate was created.

Artifacts:

- `ideas/formula_extracted/multi-strategy-fx-futures-20260526.md`
- `ideas/data_requirements/multi-strategy-fx-futures-20260526.md`
- `ideas/translation_blocked/multi-strategy-fx-futures-20260525.md`
- `idea_reviews/translation_blockers_2026-05-26.md`
- `idea_reviews/translation_blockers_2026-05-26.json`

Review:

- The source is now usable as a documented research source.
- It is not yet usable as a local backtest candidate because V2 still needs
  futures/yield/equity/commodity data or an explicit reduced proxy decision.
- A spot-FX-only proxy would be incomplete and should be labelled as such.

Next step:

- Run the phase gate audit for formula extraction.

Audit:

- Phase gate: pass
- Focused tests: 7 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260526T094213Z_formula-extraction-multi-strategy-fx-futures.md`

Clean checkpoint:

- The last known high-quality formula-blocked source is no longer blocked on
  missing formulas.
- It remains blocked on data acquisition and local proxy design.
- No strategy candidate, backtest code, or live path was created from an
  incomplete source translation.

## Phase - Candidate Queue Data-Blocked Alignment

Goal:

- Make `select-next-candidates` agree with the formula extraction and
  translation blocker state.

Status: complete

- Added translation-blocked registry awareness to candidate selection.
- Added CLI support for `--translation-blocked-dir`.
- Added a regression test for formula-extracted/data-blocked sources.
- Refreshed candidate selection output.

Result:

- Reviewed items: 10
- Translate next: 0
- Blocked/hold: 10
- Multi-strategy FX futures now reports `DATA_BLOCKED`, not
  `NEEDS_RULE_TRANSLATION`.
- Next action now points to data coverage or a documented reduced proxy.

Artifacts:

- `src/tar_system/research/candidate_selection.py`
- `src/tar_system/cli.py`
- `tests/test_candidate_selection.py`
- `idea_reviews/candidate_selection_2026-05-26.md`
- `idea_reviews/candidate_selection_2026-05-26.json`

Review:

- The queue now avoids sending agents back into formula extraction that has
  already been completed.
- The system still correctly refuses to create a strategy candidate until data
  coverage or reduced proxy design is explicit.

Next step:

- Run the phase gate audit for candidate queue alignment.

Audit:

- Phase gate: pass
- Focused tests: 8 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260526T094948Z_candidate-queue-data-blocked-alignment.md`

Clean checkpoint:

- Candidate selection now routes formula-extracted/data-blocked sources toward
  data readiness instead of duplicate rule extraction.
- The queue has zero ready translations and zero open implementation
  candidates.

## Phase - Data Requirements Review

Goal:

- Compare data requirement notes against local `data/raw` files before any
  reduced proxy or candidate conversion.

Status: complete

- Added `review-data-requirements`.
- Added data requirements review tests.
- Ran the live review against V2 raw data.

Result:

- Data requirement notes: 1
- Fully ready: 0
- Blocked: 1
- FX futures/spot proxy: partial. Local spot symbols exist for AUDUSD, EURUSD,
  GBPUSD, USDCAD, and USDJPY, but this is not the paper's full futures basket.
- Yields: missing.
- Linked equity indices: missing.
- Commodities: partial. XAUUSD can proxy gold and USOUSD can proxy oil, but
  GSCI, Brent, and agriculture are missing.
- Cost model: decision required.

Artifacts:

- `src/tar_system/research/data_requirements_review.py`
- `src/tar_system/cli.py`
- `tests/test_data_requirements_review.py`
- `idea_reviews/data_requirements_2026-05-26.md`
- `idea_reviews/data_requirements_2026-05-26.json`

Review:

- The multi-strategy FX futures source should stay blocked.
- A local proxy can only be a clearly labelled incomplete proxy unless yield,
  equity index, commodity, and futures-cost data are added.

Next step:

- Run the phase gate audit for data requirements review.

Audit:

- Phase gate: pass
- Focused tests: 10 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260526T100411Z_data-requirements-review.md`

Clean checkpoint:

- The remaining high-quality source is now formula-extracted, queue-aligned,
  and explicitly data-reviewed.
- No current source is ready for candidate conversion without either new data
  or a reduced-proxy decision note.

## Phase - Guarded Proxy Decision Draft

Goal:

- Create an explicit reduced-proxy decision artifact for data-blocked sources
  so agents do not accidentally treat incomplete local data as the full paper.

Status: complete

- Added `draft-proxy-decisions`.
- Added guarded proxy decision tests.
- Drafted one live proxy decision note.

Result:

- Drafted notes: 1
- Decision: `DO_NOT_CONVERT_FULL_SOURCE`
- Proxy scope: `incomplete_local_spot_price_proxy_only`
- Candidate conversion remains blocked without operator approval.

Artifacts:

- `src/tar_system/research/proxy_decisions.py`
- `src/tar_system/cli.py`
- `tests/test_proxy_decisions.py`
- `ideas/proxy_decisions/multi-strategy-fx-futures-20260525-20260526.md`
- `idea_reviews/proxy_decisions_2026-05-26.md`
- `idea_reviews/proxy_decisions_2026-05-26.json`

Review:

- The draft keeps the source useful for future work but prevents accidental
  promotion of an incomplete proxy.
- Missing components remain explicit: futures basket, yields, linked equities,
  commodity set, and cost model.

Next step:

- Run the phase gate audit for guarded proxy decisions.

Audit:

- Phase gate: pass
- Focused tests: 12 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260526T104147Z_guarded-proxy-decision-draft.md`

Clean checkpoint:

- The data-blocked source now has an explicit proxy decision note.
- The decision blocks full-source conversion and requires operator approval
  before any incomplete local proxy backtest.

## Phase - Candidate Queue Proxy Decision Alignment

Goal:

- Make candidate selection aware of proxy decision notes so queue output points
  to the real remaining decision.

Status: complete

- Added proxy-decision registry awareness to candidate selection.
- Added CLI support for `--proxy-decisions-dir`.
- Added a regression test for proxy-decision-required sources.
- Refreshed candidate selection output.

Result:

- Reviewed items: 10
- Translate next: 0
- Blocked/hold: 10
- Multi-strategy FX futures now reports `PROXY_DECISION_REQUIRED`.
- Next action is now to add missing data or explicitly approve the incomplete
  proxy scope before candidate conversion.

Artifacts:

- `src/tar_system/research/candidate_selection.py`
- `src/tar_system/cli.py`
- `tests/test_candidate_selection.py`
- `idea_reviews/candidate_selection_2026-05-26.md`
- `idea_reviews/candidate_selection_2026-05-26.json`

Review:

- The queue no longer asks agents to document a proxy decision that already
  exists.
- The source still cannot become a candidate without either new data or explicit
  operator approval of the incomplete proxy.

Next step:

- Run the phase gate audit for candidate queue proxy decision alignment.

Audit:

- Phase gate: pass
- Focused tests: 13 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260526T105016Z_candidate-queue-proxy-decision-alignment.md`

Clean checkpoint:

- Candidate selection now reflects the full chain: formula extracted, data
  blocked, proxy decision drafted, operator approval still required.
- There are still zero ready translations and zero open implementation
  candidates.

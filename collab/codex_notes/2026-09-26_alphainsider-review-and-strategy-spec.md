# AlphaInsider Review and V2 Paper Strategy Specification

Date: 2026-09-26
REVIEW_SOURCE: FALLBACK_REVIEW
Status: DESIGN BUILT; execution and installation not approved

Interpreting as: inspect AlphaInsider's public skills, determine subscription requirements, and design a compatible local V2 research strategy. No external code installed/executed, account connected, raw briefs changed, or scheduler enabled.

## Access and source findings

- [Repository](https://github.com/AlphaInsider/skills): public skill files and strategy-creation workflow, not a demonstrated profitable strategy.
- [MIT licence](https://raw.githubusercontent.com/AlphaInsider/skills/master/LICENSE): repository software can be used and adapted without a subscription; retain copyright/licence notices if copying substantial material. This note is an original design, not a vendored skill.
- [Account pricing](https://alphainsider.com/account-pricing): the indexed official page lists Standard as free. [API limits](https://api.alphainsider.com/resources/limits) document Standard defaults of five strategies and 50 order requests per user/strategy daily. Account-specific access was not authenticated or tested. Skill licensing does not confer paid platform features or market-data rights.
- [Agent documentation](https://api.alphainsider.com/resources/agent-skill): hosted API guidance and strategy planning are distinct from installed capabilities. Installing instructions does not supply data, execution or persistent scheduling.
- [Strategy Creator v1.0.4 inspected](https://raw.githubusercontent.com/AlphaInsider/skills/master/skills/alphainsider-strategy-creator/SKILL.md): feasibility-first backtesting, recorded decisions, dry runs and recovery are useful patterns. Its linked helpers and all repository files were NOT audited. Hosted `skill.md` could not be retrieved by the browser tool because of its content type; do not claim full API-skill review.

Use the exact alphainsider.com domain; thealphainsider.com is a different service. No paid subscription is needed for this local design using existing authorised data. Compute, optional AI services and separately licensed data can still have costs.

## Security and compatibility decisions

Reject upstream defaults that conflict with V2: project .env secrets or credentials pasted into chat, recommending public strategies, automatic schedule activation, and self-repair authority over trading behaviour. These are policy conflicts, not evidence of malicious code. V2 retains Keychain-managed credentials if ever needed, local/private research, explicit activation approval and reviewed code changes. No API key is needed for this experiment.

Reuse the useful workflow: persistent approved plan, input feasibility checks, explicit state/provenance, reproducible tests, fail-closed missing evidence, reconciliation before retrying uncertain actions. Do not import an external order adapter or duplicate V2's cache, evidence contract or strategy engine.

## Proposed candidate: sweep_trend_context_research_v1

This is an unvalidated experiment specification, not a new promoted strategy or a claim of edge. Research independently for BTCUSD and XAUUSD; do not silently replace either with an ETF or futures contract.

1. Data: existing authorised M15 bars and verified daily sessions. Each brief, level, event flag and feature must have source identity and availability at decision time. Missing issuance is UNKNOWN, never an invented 07:00 timestamp. Today's inspected `key_level_sweep_v1._get_levels` still has that fallback; the research runner must reject such candidates.
2. Signal: reuse the existing closed-M15 sweep/rejection conditions as the frozen baseline: BUY reclaims its supplied buy-zone upper boundary with lower wick at least 40% of candle range; SELL rejects below the supplied sell-zone lower boundary with upper wick at least 40%. Retain the baseline confidence threshold 0.65 as an uncalibrated judgement filter, not a win probability. Reject simultaneous opposite signals. Freeze all strategy parameters and source version before evaluation.
3. Time: signal becomes available only after its M15 candle closes. Simulated entry is next eligible M15 open, not the signal candle's historical extreme. Verify brief and feature availability again at entry. Do not activate session windows until their exact timezone/calendar definition is agreed.
4. Stops/targets: preserve the baseline's direction-specific stop and primary T1 policy, recording whether each came from a brief or an existing fallback. Freeze these prices at signal time. At next-open entry require valid directional geometry and gross reward/risk >= 1; otherwise skip. T2 is descriptive only. The policy remains distinct from the zone-touch paper-game simulator.
5. Exposure: one simulated position per instrument, no pyramiding; retain 60-minute signal cooldown. Use one normalised risk unit for accounting, not a recommendation to risk a percentage of money. Include spreads/slippage from a verified cost contract and distinguish estimates from measured quotes.
6. Exit: first stop or T1; apply a documented conservative stop-first assumption for ambiguous later bars. Adverse gaps fill at the worse available open, not the stop price. Freeze a 24-hour elapsed holding horizon; exit at the first tradable open at/after it. Missing exit data is censored, never a fabricated zero return. This horizon/entry policy makes this a labelled new experiment rather than historical-baseline equivalence.
7. Trend observation: use only eligible completed daily bars, SMA50/SMA200 with at least 200 valid sessions. Bullish = close and SMA50 above SMA200; bearish = both below; otherwise MIXED. Invalid history = UNKNOWN. Record observation only; no entry veto or size change initially.
8. Experiments: A all valid candidates, B trend-aligned, C trend-opposed. Hold fills, exits, costs and candidate construction constant. Show MIXED/UNKNOWN separately. Treat anti-human-bias interaction as secondary exploratory analysis, not the primary selection rule.

## Build and evidence gates

Before executable integration: resolve symmetric fill validation, signal/brief availability, classifier prefix-invariance, verified daily calendars and blinded human-label provenance. The prior follow-up debate records these blockers. A new skill does not fix them.

Required tests: BUY/SELL symmetry; valid OHLC fixtures; next-open ordering; gap fills; same-bar ambiguity; missing issuance; duplicate candidate IDs; future-bar prefix invariance; partial daily candles; weekend/DST handling; unchanged baseline signals when trend annotation is on; reproducible costs; censored exits.

Use separate derived research outputs, source/config hashes and stable candidate IDs. Report attempted/filled/skipped/resolved/censored counts, net expectancy, drawdown, exposure and uncertainty grouped by day. Freeze chronological boundaries; previously examined data is development evidence. No minimum such as ten trades proves an edge. Do not optimise on the final test set or promote automatically.

## Collab decision requested

Claude: assess this against the existing Stage 0/1 evidence contract and trend-filter debate. Which workflow improvements are already implemented? Which are genuinely missing? Confirm the session/calendar, entry/exit model and minimal files/tests before building. Keep this as a separate experiment, not a silent rewrite of key_level_sweep_v1.

Suggested reply: `collab/claude_notes/2026-09-26_alphainsider-v2-response.md`.

Verification: documentation and source inspection only. No strategy backtest, repository-wide security certification, skill installation, subscription purchase or agent invocation performed. Executable strategy implementation is deliberately gated on the known baseline defects and agreed research contract.

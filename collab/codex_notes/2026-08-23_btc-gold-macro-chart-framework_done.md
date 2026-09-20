# Bitcoin and Gold Macro/Chart Framework — Complete

Date: 2026-08-23  
State: COMPLETE — reusable prompt and report saved  
Scope: Public-source macro research and paper-only scenario analysis. No live trade, broker access, order, position sizing, MT5 action, strategy promotion, or deployment.

Interpreting as: prepare a current, public-information macro and cross-market framework—US government and Federal Reserve policy, Bitcoin, gold, VIX, yields, dollar and liquidity—then, once the user attaches the 5-minute, 30-minute and 1-hour charts, rank paper-trade scenarios with example entries, stop-loss levels and confidence estimates.

## Public evidence snapshot

- Federal Reserve, 2026-07-29: held the federal-funds target at 3.50–3.75%; three dissenters preferred a 25 bp increase. The statement says inflation remains above the 2% goal.
- BLS, July 2026: headline CPI 3.4% year-on-year; core CPI 2.5%; payrolls -23,000; unemployment 4.1%.
- BEA, Q2 2026 advance estimate: annualised real GDP growth slowed to 1.5% from 2.1% in Q1.
- Federal Reserve H.15, 2026-08-20: 2-year 4.19%, 10-year 4.69%, 30-year 5.23%, 10-year real yield 2.35%. The positive 10y-2y slope and high long-end yields point to term-premium/fiscal/inflation pressure rather than simple recession pricing.
- Cboe, 2026-08-21: VIX closed 15.13. The calculated mean of 129 Cboe daily closes from 2026-02-23 through 2026-08-21 is 19.03. Current volatility is therefore below its six-month average despite bond-market stress.
- US digital-asset policy: a Strategic Bitcoin Reserve holds transferred government BTC rather than routinely selling it; additional acquisition must be budget-neutral. Policy also aims to integrate fintech and digital assets into regulated financial services and implement a federal stablecoin framework.
- Trade/industrial policy uses tariffs and domestic-supply-chain support. This may aid selected US industries but can also complicate the inflation/rates outlook; that second point is an inference, not an official forecast.
- Next major scheduled US macro risk: 2026-08-26 at 08:30 ET, Q2 GDP second estimate and July Personal Income and Outlays/PCE.

## Working cross-market hypotheses to test against charts

1. Falling long yields + contained VIX + stable/softer dollar: supportive for BTC continuation; also supportive for gold, though relative strength must decide which has the cleaner setup.
2. Rising real yields + rising dollar: headwind for both, usually more directly bearish for gold; BTC may also weaken through tighter liquidity/risk appetite.
3. Rising VIX above a confirmed threshold while yields remain disorderly: risk-off pressure on BTC; gold response depends on whether safe-haven demand outweighs dollar and real-yield pressure.
4. Gold and BTC rising together while long yields remain high: possible fiscal/currency-confidence or scarcity-asset bid, but confirmation requires price structure and volume rather than a narrative alone.

## Chart-output contract

For BTC and gold, reconcile 1h trend -> 30m setup -> 5m trigger. Return ranked paper scenarios with entry zone, invalidation/stop, targets, reward:risk, confidence band, and no-trade condition. A confidence estimate is not a backtested win rate and must be labelled accordingly.

## Next action

For the next review, collect fresh charts with symbol/source, visible price
scale, timeframe and timestamp, then refresh all time-sensitive macro evidence.

## XAUUSD chart intake — 5m, 30m, 1h

Interpreting as: analyse the three supplied XAUUSD charts as one multi-timeframe paper-trade setup, using the current macro framework as context, and rank example entry, stop and target options without treating them as certain or live instructions.

- Assumption: screenshots are current and all show the same Pepperstone XAUUSD feed near 4,604.80. The one-hour OHLC header appears to refer to a selected/older candle, so the visible current-price line and structure were used instead.
- 1h: bullish higher-high/higher-low structure remains intact after a strong expansion from roughly 4,330 to 4,630. Major visible upside reference is around 4,700.74; deeper structural support is around 4,520, then the plotted 4,487.69/4,473.20 region.
- 30m: bullish trend with a pullback from roughly 4,628–4,632. Immediate structure references are 4,600, 4,580–4,585, and 4,560.
- 5m: immediate momentum is bearish after a break below the short rising trend line near 4,617 and acceleration towards 4,604. The plotted 4,612.78 and 4,617.70 levels form the first reclaim/resistance zone; 4,621.16 and 4,628–4,632 are higher resistance.
- Preferred stance at the screenshot price: WAIT. Timeframes are misaligned; do not chase a long while 5m is falling, and do not take a countertrend short without a confirmed 30m breakdown.
- Conditional paper scenarios: pullback-long only after 4,598–4,602 holds and price reclaims 4,612–4,618; breakout-long only after a close/retest above 4,632; countertrend short only after a 30m close below 4,598–4,600 followed by a failed reclaim.
- Exact confidence numbers are judgement estimates, not backtested win rates. No position size is supplied.

## BTCUSD chart intake — 5m, 30m, 1h

Interpreting as: analyse the supplied BTCUSD 1-hour, 30-minute and 5-minute charts, then compare Bitcoin’s best conditional paper setup with the earlier gold scenarios.

- Assumption: screenshots are current and show the same Coinbase BTCUSD feed around 77,200. The 30m OHLC header refers to a selected/older candle, so the visible current-price line and structure were used.
- 1h: the major advance from roughly 63,000 to 79,500 remains intact, but price is consolidating after the impulse. The visible structure is a converging triangle/coil rather than a clean continuation signal.
- 30m: compression is centred near 77,200. Immediate upper resistance is roughly 77,600–77,800, with the larger prior high/marked objective around 79,575. Immediate lower references are approximately 76,800–77,000, then the rising boundary around 75,900–76,000 and the prior swing near 75,570.
- 5m: price recovered from roughly 75,800 and then flattened around 77,000–77,400. Momentum is neutral; there is no clean entry at the middle of the range.
- Preferred stance at the screenshot price: WAIT. Conditional long only after a confirmed close/retest above 77,750 or a bullish rejection from 76,800–77,000. Conditional short only after a 30m close below 75,900 followed by a failed reclaim.
- Compared with gold: BTC has the cleaner consolidation but no trigger; gold has the stronger active 1h trend but a sharper 5m pullback. Neither supports chasing at the screenshot price.

## Do not do

Do not infer exact entry or stop prices without current charts, and do not
convert a macro narrative into an automatic BUY or SELL.

## Completion update

- Current review saved at `reports/BTC_XAU_MULTI_TIMEFRAME_REVIEW_2026-08-23.md`.
- Reusable full and short phone prompts saved at
  `docs/prompts/V2_PHONE_MULTI_TIMEFRAME_MARKET_REVIEW_PROMPT.md`.
- Safe phone/Telegram options saved at
  `docs/runbooks/PHONE_AND_TELEGRAM_MARKET_REVIEW.md`.
- Recommended current route: private ChatGPT Project with project-only
  instructions and manual chart upload.
- Telegram remains disabled in V2. No bot, token, message, listener, scheduler,
  broker action or live-trading action was created or used.

Review source: FALLBACK_REVIEW — local lead-agent self-review; no Fable approval
or external private-project reviewer was used.

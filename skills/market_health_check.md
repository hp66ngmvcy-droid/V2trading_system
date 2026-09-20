# Market Health Check

Purpose: deliver a rapid macro regime read before any trading decision. One structured
output, six sections, one directional takeaway. No hedging.

Use this skill when the user asks about market conditions, regime, macro backdrop,
whether to press or trim risk, or what kind of market they are trading in.

## Hard Boundaries

- This skill is analytical only. No live orders, no MT5 actions, no position sizing.
- Paper mode only. Output feeds strategy go/no-go decisions, not execution.
- Do not conflate the regime read with a signal to promote any strategy.

---

## Prompt

Act as a macro strategist. I am not asking about one stock. Tell me what kind of
market I am trading in.

### 01 Regime
Strong bull, bull, choppy, correction, or bear?
Justify with price action, not vibes. Use index levels and recent trend structure.

### 02 Breadth
Broad participation or a few mega-caps?
Percent of S&P 500 stocks above their 200-day moving average. High (>70%) = healthy.
Low (<40%) = narrow, fragile.

### 03 Volatility
VIX now vs its 6-month average.
Complacency (<15), normal (15–20), or elevated (>25)?
Rising VIX = expanding risk; falling VIX = compression before a move.

### 04 Rates
Fed funds rate, next expected move (CME FedWatch), 10-year yield direction.
Tightening or loosening? Yield curve shape (inverted / flat / steepening).

### 05 Leadership
Leading and lagging sectors this month (use sector ETF performance).
Offensive leadership (XLK, XLY, XLC) = risk-on.
Defensive leadership (XLU, XLP, XLV) = risk-off signal.

### 06 Takeaway
**Press risk, trim risk, or stay neutral?**
One answer. No hedge. State the dominant regime signal and the single most
important risk to that read.

---

## Output format

Return each section as a numbered block. End with a one-line verdict in bold.
Example: **VERDICT: CHOPPY — stay neutral, reduce size, wait for breadth confirmation.**

---

## Integration with V2

- Run before a new strategy test cycle to calibrate expectations.
- A bear or high-VIX regime context should raise the WF PF gate (use 1.30 not 1.10).
- A strong-bull, low-VIX regime validates breakout strategies over mean-reversion.
- Record the regime read in `collab/agent_memory/` alongside any WF result for future reference.
- Source: macro data from web search (CNBC, Bloomberg snippet, CME FedWatch) — always
  state data freshness and flag if >1 week old.

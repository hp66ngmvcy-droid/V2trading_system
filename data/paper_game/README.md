# V2 Paper Game

Paper-only trading journal. No real money. No live execution.

## Structure

```
data/paper_game/
  sessions/YYYY-MM-DD.md   — daily plan + outcome notes
  trades.jsonl             — append-only trade log (one JSON line per trade)
  open.json                — current watching/open positions snapshot
  README.md                — this file
```

## Paper account

Starting capital: $10,000 USD (notional)
Risk per trade: 1% = $100 max loss-at-stop
Sizing: `lots = $100 / (stop_distance_pts * $/pt)`

XAUUSD: 1 standard lot = 100 oz = ~$10/pt. So $100 / (stop_pts * 10) = lots.
BTCUSD: 1 lot = 1 BTC. $100 / stop_distance_$ = lots.

## How to log a trade

When a level is hit, append a line to trades.jsonl:

```json
{"date":"2026-09-23","symbol":"XAUUSD","side":"SELL","status":"OPEN","entry":4334.0,"stop":4348.0,"t1":4305.0,"t2":4290.0,"lots":0.05,"risk_usd":100,"rr_t1":1.15,"confidence":0.64,"note":"rebound sell after PMI"}
```

When trade closes, append a CLOSED line:

```json
{"date":"2026-09-23","symbol":"XAUUSD","side":"SELL","status":"CLOSED","entry":4334.0,"exit":4305.0,"result":"TP","pnl_pts":29,"pnl_usd":145,"r_multiple":1.45,"note":"T1 hit"}
```

## Rules

- Only trade levels from the daily brief (data/daily_briefs/)
- WAIT means no entry — do not force
- Log outcomes next morning using scripts/log_outcome.py for the formal record
- This folder is for human readable tracking only

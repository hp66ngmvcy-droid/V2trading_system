# Gold Regime Tracker

Streamlit dashboard that classifies gold's current price driver using FRED macro data and rolling correlation analysis.

## How to run

```bash
cd ~/Dev/V2trading_system
export FRED_API_KEY=your_key_here
streamlit run ui/gold_regime_tracker.py
```

Alternatively, enter the key in the sidebar when the app loads (password field). The key is never written to disk.

## How to get a FRED API key

1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
2. Create a free account and verify your email.
3. Under My Account → API Keys, click "Request API Key".
4. Copy the key and set it as `FRED_API_KEY` in your environment or paste it into the sidebar.

The key is free with no rate-limit issues for personal use.

## What each regime means

**RATES GOLD** (red) — Gold is moving primarily in response to real interest rate changes. The 90-day rolling correlation of gold with TIPS real yields is below -0.5, meaning gold rises as real yields fall and vice versa. This is the "textbook" gold driver and dominated during 2020–2022. Trading implication: watch Fed guidance and breakeven inflation closely.

**DOLLAR GOLD** (blue) — Gold is moving primarily as a dollar hedge. The 90-day rolling correlation with DXY is below -0.5 while the TIPS relationship has faded. Gold is pricing currency weakness rather than rate expectations. Common during periods of broad dollar selling. Trading implication: watch DXY and USD positioning.

**RESERVE GOLD** (yellow) — Gold is decoupled from both rates and the dollar. Price is above the 200-day MA, the TIPS correlation has collapsed (|corr| < 0.3), and either large speculative positioning (COT net > 200k contracts) or positive price momentum despite rising real yields is present. This regime often reflects central bank buying or structural de-dollarisation demand. Trending, persistent moves are typical.

**FEAR GOLD** (orange) — A short, sharp spike: gold up more than 3% over the last 10 days with no sustained 30-day trend behind it. Driven by geopolitical shock or risk-off panic rather than macro fundamentals. These moves are often mean-reverting once the catalyst fades. Trading implication: fade aggressively if fundamentals have not changed.

**MIXED/UNCLEAR** (grey) — No single driver is dominant. Correlations are weak across all factors. Regimes often transition through this state. Reduce position size and wait for a cleaner signal.

## COT data input

The sidebar accepts a manual net speculator position (number of contracts). Check the latest CFTC Commitments of Traders report at:
https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm

The "Disaggregated Futures Only" gold (COMEX) row — subtract short positions from long positions for managed money to get the net figure.

## Data sources

| Series | FRED ID | Description |
|--------|---------|-------------|
| Gold price | GOLDPMGBD228NLBM | London PM fix, USD/troy oz, daily |
| TIPS real yield | DFII10 | 10-year Treasury Inflation-Indexed, daily |
| DXY | DTWEXBGS | Broad trade-weighted USD index, daily |

Data is cached for 1 hour. Use the "Refresh Data" button in the sidebar to force a reload.

import os
import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="Gold Regime Tracker", layout="wide")

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"

REGIME_COLORS = {
    "RATES GOLD": "#e74c3c",
    "DOLLAR GOLD": "#2980b9",
    "RESERVE GOLD": "#f1c40f",
    "FEAR GOLD": "#e67e22",
    "MIXED/UNCLEAR": "#7f8c8d",
}

# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_fred_series(series_id: str, api_key: str, start: str, end: str) -> pd.Series:
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
        "observation_end": end,
    }
    r = requests.get(FRED_BASE, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    obs = data.get("observations", [])
    if not obs:
        return pd.Series(dtype=float)
    df = pd.DataFrame(obs)[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna().set_index("date")["value"]
    return df


@st.cache_data(ttl=3600)
def fetch_yahoo_series(ticker: str, start: str, end: str) -> pd.Series:
    start_ts = int(datetime.strptime(start, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end, "%Y-%m-%d").timestamp())
    url = f"{YAHOO_BASE}{ticker}"
    params = {"interval": "1d", "period1": start_ts, "period2": end_ts}
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    dates = pd.to_datetime(timestamps, unit="s").normalize()
    s = pd.Series(closes, index=dates, dtype=float).dropna()
    s.index = s.index.tz_localize(None)
    return s



# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def align_series(*series):
    combined = pd.concat(series, axis=1, join="inner")
    combined.columns = range(len(series))
    return [combined[i] for i in range(len(series))]


def rolling_corr(a: pd.Series, b: pd.Series, window: int = 90) -> pd.Series:
    combined = pd.concat([a, b], axis=1).dropna()
    if len(combined) < window:
        return pd.Series(dtype=float)
    return combined.iloc[:, 0].rolling(window).corr(combined.iloc[:, 1])


def classify_regime(
    gold: pd.Series,
    tips: pd.Series,
    dxy: pd.Series,
    cot_net: int,
) -> tuple[str, float, pd.DataFrame]:
    gold_d, tips_d, dxy_d = align_series(gold, tips, dxy)

    corr_tips = rolling_corr(gold_d, tips_d, 90)
    corr_dxy = rolling_corr(gold_d, dxy_d, 90)

    ma200 = gold_d.rolling(200).mean()

    current_corr_tips = float(corr_tips.dropna().iloc[-1]) if len(corr_tips.dropna()) else 0.0
    current_corr_dxy = float(corr_dxy.dropna().iloc[-1]) if len(corr_dxy.dropna()) else 0.0
    current_price = float(gold_d.iloc[-1]) if len(gold_d) else 0.0
    current_ma200 = float(ma200.dropna().iloc[-1]) if len(ma200.dropna()) else 0.0

    # Fear: gold up >3% in last 10 days with no sustained trend
    recent = gold_d.iloc[-10:] if len(gold_d) >= 10 else gold_d
    pct_change_10d = float((recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100) if len(recent) >= 2 else 0.0
    longer = gold_d.iloc[-30:] if len(gold_d) >= 30 else gold_d
    pct_change_30d = float((longer.iloc[-1] - longer.iloc[0]) / longer.iloc[0] * 100) if len(longer) >= 2 else 0.0

    above_ma = (current_price - current_ma200) / current_ma200 * 100 if current_ma200 else 0.0

    # Spike history for "days since last 3%+ 10-day spike"
    spike_days = None
    if len(gold_d) >= 10:
        rolling_10d_ret = gold_d.pct_change(10) * 100
        spikes = rolling_10d_ret[rolling_10d_ret > 3]
        if len(spikes):
            last_spike_date = spikes.index[-1]
            spike_days = (gold_d.index[-1] - last_spike_date).days

    # Classify — ordered by specificity
    regime = "MIXED/UNCLEAR"
    confidence = 50.0

    fear_spike = pct_change_10d > 3 and abs(pct_change_30d) < 6
    rates_gold = current_corr_tips < -0.5 and current_corr_dxy > -0.3
    dollar_gold = current_corr_dxy < -0.5 and current_corr_tips > -0.3
    reserve_gold = (
        above_ma > 0
        and abs(current_corr_tips) < 0.3
        and (cot_net > 200000 or (pct_change_30d > 0 and tips_d.iloc[-1] > 0))
    )

    if fear_spike:
        regime = "FEAR GOLD"
        strength = min(100, (pct_change_10d - 3) / 5 * 100)
        confidence = round(50 + strength * 0.5, 1)
    elif rates_gold:
        regime = "RATES GOLD"
        strength = min(1.0, (-current_corr_tips - 0.5) / 0.5)
        confidence = round(50 + strength * 50, 1)
    elif dollar_gold:
        regime = "DOLLAR GOLD"
        strength = min(1.0, (-current_corr_dxy - 0.5) / 0.5)
        confidence = round(50 + strength * 50, 1)
    elif reserve_gold:
        regime = "RESERVE GOLD"
        strength = min(1.0, above_ma / 10)
        confidence = round(50 + strength * 50, 1)
    else:
        max_corr = max(abs(current_corr_tips), abs(current_corr_dxy))
        confidence = round(max(10, 50 - max_corr * 50), 1)

    # Monthly regime history
    regime_history = _build_regime_history(gold_d, tips_d, dxy_d, cot_net)

    stats = {
        "Gold Price": f"${current_price:,.2f}",
        "TIPS 10Y Real Yield": f"{tips_d.iloc[-1]:.2f}%" if len(tips_d) else "N/A",
        "DXY": f"{dxy_d.iloc[-1]:.2f}" if len(dxy_d) else "N/A",
        "90d Gold/TIPS Corr": f"{current_corr_tips:.3f}",
        "90d Gold/DXY Corr": f"{current_corr_dxy:.3f}",
        "Days Since 3%+ Spike": str(spike_days) if spike_days is not None else "N/A",
        "Gold vs 200d MA": f"{above_ma:+.2f}%",
    }

    return regime, confidence, corr_tips, corr_dxy, gold_d, tips_d, dxy_d, ma200, regime_history, stats


def _classify_point(corr_tips, corr_dxy, above_ma, cot_net, pct_10d, pct_30d, tips_val):
    fear_spike = pct_10d > 3 and abs(pct_30d) < 6
    rates_gold = corr_tips < -0.5 and corr_dxy > -0.3
    dollar_gold = corr_dxy < -0.5 and corr_tips > -0.3
    reserve_gold = (
        above_ma > 0
        and abs(corr_tips) < 0.3
        and (cot_net > 200000 or (pct_30d > 0 and tips_val > 0))
    )
    if fear_spike:
        return "FEAR GOLD"
    if rates_gold:
        return "RATES GOLD"
    if dollar_gold:
        return "DOLLAR GOLD"
    if reserve_gold:
        return "RESERVE GOLD"
    return "MIXED/UNCLEAR"


def _build_regime_history(gold_d, tips_d, dxy_d, cot_net):
    g, t, dx = align_series(gold_d, tips_d, dxy_d)
    ct = g.rolling(90).corr(t)
    cd = g.rolling(90).corr(dx)
    ma200 = g.rolling(200).mean()
    r10 = g.pct_change(10) * 100
    r30 = g.pct_change(30) * 100
    above = (g - ma200) / ma200 * 100

    records = []
    monthly = g.resample("ME").last()
    for dt in monthly.index:
        subset = g.loc[:dt]
        if len(subset) < 200:
            continue
        idx = subset.index[-1]
        try:
            _ct = float(ct.loc[idx]) if idx in ct.index else 0.0
            _cd = float(cd.loc[idx]) if idx in cd.index else 0.0
            _ab = float(above.loc[idx]) if idx in above.index else 0.0
            _r10 = float(r10.loc[idx]) if idx in r10.index else 0.0
            _r30 = float(r30.loc[idx]) if idx in r30.index else 0.0
            _tv = float(t.loc[idx]) if idx in t.index else 0.0
        except Exception:
            continue
        regime = _classify_point(_ct, _cd, _ab, cot_net, _r10, _r30, _tv)
        records.append({"date": dt, "regime": regime})

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Macro calendar (Trading Economics)
# ---------------------------------------------------------------------------

MACRO_KEYWORDS = ["CPI", "Consumer Price", "FOMC", "Federal Funds", "Nonfarm", "PCE",
                  "PPI", "Producer Price", "GDP", "Employment Situation", "Interest Rate"]

@st.cache_data(ttl=21600)
def fetch_macro_calendar(api_key: str) -> pd.DataFrame:
    today = datetime.today().date()
    end = today + timedelta(days=45)
    try:
        r = requests.get(
            "https://api.stlouisfed.org/fred/releases/dates",
            params={"api_key": api_key, "file_type": "json",
                    "realtime_start": str(today), "realtime_end": str(end),
                    "include_release_dates_with_no_data": "false", "limit": 200},
            timeout=15,
        )
        r.raise_for_status()
        releases = r.json().get("release_dates", [])
    except Exception:
        return pd.DataFrame()

    rows = []
    for rel in releases:
        name = rel.get("release_name", "")
        if any(kw.lower() in name.lower() for kw in MACRO_KEYWORDS):
            rows.append({"date": rel["date"], "event": name})
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.drop_duplicates(subset=["date", "event"]).sort_values("date")
    return df


def render_macro_calendar(today, api_key: str):
    df = fetch_macro_calendar(api_key)
    st.subheader("Upcoming Macro Events")
    if df.empty:
        st.caption("No upcoming macro events found via FRED releases.")
        return
    for _, row in df.head(10).iterrows():
        days = (pd.Timestamp(row["date"]) - pd.Timestamp(today)).days
        flag = "🔴" if days <= 1 else ("🟡" if days <= 5 else "🟢")
        label = "Today" if days == 0 else f"in {days}d"
        st.markdown(f"{flag} **{row['event']}** — `{row['date']}` — {label}")


# ---------------------------------------------------------------------------
# Sector rotation (Sector SPDRs via Yahoo Finance)
# ---------------------------------------------------------------------------

SECTORS = {
    "GLD": "Gold",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLK": "Technology",
    "XLU": "Utilities",
    "XLB": "Materials",
    "TLT": "Long Bonds",
}

@st.cache_data(ttl=3600)
def fetch_sector_returns(start: str, end: str) -> pd.DataFrame:
    records = []
    for ticker, name in SECTORS.items():
        try:
            s = fetch_yahoo_series(ticker, start, end)
            if len(s) < 2:
                continue
            ret_30d = float((s.iloc[-1] - s.iloc[-min(30, len(s))]) / s.iloc[-min(30, len(s))] * 100)
            ret_5d = float((s.iloc[-1] - s.iloc[-min(5, len(s))]) / s.iloc[-min(5, len(s))] * 100)
            records.append({"Sector": name, "Ticker": ticker, "5d %": round(ret_5d, 2), "30d %": round(ret_30d, 2)})
        except Exception:
            continue
    return pd.DataFrame(records)


def chart_sector_rotation(df: pd.DataFrame) -> go.Figure:
    df_sorted = df.sort_values("30d %", ascending=True)
    colors = ["#e74c3c" if v < 0 else "#2ecc71" for v in df_sorted["30d %"]]
    fig = go.Figure(go.Bar(
        x=df_sorted["30d %"],
        y=df_sorted["Sector"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in df_sorted["30d %"]],
        textposition="outside",
        hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title="Sector Rotation — 30d Returns",
        template="plotly_dark",
        height=320,
        xaxis=dict(title="30d Return (%)", zeroline=True, zerolinecolor="#555"),
        margin=dict(l=100, r=60, t=50, b=40),
    )
    return fig


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def chart_real_yield_gold(gold: pd.Series, tips: pd.Series, corr_tips: pd.Series):
    g, t = align_series(gold, tips)
    current_corr = float(corr_tips.dropna().iloc[-1]) if len(corr_tips.dropna()) else float("nan")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=g.index, y=g.values, name="Gold (USD)", line=dict(color="#f1c40f", width=2)),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=t.index, y=t.values, name="TIPS 10Y Real Yield (%)", line=dict(color="#e74c3c", width=1.5, dash="dot")),
        secondary_y=True,
    )
    fig.update_layout(
        title=f"Real Yield vs Gold  |  Rolling 90d Correlation: {current_corr:.3f}",
        template="plotly_dark",
        height=380,
        legend=dict(orientation="h", y=1.08),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.update_yaxes(title_text="Gold Price (USD)", secondary_y=False)
    fig.update_yaxes(title_text="Real Yield (%)", secondary_y=True)
    return fig


def chart_dxy_gold(gold: pd.Series, dxy: pd.Series, corr_dxy: pd.Series):
    g, d = align_series(gold, dxy)
    current_corr = float(corr_dxy.dropna().iloc[-1]) if len(corr_dxy.dropna()) else float("nan")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=g.index, y=g.values, name="Gold (USD)", line=dict(color="#f1c40f", width=2)),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=d.index, y=d.values, name="DXY Index", line=dict(color="#2980b9", width=1.5, dash="dot")),
        secondary_y=True,
    )
    fig.update_layout(
        title=f"DXY vs Gold  |  Rolling 90d Correlation: {current_corr:.3f}",
        template="plotly_dark",
        height=380,
        legend=dict(orientation="h", y=1.08),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.update_yaxes(title_text="Gold Price (USD)", secondary_y=False)
    fig.update_yaxes(title_text="DXY", secondary_y=True)
    return fig


def chart_regime_history(history: pd.DataFrame):
    if history.empty:
        return None
    colors = [REGIME_COLORS.get(r, "#7f8c8d") for r in history["regime"]]
    fig = go.Figure(
        go.Bar(
            x=history["date"],
            y=[1] * len(history),
            marker_color=colors,
            text=history["regime"],
            textposition="inside",
            hovertemplate="%{x|%b %Y}<br>%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Monthly Regime History",
        template="plotly_dark",
        height=220,
        yaxis=dict(showticklabels=False, showgrid=False),
        xaxis=dict(title=""),
        margin=dict(l=40, r=40, t=50, b=40),
        bargap=0.05,
    )
    return fig


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    st.title("Gold Regime Tracker")
    st.caption("Classifies gold's current price driver: rates, dollar, reserve demand, or fear.")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Settings")

        env_key = os.environ.get("FRED_API_KEY", "")
        api_key_input = st.text_input(
            "FRED API Key",
            value=env_key,
            type="password",
            help="Get a free key at fred.stlouisfed.org/docs/api/api_key.html",
        )
        api_key = api_key_input.strip() or env_key.strip()

        today = datetime.today().date()
        default_start = today - timedelta(days=730)
        date_range = st.date_input(
            "Date range",
            value=(default_start, today),
            min_value=datetime(2000, 1, 1).date(),
            max_value=today,
        )

        cot_net = st.number_input(
            "COT Net Speculator Position (contracts)",
            value=0,
            step=1000,
            help="Enter the latest weekly CFTC net speculator position for gold futures. "
                 "Available at cftc.gov/MarketReports/CommitmentsofTraders.",
        )

        refresh = st.button("Refresh Data", use_container_width=True)

    # Guard: API key required
    if not api_key:
        st.error(
            "FRED API key not found. "
            "Set the `FRED_API_KEY` environment variable or enter your key in the sidebar.\n\n"
            "**Get a free key:** https://fred.stlouisfed.org/docs/api/api_key.html — "
            "register, verify your email, then generate an API key under My Account."
        )
        st.stop()

    # Parse date range
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_str = str(date_range[0])
        end_str = str(date_range[1])
    else:
        start_str = str(default_start)
        end_str = str(today)

    # Trigger cache bust on refresh
    if refresh:
        fetch_fred_series.clear()
        fetch_yahoo_series.clear()
        fetch_macro_calendar.clear()
        fetch_sector_returns.clear()

    # Load data
    with st.spinner("Fetching market data..."):
        try:
            gold = fetch_yahoo_series("GC=F", start_str, end_str)
        except requests.exceptions.HTTPError as e:
            st.error(f"Yahoo Finance error fetching gold price: {e}")
            st.stop()
        except Exception as e:
            st.error(f"Gold price fetch failed: {e}")
            st.stop()

        try:
            tips = fetch_fred_series("DFII10", api_key, start_str, end_str)
            dxy = fetch_fred_series("DTWEXBGS", api_key, start_str, end_str)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in (400, 403):
                st.error(
                    "FRED API returned an error. Check your API key is valid "
                    "and has not been revoked. Status: " + str(e.response.status_code)
                )
            else:
                st.error(f"FRED API error: {e}")
            st.stop()
        except Exception as e:
            st.error(f"FRED data fetch failed: {e}")
            st.stop()

    if gold.empty or tips.empty or dxy.empty:
        st.warning("One or more FRED series returned no data for the selected date range.")
        st.stop()

    regime, confidence, corr_tips, corr_dxy, gold_d, tips_d, dxy_d, ma200, history, stats = classify_regime(
        gold, tips, dxy, int(cot_net)
    )

    # --- Regime badge ---
    badge_color = REGIME_COLORS.get(regime, "#7f8c8d")
    st.markdown(
        f"""
        <div style="
            display:inline-block;
            background:{badge_color};
            color:#fff;
            font-size:1.6rem;
            font-weight:700;
            padding:0.4rem 1.4rem;
            border-radius:8px;
            letter-spacing:0.05em;
            margin-bottom:0.2rem;
        ">{regime}</div>
        <div style="color:#aaa;font-size:0.95rem;margin-bottom:1.2rem;">
            Regime confidence: <b style="color:#fff;">{confidence:.1f}%</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Key stats table ---
    st.subheader("Key Stats")
    stats_df = pd.DataFrame(list(stats.items()), columns=["Metric", "Value"])
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- Charts ---
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(chart_real_yield_gold(gold_d, tips_d, corr_tips), use_container_width=True)
    with col2:
        st.plotly_chart(chart_dxy_gold(gold_d, dxy_d, corr_dxy), use_container_width=True)

    regime_fig = chart_regime_history(history)
    if regime_fig:
        st.plotly_chart(regime_fig, use_container_width=True)
    else:
        st.info("Regime history requires at least 200 trading days of data.")

    st.divider()

    # --- Sector rotation ---
    sector_df = fetch_sector_returns(start_str, end_str)
    if not sector_df.empty:
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            st.plotly_chart(chart_sector_rotation(sector_df), use_container_width=True)
        with col_s2:
            st.subheader("5d vs 30d")
            st.dataframe(
                sector_df[["Sector", "5d %", "30d %"]].sort_values("30d %", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.warning("Sector rotation data unavailable.")

    st.divider()

    # --- Macro calendar ---
    render_macro_calendar(today, api_key)

    # --- Legend ---
    with st.expander("Regime definitions"):
        for name, color in REGIME_COLORS.items():
            st.markdown(
                f'<span style="display:inline-block;width:12px;height:12px;'
                f'background:{color};border-radius:2px;margin-right:6px;vertical-align:middle;"></span>'
                f'**{name}**',
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()

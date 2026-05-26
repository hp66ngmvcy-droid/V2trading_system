//+------------------------------------------------------------------+
//|  VolFilteredMomentumV1 — XAUUSD M15                              |
//|  Tuned params: RSI 57/43, session 08-15 UTC, ATR cap 8.2761      |
//|  Paper-tested: IS Sharpe 1.60, OOS avg Sharpe 1.81 (6/6 splits) |
//|  DO NOT DEPLOY without paper signal test ≥ 2 weeks first.        |
//+------------------------------------------------------------------+
#property strict

//--- tuned parameters (locked — do not change without re-running tuner)
input double   RSI_BUY_THRESHOLD     = 57.0;
input double   RSI_SELL_THRESHOLD    = 43.0;
input int      SESSION_START_UTC     = 8;       // 08:00 UTC
input int      SESSION_END_UTC       = 15;      // 15:00 UTC (exclusive)
input double   ATR_CAP               = 8.2761;  // P90 cap from tuner
input double   EMA_SLOPE_THRESHOLD   = 0.00015; // normalised slope
input double   ATR_MULTIPLIER        = 2.0;     // stop distance = ATR * this
input double   REWARD_RISK           = 2.5;     // TP = stop * this
input double   ATR_FLOOR_MULT        = 0.55;    // min ATR vs median
input double   ATR_CEIL_MULT         = 2.75;    // max ATR vs median (pre-cap gate)
input double   MIN_BODY_ATR          = 0.20;    // min candle body relative to ATR
input double   LOT_SIZE              = 0.01;    // fixed lot — adjust after paper test

//--- indicator periods (match Python feature_builder exactly)
input int      EMA_FAST_PERIOD       = 12;
input int      EMA_SLOW_PERIOD       = 26;
input int      RSI_PERIOD            = 14;
input int      ATR_PERIOD            = 14;
input int      ATR_MEDIAN_PERIOD     = 50;      // rolling median window
input int      SLOPE_SHIFT           = 3;       // bars back for slope calc

//--- indicator handles
int hEmaFast, hEmaSlow, hRsi, hAtr;

//+------------------------------------------------------------------+
int OnInit()
{
    hEmaFast = iMA(_Symbol, PERIOD_M15, EMA_FAST_PERIOD, 0, MODE_EMA, PRICE_CLOSE);
    hEmaSlow = iMA(_Symbol, PERIOD_M15, EMA_SLOW_PERIOD, 0, MODE_EMA, PRICE_CLOSE);
    hRsi     = iRSI(_Symbol, PERIOD_M15, RSI_PERIOD, PRICE_CLOSE);
    hAtr     = iATR(_Symbol, PERIOD_M15, ATR_PERIOD);

    if (hEmaFast == INVALID_HANDLE || hEmaSlow == INVALID_HANDLE ||
        hRsi == INVALID_HANDLE || hAtr == INVALID_HANDLE)
    {
        Print("ERROR: failed to create indicator handles");
        return INIT_FAILED;
    }
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    IndicatorRelease(hEmaFast);
    IndicatorRelease(hEmaSlow);
    IndicatorRelease(hRsi);
    IndicatorRelease(hAtr);
}

//+------------------------------------------------------------------+
void OnTick()
{
    // Only act on new bar
    static datetime lastBar = 0;
    datetime currentBar = iTime(_Symbol, PERIOD_M15, 0);
    if (currentBar == lastBar) return;
    lastBar = currentBar;

    // --- session gate (UTC hour of closed bar = bar index 1) ---
    MqlDateTime dt;
    TimeToStruct(iTime(_Symbol, PERIOD_M15, 1), dt);
    int hourUTC = dt.hour;
    if (hourUTC < SESSION_START_UTC || hourUTC >= SESSION_END_UTC) return;

    // --- read indicators on last closed bar (index 1) ---
    double emaFast[4], emaSlow[4], rsiVal[2], atrVal[2];
    if (CopyBuffer(hEmaFast, 0, 1, 4, emaFast) < 4) return;
    if (CopyBuffer(hEmaSlow, 0, 1, 4, emaSlow) < 4) return;
    if (CopyBuffer(hRsi,     0, 1, 2, rsiVal)  < 2) return;
    if (CopyBuffer(hAtr,     0, 1, 2, atrVal)  < 2) return;

    double fast      = emaFast[0];   // bar 1 (most recent closed)
    double slow      = emaSlow[0];
    double fastPrev  = emaFast[SLOPE_SHIFT];  // bar 1+3=4 (shift=3)
    double slowPrev  = emaSlow[SLOPE_SHIFT];
    double close1    = iClose(_Symbol, PERIOD_M15, 1);
    double open1     = iOpen(_Symbol,  PERIOD_M15, 1);
    double atr       = atrVal[0];
    double rsi       = rsiVal[0];

    if (close1 <= 0 || atr <= 0) return;

    // --- ATR cap gate (tuned: hard cap 8.2761) ---
    if (atr > ATR_CAP) return;

    // --- ATR median (rolling 50-bar median — approximated via simple average) ---
    // Note: MQL5 has no native rolling median. Using 50-bar ATR SMA as proxy.
    // For production accuracy replace with a custom median buffer.
    double atrBuf[50];
    if (CopyBuffer(hAtr, 0, 1, 50, atrBuf) < 50) return;
    double atrSum = 0;
    for (int i = 0; i < 50; i++) atrSum += atrBuf[i];
    double atrMedian = atrSum / 50.0;

    if (atrMedian > 0)
    {
        if (atr < ATR_FLOOR_MULT * atrMedian) return;  // too compressed
        if (atr > ATR_CEIL_MULT  * atrMedian) return;  // extreme volatility
    }

    // --- candle body gate ---
    double bodyAtr = (atr > 0) ? MathAbs(close1 - open1) / atr : 0.0;
    if (bodyAtr < MIN_BODY_ATR) return;

    // --- EMA slope (normalised: change over SLOPE_SHIFT bars / close) ---
    double fastSlope = (fast - fastPrev) / SLOPE_SHIFT / close1;
    double slowSlope = (slow - slowPrev) / SLOPE_SHIFT / close1;

    // --- skip if already in a position ---
    if (PositionSelect(_Symbol)) return;

    double stopDist = atr * ATR_MULTIPLIER;
    double entry    = SymbolInfoDouble(_Symbol, SYMBOL_ASK);  // BUY uses Ask
    double entryBid = SymbolInfoDouble(_Symbol, SYMBOL_BID);  // SELL uses Bid

    // --- BUY signal ---
    if (fast > slow &&
        fastSlope >  EMA_SLOPE_THRESHOLD &&
        slowSlope >= 0 &&
        rsi >= RSI_BUY_THRESHOLD)
    {
        double sl = entry    - stopDist;
        double tp = entry    + stopDist * REWARD_RISK;
        OpenPosition(ORDER_TYPE_BUY, LOT_SIZE, entry, sl, tp);
        return;
    }

    // --- SELL signal ---
    if (fast < slow &&
        fastSlope < -EMA_SLOPE_THRESHOLD &&
        slowSlope <= 0 &&
        rsi <= RSI_SELL_THRESHOLD)
    {
        double sl = entryBid + stopDist;
        double tp = entryBid - stopDist * REWARD_RISK;
        OpenPosition(ORDER_TYPE_SELL, LOT_SIZE, entryBid, sl, tp);
    }
}

//+------------------------------------------------------------------+
void OpenPosition(ENUM_ORDER_TYPE type, double lots, double price,
                  double sl, double tp)
{
    MqlTradeRequest req = {};
    MqlTradeResult  res = {};

    req.action       = TRADE_ACTION_DEAL;
    req.symbol       = _Symbol;
    req.volume       = lots;
    req.type         = type;
    req.price        = price;
    req.sl           = NormalisePrice(sl);
    req.tp           = NormalisePrice(tp);
    req.deviation    = 10;
    req.magic        = 20260526;
    req.comment      = "vol_filtered_momentum_v1";
    req.type_filling = ORDER_FILLING_IOC;  // broker requires Immediate or Cancel

    if (!OrderSend(req, res))
        Print("OrderSend failed: ", res.retcode, " ", res.comment);
    else
        Print("Order opened: ", EnumToString(type), " lot=", lots,
              " sl=", req.sl, " tp=", req.tp);
}

//+------------------------------------------------------------------+
double NormalisePrice(double price)
{
    double tick = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
    if (tick <= 0)
    {
        // Fallback: derive from digits (broker shows tick size as 0.00)
        int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
        tick = MathPow(10, -digits);
    }
    return NormalizeDouble(MathRound(price / tick) * tick,
                           (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS));
}

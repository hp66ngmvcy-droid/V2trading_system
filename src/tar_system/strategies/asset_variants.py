"""Asset-aware strategy variant settings."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class StrategyVariant:
    base_strategy: str
    variant_name: str
    symbol: str
    timeframe: str
    parameters: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_variant(base_strategy: str, symbol: str, timeframe: str) -> StrategyVariant:
    key = f"{base_strategy}_{symbol.lower()}_{timeframe.lower()}"
    params: dict[str, object] = {}
    if base_strategy == "gold_v2":
        params = _gold_v2_params(symbol.upper(), timeframe.upper())
    if base_strategy == "rsi_reversion_v1":
        params = _rsi_reversion_params(symbol.upper(), timeframe.upper())
    return StrategyVariant(base_strategy=base_strategy, variant_name=key, symbol=symbol.upper(), timeframe=timeframe.upper(), parameters=params)


def _gold_v2_params(symbol: str, timeframe: str) -> dict[str, object]:
    session_filter = symbol not in {"BTCUSD", "ETHUSD", "XRPUSD"}
    if symbol in {"BTCUSD", "ETHUSD", "XRPUSD"}:
        return {"fast_ema": 10, "slow_ema": 30, "rsi_buy_threshold": 58, "rsi_sell_threshold": 42, "atr_multiplier": 2.2, "reward_risk": 2.2, "session_filter": session_filter}
    if symbol == "XAUUSD":
        return {"fast_ema": 12, "slow_ema": 26, "rsi_buy_threshold": 55, "rsi_sell_threshold": 45, "atr_multiplier": 1.5, "reward_risk": 2.0, "session_filter": session_filter}
    if symbol == "USOUSD":
        return {"fast_ema": 14, "slow_ema": 32, "rsi_buy_threshold": 56, "rsi_sell_threshold": 44, "atr_multiplier": 1.8, "reward_risk": 2.0, "session_filter": session_filter}
    return {"fast_ema": 10, "slow_ema": 24, "rsi_buy_threshold": 54, "rsi_sell_threshold": 46, "atr_multiplier": 1.4, "reward_risk": 1.8, "session_filter": session_filter}


def _rsi_reversion_params(symbol: str, timeframe: str) -> dict[str, object]:
    session_filter = symbol not in {"BTCUSD", "ETHUSD", "XRPUSD"}
    params: dict[str, object] = {
        "rsi_period": 14,
        "oversold": 30,
        "overbought": 70,
        "bb_period": 20,
        "session_filter": session_filter,
    }
    if symbol == "BTCUSD":
        params.update({"oversold": 28, "overbought": 72, "session_filter": False})
    if timeframe == "M5":
        params.update({"rsi_period": 9, "oversold": 28, "overbought": 72})
    return params


_FX_MAJORS = {"EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDJPY"}


def asset_seed_overrides(strategy: str, symbol: str, timeframe: str = "M15") -> dict[str, object]:
    """Per-asset parameter overrides vs class defaults for initial candidate seeding.

    Only keys present in the strategy's class defaults are applied; extra keys are ignored.
    Returns an empty dict when no override is needed (use class defaults as-is).
    """
    s = symbol.upper()
    tf = timeframe.upper()
    if strategy == "gold_v2":
        return _gold_v2_params(s, tf)
    if strategy == "rsi_reversion_v1":
        return _rsi_reversion_params(s, tf)
    if strategy == "rsi_only_v3":
        return _rsi_only_v3_overrides(s)
    if strategy == "atr_breakout_v3":
        return _atr_breakout_overrides(s)
    if strategy == "ema_volume_v3":
        return _ema_volume_overrides(s)
    if strategy == "momentum_crossover_v3":
        return _momentum_crossover_overrides(s)
    if strategy == "multi_timeframe_v3":
        return _multi_timeframe_overrides(s)
    if strategy == "liquidity_sweep_v1":
        return _liquidity_sweep_overrides(s)
    return {}


def _rsi_only_v3_overrides(symbol: str) -> dict[str, object]:
    # Default window (40–70 buy, 30–60 sell) is broad enough for FX.
    # Widen for BTC to account for larger RSI swings.
    if symbol == "BTCUSD":
        return {"rsi_buy_level": 35.0, "rsi_sell_level": 65.0, "atr_multiplier": 2.0}
    return {}


def _atr_breakout_overrides(symbol: str) -> dict[str, object]:
    # Default atr_multiplier=2.0 is calibrated for gold. FX M15 rarely breaks 2 ATRs —
    # lower the threshold so the strategy can generate entries.
    if symbol in _FX_MAJORS:
        return {"atr_multiplier": 1.5}
    if symbol == "USOUSD":
        return {"atr_multiplier": 1.8}
    if symbol == "BTCUSD":
        return {"atr_multiplier": 3.0}
    return {}


def _ema_volume_overrides(symbol: str) -> dict[str, object]:
    if symbol == "BTCUSD":
        return {"atr_multiplier": 2.0}
    return {}


def _momentum_crossover_overrides(symbol: str) -> dict[str, object]:
    if symbol == "BTCUSD":
        return {"fast_period": 8, "slow_period": 18, "atr_multiplier": 2.0}
    return {}


def _multi_timeframe_overrides(symbol: str) -> dict[str, object]:
    if symbol == "BTCUSD":
        return {"atr_multiplier": 2.0}
    return {}


def _liquidity_sweep_overrides(symbol: str) -> dict[str, object]:
    # Default wick_ratio=0.45 and min_confidence=0.6 are strict; relax for FX
    # where wicks are proportionally smaller.
    if symbol in _FX_MAJORS:
        return {"wick_ratio": 0.35, "min_confidence": 0.5}
    if symbol == "BTCUSD":
        return {"wick_ratio": 0.5, "min_confidence": 0.65}
    return {}


_WIDE_MOVE_ASSETS = {"BTCUSD", "XAUUSD", "USOUSD"}


def tsds_seed_params(strategy: str, symbol: str, timeframe: str, atr_pct_median: float) -> dict[str, object]:
    """Return volatility-calibrated seed params for TSDS discovery runs.

    Uses SCA (Seed Calibration Agent) logic:
    - atr_multiplier scaled to asset volatility
    - RSI bands widened on M15 (noisy), standard on H1
    - reward_risk tighter for FX, wider for trending/volatile assets
    """
    s = symbol.upper()
    tf = timeframe.upper()

    atr_mult = round(max(0.8, min(atr_pct_median * 12, 3.0)), 4)
    reward_risk = 2.5 if s in _WIDE_MOVE_ASSETS else 1.5

    params: dict[str, object] = {
        "atr_multiplier": atr_mult,
        "reward_risk": reward_risk,
    }

    if strategy in {"rsi_reversion_v1", "rsi_only_v3"}:
        if tf == "M15":
            params.update({"oversold": 25, "overbought": 75})
        else:
            params.update({"oversold": 30, "overbought": 70})

    if strategy == "rsi_only_v3":
        if tf == "M15":
            params.update({"rsi_buy_level": 35.0, "rsi_sell_level": 65.0})
        else:
            params.update({"rsi_buy_level": 40.0, "rsi_sell_level": 60.0})

    if strategy == "atr_breakout_v3":
        params["atr_multiplier"] = round(max(0.5, atr_pct_median * 8), 4)

    if strategy == "liquidity_sweep_v1":
        params["min_confidence"] = 0.4

    return params

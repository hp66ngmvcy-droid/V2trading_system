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

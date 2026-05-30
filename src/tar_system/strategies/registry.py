"""Strategy registry."""

from __future__ import annotations

import inspect

from .gold_v2 import GoldV2
from .rsi_reversion_v1 import RsiReversionV1
from .goldv2_v2 import GoldV2V2
from .rsi_only_v3 import RSIOnlyV3
from .ema_volume_v3 import EMAVolumeV3
from .atr_breakout_v3 import ATRBreakoutV3
from .momentum_crossover_v3 import MomentumCrossoverV3
from .multi_timeframe_v3 import MultiTimeframeV3
from .ema_volume_fixed import EMAVolumeFixed
from .atr_breakout_fixed import ATRBreakoutFixed
from .liquidity_sweep_v1 import LiquiditySweepV1
from .rsi_trend_v4 import RSITrendV4
from .vol_filtered_momentum_v1 import VolFilteredMomentumV1

REGISTRY = {
    "gold_v2": GoldV2,
    "rsi_reversion_v1": RsiReversionV1,
    "goldv2_v2": GoldV2V2,
    "rsi_only_v3": RSIOnlyV3,
    "ema_volume_v3": EMAVolumeV3,
    "atr_breakout_v3": ATRBreakoutV3,
    "momentum_crossover_v3": MomentumCrossoverV3,
    "multi_timeframe_v3": MultiTimeframeV3,
    "ema_volume_fixed": EMAVolumeFixed,
    "atr_breakout_fixed": ATRBreakoutFixed,
    "liquidity_sweep_v1": LiquiditySweepV1,
    "rsi_trend_v4": RSITrendV4,
    "vol_filtered_momentum_v1": VolFilteredMomentumV1,
}


ALIASES = {
    "rsi_v3": RSIOnlyV3,
    "ema_vol_v3": EMAVolumeV3,
    "atr_v3": ATRBreakoutV3,
    "momentum_v3": MomentumCrossoverV3,
    "mtf_v3": MultiTimeframeV3,
    "liquidity_sweep": LiquiditySweepV1,
    "vol_momo_v1": VolFilteredMomentumV1,
}


STRATEGIES = {**REGISTRY, **ALIASES}


RESEARCH_REGISTRY = {
    "gold_v2": GoldV2,
    "rsi_reversion_v1": RsiReversionV1,
}


def get_strategy(name: str, **parameters: object):
    if name not in STRATEGIES:
        raise KeyError(f"Unknown strategy: {name}. Available: {list(STRATEGIES.keys())}")
    strategy_class = STRATEGIES[name]
    signature = inspect.signature(strategy_class)
    accepted = {key: value for key, value in parameters.items() if key in signature.parameters}
    return strategy_class(**accepted)

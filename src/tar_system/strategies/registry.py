"""Strategy registry"""
from .goldv2_v2 import GoldV2V2
from .rsi_only_v3 import RSIOnlyV3
from .ema_volume_v3 import EMAVolumeV3
from .atr_breakout_v3 import ATRBreakoutV3
from .momentum_crossover_v3 import MomentumCrossoverV3
from .multi_timeframe_v3 import MultiTimeframeV3
from .ema_volume_fixed import EMAVolumeFixed
from .atr_breakout_fixed import ATRBreakoutFixed
from .vol_filtered_momentum_v1 import VolFilteredMomentumV1
from .gold_v2 import GoldV2
from .rsi_reversion_v1 import RsiReversionV1
from .arsb_v1 import ArsbV1
from .gold_orb_v1 import GoldOrbV1
from .rsi_trend_v4 import RSITrendV4

# Canonical strategies — no aliases
REGISTRY = {
    "goldv2_v2": GoldV2V2,
    "rsi_only_v3": RSIOnlyV3,
    "ema_volume_v3": EMAVolumeV3,
    "atr_breakout_v3": ATRBreakoutV3,
    "momentum_crossover_v3": MomentumCrossoverV3,
    "multi_timeframe_v3": MultiTimeframeV3,
    "ema_volume_fixed": EMAVolumeFixed,
    "atr_breakout_fixed": ATRBreakoutFixed,
    "vol_filtered_momentum_v1": VolFilteredMomentumV1,
    "gold_v2": GoldV2,
    "rsi_reversion_v1": RsiReversionV1,
    "arsb_v1": ArsbV1,
    "gold_orb_v1": GoldOrbV1,
    "rsi_trend_v4": RSITrendV4,
}

# Short aliases — not in REGISTRY
ALIASES = {
    "rsi_v3": RSIOnlyV3,
    "ema_vol_v3": EMAVolumeV3,
    "atr_v3": ATRBreakoutV3,
    "momentum_v3": MomentumCrossoverV3,
    "mtf_v3": MultiTimeframeV3,
    "vol_momo_v1": VolFilteredMomentumV1,
}

# Research-only strategies (not in production rotation)
RESEARCH_REGISTRY = {"gold_v2", "rsi_reversion_v1"}

# Legacy combined dict for backwards compatibility
STRATEGIES = {**REGISTRY, **ALIASES}


def get_strategy(name, **kwargs):
    if name in REGISTRY:
        return REGISTRY[name](**kwargs)
    if name in ALIASES:
        return ALIASES[name](**kwargs)
    raise KeyError(f"Unknown strategy: {name}. Available: {list(REGISTRY.keys())}")


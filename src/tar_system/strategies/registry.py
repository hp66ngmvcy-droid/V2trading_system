"""Strategy registry."""

from __future__ import annotations

from tar_system.strategies.gold_v2 import GoldV2
from tar_system.strategies.rsi_reversion_v1 import RsiReversionV1

REGISTRY = {"gold_v2": GoldV2, "rsi_reversion_v1": RsiReversionV1}


def get_strategy(name: str, **kwargs: object) -> object:
    if name not in REGISTRY:
        raise KeyError(f"Unknown strategy: {name}")
    return REGISTRY[name](**kwargs)

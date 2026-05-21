"""
Paper Trading Strategy Research Module

Implements quantitative trading strategies from academic papers:
- Mean Reversion (Serban 2010)
- Momentum (LeBaron 1999)
- Opening Range Breakout (ORB Research 2013)
- Volatility Breakout (2025)
- Hybrid Mean Reversion + Momentum (Serban 2010)
"""

from .strategy_importer import (
    PaperStrategy,
    StrategyParams,
    PaperReference,
    create_strategy_from_paper,
    PAPER_STRATEGIES,
)
from .strategy_enhancements import (
    AdaptiveParameters,
    VolumeConfirmation,
    RegimeDetection,
    MultiTimeframeFilter,
    PerformanceAdaptation,
)
from .multi_asset_backtester import MultiAssetBacktester

__all__ = [
    "PaperStrategy",
    "StrategyParams",
    "PaperReference",
    "create_strategy_from_paper",
    "PAPER_STRATEGIES",
    "AdaptiveParameters",
    "VolumeConfirmation",
    "RegimeDetection",
    "MultiTimeframeFilter",
    "PerformanceAdaptation",
    "MultiAssetBacktester",
]

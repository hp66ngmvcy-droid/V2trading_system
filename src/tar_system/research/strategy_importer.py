"""
Academic Paper Strategy Importer

Converts quantitative trading research papers into executable strategy classes.
Each strategy is backtestable and includes citations and peer-review references.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class PaperReference:
    """Citation tracking for academic paper origin"""

    title: str
    authors: str
    year: int
    journal: str
    doi: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "url": self.url,
        }


@dataclass
class StrategyParams:
    """Validated strategy parameters"""

    strategy_name: str
    asset: str = "XAUUSD"
    timeframe: str = "M15"
    lookback_period: int = 20
    entry_threshold: float = 0.01
    exit_percentage: float = 0.02
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.10

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "lookback_period": self.lookback_period,
            "entry_threshold": self.entry_threshold,
            "exit_percentage": self.exit_percentage,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
        }

    @staticmethod
    def validate(params: Dict[str, Any]) -> None:
        """Validate parameter ranges"""
        assert 5 <= params.get("lookback_period", 20) <= 200, "Invalid lookback_period"
        assert 0 < params.get("entry_threshold", 0.01) <= 10, "Invalid entry_threshold"
        assert 0 < params.get("stop_loss_pct", 0.05) <= 1, "Invalid stop_loss_pct"
        assert 0 < params.get("take_profit_pct", 0.10) <= 1, "Invalid take_profit_pct"


class PaperStrategy(ABC):
    """Abstract base class for paper-based academic strategies"""

    def __init__(
        self,
        name: str,
        reference: PaperReference,
        params: StrategyParams,
    ):
        self.name = name
        self.reference = reference
        self.params = params

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, i: int) -> int:
        """
        Generate trading signal at row i
        Returns: 1 (BUY), -1 (SELL), 0 (HOLD)
        """
        pass

    def get_reference(self) -> str:
        """Return formatted citation"""
        return (
            f"{self.reference.authors} ({self.reference.year}). "
            f"\"{self.reference.title}\" - {self.reference.journal}"
        )


class MeanReversionStrategy(PaperStrategy):
    """
    Mean Reversion Strategy from Serban (2010)
    Concept: Price deviates from mean, expects reversion
    Best For: Ranging/choppy markets, XAUUSD, EURUSD
    """

    def generate_signal(self, df: pd.DataFrame, i: int) -> int:
        if i < self.params.lookback_period:
            return 0

        window = df.iloc[i - self.params.lookback_period : i]
        close = window["close"].values

        mean = np.mean(close)
        std = np.std(close)
        current_price = close[-1]

        threshold = self.params.entry_threshold

        # Buy when price is below mean - 2 std dev
        if current_price < mean - threshold * std:
            return 1

        # Sell when price is above mean + 2 std dev
        if current_price > mean + threshold * std:
            return -1

        return 0


class MomentumStrategy(PaperStrategy):
    """
    Momentum Strategy from LeBaron (1999)
    Concept: Trend following based on rate of change
    Best For: Trending markets
    """

    def generate_signal(self, df: pd.DataFrame, i: int) -> int:
        if i < self.params.lookback_period:
            return 0

        window = df.iloc[i - self.params.lookback_period : i]
        close = window["close"].values

        # Calculate momentum (ROC)
        roc = (close[-1] - close[0]) / close[0]

        threshold = self.params.entry_threshold

        # Buy if momentum is positive
        if roc > threshold:
            return 1

        # Sell if momentum is negative
        if roc < -threshold:
            return -1

        return 0


class ORBStrategy(PaperStrategy):
    """
    Opening Range Breakout (ORB) Strategy (2013)
    Concept: Trade breakouts of first N period's range
    Best For: Intraday/volatile assets (gold, indices)
    """

    def generate_signal(self, df: pd.DataFrame, i: int) -> int:
        if i < self.params.lookback_period:
            return 0

        window = df.iloc[i - self.params.lookback_period : i]
        high = window["high"].values
        low = window["low"].values
        close = window["close"].values

        opening_high = high[0]
        opening_low = low[0]
        opening_range = opening_high - opening_low

        current_price = close[-1]
        threshold_pips = self.params.entry_threshold

        # Buy on breakout above opening range high
        if current_price > opening_high + threshold_pips:
            return 1

        # Sell on breakout below opening range low
        if current_price < opening_low - threshold_pips:
            return -1

        return 0


class VolatilityBreakoutStrategy(PaperStrategy):
    """
    Volatility Breakout Strategy (2025)
    Concept: Detect squeeze (low vol), trade breakout (high vol)
    Best For: Commodities (gold, oil)
    """

    def generate_signal(self, df: pd.DataFrame, i: int) -> int:
        if i < self.params.lookback_period * 2:
            return 0

        # Get two windows: recent and historical
        recent_window = df.iloc[i - self.params.lookback_period : i]
        historical_window = df.iloc[
            i - self.params.lookback_period * 2 : i - self.params.lookback_period
        ]

        recent_vol = recent_window["close"].std()
        historical_vol = historical_window["close"].std()

        vol_ratio = recent_vol / (historical_vol + 1e-8)
        threshold = self.params.entry_threshold

        # Buy if recent volatility > historical (breakout signal)
        if vol_ratio > threshold:
            return 1

        # Sell if volatility ratio is low (potential breakout from other direction)
        if vol_ratio < 1 / threshold:
            return -1

        return 0


class HybridStrategy(PaperStrategy):
    """
    Hybrid Mean Reversion + Momentum Strategy (Serban 2010)
    Concept: Both signals must align before entry (reduces false signals)
    Best For: Multi-asset trading, reduces false signals
    """

    def generate_signal(self, df: pd.DataFrame, i: int) -> int:
        if i < self.params.lookback_period:
            return 0

        window = df.iloc[i - self.params.lookback_period : i]
        close = window["close"].values

        # Mean Reversion Signal
        mean = np.mean(close)
        std = np.std(close)
        current_price = close[-1]
        threshold_mr = self.params.entry_threshold

        mr_signal = 0
        if current_price < mean - threshold_mr * std:
            mr_signal = 1
        elif current_price > mean + threshold_mr * std:
            mr_signal = -1

        # Momentum Signal
        roc = (close[-1] - close[0]) / close[0]
        threshold_mom = self.params.entry_threshold * 0.5  # Lower for convergence

        mom_signal = 0
        if roc > threshold_mom:
            mom_signal = 1
        elif roc < -threshold_mom:
            mom_signal = -1

        # Combined signal - both must agree
        if mr_signal == 1 and mom_signal == 1:
            return 1
        elif mr_signal == -1 and mom_signal == -1:
            return -1

        return 0


# Paper Strategy Registry
PAPER_STRATEGIES: Dict[str, Tuple[type, PaperReference, Dict[str, Any]]] = {
    "mean_reversion": (
        MeanReversionStrategy,
        PaperReference(
            title="Combining mean reversion and momentum trading strategies in foreign exchange markets",
            authors="Serban, A. et al.",
            year=2010,
            journal="Journal of Banking & Finance",
            doi="10.1016/j.jbankfin.2009.10.003",
        ),
        {
            "lookback_period": 20,
            "entry_threshold": 2.0,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10,
        },
    ),
    "momentum": (
        MomentumStrategy,
        PaperReference(
            title="Technical Trading Rule Profitability and Foreign Exchange Intervention",
            authors="LeBaron, B.",
            year=1999,
            journal="Journal of International Economics",
            doi="10.1016/S0022-1996(99)00009-9",
        ),
        {
            "lookback_period": 20,
            "entry_threshold": 0.01,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10,
        },
    ),
    "orb": (
        ORBStrategy,
        PaperReference(
            title="Assessing the profitability of intraday opening range breakout strategies",
            authors="Academic researchers",
            year=2013,
            journal="International Journal of Financial Markets and Derivatives",
        ),
        {
            "lookback_period": 15,
            "entry_threshold": 0.5,
            "stop_loss_pct": 0.03,
            "take_profit_pct": 0.08,
        },
    ),
    "volatility_breakout": (
        VolatilityBreakoutStrategy,
        PaperReference(
            title="Volatility-Based Trading Systems: A Dual-Model Analysis",
            authors="Quantitative trading researchers",
            year=2025,
            journal="SSRN/Academic Paper",
        ),
        {
            "lookback_period": 20,
            "entry_threshold": 1.5,
            "stop_loss_pct": 0.04,
            "take_profit_pct": 0.12,
        },
    ),
    "hybrid": (
        HybridStrategy,
        PaperReference(
            title="Combining mean reversion and momentum trading strategies in foreign exchange markets",
            authors="Serban, A. et al.",
            year=2010,
            journal="Journal of Banking & Finance",
            doi="10.1016/j.jbankfin.2009.10.003",
        ),
        {
            "lookback_period": 20,
            "entry_threshold": 1.5,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10,
        },
    ),
}


def create_strategy_from_paper(
    strategy_name: str,
    asset: str = "XAUUSD",
    timeframe: str = "M15",
    **param_overrides,
) -> Tuple[PaperStrategy, StrategyParams]:
    """
    Factory function to create strategy from paper

    Args:
        strategy_name: Key in PAPER_STRATEGIES ('mean_reversion', 'momentum', etc)
        asset: Trading asset
        timeframe: Time frame
        **param_overrides: Override default parameters

    Returns:
        Tuple of (strategy_instance, params)
    """
    if strategy_name not in PAPER_STRATEGIES:
        raise ValueError(
            f"Unknown strategy: {strategy_name}. "
            f"Available: {list(PAPER_STRATEGIES.keys())}"
        )

    strategy_class, reference, default_params = PAPER_STRATEGIES[strategy_name]

    # Merge defaults with overrides
    final_params = {
        **default_params,
        **param_overrides,
        "strategy_name": strategy_name,
        "asset": asset,
        "timeframe": timeframe,
    }

    # Validate
    StrategyParams.validate(final_params)

    # Create params object
    params = StrategyParams(**final_params)

    # Create strategy instance
    strategy = strategy_class(strategy_name, reference, params)

    return strategy, params

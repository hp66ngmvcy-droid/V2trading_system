"""Local asset profiles used by strategy and broker-aware risk layers."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AssetProfile:
    symbol: str
    asset_class: str
    volatility_level: str
    preferred_regimes: list[str]
    blocked_regimes: list[str]
    slippage_assumption: str | float
    spread_assumption: float
    risk_limit: float
    session_model: str
    available: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def slippage_bps(self) -> float:
        if isinstance(self.slippage_assumption, (int, float)):
            return float(self.slippage_assumption)
        return {
            "low": 1.0,
            "medium": 3.0,
            "medium_high": 5.0,
            "high": 8.0,
        }.get(self.slippage_assumption.lower(), 3.0)


ASSET_PROFILES: dict[str, AssetProfile] = {
    "XAUUSD": AssetProfile("XAUUSD", "metals", "medium_high", ["TRENDING"], ["VOLATILE"], "medium", 15.0, 0.01, "LONDON_NY", True),
    "XAGUSD": AssetProfile("XAGUSD", "metals", "medium_high", ["TRENDING"], ["VOLATILE"], "medium", 3.0, 0.01, "LONDON_NY", False, "no data file yet, stub for future use"),
    "BTCUSD": AssetProfile("BTCUSD", "crypto", "high", ["TRENDING", "VOLATILE"], [], "high", 50.0, 0.005, "ALL_HOURS", True),
    "EURUSD": AssetProfile("EURUSD", "forex", "low_medium", ["TRENDING"], ["VOLATILE"], "low", 0.5, 0.01, "LONDON_NY", True),
    "GBPUSD": AssetProfile("GBPUSD", "forex", "medium", ["TRENDING", "RANGING"], ["VOLATILE"], "low", 0.8, 0.01, "LONDON_NY", True),
    "USDJPY": AssetProfile("USDJPY", "forex", "low_medium", ["TRENDING"], ["VOLATILE"], "low", 0.5, 0.01, "LONDON_NY", True),
    "USDCAD": AssetProfile("USDCAD", "forex", "low_medium", ["TRENDING", "RANGING"], ["VOLATILE"], "low", 1.0, 0.01, "LONDON_NY", True),
    "AUDUSD": AssetProfile("AUDUSD", "forex", "low_medium", ["TRENDING", "RANGING"], ["VOLATILE"], "low", 0.7, 0.01, "LONDON_NY", True),
    "USOUSD": AssetProfile("USOUSD", "commodity", "medium_high", ["TRENDING"], ["VOLATILE"], "medium_high", 3.0, 0.01, "LONDON_NY", True, "WTI crude oil CFD 1 lot = 1000 barrels; avoid trading during EIA report Wednesdays 15:30 UTC"),
    "ETHUSD": AssetProfile("ETHUSD", "crypto", "high", ["TRENDING", "VOLATILE"], [], "high", 30.0, 0.005, "ALL_HOURS", False, "no data file yet, stub for future use"),
    "XRPUSD": AssetProfile("XRPUSD", "crypto", "high", ["TRENDING", "VOLATILE"], [], "high", 20.0, 0.005, "ALL_HOURS", False, "no data file yet, stub for future use"),
}

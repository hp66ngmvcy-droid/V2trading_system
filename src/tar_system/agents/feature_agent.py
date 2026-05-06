"""Feature agent wrapper."""

from __future__ import annotations

from tar_system.features.engineering import build_features


class FeatureAgent:
    def run(self, df: object, symbol: str, timeframe: str) -> object:
        return build_features(df, symbol, timeframe)  # type: ignore[arg-type]

"""Data validation agent wrapper."""

from __future__ import annotations

from tar_system.data.validator import validate_ohlcv


class DataValidationAgent:
    def run(self, df: object) -> object:
        return validate_ohlcv(df)  # type: ignore[arg-type]

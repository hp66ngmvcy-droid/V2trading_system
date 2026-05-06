"""Dashboard table helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd


def leaderboard_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    columns = [
        "strategy",
        "asset",
        "symbol",
        "timeframe",
        "win_rate",
        "profit_factor",
        "max_drawdown",
        "trade_count",
        "expectancy",
        "score",
        "verdict",
        "environment_state",
        "last_tested_date",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows).reindex(columns=columns)

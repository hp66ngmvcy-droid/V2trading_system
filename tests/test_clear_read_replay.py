from __future__ import annotations

import pandas as pd

import pytest

from tar_system.signals.clear_read_replay import (
    compare_clear_read_modes,
    compare_trend_continuation_with_confirmation,
    sequence_trend_continuation_equity,
    split_trend_continuation_equity_by_year,
)


def _features() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    closes = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
    for index, close in enumerate(closes):
        rows.append(
            {
                "timestamp": pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(hours=index),
                "symbol": "BTCUSD",
                "timeframe": "H1",
                "open": close - 0.8,
                "high": close + 0.2,
                "low": close - 1.0,
                "close": close,
                "ema_fast": close + 1.0,
                "ema_slow": close - 1.0,
                "ema_fast_slope": 0.001,
                "rsi": 58.0,
                "atr": 1.0,
                "macd": 1.0,
                "macd_signal": 0.5,
                "volume": 150.0,
                "volume_sma": 100.0,
                "prior_rolling_high": close + 5.0,
                "prior_rolling_low": close - 5.0,
                "rolling_volatility": 0.01,
                "range_compression": 0.4,
                "is_liquid_session": True,
            }
        )
    return pd.DataFrame(rows)


def _m15_features() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for hour in range(6):
        for minute in (15, 30, 45):
            close = 100.0 + hour + minute / 60
            rows.append(
                {
                    "timestamp": pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(hours=hour, minutes=minute),
                    "symbol": "BTCUSD",
                    "timeframe": "M15",
                    "open": close - 0.8,
                    "high": close + 0.2,
                    "low": close - 1.0,
                    "close": close,
                    "ema_fast": close + 1.0,
                    "ema_slow": close - 1.0,
                    "ema_fast_slope": 0.001,
                    "rsi": 58.0,
                    "atr": 1.0,
                    "macd": 1.0,
                    "macd_signal": 0.5,
                    "volume": 150.0,
                    "volume_sma": 100.0,
                    "prior_rolling_high": close + 5.0,
                    "prior_rolling_low": close - 5.0,
                    "rolling_volatility": 0.01,
                    "range_compression": 0.4,
                    "is_liquid_session": True,
                }
            )
    return pd.DataFrame(rows)


def test_replay_compares_strict_and_trend_continuation_without_writing_files() -> None:
    summary = compare_clear_read_modes(_features(), horizons=(2,), cost_bps=10.0)

    strict = summary["strict_sweep"]
    trend = summary["trend_continuation"]

    assert strict.paper_only is True
    assert trend.paper_only is True
    assert strict.side_counts["WAIT"] == 6
    assert trend.side_counts["LONG"] == 6
    assert trend.movement["LONG"][2].count == 4
    assert trend.movement["LONG"][2].avg_favorable_pct > 0
    assert trend.movement["LONG"][2].avg_adverse_pct >= 0
    assert trend.movement["LONG"][2].avg_net_exit_pct > 0
    assert trend.movement["LONG"][2].win_rate_after_cost == 1.0


def test_replay_can_gate_trend_continuation_with_m15_confirmation() -> None:
    summary = compare_trend_continuation_with_confirmation(_features(), _m15_features(), horizons=(2,), cost_bps=10.0)

    base = summary["trend_continuation"]
    confirmed = summary["trend_continuation_m15_confirmed"]

    assert base.side_counts["LONG"] == 6
    assert confirmed.side_counts["LONG"] == 5
    assert confirmed.side_counts["WAIT"] == 1
    assert confirmed.movement["LONG"][2].count == 3
    assert confirmed.paper_only is True


def test_replay_sequences_non_overlapping_long_only_equity() -> None:
    summary = sequence_trend_continuation_equity(_features(), side="LONG", horizon=2, cost_bps=10.0)

    assert summary.paper_only is True
    assert summary.side == "LONG"
    assert summary.trades == 2
    assert summary.cumulative_return_pct > 0
    assert summary.max_drawdown_pct == 0.0
    assert summary.win_rate == 1.0
    assert summary.profit_factor > 0


def test_replay_sequence_can_block_high_volatility_entries() -> None:
    summary = sequence_trend_continuation_equity(
        _features(),
        side="LONG",
        horizon=2,
        cost_bps=10.0,
        max_rolling_volatility=0.005,
    )

    assert summary.paper_only is True
    assert summary.trades == 0


def test_replay_splits_equity_sequence_by_year() -> None:
    first = _features()
    second = _features()
    second["timestamp"] = second["timestamp"] + pd.DateOffset(years=1)
    combined = pd.concat([first, second], ignore_index=True)

    result = split_trend_continuation_equity_by_year(combined, side="LONG", horizon=2, cost_bps=10.0)

    assert set(result) == {2026, 2027}
    assert result[2026].paper_only is True
    assert result[2026].trades == 2
    assert result[2027].trades == 2


def test_replay_sequence_rejects_unknown_side() -> None:
    with pytest.raises(ValueError, match="side must be LONG or SHORT"):
        sequence_trend_continuation_equity(_features(), side="BOTH", horizon=2)

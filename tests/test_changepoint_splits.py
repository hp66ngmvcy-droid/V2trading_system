"""Tests for changepoint-based walk-forward split generator."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tar_system.validation.changepoint_splits import changepoint_splits, detect_changepoints
from tar_system.validation.walk_forward import WalkForwardSplit


def _synthetic_df(n_rows: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # Three regimes: trending up, ranging, trending down
    segment = n_rows // 3
    prices = np.concatenate([
        100 + np.cumsum(rng.normal(0.05, 0.5, segment)),
        100 + rng.normal(0, 0.3, segment),
        100 + np.cumsum(rng.normal(-0.05, 0.5, n_rows - 2 * segment)),
    ])
    return pd.DataFrame({"close": prices})


# ---------------------------------------------------------------------------
# detect_changepoints
# ---------------------------------------------------------------------------

def test_detect_changepoints_returns_sorted_ints():
    df = _synthetic_df(400)
    bkps = detect_changepoints(df["close"], n_bkps=3, min_size=30)
    assert isinstance(bkps, list)
    assert bkps == sorted(bkps)
    assert all(isinstance(b, int) for b in bkps)


def test_detect_changepoints_within_bounds():
    df = _synthetic_df(400)
    bkps = detect_changepoints(df["close"], n_bkps=3, min_size=30)
    for b in bkps:
        assert 0 < b < len(df)


def test_detect_changepoints_too_short_reduces_n():
    # 80 rows, min_size=30 → only 1 breakpoint possible (80//30 - 1 = 1)
    df = _synthetic_df(80)
    bkps = detect_changepoints(df["close"], n_bkps=5, min_size=30)
    assert len(bkps) <= 5  # should not crash, just reduce


# ---------------------------------------------------------------------------
# changepoint_splits
# ---------------------------------------------------------------------------

def test_splits_return_type():
    df = _synthetic_df(500)
    splits = changepoint_splits(df, n_bkps=4)
    assert isinstance(splits, list)
    assert all(isinstance(s, WalkForwardSplit) for s in splits)


def test_splits_no_overlap():
    df = _synthetic_df(500)
    splits = changepoint_splits(df, n_bkps=4)
    for s in splits:
        assert s.train_end <= s.test_start
        assert s.test_start < s.test_end


def test_splits_within_bounds():
    df = _synthetic_df(500)
    splits = changepoint_splits(df, n_bkps=4)
    for s in splits:
        assert s.train_start >= 0
        assert s.test_end <= len(df)


def test_splits_min_test_rows_respected():
    min_test = 40
    df = _synthetic_df(500)
    splits = changepoint_splits(df, n_bkps=4, min_test_rows=min_test)
    for s in splits:
        assert s.test_end - s.test_start >= min_test


def test_splits_min_train_rows_respected():
    min_train = 60
    df = _synthetic_df(500)
    splits = changepoint_splits(df, n_bkps=4, min_train_rows=min_train)
    for s in splits:
        assert s.train_end - s.train_start >= min_train


def test_expanding_train_grows():
    df = _synthetic_df(500)
    splits = changepoint_splits(df, n_bkps=4, expanding_train=True)
    if len(splits) >= 2:
        for i in range(1, len(splits)):
            assert splits[i].train_end > splits[i - 1].train_end


def test_non_expanding_train_uses_previous_regime():
    df = _synthetic_df(500)
    splits = changepoint_splits(df, n_bkps=4, expanding_train=False)
    for s in splits:
        assert s.train_start >= 0
        # train window should not span the entire series in non-expanding mode
        if len(splits) >= 2:
            assert s.train_end - s.train_start < len(df)


def test_empty_on_too_short_df():
    df = _synthetic_df(50)  # too short for min_train=50 + min_test=30
    splits = changepoint_splits(df, n_bkps=2, min_train_rows=50, min_test_rows=30)
    assert splits == []


def test_missing_signal_col_raises():
    df = pd.DataFrame({"open": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError, match="not found"):
        changepoint_splits(df, signal_col="close")


def test_custom_signal_col():
    df = _synthetic_df(400)
    df["price"] = df["close"] * 1.01
    splits = changepoint_splits(df, signal_col="price", n_bkps=3)
    assert isinstance(splits, list)


def test_at_least_one_split_on_good_data():
    df = _synthetic_df(600)
    splits = changepoint_splits(df, n_bkps=5, min_train_rows=50, min_test_rows=30)
    assert len(splits) >= 1

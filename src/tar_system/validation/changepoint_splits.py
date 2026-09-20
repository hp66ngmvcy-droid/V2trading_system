"""
Changepoint-based walk-forward split generator.

Uses ruptures (Pelt algorithm) to detect structural breakpoints in a price
series, then uses those breakpoints as natural train/test boundaries instead
of fixed-size windows.

Why: fixed windows may split mid-regime, contaminating test sets with the
same market condition as training. Changepoint boundaries align splits with
actual market structure shifts.

Returns list[WalkForwardSplit] — same interface as rolling_splits() in
walk_forward.py, so it is a drop-in alternative.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from tar_system.validation.walk_forward import WalkForwardSplit

logger = logging.getLogger(__name__)


def _log_returns(series: pd.Series) -> np.ndarray:
    """Convert price series to log returns for changepoint detection."""
    prices = series.to_numpy(dtype=float)
    returns = np.diff(np.log(np.maximum(prices, 1e-10)))
    return returns


def detect_changepoints(
    series: pd.Series,
    n_bkps: int = 5,
    model: str = "rbf",
    min_size: int = 30,
) -> list[int]:
    """
    Detect structural breakpoints in a price series using ruptures Pelt.

    Parameters
    ----------
    series : pd.Series
        Price series (e.g. 'close' column).
    n_bkps : int
        Number of breakpoints to find.
    model : str
        ruptures cost model. 'rbf' is robust to financial noise.
    min_size : int
        Minimum number of rows between breakpoints.

    Returns
    -------
    list[int]
        Row indices of breakpoints (each is the first row of the new segment).
        Does NOT include 0 or len(series).
    """
    try:
        import ruptures as rpt
    except ImportError:
        raise RuntimeError(
            "ruptures is not installed. Run: pip install ruptures"
        )

    signal = _log_returns(series).reshape(-1, 1)
    if len(signal) < min_size * (n_bkps + 1):
        logger.warning(
            "Not enough rows (%d) for %d breakpoints with min_size=%d. "
            "Reducing n_bkps.",
            len(signal), n_bkps, min_size,
        )
        n_bkps = max(1, len(signal) // min_size - 1)

    algo = rpt.Pelt(model=model, min_size=min_size).fit(signal)
    # ruptures returns breakpoints including len(signal); exclude the last one
    raw = algo.predict(pen=1.0)
    breakpoints = [bp for bp in raw if bp < len(signal)]

    # If Pelt with pen=1.0 finds too many, cap to n_bkps evenly spaced ones
    if len(breakpoints) > n_bkps:
        step = len(breakpoints) // n_bkps
        breakpoints = breakpoints[step - 1 :: step][:n_bkps]

    # Shift back by 1: log_returns has len(series)-1 rows; map to price index
    # breakpoint at returns index i means the regime shifts at price index i+1
    breakpoints = [bp + 1 for bp in breakpoints]

    logger.info("Detected %d changepoints at rows: %s", len(breakpoints), breakpoints)
    return sorted(breakpoints)


def changepoint_splits(
    df: pd.DataFrame,
    signal_col: str = "close",
    n_bkps: int = 5,
    min_test_rows: int = 30,
    min_train_rows: int = 50,
    expanding_train: bool = True,
) -> list[WalkForwardSplit]:
    """
    Build walk-forward splits aligned to structural breakpoints.

    Each test window covers exactly one regime (the segment between two
    consecutive breakpoints). The training window either expands from row 0
    (expanding_train=True, default) or uses only the previous regime as train
    (expanding_train=False).

    Parameters
    ----------
    df : pd.DataFrame
        Feature DataFrame. Must contain signal_col.
    signal_col : str
        Column used for changepoint detection (default: 'close').
    n_bkps : int
        Target number of breakpoints (actual count may be lower).
    min_test_rows : int
        Minimum rows required in a test window; short regimes are skipped.
    min_train_rows : int
        Minimum rows required in a train window; splits with too little train
        data are skipped.
    expanding_train : bool
        If True, train window grows from row 0 to the split boundary.
        If False, train window = previous regime only.

    Returns
    -------
    list[WalkForwardSplit]
        Ready to pass to run_walk_forward or used directly with the backtest
        engine. Empty list if not enough data.
    """
    if signal_col not in df.columns:
        raise ValueError(f"Column {signal_col!r} not found in DataFrame.")

    row_count = len(df)
    if row_count < min_train_rows + min_test_rows:
        logger.warning(
            "DataFrame too short (%d rows) for changepoint splits "
            "(need >= %d). Returning empty.",
            row_count, min_train_rows + min_test_rows,
        )
        return []

    breakpoints = detect_changepoints(
        df[signal_col],
        n_bkps=n_bkps,
        min_size=min_test_rows,
    )

    # Build boundary list: 0, bp1, bp2, ..., bpN, row_count
    boundaries = [0] + breakpoints + [row_count]

    splits: list[WalkForwardSplit] = []

    for i in range(1, len(boundaries) - 1):
        test_start = boundaries[i]
        test_end = boundaries[i + 1]

        if expanding_train:
            train_start = 0
            train_end = test_start
        else:
            train_start = boundaries[i - 1]
            train_end = test_start

        test_rows = test_end - test_start
        train_rows = train_end - train_start

        if test_rows < min_test_rows:
            logger.debug(
                "Skipping split %d: test window too short (%d < %d rows).",
                i, test_rows, min_test_rows,
            )
            continue

        if train_rows < min_train_rows:
            logger.debug(
                "Skipping split %d: train window too short (%d < %d rows).",
                i, train_rows, min_train_rows,
            )
            continue

        splits.append(WalkForwardSplit(
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))

    logger.info(
        "changepoint_splits: %d usable splits from %d breakpoints "
        "(expanding_train=%s).",
        len(splits), len(breakpoints), expanding_train,
    )
    return splits

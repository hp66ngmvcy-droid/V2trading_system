"""Cross-Asset Correlation V2 — VIX onset trigger + correlation persistence.

Improvements over V1:
  1. VIX onset trigger: fire on 5-day VIX spike (>15% rise from 5-day min)
     rather than VIX level. Academic edge lives in first 15 days post-shock.
  2. Correlation persistence: require corr < threshold for N consecutive days
     (min_corr_days), reducing false-positive single-day divergence signals.
  3. Wider default stop/target: atr_multiplier=2.5, reward_risk=3.0.

Academic basis: Baur & Lucey (2010), Connolly et al (2005).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.strategies.base import Signal

_REPO = Path(__file__).resolve().parents[3]
_VALIDATED = _REPO / "data" / "validated"


def _load_close(symbol_tf: str) -> pd.Series | None:
    path = _VALIDATED / f"{symbol_tf}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.normalize()
    return df.set_index("timestamp")["close"]


@dataclass
class CrossAssetCorrelationV2:
    corr_window: int = 20
    vix_spike_pct: float = 1.15       # 5-day VIX / 5-day min > this → onset
    vix_lookback: int = 5
    corr_threshold: float = -0.3
    min_corr_days: int = 3            # consecutive days corr must stay below threshold
    dxy_slope_window: int = 5
    dxy_slope_suppress: float = 0.3
    atr_multiplier: float = 2.5       # wider stop (v1 was 1.5)
    reward_risk: float = 3.0          # wider target (v1 was 2.0)

    name: str = "cross_asset_correlation_v2"
    version: str = "0.1.0"

    _gold_ret: deque = field(default_factory=deque, init=False, repr=False)
    _nq_ret: deque = field(default_factory=deque, init=False, repr=False)
    _gold_prev: float = field(default=0.0, init=False, repr=False)
    _nq_prev: float = field(default=0.0, init=False, repr=False)
    _dxy_hist: deque = field(default_factory=deque, init=False, repr=False)
    _vix_hist: deque = field(default_factory=deque, init=False, repr=False)
    _consec_corr_days: int = field(default=0, init=False, repr=False)
    _vix: pd.Series | None = field(default=None, init=False, repr=False)
    _nq: pd.Series | None = field(default=None, init=False, repr=False)
    _dxy: pd.Series | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._gold_ret = deque(maxlen=self.corr_window)
        self._nq_ret = deque(maxlen=self.corr_window)
        self._dxy_hist = deque(maxlen=self.dxy_slope_window)
        self._vix_hist = deque(maxlen=self.vix_lookback)
        self._vix = _load_close("VIX_D1")
        self._nq = _load_close("NQ_D1")
        self._dxy = _load_close("DXY_D1")

    def _get(self, series: pd.Series | None, ts: pd.Timestamp) -> float | None:
        if series is None:
            return None
        key = ts.normalize()
        return float(series.loc[key]) if key in series.index else None

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        entry = float(row["close"])
        atr = float(row.get("atr", 0) or 0)
        ts = pd.Timestamp(row["timestamp"])

        base = {
            "timestamp": ts,
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {"regime": regime},
        }
        hold = Signal(side="HOLD", confidence=0.0, stop_loss=None,
                      take_profit=None, reason_code=rc.SIGNAL_HOLD, **base)

        vix = self._get(self._vix, ts)
        nq = self._get(self._nq, ts)
        dxy = self._get(self._dxy, ts)

        # Accumulate daily returns
        if self._gold_prev > 0:
            self._gold_ret.append((entry - self._gold_prev) / self._gold_prev)
        self._gold_prev = entry

        if nq is not None:
            if self._nq_prev > 0:
                self._nq_ret.append((nq - self._nq_prev) / self._nq_prev)
            self._nq_prev = nq

        if dxy is not None:
            self._dxy_hist.append(dxy)

        if vix is not None:
            self._vix_hist.append(vix)

        # Need full return window
        if len(self._gold_ret) < self.corr_window or len(self._nq_ret) < self.corr_window:
            return hold

        # VIX onset trigger: spike from 5-day min (replaces static VIX level gate)
        if len(self._vix_hist) < self.vix_lookback:
            return hold
        vix_min = min(self._vix_hist)
        if vix_min <= 0 or (self._vix_hist[-1] / vix_min) < self.vix_spike_pct:
            return hold

        # DXY suppression
        if len(self._dxy_hist) >= self.dxy_slope_window:
            dxy_old = self._dxy_hist[0]
            if dxy_old and dxy_old > 0:
                dxy_pct = (self._dxy_hist[-1] - dxy_old) / dxy_old * 100
                if dxy_pct > self.dxy_slope_suppress:
                    return hold

        # Rolling correlation
        corr = float(pd.Series(list(self._gold_ret)).corr(pd.Series(list(self._nq_ret))))
        if pd.isna(corr):
            self._consec_corr_days = 0
            return hold

        # Correlation persistence: count consecutive days below threshold
        if corr < self.corr_threshold:
            self._consec_corr_days += 1
        else:
            self._consec_corr_days = 0

        if self._consec_corr_days < self.min_corr_days:
            return hold

        # All conditions met — long Gold
        vix_ratio = self._vix_hist[-1] / vix_min
        confidence = min(0.95, 0.5 + (vix_ratio - 1.0) * 1.5 + abs(corr) * 0.3)
        stop_dist = atr * self.atr_multiplier if atr > 0 else entry * 0.005

        return Signal(
            side="BUY",
            confidence=confidence,
            stop_loss=entry - stop_dist,
            take_profit=entry + stop_dist * self.reward_risk,
            reason_code=rc.SIGNAL_BUY,
            **{**base, "metadata": {
                "regime": regime,
                "vix": round(vix, 2) if vix else None,
                "vix_ratio": round(vix_ratio, 3),
                "nq_gold_corr": round(corr, 3),
                "consec_corr_days": self._consec_corr_days,
                "dxy": round(dxy, 3) if dxy else None,
            }},
        )

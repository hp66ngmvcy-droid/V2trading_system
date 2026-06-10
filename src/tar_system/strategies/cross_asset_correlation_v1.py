"""Cross-Asset Correlation V1 — VIX/NQ/DXY regime signal for Gold long.

Signal logic:
  BUY Gold when:
    - Rolling correlation(Gold, NQ) < corr_threshold (negative divergence)
    - VIX >= vix_threshold (stress regime active)
    - DXY 10-bar slope <= dxy_slope_suppress% (dollar not surging)

Academic basis: Baur & Lucey (2010), Connolly et al (2005).
Key risk: 2022 inflation regime breaks correlation — no fix yet, fails OOS.
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
class CrossAssetCorrelationV1:
    corr_window: int = 20
    vix_threshold: float = 25.0
    corr_threshold: float = -0.3
    dxy_slope_window: int = 10
    dxy_slope_suppress: float = 0.3   # % DXY rise over window → suppress entry
    atr_multiplier: float = 1.5
    reward_risk: float = 2.0

    name: str = "cross_asset_correlation_v1"
    version: str = "0.1.0"

    _gold_hist: deque = field(default_factory=deque, init=False, repr=False)
    _nq_hist: deque = field(default_factory=deque, init=False, repr=False)
    _dxy_hist: deque = field(default_factory=deque, init=False, repr=False)
    _vix: pd.Series | None = field(default=None, init=False, repr=False)
    _nq: pd.Series | None = field(default=None, init=False, repr=False)
    _dxy: pd.Series | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._gold_hist = deque(maxlen=self.corr_window)
        self._nq_hist = deque(maxlen=self.corr_window)
        self._dxy_hist = deque(maxlen=self.dxy_slope_window)
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

        self._gold_hist.append(entry)

        vix = self._get(self._vix, ts)
        nq = self._get(self._nq, ts)
        dxy = self._get(self._dxy, ts)

        if nq is not None:
            self._nq_hist.append(nq)
        if dxy is not None:
            self._dxy_hist.append(dxy)

        # Need full correlation window
        if len(self._gold_hist) < self.corr_window or len(self._nq_hist) < self.corr_window:
            return hold

        # VIX stress gate
        if vix is None or vix < self.vix_threshold:
            return hold

        # DXY suppression — surging dollar overrides gold safe-haven bid
        if len(self._dxy_hist) >= self.dxy_slope_window:
            dxy_old = self._dxy_hist[0]
            if dxy_old and dxy_old > 0:
                dxy_pct = (self._dxy_hist[-1] - dxy_old) / dxy_old * 100
                if dxy_pct > self.dxy_slope_suppress:
                    return hold

        # Rolling correlation Gold vs NQ
        corr = float(pd.Series(list(self._gold_hist)).corr(pd.Series(list(self._nq_hist))))
        if pd.isna(corr) or corr >= self.corr_threshold:
            return hold

        # All conditions met — long Gold
        confidence = min(0.95, 0.5 + (vix - self.vix_threshold) / 30 + abs(corr) * 0.3)
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
                "nq_gold_corr": round(corr, 3),
                "dxy": round(dxy, 3) if dxy else None,
            }},
        )

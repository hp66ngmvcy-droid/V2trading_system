"""Key Level Sweep strategy v1.

Trades daily key levels from morning brief JSON files, confirmed by
price-action sweep/rejection signals on M15 bars.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.data.daily_brief_loader import load_daily_levels, load_macro
from tar_system.strategies.base import Signal

# Cache so we only hit disk once per (date, symbol) pair per run
_brief_cache: dict[tuple[str, str, Path], dict | None] = {}


def _get_levels(
    date: str,
    symbol: str,
    briefs_dir: Path,
    bar_ts: pd.Timestamp | None = None,
) -> dict | None:
    key = (date, symbol, briefs_dir)
    if key not in _brief_cache:
        _brief_cache[key] = load_daily_levels(date, symbol, briefs_dir)
    data = _brief_cache[key]
    if data is None or bar_ts is None:
        return data
    # Look-ahead gate: only use brief if issued_at <= bar_ts.
    # Briefs without issued_at default to 07:00 UTC (London open — conservative).
    issued_raw = data.get("issued_at") or f"{date}T07:00:00+00:00"
    try:
        issued = pd.Timestamp(issued_raw)
        if issued.tzinfo is None:
            issued = issued.tz_localize("UTC")
        bar = bar_ts.tz_localize("UTC") if bar_ts.tzinfo is None else bar_ts.tz_convert("UTC")
        if issued > bar:
            return None
    except Exception:
        pass
    return data


@dataclass
class KeyLevelSweepV1:
    symbol: str = "XAUUSD"
    min_confidence: float = 0.65
    atr_multiplier: float = 2.0
    wick_ratio: float = 0.40
    signal_cooldown_minutes: int = 60
    briefs_dir: Path = Path("data/daily_briefs")
    name: str = "key_level_sweep_v1"
    version: str = "0.1.0"

    def __post_init__(self) -> None:
        self._last_signal_ts: pd.Timestamp | None = None

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        entry = float(row["close"])
        high = float(row["high"])
        low = float(row["low"])
        open_price = float(row["open"])
        atr = float(row.get("atr", 0) or 0)
        ts = pd.Timestamp(row["timestamp"])
        date_str = str(ts.date())

        base = {
            "timestamp": ts,
            "symbol": str(row["symbol"]),
            "timeframe": str(row["timeframe"]),
            "strategy": self.name,
            "version": self.version,
            "entry": entry,
            "metadata": {"regime": regime, "brief_date": date_str},
        }

        hold = Signal(
            side="HOLD",
            confidence=0.0,
            stop_loss=None,
            take_profit=None,
            reason_code=rc.SIGNAL_HOLD,
            **base,
        )

        # ATR floor
        if atr == 0:
            return hold

        # Event-gate: block trading during flagged macro windows
        macro = load_macro(date_str, self.briefs_dir)
        event = macro.get("event_gate", {})
        if event.get("active", False):
            return Signal(
                side="HOLD",
                confidence=0.0,
                stop_loss=None,
                take_profit=None,
                reason_code=rc.EVENT_GATE,
                **base,
            )

        # Cooldown: suppress signals within signal_cooldown_minutes of last signal
        if self._last_signal_ts is not None:
            elapsed = (ts - self._last_signal_ts).total_seconds() / 60
            if elapsed < self.signal_cooldown_minutes:
                return hold

        # Load brief for this day — gated by issued_at to prevent look-ahead
        levels_data = _get_levels(date_str, self.symbol, self.briefs_dir, bar_ts=ts)
        if levels_data is None:
            return hold

        kl = levels_data.get("key_levels", {})
        sell_conf = float(levels_data.get("sell_confidence", 0))
        buy_conf = float(levels_data.get("buy_confidence", 0))
        targets = levels_data.get("top_scenario_targets", [])

        bar_range = max(high - low, 1e-9)

        # No-trade zone: block price drifting in range but not confirmed level sweeps.
        # A valid sell rejection has entry < sell_zone_low (which equals no_trade_high),
        # and a valid buy reclaim has entry > buy_zone_high (which sits inside the zone).
        # So only apply the gate when neither directional zone was swept on this bar.
        ntl = kl.get("no_trade_low")
        nth = kl.get("no_trade_high")
        if ntl is not None and nth is not None:
            ntl_f, nth_f = float(ntl), float(nth)
            if ntl_f <= entry <= nth_f:
                szl_nt = kl.get("sell_zone_low")
                szh_nt = kl.get("sell_zone_high")
                bzl_nt = kl.get("buy_zone_low")
                bzh_nt = kl.get("buy_zone_high")
                sell_swept = (szl_nt is not None and szh_nt is not None
                              and float(szl_nt) <= high <= float(szh_nt))
                buy_swept = (bzl_nt is not None and bzh_nt is not None
                             and float(bzl_nt) <= low <= float(bzh_nt))
                if not sell_swept and not buy_swept:
                    return hold

        # SELL signal
        if sell_conf >= self.min_confidence:
            szl = kl.get("sell_zone_low")
            szh = kl.get("sell_zone_high")
            bi = kl.get("bearish_invalidation")
            if szl is not None and szh is not None and bi is not None:
                szl, szh, bi = float(szl), float(szh), float(bi)
                if szl <= high <= szh:
                    upper_wick = high - max(open_price, entry)
                    if upper_wick / bar_range >= self.wick_ratio and entry < szl:
                        t1 = float(targets[0]) if len(targets) > 0 else entry - atr * 2
                        t2 = float(targets[1]) if len(targets) > 1 else entry - atr * 4
                        # Sanity: TP must be below entry for a SELL
                        if t1 >= entry:
                            t1 = entry - atr * 2
                        if t2 >= entry:
                            t2 = entry - atr * 4
                        base["metadata"] = {
                            **base["metadata"],
                            "sell_conf": sell_conf,
                            "sell_zone": [szl, szh],
                            "targets": [t1, t2],
                        }
                        self._last_signal_ts = ts
                        return Signal(
                            side="SELL",
                            confidence=sell_conf,
                            stop_loss=bi,
                            take_profit=t1,
                            reason_code=rc.SIGNAL_SELL,
                            **base,
                        )

        # BUY signal
        if buy_conf >= self.min_confidence:
            bzl = kl.get("buy_zone_low")
            bzh = kl.get("buy_zone_high")
            if bzl is not None and bzh is not None:
                bzl_f, bzh_f = float(bzl), float(bzh)
                # Stop anchor: XAUUSD uses asia_liquidity_low; BTCUSD uses breakdown_trigger;
                # if neither is present, derive 1 ATR below buy zone low.
                raw_anchor = kl.get("asia_liquidity_low") or kl.get("breakdown_trigger")
                stop_anchor = float(raw_anchor) if raw_anchor is not None else bzl_f - atr
                if bzl_f <= low <= bzh_f:
                    lower_wick = min(open_price, entry) - low
                    if lower_wick / bar_range >= self.wick_ratio and entry > bzh_f:
                        stop = stop_anchor - (atr * self.atr_multiplier)
                        szl_fallback = float(kl.get("sell_zone_low", entry + atr * 2))
                        szh_fallback = float(kl.get("sell_zone_high", entry + atr * 4))
                        base["metadata"] = {
                            **base["metadata"],
                            "buy_conf": buy_conf,
                            "buy_zone": [bzl_f, bzh_f],
                        }
                        self._last_signal_ts = ts
                        return Signal(
                            side="BUY",
                            confidence=buy_conf,
                            stop_loss=stop,
                            take_profit=szl_fallback,
                            reason_code=rc.SIGNAL_BUY,
                            **base,
                        )

        return hold

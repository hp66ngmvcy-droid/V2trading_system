"""Paper-only position sizing models."""

from __future__ import annotations

from dataclasses import dataclass

from tar_system import reason_codes as rc
from tar_system.assets.profiles import AssetProfile
from tar_system.brokers.profiles import BrokerProfile, BrokerSymbolProfile
from tar_system.optimisation.parameter_anchors import ATR_STOP_ANCHORS


@dataclass(frozen=True)
class PositionSize:
    recommended_lot: float
    notional_exposure: float
    margin_required: float
    risk_amount: float
    risk_pct: float
    effective_leverage: float
    sizing_model: str
    capped: bool
    reason: str


def size_position(
    model: str,
    symbol: str,
    price: float,
    equity: float,
    broker_profile: BrokerProfile,
    asset_profile: AssetProfile,
    stop_distance: float | None = None,
    risk_pct: float = 0.01,
    fixed_lot: float = 0.01,
    atr: float | None = None,
    atr_multiplier: float | None = None,
    win_rate: float = 0.5,
    avg_win: float = 1.0,
    avg_loss: float = 1.0,
    current_asset_class_exposure: float = 0.0,
) -> PositionSize:
    symbol_profile = broker_profile.symbol_profile(symbol)
    if current_asset_class_exposure >= equity * 0.3:
        return PositionSize(0.0, 0.0, 0.0, 0.0, risk_pct, 0.0, model, True, rc.ASSET_CLASS_EXPOSURE_LIMIT)
    risk_amount = equity * risk_pct
    resolved_stop = _stop_distance(symbol, stop_distance, atr, atr_multiplier)
    if model == "FIXED_LOT":
        raw_lot = fixed_lot
    elif model == "FIXED_RISK_PCT":
        raw_lot = risk_amount / max(resolved_stop * symbol_profile.contract_size, 1e-9)
    elif model == "ATR_BASED":
        raw_lot = risk_amount / max(resolved_stop * symbol_profile.contract_size, 1e-9)
    elif model == "HALF_KELLY":
        loss_rate = 1 - win_rate
        full_kelly = (win_rate * avg_win - loss_rate * avg_loss) / max(avg_win, 1e-9)
        raw_lot = max(0.0, equity * (full_kelly * 0.5) / symbol_profile.contract_size)
        risk_amount = raw_lot * symbol_profile.contract_size
    else:
        raise ValueError(f"Unknown sizing model: {model}")
    lot, capped, reason = _apply_caps(raw_lot, price, equity, broker_profile, symbol_profile)
    notional = price * symbol_profile.contract_size * lot
    margin = notional / max(broker_profile.max_leverage, 1.0)
    leverage = notional / equity if equity else 0.0
    return PositionSize(lot, notional, margin, risk_amount, risk_pct, leverage, model, capped, reason)


def _stop_distance(symbol: str, stop_distance: float | None, atr: float | None, atr_multiplier: float | None) -> float:
    if stop_distance and stop_distance > 0:
        return stop_distance
    multiplier = atr_multiplier or float(ATR_STOP_ANCHORS.get(symbol.upper(), {}).get("atr_multiplier", 2.0))
    return max((atr or 0.0) * multiplier, 1e-9)


def _apply_caps(raw_lot: float, price: float, equity: float, broker_profile: BrokerProfile, symbol_profile: BrokerSymbolProfile) -> tuple[float, bool, str]:
    capped = False
    reason = ""
    lot = max(raw_lot, 0.0)
    max_notional = equity * broker_profile.max_leverage * 0.1
    max_lot_by_leverage = max_notional / max(price * symbol_profile.contract_size, 1e-9)
    if lot > max_lot_by_leverage:
        lot = max_lot_by_leverage
        capped = True
        reason = rc.LEVERAGE_SAFETY_CAP
    if lot > symbol_profile.max_lot_size:
        lot = symbol_profile.max_lot_size
        capped = True
        reason = reason or "BROKER_MAX_LOT"
    if 0 < lot < symbol_profile.min_lot_size:
        lot = symbol_profile.min_lot_size
        capped = True
        reason = reason or "BROKER_MIN_LOT"
    stepped = int((lot + 1e-9) / symbol_profile.lot_step) * symbol_profile.lot_step
    lot = round(max(symbol_profile.min_lot_size if lot > 0 else 0.0, stepped), 8)
    return lot, capped, reason

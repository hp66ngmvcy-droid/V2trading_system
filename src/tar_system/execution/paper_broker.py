"""Paper-only execution simulation."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass

import pandas as pd

from tar_system import reason_codes as rc
from tar_system.assets.profiles import AssetProfile
from tar_system.audit.writer import append_audit_event
from tar_system.brokers.profiles import BrokerProfile, BrokerSymbolProfile
from tar_system.risk.position_sizer import PositionSize
from tar_system.strategies.base import Signal

logger = logging.getLogger(__name__)


@dataclass
class Fill:
    timestamp: pd.Timestamp
    symbol: str
    side: str
    quantity: float
    price: float
    commission: float
    metadata: dict[str, object]
    swap_cost: float = 0.0
    days_held: float = 0.0
    slippage_cost: float = 0.0
    spread_cost: float = 0.0
    total_cost: float = 0.0
    net_pnl: float = 0.0


@dataclass(frozen=True)
class MarginEstimate:
    symbol: str
    lot_size: float
    notional_exposure: float
    margin_required: float
    margin_utilisation: float
    free_margin: float
    spread_cost: float
    slippage_cost: float
    commission: float
    swap: float
    liquidation_warning: bool
    reason_codes: list[str]


@dataclass
class PaperBroker:
    default_spread: float = 0.0
    slippage_bps: float = 1.0
    commission_per_trade: float = 0.0
    random_seed: int = 42

    def execute(
        self,
        signal: Signal,
        quantity: float = 1.0,
        spread: float | None = None,
        broker_profile: BrokerProfile | None = None,
        contract_size: float | None = None,
        cost_multiplier: float = 1.0,
        position_size: PositionSize | None = None,
    ) -> Fill:
        if position_size is not None:
            quantity = position_size.recommended_lot
        symbol_profile = broker_profile.symbol_profile(signal.symbol) if broker_profile else None
        spread_model = _cost_model(symbol_profile) if symbol_profile else None
        effective_spread = self._spread_amount(signal.entry, signal.symbol, spread_model, spread) * cost_multiplier
        slippage = self._slippage_amount(signal.entry, signal.symbol, symbol_profile.slippage_model if symbol_profile else None) * cost_multiplier
        direction = 1 if signal.side == "BUY" else -1
        price = signal.entry + direction * (effective_spread / 2 + slippage)
        units = quantity * (contract_size if contract_size is not None else (symbol_profile.contract_size if symbol_profile else 1.0))
        spread_cost = abs(effective_spread * units)
        slippage_cost = abs(slippage * units)
        total_cost = spread_cost + slippage_cost + self.commission_per_trade
        return Fill(
            timestamp=signal.timestamp,
            symbol=signal.symbol,
            side=signal.side,
            quantity=quantity,
            price=float(price),
            commission=self.commission_per_trade,
            metadata={
                "spread": float(effective_spread),
                "slippage": float(slippage),
                "spread_model": spread_model or "manual",
                "position_size": position_size.__dict__ if position_size else {},
            },
            slippage_cost=slippage_cost,
            spread_cost=spread_cost,
            total_cost=total_cost,
            net_pnl=-total_cost,
        )

    def close_position(
        self,
        position,
        timestamp: pd.Timestamp,
        exit_price: float,
        broker_profile: BrokerProfile | None = None,
        contract_size: float | None = None,
        cost_multiplier: float = 1.0,
        timeframe: str = "H1",
    ) -> Fill:
        symbol_profile = broker_profile.symbol_profile(position.symbol) if broker_profile else None
        spread_model = _cost_model(symbol_profile) if symbol_profile else None
        effective_spread = self._spread_amount(exit_price, position.symbol, spread_model, None) * cost_multiplier
        slippage = self._slippage_amount(exit_price, position.symbol, symbol_profile.slippage_model if symbol_profile else None) * cost_multiplier
        side = "BUY" if position.side == "SELL" else "SELL"
        quantity = position.quantity
        units = quantity * (contract_size if contract_size is not None else (symbol_profile.contract_size if symbol_profile else 1.0))
        spread_cost = abs(effective_spread * units)
        slippage_cost = abs(slippage * units)
        swap_cost = 0.0
        if symbol_profile and hasattr(position, "timestamp"):
            bars_held = max(1, int((timestamp - position.timestamp).total_seconds() / max(1, timeframe_day_fraction(timeframe) * 86400)))
            notional = exit_price * units
            swap_cost, _ = self.calculate_swap_cost(symbol_profile, position.side, quantity, notional, timeframe, bars_held)
            swap_cost = abs(swap_cost) * cost_multiplier
        total_cost = spread_cost + slippage_cost + swap_cost + self.commission_per_trade
        return Fill(
            timestamp=timestamp,
            symbol=position.symbol,
            side=side,
            quantity=quantity,
            price=float(exit_price),
            commission=self.commission_per_trade,
            metadata={
                "spread": float(effective_spread),
                "slippage": float(slippage),
                "spread_model": spread_model or "manual",
                "close_position": True,
            },
            slippage_cost=slippage_cost,
            spread_cost=spread_cost,
            total_cost=total_cost,
            net_pnl=-total_cost,
        )

    def calculate_swap_cost(self, symbol_profile: BrokerSymbolProfile, side: str, lots: float, notional: float, timeframe: str, bars_held: int) -> tuple[float, float]:
        days = bars_held * timeframe_day_fraction(timeframe)
        swap_rate = symbol_profile.swap_long if side.upper() == "BUY" else symbol_profile.swap_short
        if symbol_profile.swap_type == "percentage":
            return notional * (swap_rate / 100 / 365) * days, days
        return swap_rate * lots * days, days

    def estimate_margin(
        self,
        signal: Signal,
        broker_profile: BrokerProfile,
        asset_profile: AssetProfile,
        account_equity: float,
        lot_size: float | None = None,
        holding_bars: int = 1,
        held_overnight: bool = False,
    ) -> MarginEstimate:
        symbol_profile = broker_profile.symbol_profile(signal.symbol)
        if signal.symbol.upper() == "XAGUSD":
            message = "XAGUSD sizing warning: contract_size is 5000 oz per lot, much larger than XAUUSD 100 oz."
            logger.warning(message)
            append_audit_event("broker_margin_warning", signal.strategy, signal.symbol, signal.timeframe, "WARNING", "XAGUSD_CONTRACT_SIZE_WARNING", {"contract_size": symbol_profile.contract_size})
        lots = self._safe_lot_size(symbol_profile, account_equity, signal.entry, asset_profile.risk_limit, broker_profile.max_leverage, lot_size)
        notional = abs(signal.entry * symbol_profile.contract_size * lots)
        effective_leverage = min(max(broker_profile.max_leverage, 1.0), 30.0)
        margin_required = notional / max(broker_profile.max_leverage, 1.0)
        spread_cost = abs(asset_profile.spread_assumption * symbol_profile.contract_size * lots)
        slippage_cost = abs(signal.entry * asset_profile.slippage_bps() / 10_000 * symbol_profile.contract_size * lots)
        commission = symbol_profile.commission_per_lot * lots
        swap = symbol_profile.swap_long if signal.side == "BUY" else symbol_profile.swap_short
        reason_codes: list[str] = []
        if signal.symbol.upper() == "USOUSD" and held_overnight and holding_bars > 1:
            reason_codes.append(rc.HIGH_SWAP_DRAG)
            logger.warning(
                "HIGH_SWAP_DRAG: %s %s held overnight for %s bars; swap=%s points",
                signal.symbol,
                signal.side,
                holding_bars,
                swap,
            )
            append_audit_event(
                "broker_cost_warning",
                signal.strategy,
                signal.symbol,
                signal.timeframe,
                "WARNING",
                rc.HIGH_SWAP_DRAG,
                {"side": signal.side, "holding_bars": holding_bars, "held_overnight": held_overnight, "swap": float(swap)},
            )
        free_margin = account_equity - margin_required - spread_cost - slippage_cost - commission
        utilisation = margin_required / account_equity if account_equity > 0 else 1.0
        return MarginEstimate(
            symbol=signal.symbol,
            lot_size=lots,
            notional_exposure=notional,
            margin_required=margin_required,
            margin_utilisation=utilisation,
            free_margin=free_margin,
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            commission=commission,
            swap=float(swap),
            liquidation_warning=utilisation > 0.5 or free_margin < account_equity * 0.25,
            reason_codes=reason_codes,
        )

    def close_trade_costs(
        self,
        symbol_profile: BrokerSymbolProfile,
        side: str,
        entry_price: float,
        exit_price: float,
        lots: float,
        timeframe: str,
        bars_held: int,
        cost_multiplier: float = 1.0,
    ) -> dict[str, float | list[str]]:
        notional = abs(entry_price * symbol_profile.contract_size * lots)
        swap_cost, days = self.calculate_swap_cost(symbol_profile, side, lots, notional, timeframe, bars_held)
        spread_cost = abs(self._spread_amount(exit_price, symbol_profile.symbol, _cost_model(symbol_profile), None) * symbol_profile.contract_size * lots) * cost_multiplier
        slippage_cost = abs(self._slippage_amount(exit_price, symbol_profile.symbol, symbol_profile.slippage_model) * symbol_profile.contract_size * lots) * cost_multiplier
        total_cost = spread_cost + slippage_cost + abs(swap_cost)
        reason_codes = [rc.HIGH_SWAP_DRAG] if symbol_profile.symbol == "USOUSD" and bars_held > 1 and days > 0 and abs(swap_cost) > 0 else []
        return {
            "swap_cost": swap_cost,
            "days_held": days,
            "spread_cost": spread_cost,
            "slippage_cost": slippage_cost,
            "total_cost": total_cost,
            "reason_codes": reason_codes,
        }

    def _safe_lot_size(
        self,
        symbol_profile: BrokerSymbolProfile,
        account_equity: float,
        entry: float,
        risk_limit: float,
        max_leverage: float,
        requested_lot: float | None,
    ) -> float:
        if requested_lot is not None:
            raw_lot = requested_lot
        else:
            max_notional = account_equity * max(risk_limit, 0.001) * min(max_leverage, 30.0)
            raw_lot = max_notional / max(entry * symbol_profile.contract_size, 1.0)
        stepped = int(raw_lot / symbol_profile.lot_step) * symbol_profile.lot_step
        return max(symbol_profile.min_lot_size, min(symbol_profile.max_lot_size, round(stepped, 8)))

    def _spread_amount(self, price: float, symbol: str, model: str | None, manual_spread: float | None) -> float:
        if manual_spread is not None:
            # Data stores spread in points; convert to price units.
            return float(manual_spread) * pip_size(symbol)
        if model == "high":
            return price * 0.001
        pips = {"low": 0.5, "medium": 1.5, "medium_high": 3.0}.get(model or "", self.default_spread)
        return float(pips) * pip_size(symbol)

    def _slippage_amount(self, price: float, symbol: str, model: str | None) -> float:
        if model == "high":
            max_value = price * 0.002
        else:
            pips = {"low": 0.2, "medium": 0.5, "medium_high": 1.0}.get(model or "", self.slippage_bps)
            max_value = float(pips) * pip_size(symbol)
        return random.Random(self.random_seed).uniform(0.0, max_value)


def pip_size(symbol: str) -> float:
    symbol = symbol.upper()
    if symbol.endswith("JPY"):
        return 0.01
    if symbol in {"XAUUSD", "XAGUSD", "USOUSD"}:
        return 0.01
    return 0.0001


def timeframe_day_fraction(timeframe: str) -> float:
    return {
        "M1": 1 / 1440,
        "M5": 1 / 288,
        "M15": 1 / 96,
        "M30": 1 / 48,
        "H1": 1 / 24,
        "H4": 1 / 6,
        "D1": 1.0,
    }.get(timeframe.upper(), 0.0)


def _cost_model(symbol_profile: BrokerSymbolProfile) -> str:
    return symbol_profile.slippage_model if symbol_profile.spread_model == "floating" else symbol_profile.spread_model

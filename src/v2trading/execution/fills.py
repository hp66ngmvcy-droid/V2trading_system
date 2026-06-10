"""Simple realistic fill-cost model for research simulations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class FillCost:
    """Breakdown of entry costs."""

    entry_price: float
    bid_ask_cost: float
    slippage_cost: float
    commission_cost: float
    total_entry_cost: float


class FillModel:
    def __init__(
        self,
        slippage_bps: float = 1.0,
        commission_bps: float = 0.1,
        bid_ask_spread_pips: float = 0.5,
        pip_value: float = 0.01,
    ) -> None:
        self.slippage_bps = slippage_bps
        self.commission_bps = commission_bps
        self.bid_ask_spread_pips = bid_ask_spread_pips
        self.pip_value = pip_value

    def calculate_fill_price(
        self,
        signal_price: float,
        direction: Literal["long", "short"] = "long",
    ) -> float:
        spread_adjustment = self.bid_ask_spread_pips * self.pip_value
        slippage = signal_price * (self.slippage_bps / 10_000)
        if direction == "long":
            fill_price = signal_price + spread_adjustment + slippage
        else:
            fill_price = signal_price - spread_adjustment - slippage
        return round(fill_price, 5)

    def calculate_entry_cost(
        self,
        signal_price: float,
        position_size: float,
        direction: Literal["long", "short"] = "long",
    ) -> FillCost:
        entry_price = self.calculate_fill_price(signal_price, direction)
        notional = abs(position_size) * signal_price
        bid_ask_cost = abs(entry_price - signal_price) * abs(position_size)
        slippage_cost = notional * (self.slippage_bps / 10_000)
        commission_cost = notional * (self.commission_bps / 10_000)
        total_entry_cost = bid_ask_cost + slippage_cost + commission_cost
        return FillCost(
            entry_price=entry_price,
            bid_ask_cost=round(bid_ask_cost, 5),
            slippage_cost=round(slippage_cost, 5),
            commission_cost=round(commission_cost, 5),
            total_entry_cost=round(total_entry_cost, 5),
        )

    def calculate_exit_price(
        self,
        signal_price: float,
        direction: Literal["long", "short"] = "long",
    ) -> float:
        spread_adjustment = self.bid_ask_spread_pips * self.pip_value
        slippage = signal_price * (self.slippage_bps / 10_000)
        if direction == "long":
            exit_price = signal_price - spread_adjustment - slippage
        else:
            exit_price = signal_price + spread_adjustment + slippage
        return round(exit_price, 5)

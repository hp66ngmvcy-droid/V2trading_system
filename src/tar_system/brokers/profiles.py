"""Broker profile dataclasses."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BrokerSymbolProfile:
    symbol: str
    contract_size: float
    min_lot_size: float
    lot_step: float
    max_lot_size: float
    spread_model: str
    slippage_model: str
    margin_currency: str
    profit_currency: str
    swap_type: str
    swap_long: float
    swap_short: float
    commission_per_lot: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BrokerProfile:
    broker_name: str
    account_currency: str
    max_leverage: float
    paper_mode_only: bool
    symbols: dict[str, BrokerSymbolProfile]

    def symbol_profile(self, symbol: str) -> BrokerSymbolProfile:
        key = symbol.upper()
        if key not in self.symbols:
            logger.warning("symbol %s not in broker config, using fallback defaults", key)
            return BrokerSymbolProfile(
                symbol=key,
                contract_size=1.0,
                min_lot_size=0.01,
                lot_step=0.01,
                max_lot_size=1.0,
                spread_model="medium",
                slippage_model="medium",
                margin_currency="",
                profit_currency="",
                swap_type="points",
                swap_long=0.0,
                swap_short=0.0,
            )
        return self.symbols[key]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["symbols"] = {key: value.to_dict() for key, value in self.symbols.items()}
        return payload

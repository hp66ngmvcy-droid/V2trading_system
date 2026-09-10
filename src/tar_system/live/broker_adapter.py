"""Broker adapter — sealed stub. Raises on every call. Paper-mode only."""

_MSG = "Live trading disabled — paper-mode only."


class BrokerAdapter:
    def __init__(self, broker_type: str = "mt5") -> None:
        raise NotImplementedError(_MSG)

    def can_trade_live(self) -> bool:
        raise NotImplementedError(_MSG)

    def connect(self, account: str, password: str) -> bool:
        raise NotImplementedError(_MSG)

    def is_connected(self) -> bool:
        raise NotImplementedError(_MSG)

    def place_live_order(self, symbol: str, size: float, order_type: str) -> None:
        raise NotImplementedError(_MSG)

    def disconnect(self) -> None:
        raise NotImplementedError(_MSG)

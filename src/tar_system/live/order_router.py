"""Order router — sealed stub. Raises on every call. Paper-mode only."""

_MSG = "Live trading disabled — paper-mode only."


class OrderRouter:
    def __init__(self) -> None:
        raise NotImplementedError(_MSG)

    def route(self, signal: int, symbol: str, size: float) -> None:
        raise NotImplementedError(_MSG)

    def cancel(self, order_id: str) -> None:
        raise NotImplementedError(_MSG)

    def status(self, order_id: str) -> None:
        raise NotImplementedError(_MSG)

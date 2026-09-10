"""Live runner — sealed stub. Raises on every call. Paper-mode only."""

_MSG = "Live trading disabled — paper-mode only."


class LiveRunner:
    def __init__(self) -> None:
        raise NotImplementedError(_MSG)

    def start(self) -> None:
        raise NotImplementedError(_MSG)

    def stop(self) -> None:
        raise NotImplementedError(_MSG)

    def run_cycle(self) -> None:
        raise NotImplementedError(_MSG)

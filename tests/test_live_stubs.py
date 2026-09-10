"""Assert all live/ stubs raise NotImplementedError — no live path exists."""
import pytest

from tar_system.live.broker_adapter import BrokerAdapter
from tar_system.live.order_router import OrderRouter
from tar_system.live.live_runner import LiveRunner


def test_broker_adapter_init_raises():
    with pytest.raises(NotImplementedError, match="paper-mode only"):
        BrokerAdapter()


def test_broker_adapter_methods_raise():
    for method, args in [
        ("can_trade_live", []),
        ("connect", ["acc", "pw"]),
        ("is_connected", []),
        ("place_live_order", ["XAUUSD", 0.1, "BUY"]),
        ("disconnect", []),
    ]:
        with pytest.raises(NotImplementedError, match="paper-mode only"):
            getattr(BrokerAdapter, method)(object.__new__(BrokerAdapter), *args)


def test_order_router_init_raises():
    with pytest.raises(NotImplementedError, match="paper-mode only"):
        OrderRouter()


def test_order_router_methods_raise():
    for method, args in [
        ("route", [1, "XAUUSD", 0.1]),
        ("cancel", ["order-123"]),
        ("status", ["order-123"]),
    ]:
        with pytest.raises(NotImplementedError, match="paper-mode only"):
            getattr(OrderRouter, method)(object.__new__(OrderRouter), *args)


def test_live_runner_init_raises():
    with pytest.raises(NotImplementedError, match="paper-mode only"):
        LiveRunner()


def test_live_runner_methods_raise():
    for method in ["start", "stop", "run_cycle"]:
        with pytest.raises(NotImplementedError, match="paper-mode only"):
            getattr(LiveRunner, method)(object.__new__(LiveRunner))

"""Broker Adapter: Sealed connection - LIVE_TRADING_ENABLED = False"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BrokerAdapter:
    LIVE_TRADING_ENABLED = False
    
    def __init__(self, broker_type: str = "mt5"):
        self.broker_type = broker_type
        self.connected = False
        logger.info(f"BrokerAdapter: {broker_type}, LIVE_TRADING_ENABLED={self.LIVE_TRADING_ENABLED}")
    
    def can_trade_live(self) -> bool:
        return False
    
    def connect(self, account: str, password: str) -> bool:
        logger.warning("[BLOCKED] Live trading disabled")
        return False
    
    def is_connected(self) -> bool:
        return False
    
    def place_live_order(self, symbol: str, size: float, order_type: str) -> Optional[str]:
        logger.warning("[BLOCKED] Cannot place live order")
        return None
    
    def disconnect(self):
        self.connected = False

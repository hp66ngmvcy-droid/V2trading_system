"""Paper Broker: Simulates broker execution with realistic fills"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PaperBroker:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.fills = []
        self.prices = {}
        logger.info(f"PaperBroker: ${initial_capital:.2f}")
    
    def update_prices(self, price_dict: Dict[str, float]):
        self.prices.update(price_dict)
    
    def place_order(self, symbol: str, size: float, order_type: str = 'BUY') -> float:
        current_price = self.prices.get(symbol, 0)
        if current_price == 0:
            raise ValueError(f"No price for {symbol}")
        
        fill_price = current_price * 1.0001 if order_type == 'BUY' else current_price * 0.9999
        cost = fill_price * size
        if order_type == 'BUY':
            self.cash -= cost
            self.positions[symbol] = self.positions.get(symbol, 0) + size
        else:
            self.cash += cost
            self.positions[symbol] = self.positions.get(symbol, 0) - size
        self.fills.append({'symbol': symbol, 'order_type': order_type, 'size': size, 'fill_price': fill_price})
        return fill_price
    
    def get_portfolio_value(self) -> float:
        return self.cash + sum(size * self.prices.get(symbol, 0) for symbol, size in self.positions.items())
    
    def get_cash(self) -> float:
        return self.cash
    
    def get_positions(self) -> Dict[str, float]:
        return self.positions.copy()

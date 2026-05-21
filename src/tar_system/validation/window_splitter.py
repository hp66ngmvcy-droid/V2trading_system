"""
Window Splitter: Rolling Train/Test Window Generator
Based on Backtrader walk-forward pattern
Creates rolling windows for blind out-of-sample testing
"""

from typing import Tuple, Generator
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class RollingWindowSplitter:
    """
    Creates rolling train/test windows for walk-forward validation.
    
    Pattern from Backtrader walkforward.py
    Prevents lookahead bias by ensuring train/test periods don't overlap
    """
    
    def __init__(self, data: pd.DataFrame, train_months: int = 12, test_months: int = 3):
        """
        Args:
            data: DataFrame with datetime index and OHLCV data
            train_months: Length of training window (months)
            test_months: Length of test window (months)
        """
        self.data = data
        self.train_months = train_months
        self.test_months = test_months
        
        # Convert months to trading days (approximately 21 trading days per month)
        self.train_bars = train_months * 21
        self.test_bars = test_months * 21
        
        logger.info(
            f"RollingWindowSplitter initialized: "
            f"train={train_months}mo ({self.train_bars} bars), "
            f"test={test_months}mo ({self.test_bars} bars)"
        )
    
    def generate_windows(self) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
        """
        Generate rolling (train_data, test_data) tuples.
        
        Yields:
            Tuple of (train_df, test_df) - train and test windows
            
        CRITICAL: train and test windows NEVER overlap
        """
        total_bars = len(self.data)
        required_bars = self.train_bars + self.test_bars
        
        if total_bars < required_bars:
            logger.warning(
                f"Data length ({total_bars} bars) < required ({required_bars} bars). "
                f"Cannot generate windows."
            )
            return
        
        window_num = 0
        idx = 0
        
        while idx + required_bars <= total_bars:
            window_num += 1
            
            # Training window: learn parameters
            train_start = idx
            train_end = idx + self.train_bars
            
            # Test window: verify with unseen data (comes AFTER train window)
            test_start = train_end
            test_end = train_end + self.test_bars
            
            train_data = self.data.iloc[train_start:train_end]
            test_data = self.data.iloc[test_start:test_end]
            
            logger.info(
                f"Window {window_num}: "
                f"train=[{train_data.index[0].date()} to {train_data.index[-1].date()}], "
                f"test=[{test_data.index[0].date()} to {test_data.index[-1].date()}]"
            )
            
            yield train_data, test_data
            
            # Move forward by test period (rolling window)
            idx += self.test_bars
    
    def count_windows(self) -> int:
        """Count how many windows will be generated"""
        total_bars = len(self.data)
        required_bars = self.train_bars + self.test_bars
        
        if total_bars < required_bars:
            return 0
        
        count = 0
        idx = 0
        while idx + required_bars <= total_bars:
            count += 1
            idx += self.test_bars
        
        return count


# Example usage
if __name__ == "__main__":
    # Create sample data
    import numpy as np
    from datetime import datetime, timedelta
    
    dates = pd.date_range('2018-01-01', '2024-01-01', freq='D')
    data = pd.DataFrame({
        'open': np.random.randn(len(dates)).cumsum() + 2000,
        'high': np.random.randn(len(dates)).cumsum() + 2050,
        'low': np.random.randn(len(dates)).cumsum() + 1950,
        'close': np.random.randn(len(dates)).cumsum() + 2000,
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Create splitter
    splitter = RollingWindowSplitter(data, train_months=12, test_months=3)
    
    # Generate windows
    print(f"Total data: {len(data)} bars")
    print(f"Windows to generate: {splitter.count_windows()}")
    print()
    
    for i, (train, test) in enumerate(splitter.generate_windows(), 1):
        print(f"Window {i}:")
        print(f"  Train: {len(train)} bars")
        print(f"  Test:  {len(test)} bars")
        print()

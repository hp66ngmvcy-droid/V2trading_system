"""Position Size Calculator - Core math functions (from PSCalc MIT license)"""

def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    Kelly Criterion formula for optimal position sizing
    
    Args:
        win_rate: Percentage of winning trades (0-1)
        avg_win: Average win size
        avg_loss: Average loss size
        
    Returns:
        Optimal position size as % of account
    """
    if avg_loss == 0:
        return 0
    
    ratio = avg_win / avg_loss
    kelly = (win_rate * ratio - (1 - win_rate)) / ratio
    return max(0, kelly)  # Never negative


def fixed_fractional(account_balance: float, risk_percent: float, stop_loss_pips: float) -> float:
    """
    Fixed Fractional position sizing
    
    Args:
        account_balance: Current account balance
        risk_percent: % of account to risk per trade (0-1)
        stop_loss_pips: Stop loss distance in pips
        
    Returns:
        Position size
    """
    risk_amount = account_balance * risk_percent
    position_size = risk_amount / (stop_loss_pips * 10)
    return position_size


def risk_percent(account_balance: float, risk_amount: float) -> float:
    """
    Calculate risk percentage
    
    Args:
        account_balance: Current account balance
        risk_amount: Amount risking on trade
        
    Returns:
        Risk as percentage of account
    """
    if account_balance == 0:
        return 0
    return risk_amount / account_balance


def position_from_risk(account_balance: float, risk_percent_val: float, 
                       entry: float, stop_loss: float) -> float:
    """
    Calculate position size from risk parameters
    
    Args:
        account_balance: Current account balance
        risk_percent_val: % of account to risk
        entry: Entry price
        stop_loss: Stop loss price
        
    Returns:
        Position size
    """
    risk_amount = account_balance * risk_percent_val
    price_diff = abs(entry - stop_loss)
    
    if price_diff == 0:
        return 0
    
    position_size = risk_amount / price_diff
    return position_size


if __name__ == "__main__":
    # Test examples
    print("Kelly Criterion (55% win, 1.5 ratio):", kelly_criterion(0.55, 1.5, 1.0))
    print("Fixed Fractional ($10k, 2%, 50 pips):", fixed_fractional(10000, 0.02, 50))
    print("Risk % ($10k, $200 risk):", risk_percent(10000, 200))

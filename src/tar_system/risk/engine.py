"""Paper-only risk gates."""

from __future__ import annotations

from dataclasses import dataclass

from tar_system import reason_codes as rc
from tar_system import settings
from tar_system.strategies.base import Signal


@dataclass
class RiskDecision:
    approved: bool
    reason_code: str
    message: str


@dataclass
class RiskEngine:
    confidence_threshold: float = settings.DEFAULT_CONFIDENCE_THRESHOLD
    max_drawdown: float = settings.DEFAULT_MAX_DRAWDOWN
    max_exposure: float = settings.DEFAULT_MAX_EXPOSURE
    volatility_cap: float = 0.03

    def evaluate(
        self,
        signal: Signal,
        current_drawdown: float = 0.0,
        current_exposure: float = 0.0,
        current_volatility: float = 0.0,
        expected_swap_drag: float = 0.0,
        consecutive_losses: int = 0,
        daily_loss_pct: float = 0.0,
        weekly_loss_pct: float = 0.0,
        loss_guard_status: str = "ACTIVE",
    ) -> RiskDecision:
        if not settings.PAPER_MODE or settings.LIVE_TRADING_ALLOWED:
            return RiskDecision(False, rc.RISK_LIVE_TRADING_BLOCKED, "Live trading is blocked")
        if signal.side == "HOLD":
            return RiskDecision(False, rc.SIGNAL_HOLD, "Hold signal")
        if signal.confidence < self.confidence_threshold:
            return RiskDecision(False, rc.RISK_LOW_CONFIDENCE, "Signal confidence below threshold")
        if current_drawdown >= self.max_drawdown:
            return RiskDecision(False, rc.RISK_DRAWDOWN_LIMIT, "Drawdown guard triggered")
        if current_exposure >= self.max_exposure:
            return RiskDecision(False, rc.RISK_EXPOSURE_LIMIT, "Exposure limit reached")
        if current_volatility >= self.volatility_cap:
            return RiskDecision(False, rc.RISK_VOLATILITY_CAP, "Volatility cap reached")
        if expected_swap_drag > 0.3:
            return RiskDecision(False, rc.HIGH_SWAP_DRAG, "Expected swap drag above threshold")
        if loss_guard_status == rc.PAUSED_HUMAN_RESET_REQUIRED:
            return RiskDecision(False, rc.PAUSED_HUMAN_RESET_REQUIRED, "Loss guard requires human reset")
        if consecutive_losses >= settings.DEFAULT_MAX_CONSECUTIVE_LOSSES:
            return RiskDecision(False, rc.CONSECUTIVE_LOSS_LIMIT, "Consecutive loss limit reached")
        if daily_loss_pct >= settings.DEFAULT_DAILY_LOSS_LIMIT:
            return RiskDecision(False, rc.DAILY_LOSS_LIMIT, "Daily loss limit reached")
        if weekly_loss_pct >= settings.DEFAULT_WEEKLY_LOSS_LIMIT:
            return RiskDecision(False, rc.WEEKLY_LOSS_LIMIT, "Weekly loss limit reached")
        return RiskDecision(True, rc.RISK_APPROVED, "Risk approved")

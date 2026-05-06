"""Convert legacy research presets into TAR risk-engine inputs."""

from __future__ import annotations

from dataclasses import dataclass

from tar_system import reason_codes as rc
from tar_system.legacy.preset_loader import LegacyRiskPreset


@dataclass(frozen=True)
class LegacyRiskInputs:
    confidence_threshold_adjustment: float
    max_drawdown: float
    max_exposure: float
    max_spread_pips: float
    min_stop_pips: float
    max_stop_pips: float
    max_consecutive_losses: int
    daily_loss_limit: float
    weekly_loss_limit: float
    cooldown_after_loss_bars: int
    max_margin_utilisation: float
    reason_codes: list[str]
    research_only: bool = True


def adapt_legacy_preset_to_risk_inputs(preset: LegacyRiskPreset) -> LegacyRiskInputs:
    """Return risk controls that can be passed into TAR checks later.

    This adapter deliberately produces limits and reason-code context only.
    It does not create signals, orders, pending entries or live execution hooks.
    """
    return LegacyRiskInputs(
        confidence_threshold_adjustment=0.0,
        max_drawdown=float(preset.risk.get("max_drawdown_pct", 0.2)),
        max_exposure=float(preset.risk.get("max_exposure_pct", 0.3)),
        max_spread_pips=float(preset.spread.get("max_spread_pips", 0.0)),
        min_stop_pips=float(preset.stop_constraints.get("min_stop_pips", 0.0)),
        max_stop_pips=float(preset.stop_constraints.get("max_stop_pips", 0.0)),
        max_consecutive_losses=int(preset.risk.get("max_consecutive_losses", 3)),
        daily_loss_limit=float(preset.risk.get("max_daily_loss_pct", 0.02)),
        weekly_loss_limit=float(preset.risk.get("max_weekly_loss_pct", 0.05)),
        cooldown_after_loss_bars=int(preset.cooldown.get("after_loss_bars", 0)),
        max_margin_utilisation=float(preset.margin.get("max_margin_utilisation", 0.3)),
        reason_codes=[
            rc.LEGACY_RISK_PRESET_LOADED,
            rc.LEGACY_RESEARCH_ONLY,
        ],
    )

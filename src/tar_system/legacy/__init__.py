"""Research-only legacy intelligence adapters."""

from tar_system.legacy.preset_loader import LegacyRiskPreset, load_legacy_risk_preset
from tar_system.legacy.risk_preset_adapter import LegacyRiskInputs, adapt_legacy_preset_to_risk_inputs

__all__ = [
    "LegacyRiskInputs",
    "LegacyRiskPreset",
    "adapt_legacy_preset_to_risk_inputs",
    "load_legacy_risk_preset",
]

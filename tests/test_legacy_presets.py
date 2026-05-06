from __future__ import annotations

from pathlib import Path

import pytest

from tar_system import reason_codes as rc
from tar_system.legacy import adapt_legacy_preset_to_risk_inputs, load_legacy_risk_preset


def test_legacy_risk_preset_loads_research_only() -> None:
    preset = load_legacy_risk_preset()

    assert preset.is_research_only
    assert preset.source == "legacy_mt5_ea"
    assert preset.live_enabled is False
    assert "pullback_entries" in preset.excluded_logic


def test_legacy_risk_adapter_extracts_limits_only() -> None:
    preset = load_legacy_risk_preset()
    inputs = adapt_legacy_preset_to_risk_inputs(preset)

    assert inputs.research_only is True
    assert inputs.max_drawdown == 0.2
    assert inputs.max_spread_pips == 2.0
    assert inputs.min_stop_pips == 5.0
    assert inputs.max_stop_pips == 80.0
    assert inputs.max_consecutive_losses == 3
    assert inputs.reason_codes == [rc.LEGACY_RISK_PRESET_LOADED, rc.LEGACY_RESEARCH_ONLY]


def test_legacy_preset_rejects_live_enabled(tmp_path: Path) -> None:
    preset_dir = tmp_path / "configs"
    preset_dir.mkdir()
    (preset_dir / "bad.yaml").write_text(
        """
name: bad
status: research_only
source: legacy_mt5_ea
live_enabled: true
requires_validation: true
risk:
  max_risk_per_trade_pct: 0.01
margin:
  never_use_full_leverage: true
excluded_logic:
  - pullback_entries
  - pending_order_logic
  - execution_triggers
  - live_order_management
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="research_only"):
        load_legacy_risk_preset("bad", preset_dir)

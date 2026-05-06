"""Load local paper-only broker profiles."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from tar_system import reason_codes as rc
from tar_system.audit.writer import append_audit_event
from tar_system.brokers.profiles import BrokerProfile, BrokerSymbolProfile

logger = logging.getLogger(__name__)


def load_broker_profile(name: str = "current_broker_demo", audit: bool = False) -> BrokerProfile:
    path = Path("configs/brokers") / f"{name}.yaml"
    if not path.exists():
        bundled = Path(__file__).resolve().parents[3] / "configs" / "brokers" / f"{name}.yaml"
        if bundled.exists():
            path = bundled
        else:
            raise FileNotFoundError(f"Broker profile not found: {path}")
    raw = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    symbols = {
        symbol: BrokerSymbolProfile(
            symbol=symbol,
            contract_size=float(values.get("contract_size", 1)),
            min_lot_size=float(values.get("min_lot_size", values.get("min_lot", 0.01))),
            lot_step=float(values.get("lot_step", 0.01)),
            max_lot_size=float(values.get("max_lot_size", values.get("max_lot", 1))),
            spread_model=str(values.get("spread_model", "floating")),
            slippage_model=str(values.get("slippage_model", "medium")),
            margin_currency=str(values.get("margin_currency", "")),
            profit_currency=str(values.get("profit_currency", "")),
            swap_type=str(values.get("swap_type", "points")),
            swap_long=float(values.get("swap_long", 0)),
            swap_short=float(values.get("swap_short", 0)),
            commission_per_lot=float(values.get("commission_per_lot", 0)),
        )
        for symbol, values in raw.get("symbols", {}).items()
    }
    profile = BrokerProfile(
        broker_name=str(raw.get("broker_name", name)),
        account_currency=str(raw.get("account_currency", "USD")),
        max_leverage=float(raw.get("max_leverage", 1)),
        paper_mode_only=bool(raw.get("paper_mode_only", True)),
        symbols=symbols,
    )
    if not profile.paper_mode_only:
        raise ValueError("Broker profile must be paper_mode_only=true")
    if audit:
        append_audit_event("broker_profile", "broker", "", "", "LOADED", rc.BROKER_PROFILE_LOADED, {"broker": profile.broker_name})
    missing = list_missing_symbols(profile)
    if missing:
        logger.warning("broker profile %s missing symbols: %s", profile.broker_name, ", ".join(missing))
    return profile


def list_missing_symbols(profile: BrokerProfile, asset_profiles: object | None = None) -> list[str]:
    if asset_profiles is None:
        from tar_system.assets.profiles import ASSET_PROFILES

        symbols = list(ASSET_PROFILES)
    elif isinstance(asset_profiles, dict):
        symbols = [str(symbol).upper() for symbol in asset_profiles.keys()]
    else:
        symbols = [str(getattr(item, "symbol", item)).upper() for item in asset_profiles]  # type: ignore[union-attr]
    return sorted(symbol for symbol in symbols if symbol not in profile.symbols)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current_section: str | None = None
    current_symbol: str | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0 and line.endswith(":"):
            current_section = line[:-1]
            root[current_section] = {}
            current_symbol = None
        elif indent == 0 and ":" in line:
            key, value = line.split(":", 1)
            root[key.strip()] = _clean_value(value)
        elif current_section == "symbols" and indent == 2 and line.endswith(":"):
            current_symbol = line[:-1]
            root["symbols"][current_symbol] = {}
        elif current_section == "symbols" and current_symbol and ":" in line:
            key, value = line.split(":", 1)
            root["symbols"][current_symbol][key.strip()] = _clean_value(value)
    return root


def _clean_value(value: str) -> object:
    text = value.strip().strip('"').strip("'")
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    try:
        return float(text) if "." in text or "e" in text.lower() else int(text)
    except ValueError:
        return text

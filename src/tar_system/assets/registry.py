"""Asset profile registry."""

from __future__ import annotations

from tar_system import reason_codes as rc
from tar_system.audit.writer import append_audit_event
from tar_system.assets.profiles import ASSET_PROFILES, AssetProfile


def get_asset_profile(symbol: str, audit: bool = False) -> AssetProfile:
    key = symbol.upper()
    if key not in ASSET_PROFILES:
        raise KeyError(f"Unknown asset profile: {symbol}")
    profile = ASSET_PROFILES[key]
    if audit:
        append_audit_event("asset_profile", "asset", key, "", "LOADED", rc.ASSET_PROFILE_LOADED, profile.to_dict())
    return profile


def list_asset_profiles() -> list[AssetProfile]:
    return list(ASSET_PROFILES.values())

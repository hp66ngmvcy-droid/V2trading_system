"""Resolve strategy variants by strategy, symbol and timeframe."""

from __future__ import annotations

from dataclasses import dataclass

from tar_system import reason_codes as rc
from tar_system.assets.registry import get_asset_profile
from tar_system.assets.profiles import AssetProfile
from tar_system.audit.writer import append_audit_event
from tar_system.brokers.profiles import BrokerProfile
from tar_system.brokers.registry import load_broker_profile
from tar_system.strategies.asset_variants import StrategyVariant, default_variant
from tar_system.strategies.registry import get_strategy


@dataclass(frozen=True)
class ResolvedStrategy:
    strategy: object
    variant: StrategyVariant
    asset_profile: AssetProfile
    broker_profile: BrokerProfile


def resolve_strategy(base_strategy: str, symbol: str, timeframe: str, broker: str = "current_broker_demo", audit: bool = False) -> ResolvedStrategy:
    asset_profile = get_asset_profile(symbol, audit=audit)
    broker_profile = load_broker_profile(broker, audit=audit)
    broker_profile.symbol_profile(symbol)
    variant = default_variant(base_strategy, symbol, timeframe)
    strategy = get_strategy(base_strategy, **variant.parameters)
    if audit:
        append_audit_event(
            "strategy_variant",
            base_strategy,
            symbol.upper(),
            timeframe.upper(),
            "RESOLVED",
            rc.STRATEGY_VARIANT_RESOLVED,
            {"variant": variant.to_dict(), "broker": broker_profile.broker_name},
        )
    return ResolvedStrategy(strategy=strategy, variant=variant, asset_profile=asset_profile, broker_profile=broker_profile)

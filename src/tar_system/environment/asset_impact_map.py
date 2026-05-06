"""Manual asset impact map for event risk."""

from __future__ import annotations

ASSET_IMPACT_MAP = {
    "US": {"USD", "XAUUSD", "XAGUSD", "BTC", "ETH", "US", "SPX", "NAS", "DOW", "OIL"},
    "CPI": {"USD", "XAUUSD", "XAGUSD", "BTC", "ETH", "US", "OIL"},
    "PPI": {"USD", "XAUUSD", "XAGUSD", "BTC", "ETH", "US", "OIL"},
    "NFP": {"USD", "XAUUSD", "XAGUSD", "BTC", "ETH", "US", "OIL"},
    "FOMC": {"USD", "XAUUSD", "XAGUSD", "BTC", "ETH", "US", "OIL"},
    "CENTRAL_BANK_RATE_DECISION": {"USD", "EUR", "GBP", "XAUUSD", "XAGUSD"},
    "ECB": {"EUR", "DAX", "EU", "XAUUSD"},
    "BOE": {"GBP", "FTSE", "XAUUSD"},
    "CHINA": {"AUD", "NZD", "COPPER", "OIL", "COMMOD"},
    "OPEC": {"OIL", "CAD", "XAUUSD", "XAGUSD"},
    "CRYPTO_REGULATION": {"BTC", "ETH", "CRYPTO"},
    "CRYPTO_EXPLOIT": {"BTC", "ETH", "CRYPTO"},
    "EXCHANGE_OUTAGE": {"BTC", "ETH", "CRYPTO"},
}


def event_impacts_symbol(event_name: str, symbol: str) -> bool:
    name = event_name.upper()
    symbol_upper = symbol.upper()
    for key, impacts in ASSET_IMPACT_MAP.items():
        if key in name:
            return any(impact in symbol_upper for impact in impacts)
    return False


def event_impacts_asset(event_type: str, country: str, symbol: str, explicit_assets: list[str] | None = None) -> bool:
    symbol_upper = symbol.upper()
    if explicit_assets and any(asset.upper() in symbol_upper for asset in explicit_assets):
        return True
    keys = [event_type.upper(), country.upper()]
    return any(any(impact in symbol_upper for impact in ASSET_IMPACT_MAP.get(key, set())) for key in keys)

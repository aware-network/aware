from __future__ import annotations

from aware_economy.operator_read import (
    ECONOMY_WALLET_CAPITAL_API_VIEW_REF,
    ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF,
    ECONOMY_WALLET_CAPITAL_VIEW_PROVIDER_REF,
    resolve_wallet_capital_view_state_from_economy_replica,
    wallet_capital_view_state_from_frame,
)

wallet_capital_view_state = resolve_wallet_capital_view_state_from_economy_replica


__all__ = [
    "ECONOMY_WALLET_CAPITAL_API_VIEW_REF",
    "ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF",
    "ECONOMY_WALLET_CAPITAL_VIEW_PROVIDER_REF",
    "resolve_wallet_capital_view_state_from_economy_replica",
    "wallet_capital_view_state",
    "wallet_capital_view_state_from_frame",
]

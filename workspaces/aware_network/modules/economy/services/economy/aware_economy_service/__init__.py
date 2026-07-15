from typing import Any

from .api_service_protocol import build_aware_economy_service_protocol_handler
from .service_bindings import build_service_bindings
from .service_providers import register_plugins as register_service_plugins

_LAZY_EXPORTS = {
    "ECONOMY_WALLET_CAPITAL_API_VIEW_REF": (
        "aware_economy_service.view_state_providers",
        "ECONOMY_WALLET_CAPITAL_API_VIEW_REF",
    ),
    "ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF": (
        "aware_economy_service.view_state_providers",
        "ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF",
    ),
    "ECONOMY_WALLET_CAPITAL_VIEW_PROVIDER_REF": (
        "aware_economy_service.view_state_providers",
        "ECONOMY_WALLET_CAPITAL_VIEW_PROVIDER_REF",
    ),
    "resolve_wallet_capital_view_state_from_economy_replica": (
        "aware_economy_service.view_state_providers",
        "resolve_wallet_capital_view_state_from_economy_replica",
    ),
    "wallet_capital_view_state": (
        "aware_economy_service.view_state_providers",
        "wallet_capital_view_state",
    ),
    "wallet_capital_view_state_from_frame": (
        "aware_economy_service.view_state_providers",
        "wallet_capital_view_state_from_frame",
    ),
}

__all__ = [
    "ECONOMY_WALLET_CAPITAL_API_VIEW_REF",
    "ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF",
    "ECONOMY_WALLET_CAPITAL_VIEW_PROVIDER_REF",
    "EconomyPriceReservationSettlementAdapter",
    "build_aware_economy_service_protocol_handler",
    "build_service_bindings",
    "build_service_operation_settlement_adapter",
    "resolve_wallet_capital_view_state_from_economy_replica",
    "register_service_plugins",
    "wallet_capital_view_state",
    "wallet_capital_view_state_from_frame",
]


def __getattr__(name: str) -> Any:
    lazy_target = _LAZY_EXPORTS.get(name)
    if lazy_target is not None:
        module_name, attr_name = lazy_target
        from importlib import import_module

        return getattr(import_module(module_name), attr_name)
    if name in {
        "EconomyPriceReservationSettlementAdapter",
        "build_service_operation_settlement_adapter",
    }:
        from .service_operation_settlement_adapter import (
            EconomyPriceReservationSettlementAdapter,
            build_service_operation_settlement_adapter,
        )

        exports = {
            "EconomyPriceReservationSettlementAdapter": EconomyPriceReservationSettlementAdapter,
            "build_service_operation_settlement_adapter": build_service_operation_settlement_adapter,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

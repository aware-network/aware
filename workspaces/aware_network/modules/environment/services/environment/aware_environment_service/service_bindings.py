from __future__ import annotations

from .api_service_protocol import (
    AwareEnvironmentServiceProtocolHandler,
    build_aware_environment_service_protocol_handler,
)


def build_service_bindings() -> dict[str, AwareEnvironmentServiceProtocolHandler]:
    return {
        "aware_environment": build_aware_environment_service_protocol_handler(),
    }


__all__ = [
    "build_service_bindings",
]

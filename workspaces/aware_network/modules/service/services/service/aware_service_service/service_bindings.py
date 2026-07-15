from __future__ import annotations

from .api_service_protocol import (
    AwareServiceServiceProtocolHandler,
    build_aware_service_service_protocol_handler,
)
from .app import ServiceHostApp


def build_service_bindings(
    *,
    app: ServiceHostApp | None = None,
) -> dict[str, AwareServiceServiceProtocolHandler]:
    return {
        "aware_service": build_aware_service_service_protocol_handler(app=app),
    }


__all__ = [
    "build_service_bindings",
]

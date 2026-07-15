from __future__ import annotations

from .api_service_protocol import build_aware_code_service_protocol_handler


def build_service_bindings() -> dict[str, object]:
    return {
        "aware_code": build_aware_code_service_protocol_handler(),
    }


__all__ = [
    "build_service_bindings",
]

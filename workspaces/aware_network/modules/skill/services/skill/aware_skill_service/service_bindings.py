from __future__ import annotations

from .api_service_protocol import build_aware_skill_service_protocol_handler


def build_service_bindings() -> dict[str, object]:
    return {
        "aware_skill": build_aware_skill_service_protocol_handler(),
    }


__all__ = [
    "build_service_bindings",
]

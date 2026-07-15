from __future__ import annotations


def service_activation_requires_materialization(message: str) -> RuntimeError:
    from aware_service_runtime.implementation_package import (
        ServiceActivationRequiresMaterialization,
    )

    return ServiceActivationRequiresMaterialization(message)


__all__ = ["service_activation_requires_materialization"]

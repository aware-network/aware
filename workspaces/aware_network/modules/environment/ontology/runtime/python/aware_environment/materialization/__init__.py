from __future__ import annotations

from typing import Any


_SERVICE_EXPORTS = {
    "EnvironmentPackageMaterializationResult",
    "EnvironmentSemanticPackageMaterializationRef",
    "EnvironmentSemanticPackageMaterializationProgress",
    "materialize_environment_package_from_manifest",
}


def __getattr__(name: str) -> Any:
    if name not in _SERVICE_EXPORTS:
        raise AttributeError(name)
    from aware_environment.materialization import service

    value = getattr(service, name)
    globals()[name] = value
    return value


__all__ = sorted(_SERVICE_EXPORTS)

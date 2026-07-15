from __future__ import annotations

from importlib import import_module
from typing import Any


_LAZY_EXPORTS = {
    "NodeDeployBackend": (
        "aware_network.node_deploy.backends.base",
        "NodeDeployBackend",
    ),
    "OperatorRunNode": (
        "aware_network.node_deploy.backends.operator_run",
        "OperatorRunNode",
    ),
    "OperatorRunNodeDeployBackend": (
        "aware_network.node_deploy.backends.operator_run",
        "OperatorRunNodeDeployBackend",
    ),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attr_name = _LAZY_EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))


__all__ = sorted(_LAZY_EXPORTS)

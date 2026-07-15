from __future__ import annotations

from importlib import import_module
from typing import Any


_LAZY_EXPORTS = {
    "DefaultNodeDeploySupervisor": (
        "aware_network.node_deploy.supervisor",
        "DefaultNodeDeploySupervisor",
    ),
    "NodeDeployBackend": (
        "aware_network.node_deploy.backends.base",
        "NodeDeployBackend",
    ),
    "NodeDeployEventSink": (
        "aware_network.node_deploy.contracts",
        "NodeDeployEventSink",
    ),
    "NodeDeployLogTail": (
        "aware_network.node_deploy.models",
        "NodeDeployLogTail",
    ),
    "NodeDeployRuntimeSnapshot": (
        "aware_network.node_deploy.models",
        "NodeDeployRuntimeSnapshot",
    ),
    "NodeDeploySupervisor": (
        "aware_network.node_deploy.contracts",
        "NodeDeploySupervisor",
    ),
    "NodeDeploySupervisorError": (
        "aware_network.node_deploy.errors",
        "NodeDeploySupervisorError",
    ),
    "OperatorRunNode": (
        "aware_network.node_deploy.backends",
        "OperatorRunNode",
    ),
    "OperatorRunNodeDeployBackend": (
        "aware_network.node_deploy.backends",
        "OperatorRunNodeDeployBackend",
    ),
    "build_failure_response": (
        "aware_network.node_deploy.errors",
        "build_failure_response",
    ),
    "build_log_event": (
        "aware_network.node_deploy.models",
        "build_log_event",
    ),
    "build_status_event": (
        "aware_network.node_deploy.models",
        "build_status_event",
    ),
    "build_terminal_event": (
        "aware_network.node_deploy.models",
        "build_terminal_event",
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

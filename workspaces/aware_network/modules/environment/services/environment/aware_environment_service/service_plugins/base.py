"""Backward-compatible aliases for Environment service compatibility rails.

Canonical ownership for Environment-only compatibility moved to
`aware_service_runtime.adapters.environment`.
"""

from aware_service_runtime.contracts import (
    ServiceGraphGateway,
    ServiceOperationPluginHandler,
    StreamLifecycle,
)
from aware_service_runtime.adapters.environment import (
    EnvironmentServiceInvocationHandler as ServiceOperationInvocationHandler,
    EnvironmentServiceResult as ServiceOperationResult,
    EnvironmentServiceTransport as ServiceOperationTransport,
)

EnvironmentServicePlugin = ServiceOperationPluginHandler
EnvironmentServiceTransport = ServiceOperationTransport

__all__ = [
    "EnvironmentServicePlugin",
    "EnvironmentServiceTransport",
    "ServiceGraphGateway",
    "ServiceOperationInvocationHandler",
    "ServiceOperationPluginHandler",
    "ServiceOperationResult",
    "StreamLifecycle",
]

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from inspect import signature
from typing import cast

from aware_service_runtime.adapters.environment import EnvironmentInvocationHandlerAdapter
from aware_service_runtime.contracts import (
    ServiceOperationHandler,
    ServiceOperationPluginHandler,
    ServiceOperationInvocationHandler,
    ServiceOperationRequest,
    ServiceOperationResponse,
)


class UnsupportedServiceError(LookupError):
    """Raised when no registered handler exists for the requested service."""


@dataclass(slots=True)
class ServiceOperationRouter:
    plugins: Mapping[str, ServiceOperationPluginHandler]

    def list_services(self) -> tuple[str, ...]:
        return tuple(sorted(self.plugins.keys()))

    def resolve_handler(
        self,
        *,
        service: str,
    ) -> ServiceOperationHandler:
        plugin = self.plugins.get(service)
        if plugin is None:
            raise UnsupportedServiceError(f"Unsupported service operation: {service}")
        return _coerce_operation_handler(plugin)

    async def handle_request(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> ServiceOperationResponse:
        handler = self.resolve_handler(service=request.service)
        return await handler.handle_request(request=request)

    async def handle_notification(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None:
        handler = self.resolve_handler(service=request.service)
        await handler.handle_notification(request=request)


def _coerce_operation_handler(
    plugin: ServiceOperationPluginHandler,
) -> ServiceOperationHandler:
    handle_request = getattr(plugin, "handle_request", None)
    if not callable(handle_request):
        raise TypeError(
            f"Invalid service plugin {plugin!r}: missing handle_request(...)"
        )
    try:
        params = tuple(signature(handle_request).parameters)
    except (TypeError, ValueError):
        params = ()
    if "request" in params:
        return cast(ServiceOperationHandler, plugin)
    if "invocation" in params:
        legacy = cast(ServiceOperationInvocationHandler, plugin)
        return EnvironmentInvocationHandlerAdapter(plugin=legacy)
    raise TypeError(
        "Unsupported service plugin handler signature. Expected "
        "handle_request(*, request=...) or handle_request(*, invocation=...)."
    )

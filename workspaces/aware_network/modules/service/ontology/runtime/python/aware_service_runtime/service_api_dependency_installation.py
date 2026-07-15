from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast

from aware_code.types import JsonArray
from aware_comms import DuplexIpcEndpoint
from aware_service_runtime.contracts import (
    ActivateServiceHostLifecyclesHostControlRequest,
    ActivateServiceHostLifecyclesHostControlResponse,
    ConfigureServiceApiDependencyRoutesHostControlRequest,
    ConfigureServiceApiDependencyRoutesHostControlResponse,
    RequestStatus,
    ServiceHostControlRequest,
    ServiceHostControlResponse,
)
from aware_service_runtime.duplex_client import ServiceHostDuplexClient
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    service_api_dependency_routes_to_payload,
)


class ServiceApiDependencyRouteInstallationError(RuntimeError):
    """Raised when ServiceHost route installation fails."""


class ServiceHostLifecycleActivationError(RuntimeError):
    """Raised when prepared ServiceHost lifecycle activation fails."""


class ServiceHostControlClientLike(Protocol):
    async def send_host_control_request(
        self,
        *,
        request: ServiceHostControlRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostControlResponse: ...


async def install_service_api_dependency_routes(
    *,
    client: ServiceHostControlClientLike,
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    timeout_s: float | None = 5.0,
) -> ConfigureServiceApiDependencyRoutesHostControlResponse:
    """Install resolved API dependency routes into one ServiceHost."""

    response = await client.send_host_control_request(
        request=ConfigureServiceApiDependencyRoutesHostControlRequest(
            routes=cast(JsonArray, service_api_dependency_routes_to_payload(routes)),
        ),
        timeout_s=timeout_s,
    )
    if not isinstance(response, ConfigureServiceApiDependencyRoutesHostControlResponse):
        raise ServiceApiDependencyRouteInstallationError(
            "ServiceHost route installation returned unexpected response type "
            f"{type(response).__name__}."
        )
    if response.status != RequestStatus.succeeded:
        detail = f": {response.error}" if response.error else ""
        raise ServiceApiDependencyRouteInstallationError(
            "ServiceHost route installation failed"
            f" (status={response.status.value}){detail}."
        )
    return response


async def install_service_api_dependency_routes_for_endpoint(
    *,
    endpoint: DuplexIpcEndpoint,
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    timeout_s: float | None = 5.0,
) -> ConfigureServiceApiDependencyRoutesHostControlResponse:
    """Install resolved API dependency routes into the ServiceHost at endpoint."""

    return await install_service_api_dependency_routes(
        client=ServiceHostDuplexClient(endpoint=endpoint),
        routes=routes,
        timeout_s=timeout_s,
    )


async def install_service_api_dependency_routes_for_socket(
    *,
    socket_path: str | Path,
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    timeout_s: float | None = 5.0,
) -> ConfigureServiceApiDependencyRoutesHostControlResponse:
    """Install resolved API dependency routes into a unix-socket ServiceHost."""

    return await install_service_api_dependency_routes_for_endpoint(
        endpoint=DuplexIpcEndpoint.unix_socket(socket_path=str(socket_path)),
        routes=routes,
        timeout_s=timeout_s,
    )


async def activate_service_host_lifecycles(
    *,
    client: ServiceHostControlClientLike,
    timeout_s: float | None = 5.0,
) -> ActivateServiceHostLifecyclesHostControlResponse:
    """Activate one prepared ServiceHost after its dependency routes are installed."""

    response = await client.send_host_control_request(
        request=ActivateServiceHostLifecyclesHostControlRequest(),
        timeout_s=timeout_s,
    )
    if not isinstance(response, ActivateServiceHostLifecyclesHostControlResponse):
        raise ServiceHostLifecycleActivationError(
            "ServiceHost lifecycle activation returned unexpected response type "
            f"{type(response).__name__}."
        )
    if response.status != RequestStatus.succeeded:
        detail = f": {response.error}" if response.error else ""
        raise ServiceHostLifecycleActivationError(
            "ServiceHost lifecycle activation failed"
            f" (status={response.status.value}){detail}."
        )
    return response


async def activate_service_host_lifecycles_for_endpoint(
    *,
    endpoint: DuplexIpcEndpoint,
    timeout_s: float | None = 5.0,
) -> ActivateServiceHostLifecyclesHostControlResponse:
    return await activate_service_host_lifecycles(
        client=ServiceHostDuplexClient(endpoint=endpoint),
        timeout_s=timeout_s,
    )


__all__ = [
    "ServiceApiDependencyRouteInstallationError",
    "ServiceHostLifecycleActivationError",
    "ServiceHostControlClientLike",
    "activate_service_host_lifecycles",
    "activate_service_host_lifecycles_for_endpoint",
    "install_service_api_dependency_routes",
    "install_service_api_dependency_routes_for_endpoint",
    "install_service_api_dependency_routes_for_socket",
]

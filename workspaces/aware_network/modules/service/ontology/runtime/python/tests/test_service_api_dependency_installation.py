from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from aware_service_runtime.contracts import (
    ActivateServiceHostLifecyclesHostControlRequest,
    ActivateServiceHostLifecyclesHostControlResponse,
    ConfigureServiceApiDependencyRoutesHostControlRequest,
    ConfigureServiceApiDependencyRoutesHostControlResponse,
    RequestStatus,
    ServiceHostControlRequest,
    ServiceHostControlResponse,
)
from aware_service_runtime.service_api_dependency_installation import (
    ServiceApiDependencyRouteInstallationError,
    ServiceHostLifecycleActivationError,
    activate_service_host_lifecycles,
    install_service_api_dependency_routes,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    ServiceApiDependencyRouteKind,
    service_api_dependency_routes_from_payload,
)


class _FakeHostControlClient:
    def __init__(self, *, response: ServiceHostControlResponse) -> None:
        self.response = response
        self.requests: list[ServiceHostControlRequest] = []
        self.timeout_s: float | None = None

    async def send_host_control_request(
        self,
        *,
        request: ServiceHostControlRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostControlResponse:
        self.requests.append(request)
        self.timeout_s = timeout_s
        return self.response


def _route(tmp_path: Path) -> ServiceApiDependencyRouteDescriptor:
    return ServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=uuid4(),
        consumer_service_package_name="aware-environment-service",
        provider_service_package_id=uuid4(),
        provider_service_package_name="aware-meta-service",
        api_package_id=uuid4(),
        api_package_name="meta-service-api",
        route_kind=ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC,
        host_id="aware-meta-service-host",
        host_version="1.0.0",
        protocol_version="1",
        socket_path=tmp_path / "aware-meta-service.sock",
        request_timeout_s=7.5,
        service_names=("aware_meta",),
        endpoint_refs_by_service={
            "aware_meta": ("meta.object_instance_graph_identity.history_upsert",),
        },
    )


@pytest.mark.asyncio
async def test_install_service_api_dependency_routes_uses_host_control_request(
    tmp_path: Path,
) -> None:
    route = _route(tmp_path)
    client = _FakeHostControlClient(
        response=ConfigureServiceApiDependencyRoutesHostControlResponse(
            status=RequestStatus.succeeded,
            route_count=1,
        )
    )

    response = await install_service_api_dependency_routes(
        client=client,
        routes=(route,),
        timeout_s=11.0,
    )

    assert response.route_count == 1
    assert client.timeout_s == 11.0
    assert len(client.requests) == 1
    request = client.requests[0]
    assert isinstance(request, ConfigureServiceApiDependencyRoutesHostControlRequest)
    assert service_api_dependency_routes_from_payload(request.routes) == (route,)


@pytest.mark.asyncio
async def test_install_service_api_dependency_routes_fails_closed_on_failed_response(
    tmp_path: Path,
) -> None:
    client = _FakeHostControlClient(
        response=ConfigureServiceApiDependencyRoutesHostControlResponse(
            status=RequestStatus.failed,
            error="route rejected",
        )
    )

    with pytest.raises(
        ServiceApiDependencyRouteInstallationError,
        match="route rejected",
    ):
        await install_service_api_dependency_routes(
            client=client,
            routes=(_route(tmp_path),),
        )


@pytest.mark.asyncio
async def test_install_service_api_dependency_routes_fails_closed_on_base_response(
    tmp_path: Path,
) -> None:
    client = _FakeHostControlClient(
        response=ServiceHostControlResponse(
            operation="unexpected",
            status=RequestStatus.succeeded,
        )
    )

    with pytest.raises(
        ServiceApiDependencyRouteInstallationError,
        match="unexpected response type",
    ):
        await install_service_api_dependency_routes(
            client=client,
            routes=(_route(tmp_path),),
        )


@pytest.mark.asyncio
async def test_activate_service_host_lifecycles_uses_typed_control_request() -> None:
    client = _FakeHostControlClient(
        response=ActivateServiceHostLifecyclesHostControlResponse(
            status=RequestStatus.succeeded,
            lifecycle_handler_count=2,
        )
    )

    response = await activate_service_host_lifecycles(
        client=client,
        timeout_s=17.0,
    )

    assert response.lifecycle_handler_count == 2
    assert client.timeout_s == 17.0
    assert len(client.requests) == 1
    assert isinstance(
        client.requests[0],
        ActivateServiceHostLifecyclesHostControlRequest,
    )


@pytest.mark.asyncio
async def test_activate_service_host_lifecycles_fails_closed() -> None:
    client = _FakeHostControlClient(
        response=ActivateServiceHostLifecyclesHostControlResponse(
            status=RequestStatus.failed,
            error="route plan missing",
        )
    )

    with pytest.raises(
        ServiceHostLifecycleActivationError,
        match="route plan missing",
    ):
        await activate_service_host_lifecycles(client=client)

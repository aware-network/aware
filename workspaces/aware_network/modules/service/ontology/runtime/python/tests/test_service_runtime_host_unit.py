from __future__ import annotations

import sys
import types
from uuid import uuid4

import pytest

from aware_environment_service_dto.environment.environment_service_operation import (
    EnvironmentServiceOperation,
)
from aware_environment_service_dto.environment.environment_service_operation import (
    EnvironmentServiceOperationRequest,
)
from aware_service_runtime.adapters.environment import (
    build_environment_operation_context,
    build_service_operation_request,
    build_service_operation_context,
)
from aware_service_runtime.api_ingress.host_context import service_api_host_context
from aware_service_runtime.contracts import (
    MetaTemporalGraphRoute,
    RequestStatus,
    ServiceGraphGateway,
    ServiceHostTransport,
    ServiceOperationResponse,
    ServiceOperationResult,
)
from aware_service_runtime.host import ServiceRuntimeHost
from aware_service_runtime.registry import reset_plugin_registry_for_tests
from aware_service_runtime.router import UnsupportedServiceError


class _NoopGraphGateway(ServiceGraphGateway):
    async def resolve_graph_context(self) -> object:
        return object()

    async def invoke_function(self, *, request, graph_context=None):  # type: ignore[no-untyped-def]
        _ = request, graph_context
        raise RuntimeError("not used")


class _NoopMetaTemporalGraphRoute(MetaTemporalGraphRoute):
    async def invoke_temporal_function(self, **kwargs: object) -> object:
        _ = kwargs
        raise RuntimeError("not used")


class _NoopTransport(ServiceHostTransport):
    async def send_service_response(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        _ = kwargs

    async def close_service_stream(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        _ = kwargs

    async def get_graph_gateway(self) -> ServiceGraphGateway:
        return _NoopGraphGateway()

    async def get_meta_temporal_graph_route(self) -> MetaTemporalGraphRoute:
        return _NoopMetaTemporalGraphRoute()


class _WorkflowIssuePlugin:
    service = "workflow_issue"

    def __init__(self, *, transport: ServiceHostTransport) -> None:
        self._transport = transport

    async def handle_request(self, *, invocation) -> ServiceOperationResult:  # type: ignore[no-untyped-def]
        _ = invocation
        return ServiceOperationResult(status=RequestStatus.succeeded)

    async def handle_notification(self, *, invocation) -> None:  # type: ignore[no-untyped-def]
        _ = invocation


class _WorkspacePlugin:
    service = "workspace"

    def __init__(self, *, transport: ServiceHostTransport) -> None:
        self._transport = transport

    async def handle_request(self, *, request) -> ServiceOperationResponse:  # type: ignore[no-untyped-def]
        _ = request
        return ServiceOperationResponse(status=RequestStatus.succeeded)

    async def handle_notification(self, *, request) -> None:  # type: ignore[no-untyped-def]
        _ = request


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_plugin_registry_for_tests()
    yield
    reset_plugin_registry_for_tests()


@pytest.fixture
def _provider_module(monkeypatch: pytest.MonkeyPatch) -> str:
    provider = "aware_test_service_runtime_provider.providers"
    module = types.ModuleType(provider)

    def _register_plugins(register_plugin):  # type: ignore[no-untyped-def]
        register_plugin(_WorkflowIssuePlugin)
        register_plugin(_WorkspacePlugin)
        return None

    setattr(module, "register_plugins", _register_plugins)
    monkeypatch.setitem(sys.modules, provider, module)
    return provider


def _env_req() -> EnvironmentServiceOperationRequest:
    return EnvironmentServiceOperationRequest(
        operation="service_operation",
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="projection.test",
        service_operation=EnvironmentServiceOperation(
            service="workflow_issue",
            operation="create_issue",
        ),
    )


@pytest.mark.asyncio
async def test_service_runtime_host_configures_and_dispatches(
    _provider_module: str,
) -> None:
    host = ServiceRuntimeHost(transport=_NoopTransport())
    loaded = host.configure(provider_modules=(_provider_module,))
    assert set(loaded) == {"workflow_issue", "workspace"}
    assert host.plugin_services == ("workflow_issue", "workspace")

    env_req = _env_req()
    with pytest.raises(
        RuntimeError,
        match="Environment orchestration context must be passed explicitly",
    ):
        await host.handle_request(
            request=build_service_operation_request(env_req=env_req)
        )

    with service_api_host_context(
        operation_context=build_service_operation_context(env_req=env_req),
        environment_context=build_environment_operation_context(env_req=env_req),
    ):
        legacy_result = await host.handle_request(
            request=build_service_operation_request(env_req=env_req)
        )
    assert legacy_result.status == RequestStatus.succeeded

    workspace_req = _env_req()
    workspace_req.service_operation = EnvironmentServiceOperation(
        service="workspace",
        operation="status_get",
    )
    native_result = await host.handle_request(
        request=build_service_operation_request(env_req=workspace_req)
    )
    assert native_result.status == RequestStatus.succeeded


@pytest.mark.asyncio
async def test_service_runtime_host_raises_for_unknown_service(
    _provider_module: str,
) -> None:
    host = ServiceRuntimeHost(transport=_NoopTransport())
    host.configure(provider_modules=(_provider_module,))

    env_req = _env_req()
    env_req.service_operation = EnvironmentServiceOperation(
        service="unknown_service",
        operation="noop",
    )

    with pytest.raises(UnsupportedServiceError):
        await host.handle_request(
            request=build_service_operation_request(env_req=env_req)
        )

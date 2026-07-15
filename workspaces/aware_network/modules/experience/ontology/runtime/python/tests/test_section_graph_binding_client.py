from __future__ import annotations

# pyright: reportMissingImports=false, reportAttributeAccessIssue=false

import sys
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest

from ._experience_runtime_test_paths import REPO_ROOT

_REPO_ROOT = REPO_ROOT
for _path in (
    _REPO_ROOT / "apis" / "experience" / "python" / "aware_experience_service_api",
    _REPO_ROOT / "modules" / "experience" / "runtime",
    _REPO_ROOT / "modules" / "experience" / "structure" / "api" / "python",
    _REPO_ROOT / "modules" / "service" / "runtime",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_experience.section_graph_binding.api_models import (  # noqa: E402
    ActivateExperienceSectionGraphBindingRequest,
    ActivateExperienceSectionGraphBindingResponse,
    ExperienceSectionGraphBindingDescriptor,
    ExperienceSectionGraphBindingState,
    ExperienceViewInvocationActionApiDispatchReceipt,
    ExperienceViewInvocationActionReceipt,
    InvokeExperienceViewInvocationActionRequest,
    InvokeExperienceViewInvocationActionResponse,
    RecordExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionResponse,
)
from aware_experience.section_graph_binding.client import (  # noqa: E402
    ExperienceSectionGraphBindingClient,
    build_current_service_host_context_section_graph_binding_client,
)
import aware_experience.section_graph_binding.client as section_graph_binding_client  # noqa: E402
from aware_service_runtime.api_ingress.host_context import (
    service_api_host_context,
)  # noqa: E402
from aware_service_runtime.contracts import ServiceOperationContext  # noqa: E402
from aware_service_runtime.service_api_dependency_routes import (  # noqa: E402
    ServiceApiDependencyRouteDescriptor,
    ServiceApiDependencyRouteKind,
)


def test_section_graph_binding_client_does_not_call_module_service_directly() -> None:
    source = Path(section_graph_binding_client.__file__).read_text(encoding="utf-8")

    assert "aware_experience.section_graph_binding.service" not in source


def _service_context() -> ServiceOperationContext:
    return ServiceOperationContext(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="experience.section_graph_binding.client",
    )


def _service_api_route(
    *,
    api_package_name: str,
) -> ServiceApiDependencyRouteDescriptor:
    return ServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=uuid4(),
        consumer_service_package_name="aware-home-devices-service",
        provider_service_package_id=uuid4(),
        provider_service_package_name="aware-experience-service",
        api_package_id=uuid4(),
        api_package_name=api_package_name,
        route_kind=ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC,
        host_id="aware-experience-service-host",
        host_version="1.0.0",
        protocol_version="1",
        socket_path=Path("/tmp/aware-experience-service.sock"),
        request_timeout_s=5.0,
        service_names=("aware_experience",),
    )


def _sample_binding_state(*, binding_key: str) -> ExperienceSectionGraphBindingState:
    projection_observable_id = uuid4()
    projection_experience_graph_identity_id = uuid4()
    object_projection_graph_identity_id = uuid4()
    return ExperienceSectionGraphBindingState(
        binding=ExperienceSectionGraphBindingDescriptor(
            binding_key=binding_key,
            section_key="orchestration",
            projection_observable_id=projection_observable_id,
            projection_experience_graph_identity_id=(
                projection_experience_graph_identity_id
            ),
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            view_ref="isolated_story.door",
            graph_identity_ref="front_door",
        ),
        exists=True,
        is_active=True,
        focus_scope_id=uuid4(),
        focus_id=uuid4(),
        projection_observable_id=projection_observable_id,
        projection_experience_graph_identity_id=(
            projection_experience_graph_identity_id
        ),
        observable_id=uuid4(),
    )


class _RecordingTransport:
    def __init__(self) -> None:
        self.requests: list[object] = []

    async def send_request(self, *, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        if isinstance(request, InvokeExperienceViewInvocationActionRequest):
            return InvokeExperienceViewInvocationActionResponse(
                request_id=request.request_id,
                success=True,
                info="invoked",
                experience_name=request.experience_name,
                receipt=ExperienceViewInvocationActionReceipt(
                    projection_experience_view_instance_id=(
                        request.projection_experience_view_instance_id
                    ),
                    view_invocation_action_config_id=(
                        request.view_invocation_action_config_id
                    ),
                    experience_invocation_action_config_id=uuid4(),
                    experience_invocation_action_id=uuid4(),
                    projection_experience_view_invocation_action_id=uuid4(),
                    invocation_key=request.invocation_key,
                    actor_id=request.actor_id,
                    api_call_id=uuid4(),
                    sdk_operation_call_id=None,
                    request_ref=request.request_ref,
                    receipt_ref=request.receipt_ref,
                    status="succeeded",
                ),
                api_dispatch_receipt=ExperienceViewInvocationActionApiDispatchReceipt(
                    endpoint_ref="identity.signup_via_profile.signup_via_profile",
                    discriminant="identity.signup_via_profile.signup_via_profile",
                    status="succeeded",
                    api_call_id=uuid4(),
                    api_capability_endpoint_id=uuid4(),
                ),
                response_payload={"admitted": True},
            )
        if isinstance(request, RecordExperienceViewInvocationActionRequest):
            return RecordExperienceViewInvocationActionResponse(
                request_id=request.request_id,
                success=True,
                info="recorded",
                experience_name=request.experience_name,
                receipt=ExperienceViewInvocationActionReceipt(
                    projection_experience_view_instance_id=(
                        request.projection_experience_view_instance_id
                    ),
                    view_invocation_action_config_id=(
                        request.view_invocation_action_config_id
                    ),
                    experience_invocation_action_config_id=uuid4(),
                    experience_invocation_action_id=uuid4(),
                    projection_experience_view_invocation_action_id=uuid4(),
                    invocation_key=request.invocation_key,
                    actor_id=request.actor_id,
                    api_call_id=request.api_call_id,
                    sdk_operation_call_id=request.sdk_operation_call_id,
                    request_ref=request.request_ref,
                    receipt_ref=request.receipt_ref,
                    status=request.status,
                ),
            )
        typed_request = cast(ActivateExperienceSectionGraphBindingRequest, request)
        return ActivateExperienceSectionGraphBindingResponse(
            request_id=typed_request.request_id,
            success=True,
            info="activated",
            experience_name=typed_request.experience_name,
            catalog_revision="catalog-rev-002",
            state=_sample_binding_state(binding_key=typed_request.binding_key),
        )


class _DummyExecution:
    def __init__(self) -> None:
        self.open_requests: list[dict[str, object]] = []

    async def open(self, request):  # type: ignore[no-untyped-def]
        self.open_requests.append(dict(cast(dict[str, object], request)))
        return type("_Response", (), {"value": object()})()


async def _open_isolated_section(*, execution: _DummyExecution) -> None:
    client = build_current_service_host_context_section_graph_binding_client()
    if client is not None:
        await client.activate_binding(
            experience_name="isolated_story",
            binding_key="isolated.front_door",
            rationale="isolated.open_section:isolated.front_door",
            section_title="Isolated Section",
            focus_scope_title="Front Door",
        )
    await execution.open({"label": "front-door"})


@pytest.mark.asyncio
async def test_section_graph_binding_client_activate_binding_builds_activate_request() -> (
    None
):
    transport = _RecordingTransport()
    client = ExperienceSectionGraphBindingClient(transport=transport)

    response = await client.activate_binding(
        experience_name="isolated_story",
        binding_key="security.front_door",
        rationale="isolated.open_door:security.front_door",
        section_title="Security",
        focus_scope_title="Front Door",
    )

    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.experience_name == "isolated_story"
    assert request.binding_key == "security.front_door"
    assert request.rationale == "isolated.open_door:security.front_door"
    assert request.section_title == "Security"
    assert request.focus_scope_title == "Front Door"
    assert response.state.binding.binding_key == "security.front_door"
    assert response.state.is_active is True


@pytest.mark.asyncio
async def test_section_graph_binding_client_record_view_invocation_action_builds_request() -> (
    None
):
    transport = _RecordingTransport()
    client = ExperienceSectionGraphBindingClient(transport=transport)
    view_instance_id = uuid4()
    view_action_config_id = uuid4()
    invocation_key = uuid4()
    actor_id = uuid4()

    response = await client.record_view_invocation_action(
        experience_name="isolated_story",
        projection_experience_view_instance_id=view_instance_id,
        view_invocation_action_config_id=view_action_config_id,
        invocation_key=invocation_key,
        actor_id=actor_id,
        request_ref="sdk://isolated/open",
        status="succeeded",
    )

    assert len(transport.requests) == 1
    request = cast(RecordExperienceViewInvocationActionRequest, transport.requests[0])
    assert request.experience_name == "isolated_story"
    assert request.projection_experience_view_instance_id == view_instance_id
    assert request.view_invocation_action_config_id == view_action_config_id
    assert request.invocation_key == invocation_key
    assert request.actor_id == actor_id
    assert response.receipt.status == "succeeded"


@pytest.mark.asyncio
async def test_section_graph_binding_client_invoke_api_view_invocation_action_builds_request() -> (
    None
):
    transport = _RecordingTransport()
    client = ExperienceSectionGraphBindingClient(transport=transport)
    view_instance_id = uuid4()
    view_action_config_id = uuid4()
    invocation_key = uuid4()
    actor_id = uuid4()

    response = await client.invoke_api_view_invocation_action(
        experience_name="aware_control_identity",
        projection_experience_view_instance_id=view_instance_id,
        view_invocation_action_config_id=view_action_config_id,
        invocation_key=invocation_key,
        actor_id=actor_id,
        request_payload={"profile": {"display_name": "Luis"}},
        request_ref="interface.identity_admission.submit",
    )

    assert len(transport.requests) == 1
    request = cast(InvokeExperienceViewInvocationActionRequest, transport.requests[0])
    assert request.experience_name == "aware_control_identity"
    assert request.projection_experience_view_instance_id == view_instance_id
    assert request.view_invocation_action_config_id == view_action_config_id
    assert request.invocation_key == invocation_key
    assert request.actor_id == actor_id
    assert request.request_payload == {"profile": {"display_name": "Luis"}}
    assert request.request_ref == "interface.identity_admission.submit"
    assert response.receipt.status == "succeeded"
    assert response.api_dispatch_receipt is not None
    assert response.response_payload == {"admitted": True}


@pytest.mark.asyncio
async def test_service_handler_activates_binding_when_host_context_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_build_api_client(routes, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["routes"] = routes
        captured["route_kwargs"] = kwargs
        return object()

    class _FakeActivateCapability:
        async def activate_experience_section_graph_binding(self, request):  # type: ignore[no-untyped-def]
            captured["request"] = request
            return ActivateExperienceSectionGraphBindingResponse(
                request_id=request.request_id,
                success=True,
                info="activated",
                experience_name=request.experience_name,
                catalog_revision="catalog-rev-003",
                state=_sample_binding_state(binding_key=request.binding_key),
            )

    class _FakeExperienceApi:
        activate_experience_section_graph_binding = _FakeActivateCapability()

    class _FakeExperienceServiceApiClient:
        def __init__(self, invoker):  # type: ignore[no-untyped-def]
            captured["invoker"] = invoker
            self.experience = _FakeExperienceApi()

    import aware_experience_service_api  # noqa: E402

    monkeypatch.setattr(
        section_graph_binding_client,
        "build_service_api_client_for_api_package",
        _fake_build_api_client,
    )
    monkeypatch.setattr(
        aware_experience_service_api,
        "AwareExperienceServiceApiClient",
        _FakeExperienceServiceApiClient,
    )

    execution = _DummyExecution()
    with service_api_host_context(
        operation_context=_service_context(),
        graph_gateway=None,
        service_name="aware_experience_client_test",
        service_api_dependency_routes=(
            _service_api_route(api_package_name="experience-service-api"),
        ),
        invocation_context={"surface": {"section_key": "security"}},
    ) as host_context:
        response = await _open_isolated_section(execution=execution)

    assert response is None
    assert execution.open_requests == [{"label": "front-door"}]
    request = cast(ActivateExperienceSectionGraphBindingRequest, captured["request"])
    route_kwargs = captured["route_kwargs"]
    assert request.experience_name == "isolated_story"
    assert request.binding_key == "isolated.front_door"
    assert request.rationale == "isolated.open_section:isolated.front_door"
    assert request.section_title == "Isolated Section"
    assert request.focus_scope_title == "Front Door"
    assert request.activation_scope is not None
    assert request.activation_scope.section_key == "security"
    assert route_kwargs["routes"] == host_context.service_api_dependency_routes
    assert route_kwargs["api_package_name"] == "experience-service-api"
    assert route_kwargs["invocation_context"] == {
        "surface": {"section_key": "security"}
    }


@pytest.mark.asyncio
async def test_host_context_transport_records_view_invocation_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    view_instance_id = uuid4()
    view_action_config_id = uuid4()
    invocation_key = uuid4()
    actor_id = uuid4()

    def _fake_build_api_client(routes, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["routes"] = routes
        captured["route_kwargs"] = kwargs
        return object()

    class _FakeRecordCapability:
        async def record_experience_view_invocation_action(self, request):  # type: ignore[no-untyped-def]
            captured["request"] = request
            return RecordExperienceViewInvocationActionResponse(
                request_id=request.request_id,
                success=True,
                info="recorded",
                experience_name=request.experience_name,
                receipt=ExperienceViewInvocationActionReceipt(
                    projection_experience_view_instance_id=(
                        request.projection_experience_view_instance_id
                    ),
                    view_invocation_action_config_id=(
                        request.view_invocation_action_config_id
                    ),
                    experience_invocation_action_config_id=uuid4(),
                    experience_invocation_action_id=uuid4(),
                    projection_experience_view_invocation_action_id=uuid4(),
                    invocation_key=request.invocation_key,
                    actor_id=request.actor_id,
                    api_call_id=request.api_call_id,
                    sdk_operation_call_id=request.sdk_operation_call_id,
                    request_ref=request.request_ref,
                    receipt_ref=request.receipt_ref,
                    status=request.status,
                ),
            )

    class _FakeExperienceApi:
        record_experience_view_invocation_action = _FakeRecordCapability()

    class _FakeExperienceServiceApiClient:
        def __init__(self, invoker):  # type: ignore[no-untyped-def]
            captured["invoker"] = invoker
            self.experience = _FakeExperienceApi()

    import aware_experience_service_api  # noqa: E402

    monkeypatch.setattr(
        section_graph_binding_client,
        "build_service_api_client_for_api_package",
        _fake_build_api_client,
    )
    monkeypatch.setattr(
        aware_experience_service_api,
        "AwareExperienceServiceApiClient",
        _FakeExperienceServiceApiClient,
    )

    with service_api_host_context(
        operation_context=_service_context(),
        graph_gateway=None,
        service_name="aware_experience_client_test",
        service_api_dependency_routes=(
            _service_api_route(api_package_name="experience-service-api"),
        ),
    ) as host_context:
        client = build_current_service_host_context_section_graph_binding_client()
        assert client is not None
        response = await client.record_view_invocation_action(
            experience_name="isolated_story",
            projection_experience_view_instance_id=view_instance_id,
            view_invocation_action_config_id=view_action_config_id,
            invocation_key=invocation_key,
            actor_id=actor_id,
            request_ref="sdk://isolated/open",
            status="succeeded",
        )

    request = cast(RecordExperienceViewInvocationActionRequest, captured["request"])
    route_kwargs = captured["route_kwargs"]
    assert request.experience_name == "isolated_story"
    assert request.projection_experience_view_instance_id == view_instance_id
    assert request.view_invocation_action_config_id == view_action_config_id
    assert request.invocation_key == invocation_key
    assert request.actor_id == actor_id
    assert response.receipt.status == "succeeded"
    assert route_kwargs["routes"] == host_context.service_api_dependency_routes
    assert route_kwargs["api_package_name"] == "experience-service-api"


@pytest.mark.asyncio
async def test_host_context_transport_invokes_view_invocation_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    view_instance_id = uuid4()
    view_action_config_id = uuid4()
    invocation_key = uuid4()
    actor_id = uuid4()
    api_call_id = uuid4()

    def _fake_build_api_client(routes, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["routes"] = routes
        captured["route_kwargs"] = kwargs
        return object()

    class _FakeInvokeCapability:
        async def invoke_experience_view_invocation_action(self, request):  # type: ignore[no-untyped-def]
            captured["request"] = request
            return InvokeExperienceViewInvocationActionResponse(
                request_id=request.request_id,
                success=True,
                info="invoked",
                experience_name=request.experience_name,
                receipt=ExperienceViewInvocationActionReceipt(
                    projection_experience_view_instance_id=(
                        request.projection_experience_view_instance_id
                    ),
                    view_invocation_action_config_id=(
                        request.view_invocation_action_config_id
                    ),
                    experience_invocation_action_config_id=uuid4(),
                    experience_invocation_action_id=uuid4(),
                    projection_experience_view_invocation_action_id=uuid4(),
                    invocation_key=request.invocation_key,
                    actor_id=request.actor_id,
                    api_call_id=api_call_id,
                    sdk_operation_call_id=None,
                    request_ref=request.request_ref,
                    receipt_ref=request.receipt_ref,
                    status="succeeded",
                ),
                api_dispatch_receipt=ExperienceViewInvocationActionApiDispatchReceipt(
                    endpoint_ref="identity.signup_via_profile.signup_via_profile",
                    discriminant="identity.signup_via_profile.signup_via_profile",
                    status="succeeded",
                    api_call_id=api_call_id,
                    api_capability_endpoint_id=uuid4(),
                ),
                response_payload={"admitted": True},
            )

    class _FakeExperienceApi:
        invoke_experience_view_invocation_action = _FakeInvokeCapability()

    class _FakeExperienceServiceApiClient:
        def __init__(self, invoker):  # type: ignore[no-untyped-def]
            captured["invoker"] = invoker
            self.experience = _FakeExperienceApi()

    import aware_experience_service_api  # noqa: E402

    monkeypatch.setattr(
        section_graph_binding_client,
        "build_service_api_client_for_api_package",
        _fake_build_api_client,
    )
    monkeypatch.setattr(
        aware_experience_service_api,
        "AwareExperienceServiceApiClient",
        _FakeExperienceServiceApiClient,
    )

    with service_api_host_context(
        operation_context=_service_context(),
        graph_gateway=None,
        service_name="aware_experience_client_test",
        service_api_dependency_routes=(
            _service_api_route(api_package_name="experience-service-api"),
        ),
    ) as host_context:
        client = build_current_service_host_context_section_graph_binding_client()
        assert client is not None
        response = await client.invoke_api_view_invocation_action(
            experience_name="aware_control_identity",
            projection_experience_view_instance_id=view_instance_id,
            view_invocation_action_config_id=view_action_config_id,
            invocation_key=invocation_key,
            actor_id=actor_id,
            request_payload={"profile": {"display_name": "Luis"}},
            request_ref="interface.identity_admission.submit",
        )

    request = cast(InvokeExperienceViewInvocationActionRequest, captured["request"])
    route_kwargs = captured["route_kwargs"]
    assert request.experience_name == "aware_control_identity"
    assert request.projection_experience_view_instance_id == view_instance_id
    assert request.view_invocation_action_config_id == view_action_config_id
    assert request.invocation_key == invocation_key
    assert request.actor_id == actor_id
    assert request.request_payload == {"profile": {"display_name": "Luis"}}
    assert response.receipt.api_call_id == api_call_id
    assert response.api_dispatch_receipt is not None
    assert route_kwargs["routes"] == host_context.service_api_dependency_routes
    assert route_kwargs["api_package_name"] == "experience-service-api"


@pytest.mark.asyncio
async def test_service_handler_skips_coordination_when_host_context_is_absent() -> None:
    execution = _DummyExecution()

    response = await _open_isolated_section(execution=execution)

    assert response is None
    assert execution.open_requests == [{"label": "front-door"}]

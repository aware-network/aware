from __future__ import annotations

import pytest

from aware_api_runtime.semantic_functions.execution import (
    API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY,
    ApiSemanticFunctionCallInvocation,
    ApiSemanticFunctionCallInvocationResult,
    api_semantic_function_call_execution_backend_from_context,
    execute_api_semantic_function_call_resolutions,
)
from aware_api_runtime.semantic_functions.resolution import (
    ApiSemanticFunctionCallResolution,
    resolve_api_semantic_function_call_plan_previews,
)
from aware_api_runtime.semantic_function_refs import (
    API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    API_CREATE_CAPABILITY_FUNCTION_REF,
    API_CREATE_FUNCTION_REF,
)
from aware_code.semantic_capability import SemanticCapabilityFunctionCallPlan
from aware_code.semantic_graph_execution import (
    SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY,
    SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY,
)


class RecordingApiExecutionBackend:
    def __init__(self) -> None:
        self.invocations: list[ApiSemanticFunctionCallInvocation] = []

    async def invoke(
        self,
        invocation: ApiSemanticFunctionCallInvocation,
    ) -> ApiSemanticFunctionCallInvocationResult:
        self.invocations.append(invocation)
        object_id = _object_id_for_semantic_key(invocation.result_semantic_key)
        return ApiSemanticFunctionCallInvocationResult(
            object_id=object_id,
            evidence={"ordinal": len(self.invocations)},
        )


@pytest.mark.asyncio
async def test_api_execution_invokes_empty_lane_sequence_with_planned_receivers() -> (
    None
):
    backend = RecordingApiExecutionBackend()
    resolutions = resolve_api_semantic_function_call_plan_previews(
        plans=(
            _api_create_plan(),
            _capability_create_plan(),
            _endpoint_create_plan(),
        ),
        current_semantic_object_ids={},
        resolved_argument_ref_object_ids={
            "aware_demo_api.ReadDemoRequest": "request-class-config-id",
        },
    )

    result = await execute_api_semantic_function_call_resolutions(
        resolutions=resolutions,
        backend=backend,
    )

    assert tuple(resolution.status for resolution in resolutions) == (
        "create_root",
        "create_child",
        "create_child",
    )
    assert result.status_counts == {"invoked": 3}
    assert tuple(invocation.call_target for invocation in backend.invocations) == (
        "constructor",
        "instance",
        "instance",
    )
    assert tuple(invocation.provider_key for invocation in backend.invocations) == (
        "aware_api",
        "aware_api",
        "aware_api",
    )
    assert tuple(invocation.function_ref for invocation in backend.invocations) == (
        API_CREATE_FUNCTION_REF,
        API_CREATE_CAPABILITY_FUNCTION_REF,
        API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    )
    assert backend.invocations[0].arguments == {
        "description": None,
        "name": "demo",
    }
    assert backend.invocations[1].receiver_object_id == "api-id"
    assert backend.invocations[1].arguments == {
        "description": None,
        "name": "read_demo",
    }
    assert backend.invocations[2].receiver_object_id == "capability-id"
    assert backend.invocations[2].arguments == {
        "description": None,
        "name": "read_demo",
        "request_class_config_id": "request-class-config-id",
    }
    assert tuple(step.result_object_id for step in result.steps) == (
        "api-id",
        "capability-id",
        "endpoint-id",
    )
    assert tuple(step.receiver_object_id for step in result.steps) == (
        None,
        "api-id",
        "capability-id",
    )


@pytest.mark.asyncio
async def test_api_execution_uses_current_head_receiver_context() -> None:
    backend = RecordingApiExecutionBackend()
    resolutions = resolve_api_semantic_function_call_plan_previews(
        plans=(_endpoint_create_plan(),),
        current_semantic_object_ids={
            "api:demo/capability:read_demo": "current-capability-id",
        },
        resolved_argument_ref_object_ids={
            "aware_demo_api.ReadDemoRequest": "request-class-config-id",
        },
    )

    result = await execute_api_semantic_function_call_resolutions(
        resolutions=resolutions,
        backend=backend,
    )

    assert result.status_counts == {"invoked": 1}
    assert backend.invocations[0].receiver_object_id == "current-capability-id"
    assert backend.invocations[0].arguments["request_class_config_id"] == (
        "request-class-config-id"
    )


@pytest.mark.asyncio
async def test_api_execution_reports_missing_receiver_as_failed_step() -> None:
    backend = RecordingApiExecutionBackend()
    resolution = ApiSemanticFunctionCallResolution(
        plan=_capability_create_plan(),
        status="create_child",
        receiver_semantic_key="api:demo",
        result_semantic_key="api:demo/capability:read_demo",
    )

    result = await execute_api_semantic_function_call_resolutions(
        resolutions=(resolution,),
        backend=backend,
    )

    assert backend.invocations == []
    assert result.status_counts == {"failed": 1}
    assert result.steps[0].error is not None
    assert "receiver object id" in result.steps[0].error


def test_api_execution_backend_context_resolver_is_explicit() -> None:
    backend = RecordingApiExecutionBackend()
    generic_backend = RecordingApiExecutionBackend()
    provider_backend = RecordingApiExecutionBackend()

    assert (
        api_semantic_function_call_execution_backend_from_context(
            {API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY: backend}
        )
        is backend
    )
    assert (
        api_semantic_function_call_execution_backend_from_context(
            {API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY: object()}
        )
        is None
    )
    assert (
        api_semantic_function_call_execution_backend_from_context(
            {SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY: generic_backend}
        )
        is generic_backend
    )
    assert (
        api_semantic_function_call_execution_backend_from_context(
            {
                SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY: generic_backend,
                SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY: {
                    "aware_api": provider_backend,
                },
            }
        )
        is provider_backend
    )


def _api_create_plan() -> SemanticCapabilityFunctionCallPlan:
    return SemanticCapabilityFunctionCallPlan(
        function_ref=API_CREATE_FUNCTION_REF,
        event_key="aware_api.api.upserted",
        arguments={"name": "demo", "description": None},
        result_semantic_key="api:demo",
    )


def _capability_create_plan() -> SemanticCapabilityFunctionCallPlan:
    return SemanticCapabilityFunctionCallPlan(
        function_ref=API_CREATE_CAPABILITY_FUNCTION_REF,
        event_key="aware_api.api_capability.upserted",
        receiver_semantic_key="api:demo",
        arguments={"name": "read_demo", "description": None},
        result_semantic_key="api:demo/capability:read_demo",
    )


def _endpoint_create_plan() -> SemanticCapabilityFunctionCallPlan:
    return SemanticCapabilityFunctionCallPlan(
        function_ref=API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
        event_key="aware_api.api_capability_endpoint.upserted",
        receiver_semantic_key="api:demo/capability:read_demo",
        arguments={"name": "read_demo", "description": None},
        argument_refs={
            "request_class_config_id": "aware_demo_api.ReadDemoRequest",
        },
        result_semantic_key="api:demo/capability:read_demo/endpoint:read_demo",
    )


def _object_id_for_semantic_key(semantic_key: str | None) -> str:
    if semantic_key == "api:demo":
        return "api-id"
    if semantic_key == "api:demo/capability:read_demo":
        return "capability-id"
    if semantic_key == "api:demo/capability:read_demo/endpoint:read_demo":
        return "endpoint-id"
    return "unknown-id"

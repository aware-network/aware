from __future__ import annotations

from aware_api_runtime.semantic_functions.resolution import (
    resolve_api_semantic_function_call_plan_previews,
)
from aware_api_runtime.semantic_function_refs import (
    API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    API_CREATE_CAPABILITY_FUNCTION_REF,
    API_CREATE_FUNCTION_REF,
)
from aware_code.semantic_capability import SemanticCapabilityFunctionCallPlan


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


def _endpoint_create_plan(
    *,
    request_class_ref: str = "aware_demo_api.ReadDemoRequest",
) -> SemanticCapabilityFunctionCallPlan:
    return SemanticCapabilityFunctionCallPlan(
        function_ref=API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
        event_key="aware_api.api_capability_endpoint.upserted",
        receiver_semantic_key="api:demo/capability:read_demo",
        arguments={"name": "read_demo", "description": None},
        argument_refs={"request_class_config_id": request_class_ref},
        result_semantic_key="api:demo/capability:read_demo/endpoint:read_demo",
    )


def test_resolve_api_semantic_function_call_plans_for_empty_lane_preview() -> None:
    resolutions = resolve_api_semantic_function_call_plan_previews(
        plans=(
            _api_create_plan(),
            _capability_create_plan(),
            _endpoint_create_plan(),
        ),
        current_semantic_object_ids={},
        resolved_argument_ref_object_ids={},
    )

    assert tuple(resolution.status for resolution in resolutions) == (
        "create_root",
        "create_child",
        "needs_ref_resolution",
    )
    assert resolutions[0].receiver_source == "root"
    assert resolutions[1].receiver_source == "planned"
    assert resolutions[1].dependencies == ("api:demo",)
    assert resolutions[2].receiver_source == "planned"
    assert resolutions[2].dependencies == ("api:demo/capability:read_demo",)
    assert resolutions[2].unresolved_argument_refs == {
        "request_class_config_id": "aware_demo_api.ReadDemoRequest",
    }
    assert resolutions[2].evidence_payload()["status"] == "needs_ref_resolution"


def test_resolve_api_semantic_function_call_plans_for_existing_head_noops() -> None:
    resolutions = resolve_api_semantic_function_call_plan_previews(
        plans=(
            _api_create_plan(),
            _capability_create_plan(),
            _endpoint_create_plan(),
        ),
        current_semantic_object_ids={
            "api:demo": "api-id",
            "api:demo/capability:read_demo": "capability-id",
            "api:demo/capability:read_demo/endpoint:read_demo": "endpoint-id",
        },
    )

    assert tuple(resolution.status for resolution in resolutions) == (
        "noop_existing",
        "noop_existing",
        "noop_existing",
    )
    assert tuple(resolution.result_object_id for resolution in resolutions) == (
        "api-id",
        "capability-id",
        "endpoint-id",
    )


def test_resolve_api_semantic_function_call_plan_with_unplanned_receiver() -> None:
    resolutions = resolve_api_semantic_function_call_plan_previews(
        plans=(_endpoint_create_plan(),),
        current_semantic_object_ids={},
    )

    assert resolutions[0].status == "unresolved_receiver"
    assert resolutions[0].receiver_semantic_key == "api:demo/capability:read_demo"


def test_resolve_api_semantic_function_call_plan_with_hydrated_argument_ref() -> None:
    resolutions = resolve_api_semantic_function_call_plan_previews(
        plans=(_endpoint_create_plan(),),
        current_semantic_object_ids={
            "api:demo/capability:read_demo": "capability-id",
        },
        resolved_argument_ref_object_ids={
            "aware_demo_api.ReadDemoRequest": "request-class-config-id",
        },
    )

    assert resolutions[0].status == "create_child"
    assert resolutions[0].receiver_source == "current"
    assert resolutions[0].receiver_object_id == "capability-id"
    assert resolutions[0].resolved_argument_refs == {
        "request_class_config_id": "request-class-config-id",
    }


def test_resolve_api_semantic_function_call_plan_with_empty_argument_ref() -> None:
    resolutions = resolve_api_semantic_function_call_plan_previews(
        plans=(_endpoint_create_plan(request_class_ref=""),),
        current_semantic_object_ids={
            "api:demo/capability:read_demo": "capability-id",
        },
    )

    assert resolutions[0].status == "unresolved_argument_ref"
    assert resolutions[0].unresolved_argument_refs == {
        "request_class_config_id": "",
    }

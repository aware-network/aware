from __future__ import annotations

from aware_code.semantic_action_policy import (
    build_semantic_function_call_plan_previews,
)
from aware_code.semantic_capability import (
    SemanticCapabilityActionBinding,
    SemanticCapabilityEvent,
    SemanticCapabilityFunctionCallBinding,
)


def test_build_semantic_function_call_plan_previews_from_dataclasses() -> None:
    event = SemanticCapabilityEvent(
        event_key="aware_api.api_capability_endpoint.upserted",
        semantic_key="api:demo/capability:read_demo/endpoint:read_demo",
        verb="upsert",
        subject_type="aware_api.ApiCapabilityEndpoint",
        source="aware_api.semantic_analysis",
        payload={
            "capability_semantic_key": "api:demo/capability:read_demo",
            "name": "read_demo",
            "description": None,
            "request_class_ref": "aware_demo_api.ReadDemoRequest",
        },
    )
    action_binding = SemanticCapabilityActionBinding(
        action_key="aware_api.api_capability_endpoint.upserted.apply_ontology",
        event_key="aware_api.api_capability_endpoint.upserted",
        action_type="function_call",
        function_call_binding=SemanticCapabilityFunctionCallBinding(
            binding_key=(
                "aware_api.api_capability_endpoint.upserted."
                "api_capability_create_endpoint"
            ),
            event_key="aware_api.api_capability_endpoint.upserted",
            function_ref=(
                "aware_api_ontology.api.api_capability." "ApiCapability.create_endpoint"
            ),
            receiver_semantic_key_template="payload.capability_semantic_key",
            argument_bindings={
                "name": "payload.name",
                "description": "payload.description",
            },
            argument_ref_bindings={
                "request_class_config_id": "payload.request_class_ref",
            },
            result_semantic_key_template="semantic_key",
            metadata={"argument_ref_resolution": "class_config_id"},
        ),
    )

    plans = build_semantic_function_call_plan_previews(
        semantic_events=(event,),
        action_bindings=(action_binding,),
    )

    assert len(plans) == 1
    assert plans[0].evidence_payload() == {
        "binding_key": (
            "aware_api.api_capability_endpoint.upserted."
            "api_capability_create_endpoint"
        ),
        "action_key": "aware_api.api_capability_endpoint.upserted.apply_ontology",
        "event_key": "aware_api.api_capability_endpoint.upserted",
        "function_ref": (
            "aware_api_ontology.api.api_capability." "ApiCapability.create_endpoint"
        ),
        "receiver_semantic_key": "api:demo/capability:read_demo",
        "arguments": {
            "description": None,
            "name": "read_demo",
        },
        "argument_refs": {
            "request_class_config_id": "aware_demo_api.ReadDemoRequest",
        },
        "result_semantic_key": "api:demo/capability:read_demo/endpoint:read_demo",
        "metadata": {
            "argument_ref_resolution": "class_config_id",
            "preview_kind": "semantic_event_action_policy",
            "preview_status": "ready",
        },
    }


def test_build_semantic_function_call_plan_previews_reports_unresolved_templates() -> (
    None
):
    plans = build_semantic_function_call_plan_previews(
        semantic_events=(
            {
                "event_key": "demo.event",
                "semantic_key": "demo:subject",
                "payload": {"name": "demo"},
            },
        ),
        action_bindings=(
            {
                "action_key": "demo.event.apply",
                "event_key": "demo.event",
                "action_type": "function_call",
                "function_call_binding": {
                    "binding_key": "demo.binding",
                    "event_key": "demo.event",
                    "function_ref": "demo.Function.apply",
                    "argument_bindings": {"name": "payload.name"},
                    "argument_ref_bindings": {"missing_ref_id": "payload.missing_ref"},
                    "result_semantic_key_template": "semantic_key",
                },
            },
        ),
    )

    assert len(plans) == 1
    assert plans[0].arguments == {"name": "demo"}
    assert plans[0].argument_refs == {}
    assert plans[0].metadata["preview_status"] == "unresolved_templates"
    assert plans[0].metadata["unresolved_templates"] == (
        {
            "target": "argument_refs.missing_ref_id",
            "template": "payload.missing_ref",
        },
    )

from __future__ import annotations

from uuid import uuid4

from aware_experience.section_graph_binding.api_models import (
    ActivateExperienceSectionGraphBindingResponse,
    ApplyExperienceViewEventTransitionRequest,
    ApplyExperienceViewEventTransitionResponse,
    GetExperienceSectionGraphBindingCatalogRequest,
    RecordExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionResponse,
    WatchExperienceSectionGraphBindingsRequest,
)


def _binding_descriptor_payload() -> dict[str, object]:
    return {
        "binding_key": "issue.blocking",
        "section_key": "coordination.primary",
        "projection_observable_id": uuid4(),
        "projection_experience_graph_identity_id": uuid4(),
        "object_projection_graph_identity_id": uuid4(),
        "view_ref": "workspace.issue.detail",
        "graph_identity_ref": "issues.blocking",
    }


def _section_view_payload() -> dict[str, object]:
    return {
        "projection_experience_id": uuid4(),
        "section_id": uuid4(),
        "object_projection_graph_observable_id": uuid4(),
        "projection_experience_section_id": uuid4(),
        "projection_experience_section_view_id": uuid4(),
        "projection_experience_view_instance_id": uuid4(),
        "projection_experience_view_id": uuid4(),
        "section_graph_binding_id": uuid4(),
        "view_ref": "workspace.issue.detail",
        "view_instance_key": "coordination.primary.issue.detail",
        "section_key": "coordination.primary",
        "status": "active",
        "actions": [
            {
                "action_id": (view_action_config_id := uuid4()),
                "view_invocation_action_config_id": view_action_config_id,
                "experience_invocation_action_config_id": uuid4(),
                "api_view_capability_endpoint_id": uuid4(),
                "action_key": "issue.assign",
                "target_kind": "sdk",
                "endpoint_ref": "aware.issue.assign",
                "label": "Assign",
                "receipt_policy": "required",
                "api_capability_endpoint_id": uuid4(),
                "sdk_operation_id": uuid4(),
            }
        ],
    }


def test_parse_get_experience_section_graph_binding_catalog_request() -> None:
    payload = {
        "operation": "get_experience_section_graph_binding_catalog",
        "experience_name": "workspace_coordination",
        "section_keys": ["coordination.primary"],
        "binding_keys": ["issue.blocking"],
    }

    parsed = GetExperienceSectionGraphBindingCatalogRequest.model_validate(payload)
    assert parsed.experience_name == "workspace_coordination"
    assert parsed.section_keys == ["coordination.primary"]
    assert parsed.binding_keys == ["issue.blocking"]


def test_parse_activate_experience_section_graph_binding_response() -> None:
    payload = {
        "operation": "activate_experience_section_graph_binding",
        "experience_name": "workspace_coordination",
        "catalog_revision": "rev-001",
        "state": {
            "binding": _binding_descriptor_payload(),
            "exists": True,
            "is_active": True,
            "focus_scope_id": uuid4(),
            "focus_id": uuid4(),
            "observable_id": uuid4(),
            "section_view": _section_view_payload(),
        },
    }

    parsed = ActivateExperienceSectionGraphBindingResponse.model_validate(payload)
    assert parsed.experience_name == "workspace_coordination"
    assert parsed.catalog_revision == "rev-001"
    assert parsed.state.binding.binding_key == "issue.blocking"
    assert parsed.state.binding.graph_identity_ref == "issues.blocking"
    assert parsed.state.is_active is True
    assert parsed.state.section_view is not None
    assert parsed.state.section_view.view_instance_key == (
        "coordination.primary.issue.detail"
    )
    assert parsed.state.section_view.actions[0].action_key == "issue.assign"


def test_parse_apply_experience_view_event_transition_request() -> None:
    payload = {
        "operation": "apply_experience_view_event_transition",
        "experience_name": "aware_control_identity",
        "profile_key": "os.default",
        "transition_key": "identity_admission.actor_home",
        "source_view_ref": "aware_control_identity.identity.admission.v1",
        "event_type": "identity.admitted",
        "action_type": "experience.focus.actor_home",
    }

    parsed = ApplyExperienceViewEventTransitionRequest.model_validate(payload)

    assert parsed.transition_key == "identity_admission.actor_home"
    assert parsed.profile_key == "os.default"
    assert parsed.source_view_ref == "aware_control_identity.identity.admission.v1"
    assert parsed.event_type == "identity.admitted"
    assert parsed.action_type == "experience.focus.actor_home"
    assert parsed.target_view_ref is None
    assert parsed.target_binding_key is None


def test_parse_apply_experience_view_event_transition_response() -> None:
    payload = {
        "operation": "apply_experience_view_event_transition",
        "experience_name": "aware_control_identity",
        "catalog_revision": "rev-actor-home",
        "state": {
            "binding": _binding_descriptor_payload(),
            "exists": True,
            "is_active": True,
            "focus_scope_id": uuid4(),
            "focus_id": uuid4(),
            "observable_id": uuid4(),
            "section_view": _section_view_payload(),
        },
        "receipt": {
            "transition_key": "identity_admission.actor_home",
            "experience_name": "aware_control_identity",
            "trigger": {
                "source_view_ref": "aware_control_identity.identity.admission.v1",
                "event_type": "identity.admitted",
                "action_type": "experience.focus.actor_home",
            },
            "target": {
                "target_view_ref": "aware_control_identity.actor.home.v1",
                "target_binding_key": "actor.home",
                "target_section_key": "actor_home",
                "target_graph_identity_ref": "identity.actor",
                "section_view": _section_view_payload(),
            },
            "state": {
                "binding": _binding_descriptor_payload(),
                "exists": True,
                "is_active": True,
                "focus_scope_id": uuid4(),
                "focus_id": uuid4(),
                "observable_id": uuid4(),
                "section_view": _section_view_payload(),
            },
        },
    }

    parsed = ApplyExperienceViewEventTransitionResponse.model_validate(payload)

    assert parsed.receipt.transition_key == "identity_admission.actor_home"
    assert parsed.receipt.trigger.event_type == "identity.admitted"
    assert parsed.receipt.target.target_binding_key == "actor.home"
    assert parsed.receipt.target.section_view is not None
    assert parsed.receipt.target.section_view.actions[0].target_kind == "sdk"
    assert parsed.receipt.target.section_view.actions[0].endpoint_ref == (
        "aware.issue.assign"
    )
    assert parsed.state.is_active is True
    assert parsed.state.section_view is not None


def test_parse_record_experience_view_invocation_action_request() -> None:
    payload = {
        "operation": "record_experience_view_invocation_action",
        "experience_name": "workspace_coordination",
        "projection_experience_view_instance_id": uuid4(),
        "view_invocation_action_config_id": uuid4(),
        "invocation_key": uuid4(),
        "actor_id": uuid4(),
        "sdk_operation_call_id": uuid4(),
        "request_ref": "sdk://aware.issue.assign/request/1",
        "status": "succeeded",
    }

    parsed = RecordExperienceViewInvocationActionRequest.model_validate(payload)

    assert parsed.experience_name == "workspace_coordination"
    assert parsed.status == "succeeded"
    assert parsed.api_call_id is None


def test_parse_record_experience_view_invocation_action_response() -> None:
    view_instance_id = uuid4()
    view_action_config_id = uuid4()
    experience_action_config_id = uuid4()
    experience_action_id = uuid4()
    view_action_id = uuid4()
    payload = {
        "operation": "record_experience_view_invocation_action",
        "experience_name": "workspace_coordination",
        "receipt": {
            "projection_experience_view_instance_id": view_instance_id,
            "view_invocation_action_config_id": view_action_config_id,
            "experience_invocation_action_config_id": experience_action_config_id,
            "experience_invocation_action_id": experience_action_id,
            "projection_experience_view_invocation_action_id": view_action_id,
            "invocation_key": uuid4(),
            "actor_id": uuid4(),
            "api_call_id": uuid4(),
            "request_ref": "api://aware.issue.assign/request/1",
            "receipt_ref": "api://aware.issue.assign/receipt/1",
            "status": "succeeded",
            "object_instance_graph_commit_id": uuid4(),
            "commit_id": uuid4(),
        },
    }

    parsed = RecordExperienceViewInvocationActionResponse.model_validate(payload)

    assert parsed.receipt.projection_experience_view_instance_id == view_instance_id
    assert parsed.receipt.view_invocation_action_config_id == view_action_config_id
    assert parsed.receipt.experience_invocation_action_config_id == (
        experience_action_config_id
    )
    assert parsed.receipt.experience_invocation_action_id == experience_action_id
    assert parsed.receipt.projection_experience_view_invocation_action_id == (
        view_action_id
    )


def test_parse_watch_experience_section_graph_bindings_request() -> None:
    payload = {
        "operation": "watch_experience_section_graph_bindings",
        "experience_name": "workspace_coordination",
        "section_keys": ["coordination.primary"],
        "binding_keys": ["issue.blocking", "conversation.hot"],
        "poll_interval_ms": 250,
    }

    parsed = WatchExperienceSectionGraphBindingsRequest.model_validate(payload)
    assert parsed.binding_keys == ["issue.blocking", "conversation.hot"]
    assert parsed.poll_interval_ms == 250

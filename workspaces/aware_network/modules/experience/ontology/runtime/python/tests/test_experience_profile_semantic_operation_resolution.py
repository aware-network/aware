from __future__ import annotations

from aware_code.semantic_capability import (
    SemanticCapabilityEventVerb,
    SemanticCapabilityTypedOperation,
)
from aware_experience.profile.semantic_function_refs import (
    EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION,
    EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF,
)
from aware_experience.profile.semantic_operation_resolution import (
    EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION,
    resolve_experience_semantic_operation_function_call_plan_previews,
)


_SEMANTIC_KEY = "experience.profile:home_story:os.default"
_RECEIVER_ID = "6e5499cc-5e34-5d25-b5c2-d1ad78ff562e"


def _operation(
    *,
    operation_family: SemanticCapabilityEventVerb = "update",
    after_payload: dict[str, object] | None = None,
    semantic_operation_type: str = EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION,
) -> SemanticCapabilityTypedOperation:
    return SemanticCapabilityTypedOperation(
        operation_key="aware_experience.profile.title:home_story:os.default:update",
        operation_family=operation_family,
        semantic_operation_type=semantic_operation_type,
        semantic_key=_SEMANTIC_KEY,
        semantic_subject_type=("aware_experience.EnvironmentExperienceProfileConfig"),
        field_path="title",
        source="aware_code.semantic_source_meaning",
        after_payload=(
            {"title": "Aware Home OS"} if after_payload is None else after_payload
        ),
        requires_baseline_object_identity=True,
    )


def test_profile_title_function_ref_comes_from_materialized_orm_function() -> None:
    assert EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION.ref == (
        EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF
    )
    assert EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF.endswith(
        ".EnvironmentExperienceProfileConfig.update_title"
    )


def test_profile_title_update_resolves_to_function_call_plan() -> None:
    [resolution] = resolve_experience_semantic_operation_function_call_plan_previews(
        typed_operations=(_operation().evidence_payload(),),
        current_semantic_object_ids={_SEMANTIC_KEY: _RECEIVER_ID},
    )

    assert resolution.status == "function_call_plan_ready"
    assert resolution.receiver_object_id == _RECEIVER_ID
    assert resolution.function_call_plan is not None
    assert resolution.function_call_plan.function_ref == (
        EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF
    )
    assert resolution.function_call_plan.receiver_semantic_key == _SEMANTIC_KEY
    assert resolution.function_call_plan.arguments == {"title": "Aware Home OS"}
    evidence = resolution.evidence_payload()
    assert evidence["mutates"] is False
    assert evidence["execution_status"] == "not_requested"


def test_profile_title_delete_resolves_to_explicit_clear() -> None:
    operation = _operation(operation_family="delete")
    [resolution] = resolve_experience_semantic_operation_function_call_plan_previews(
        typed_operations=(operation,),
        baseline_semantic_object_identities={
            _SEMANTIC_KEY: {"receiver_object_id": _RECEIVER_ID}
        },
    )

    assert resolution.status == "function_call_plan_ready"
    assert resolution.function_call_plan is not None
    assert resolution.function_call_plan.arguments == {"title": None}


def test_profile_title_update_blocks_without_receiver_identity() -> None:
    [resolution] = resolve_experience_semantic_operation_function_call_plan_previews(
        typed_operations=(_operation(),),
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == "experience_profile_receiver_identity_unresolved"
    assert resolution.function_call_plan is None


def test_profile_title_update_blocks_malformed_semantic_value() -> None:
    [resolution] = resolve_experience_semantic_operation_function_call_plan_previews(
        typed_operations=(_operation(after_payload={"title": 42}),),
        current_semantic_object_ids={_SEMANTIC_KEY: _RECEIVER_ID},
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == "experience_profile_title_value_invalid"


def test_profile_resolver_rejects_foreign_operation_vocabulary() -> None:
    [resolution] = resolve_experience_semantic_operation_function_call_plan_previews(
        typed_operations=(
            _operation(semantic_operation_type="aware_meta.object_config_graph.update"),
        ),
        current_semantic_object_ids={_SEMANTIC_KEY: _RECEIVER_ID},
    )

    assert resolution.status == "unsupported_operation"
    assert resolution.reason == "experience_semantic_operation_type_unsupported"

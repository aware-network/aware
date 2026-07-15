from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Literal

from aware_code.semantic_capability import (
    SemanticCapabilityFunctionCallPlan,
    SemanticCapabilityTypedOperation,
)

from aware_experience.profile.semantic_function_refs import (
    EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF,
)
from aware_experience.semantic_registry import (
    EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
)


EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION = (
    "aware.experience.profile.semantic-operation-function-call-resolution.v0"
)
EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION = "aware_experience.profile.title.update"
EXPERIENCE_PROFILE_TITLE_UPDATE_BINDING_KEY = (
    "aware_experience.profile.title.update_title"
)

ExperienceSemanticOperationResolutionStatus = Literal[
    "function_call_plan_ready",
    "function_call_plan_blocked",
    "unsupported_operation",
]


@dataclass(frozen=True, slots=True)
class ExperienceSemanticOperationResolution:
    operation_key: str
    semantic_operation_type: str
    semantic_key: str
    status: ExperienceSemanticOperationResolutionStatus
    reason: str
    function_call_plan: SemanticCapabilityFunctionCallPlan | None = None
    receiver_object_id: str | None = None
    blockers: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "resolution_kind": (
                "experience_semantic_operation_function_call_resolution"
            ),
            "contract_version": (
                EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION
            ),
            "operation_key": self.operation_key,
            "semantic_operation_type": self.semantic_operation_type,
            "semantic_key": self.semantic_key,
            "status": self.status,
            "reason": self.reason,
            "blocker_count": len(self.blockers),
            "blockers": self.blockers,
            "metadata": dict(self.metadata),
            "mutates": False,
            "execution_status": "not_requested",
            "would_execute": False,
            "did_execute": False,
        }
        if self.receiver_object_id is not None:
            payload["receiver_object_id"] = self.receiver_object_id
        if self.function_call_plan is not None:
            payload["function_call_plan"] = self.function_call_plan.evidence_payload()
        return payload


def resolve_experience_semantic_operation_function_call_plan_previews(
    *,
    typed_operations: Iterable[SemanticCapabilityTypedOperation | Mapping[str, object]],
    current_semantic_object_ids: Mapping[str, object] | None = None,
    baseline_semantic_object_identities: (
        Mapping[str, Mapping[str, object]] | None
    ) = None,
) -> tuple[ExperienceSemanticOperationResolution, ...]:
    current_ids = _object_id_map(current_semantic_object_ids)
    baseline_identities = baseline_semantic_object_identities or {}
    return tuple(
        _resolve_operation(
            operation=_operation_payload(raw_operation),
            current_semantic_object_ids=current_ids,
            baseline_semantic_object_identities=baseline_identities,
        )
        for raw_operation in typed_operations
    )


def _resolve_operation(
    *,
    operation: Mapping[str, object],
    current_semantic_object_ids: Mapping[str, str],
    baseline_semantic_object_identities: Mapping[str, Mapping[str, object]],
) -> ExperienceSemanticOperationResolution:
    operation_key = _text(operation.get("operation_key"))
    operation_type = _text(operation.get("semantic_operation_type"))
    semantic_key = _text(operation.get("semantic_key"))
    if operation_type != EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION:
        return ExperienceSemanticOperationResolution(
            operation_key=operation_key,
            semantic_operation_type=operation_type,
            semantic_key=semantic_key,
            status="unsupported_operation",
            reason="experience_semantic_operation_type_unsupported",
            blockers=("experience_semantic_operation_type_unsupported",),
        )
    receiver_object_id = current_semantic_object_ids.get(semantic_key)
    if receiver_object_id is None:
        receiver_object_id = _baseline_receiver_object_id(
            identity=baseline_semantic_object_identities.get(semantic_key)
        )
    if receiver_object_id is None:
        return ExperienceSemanticOperationResolution(
            operation_key=operation_key,
            semantic_operation_type=operation_type,
            semantic_key=semantic_key,
            status="function_call_plan_blocked",
            reason="experience_profile_receiver_identity_unresolved",
            blockers=("experience_profile_receiver_identity_unresolved",),
        )
    title_status, title = _title_argument(operation=operation)
    if title_status is not None:
        return ExperienceSemanticOperationResolution(
            operation_key=operation_key,
            semantic_operation_type=operation_type,
            semantic_key=semantic_key,
            status="function_call_plan_blocked",
            reason=title_status,
            receiver_object_id=receiver_object_id,
            blockers=(title_status,),
        )
    event_key = _optional_text(operation.get("event_key"))
    plan = SemanticCapabilityFunctionCallPlan(
        function_ref=EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF,
        binding_key=EXPERIENCE_PROFILE_TITLE_UPDATE_BINDING_KEY,
        event_key=event_key,
        receiver_semantic_key=semantic_key,
        arguments={"title": title},
        metadata={
            "semantic_apply_boundary": "ontology_function_call",
            "semantic_operation_type": operation_type,
        },
    )
    return ExperienceSemanticOperationResolution(
        operation_key=operation_key,
        semantic_operation_type=operation_type,
        semantic_key=semantic_key,
        status="function_call_plan_ready",
        reason="experience_profile_title_function_call_plan_ready",
        function_call_plan=plan,
        receiver_object_id=receiver_object_id,
        metadata={
            "semantic_apply_boundary": "ontology_function_call",
            "function_ref": EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF,
        },
    )


def _title_argument(
    *,
    operation: Mapping[str, object],
) -> tuple[str | None, str | None]:
    operation_family = _text(operation.get("operation_family"))
    if operation_family == "delete":
        return None, None
    after_payload = operation.get("after_payload")
    if not isinstance(after_payload, Mapping):
        return "experience_profile_title_after_payload_missing", None
    title = after_payload.get("title")
    if not isinstance(title, str):
        return "experience_profile_title_value_invalid", None
    return None, title


def _operation_payload(
    operation: SemanticCapabilityTypedOperation | Mapping[str, object],
) -> Mapping[str, object]:
    if isinstance(operation, SemanticCapabilityTypedOperation):
        return operation.evidence_payload()
    return operation


def _object_id_map(values: Mapping[str, object] | None) -> dict[str, str]:
    if values is None:
        return {}
    return {
        str(key): value.strip()
        for key, value in values.items()
        if isinstance(value, str) and value.strip()
    }


def _baseline_receiver_object_id(
    *,
    identity: Mapping[str, object] | None,
) -> str | None:
    if identity is None:
        return None
    for field_name in (
        "semantic_apply_receiver_object_id",
        "receiver_object_id",
        "semantic_source_object_id",
        "object_id",
    ):
        value = _optional_text(identity.get(field_name))
        if value is not None:
            return value
    return None


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _optional_text(value: object) -> str | None:
    text = _text(value)
    return text or None


__all__ = [
    "EXPERIENCE_PROFILE_TITLE_UPDATE_BINDING_KEY",
    "EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION",
    "EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY",
    "EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION",
    "ExperienceSemanticOperationResolution",
    "resolve_experience_semantic_operation_function_call_plan_previews",
]

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from aware_identity_service_dto.actor.view import (
    ActorRoleEntryV1,
    ActorRolesViewStateV1,
)
from aware_identity_service_dto.role.assignment import RoleAssignmentBinding
from aware_identity_service_dto.role.assignment import RoleAssignmentResolveResult
from aware_service_runtime.api_ingress.view_fulfillment import (
    ServiceApiViewFulfillmentPlan,
)
from pydantic import BaseModel, ConfigDict, Field


class IdentityServiceViewFulfillmentEvidenceV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_kind: str = Field(default="identity_service")
    service_id: str | None = Field(default=None)
    api_view_id: str | None = Field(default=None)
    service_operation_config_api_view_id: str | None = Field(default=None)
    service_operation_config_id: str | None = Field(default=None)
    service_config_api_id: str | None = Field(default=None)
    service_contract_config_id: str | None = Field(default=None)
    service_contract_config_operation_grant_id: str | None = Field(default=None)
    actor_role_evidence: list[dict[str, Any]] = Field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ActorRolesV1ServiceProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    result: RoleAssignmentResolveResult | None = Field(default=None)
    actor_id: str | None = Field(default=None)
    actor_display_name: str | None = Field(default=None)
    error: str | None = Field(default=None)
    fulfillment: IdentityServiceViewFulfillmentEvidenceV1 = Field(
        default_factory=IdentityServiceViewFulfillmentEvidenceV1
    )
    provenance: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


def actor_roles_view_state_from_result(
    result: RoleAssignmentResolveResult | Mapping[str, Any] | None,
    *,
    actor_id: str | UUID | None = None,
    actor_display_name: str | None = None,
    fulfillment_plan: ServiceApiViewFulfillmentPlan | None = None,
    fulfillment: (
        IdentityServiceViewFulfillmentEvidenceV1 | Mapping[str, Any] | None
    ) = None,
    error: str | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> ActorRolesViewStateV1:
    if fulfillment_plan is not None and fulfillment is not None:
        raise ValueError("Pass either fulfillment_plan or fulfillment, not both.")
    return actor_roles_view_state_from_input(
        ActorRolesV1ServiceProviderInput(
            result=(
                RoleAssignmentResolveResult.model_validate(result)
                if result is not None
                else None
            ),
            actor_id=_optional_text(actor_id),
            actor_display_name=actor_display_name,
            error=error,
            fulfillment=(
                _fulfillment_evidence_from_plan(fulfillment_plan)
                if fulfillment_plan is not None
                else _fulfillment_evidence(fulfillment)
            ),
            provenance=dict(provenance or {}),
        )
    )


def actor_roles_view_state_from_input(
    provider_input: ActorRolesV1ServiceProviderInput | Mapping[str, Any],
) -> ActorRolesViewStateV1:
    typed_input = ActorRolesV1ServiceProviderInput.model_validate(provider_input)
    bindings = _role_bindings(typed_input)
    entries = [_actor_role_entry(binding) for binding in bindings]
    return ActorRolesViewStateV1(
        status=_provider_status(
            result=typed_input.result,
            entries=entries,
            error=typed_input.error,
        ),
        actor_id=typed_input.actor_id or _first_entry_actor_id(bindings),
        actor_display_name=typed_input.actor_display_name,
        entries=entries,
        summary=_count_summary(
            entries,
            singular="role assignment",
            plural="role assignments",
        ),
        error=typed_input.error,
        provenance=_actor_roles_provenance_payload(
            fulfillment=typed_input.fulfillment,
            provenance=typed_input.provenance,
            entry_count=len(entries),
        ),
    )


def actor_roles_view_state(
    *,
    provider_input: ActorRolesV1ServiceProviderInput | Mapping[str, Any],
) -> ActorRolesViewStateV1:
    return actor_roles_view_state_from_input(provider_input)


setattr(
    actor_roles_view_state,
    "provider_input_resolver",
    ActorRolesV1ServiceProviderInput.model_validate,
)


def _fulfillment_evidence(
    value: IdentityServiceViewFulfillmentEvidenceV1 | Mapping[str, Any] | None,
) -> IdentityServiceViewFulfillmentEvidenceV1:
    if isinstance(value, IdentityServiceViewFulfillmentEvidenceV1):
        return value
    return IdentityServiceViewFulfillmentEvidenceV1.model_validate(value or {})


def _fulfillment_evidence_from_plan(
    plan: ServiceApiViewFulfillmentPlan,
) -> IdentityServiceViewFulfillmentEvidenceV1:
    access_evidence = plan.preflight.access_evidence
    return IdentityServiceViewFulfillmentEvidenceV1(
        service_id=_uuid_text(plan.service_id),
        api_view_id=_uuid_text(plan.api_view_id),
        service_operation_config_api_view_id=_uuid_text(
            plan.service_operation_config_api_view_id
        ),
        service_operation_config_id=_uuid_text(plan.service_operation_config_id),
        service_config_api_id=_uuid_text(plan.service_config_api_id),
        service_contract_config_id=(
            _uuid_text(access_evidence.service_contract_config_id)
            if access_evidence is not None
            else None
        ),
        service_contract_config_operation_grant_id=(
            _uuid_text(access_evidence.service_contract_config_operation_grant_id)
            if access_evidence is not None
            else None
        ),
        actor_role_evidence=[
            {
                "actor_id": _uuid_text(evidence.actor_id),
                "role_config_id": _uuid_text(evidence.role_config_id),
                "access_scope": evidence.access_scope,
                "scope_kind": evidence.scope_kind,
                "scope_ref": evidence.scope_ref,
                "class_instance_identity_id": _uuid_text(
                    evidence.class_instance_identity_id
                ),
                "role_assignment_binding_id": _uuid_text(
                    evidence.role_assignment_binding_id
                ),
                "granted": evidence.granted,
            }
            for evidence in plan.preflight.actor_role_evidence
        ],
    )


def _actor_role_entry(binding: RoleAssignmentBinding) -> ActorRoleEntryV1:
    return ActorRoleEntryV1(
        role_assignment_id=_optional_text(binding.actor_role_id),
        role_config_id=_optional_text(binding.role_config_id),
        role_config_name=None,
        scope=binding.object_instance_graph_branch_key,
        status="active",
        metadata={
            "role_id": _optional_text(binding.role_id),
            "role_class_instance_id": _optional_text(binding.role_class_instance_id),
            "class_instance_identity_id": _optional_text(
                binding.class_instance_identity_id
            ),
            "role_config_class_config_id": _optional_text(
                binding.role_config_class_config_id
            ),
            "object_instance_graph_identity_id": _optional_text(
                binding.object_instance_graph_identity_id
            ),
            "object_instance_graph_branch_id": _optional_text(
                binding.object_instance_graph_branch_id
            ),
        },
    )


def _role_bindings(
    provider_input: ActorRolesV1ServiceProviderInput,
) -> list[RoleAssignmentBinding]:
    return list(
        provider_input.result.bindings if provider_input.result is not None else []
    )


def _provider_status(
    *,
    result: object | None,
    entries: Sequence[object],
    error: str | None,
) -> str:
    if error:
        return "error"
    if result is None:
        return "waiting"
    return "ready" if entries else "empty"


def _count_summary(entries: Sequence[object], *, singular: str, plural: str) -> str:
    count = len(entries)
    label = singular if count == 1 else plural
    return f"{count} {label}."


def _actor_roles_provenance_payload(
    *,
    fulfillment: IdentityServiceViewFulfillmentEvidenceV1,
    provenance: Mapping[str, Any],
    entry_count: int,
) -> dict[str, Any]:
    payload = {
        "source_kind": "identity_service",
        "state_provider_ref": "service:identity.actor.roles.v1",
        **fulfillment.to_json(),
        **dict(provenance),
    }
    payload["api_view_ref"] = ACTOR_ROLES_API_VIEW_REF
    payload["view_ref"] = ACTOR_ROLES_API_VIEW_REF
    payload["projection_view_key"] = ACTOR_ROLES_PROJECTION_VIEW_KEY
    payload["state_model_ref"] = ACTOR_ROLES_STATE_MODEL_REF
    payload["entry_count"] = entry_count
    return payload


ACTOR_ROLES_API_VIEW_REF = "identity.actor_roles"
ACTOR_ROLES_API_VIEW_KEY = "actor_roles"
ACTOR_ROLES_PROJECTION_VIEW_KEY = "actor.roles.v1"
ACTOR_ROLES_STATE_MODEL_REF = "aware_identity_service_dto.actor.ActorRolesViewStateV1"


def _first_entry_actor_id(entries: Sequence[object]) -> str | None:
    if not entries:
        return None
    return _optional_text(getattr(entries[0], "actor_id", None))


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "ActorRolesV1ServiceProviderInput",
    "IdentityServiceViewFulfillmentEvidenceV1",
    "actor_roles_view_state",
    "actor_roles_view_state_from_input",
    "actor_roles_view_state_from_result",
]

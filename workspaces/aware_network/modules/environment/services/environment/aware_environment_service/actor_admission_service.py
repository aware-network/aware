from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from typing import Any, Protocol, cast
from uuid import UUID

from pydantic import BaseModel, Field

from aware_code.types import JsonObject
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)

_IDENTITY_SERVICE_API_PACKAGE_NAME = "identity-service-api"


class EnvironmentActorAdmissionRoleEligibilitySpec(BaseModel):
    environment_profile_actor_config_id: UUID
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = None


class AdmitEnvironmentActorRequestSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    environment_profile_id: UUID
    actor_config_id: UUID
    class_instance_identity_id: UUID
    object_instance_graph_branch_key: str = "all"
    object_instance_graph_branch_id: UUID | None = None
    requested_role_config_ids: list[UUID] = Field(default_factory=list)
    requested_role_config_names: list[str] = Field(default_factory=list)
    reason: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class EnvironmentActorAdmissionRoleBindingSpec(BaseModel):
    environment_profile_actor_config_id: UUID
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = None
    actor_id: UUID
    role_id: UUID
    actor_role_id: UUID
    role_class_instance_id: UUID
    class_instance_identity_id: UUID
    role_config_class_config_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_key: str = "all"
    object_instance_graph_branch_id: UUID | None = None


class EnvironmentActorAdmissionReceiptSpec(BaseModel):
    accepted: bool = False
    status: str
    error: str | None = None
    reason: str | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    environment_profile_id: UUID
    environment_profile_actor_config_id: UUID | None = None
    actor_config_id: UUID | None = None
    class_instance_identity_id: UUID | None = None
    object_instance_graph_branch_key: str = "all"
    object_instance_graph_branch_id: UUID | None = None
    requested_role_config_ids: list[UUID] = Field(default_factory=list)
    requested_role_config_names: list[str] = Field(default_factory=list)
    eligible_roles: list[EnvironmentActorAdmissionRoleEligibilitySpec] = Field(
        default_factory=list
    )
    bindings: list[EnvironmentActorAdmissionRoleBindingSpec] = Field(
        default_factory=list
    )
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class AdmitEnvironmentActorResponseSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    accepted: bool = False
    status: str
    error: str | None = None
    receipt: EnvironmentActorAdmissionReceiptSpec
    evidence: dict[str, Any] = Field(default_factory=dict)


class EnvironmentActorAdmissionBackend(Protocol):
    async def resolve_environment_actor_config_role_eligibility(
        self,
        *,
        environment_id: UUID,
        environment_profile_id: UUID,
        actor_config_id: UUID,
    ) -> Sequence[EnvironmentActorAdmissionRoleEligibilitySpec]: ...


class _IdentityAssignRoleCapability(Protocol):
    async def assign_role(self, request: object) -> object: ...


class _IdentityAssignRoleApi(Protocol):
    @property
    def assign_role(self) -> _IdentityAssignRoleCapability: ...


class IdentityRoleAssignmentApiClient(Protocol):
    @property
    def identity(self) -> _IdentityAssignRoleApi: ...


async def admit_environment_actor(
    *,
    request: AdmitEnvironmentActorRequestSpec,
    host_context: ServiceApiHostContext,
    admission_backend: EnvironmentActorAdmissionBackend | None = None,
    identity_api_client: IdentityRoleAssignmentApiClient | None = None,
) -> AdmitEnvironmentActorResponseSpec:
    actor_id = request.actor_id or host_context.operation_context.actor_id
    base_evidence: dict[str, Any] = {
        "source": "aware_environment_service.actor_admission",
        **dict(request.evidence),
    }
    blocker = _basic_request_blocker(request=request, actor_id=actor_id)
    if blocker is not None:
        return _blocked_response(
            request=request,
            actor_id=actor_id,
            status="blocked",
            reason=blocker,
            blockers=[blocker],
            evidence=base_evidence,
        )

    if admission_backend is None:
        return _blocked_response(
            request=request,
            actor_id=actor_id,
            status="blocked",
            reason="environment_actor_admission_backend_unavailable",
            blockers=["environment_actor_admission_backend_unavailable"],
            evidence=base_evidence,
        )

    identity_client = identity_api_client or _build_identity_service_api_client(
        host_context=host_context,
    )
    if identity_client is None:
        return _blocked_response(
            request=request,
            actor_id=actor_id,
            status="blocked",
            reason="identity_service_api_route_unavailable",
            blockers=["identity_service_api_route_unavailable"],
            evidence=base_evidence,
        )

    assert actor_id is not None
    eligible_roles = tuple(
        await admission_backend.resolve_environment_actor_config_role_eligibility(
            environment_id=request.environment_id,
            environment_profile_id=request.environment_profile_id,
            actor_config_id=request.actor_config_id,
        )
    )
    selected_roles = _select_requested_roles(
        eligible_roles=eligible_roles,
        requested_role_config_ids=request.requested_role_config_ids,
        requested_role_config_names=request.requested_role_config_names,
    )
    if not selected_roles:
        return _blocked_response(
            request=request,
            actor_id=actor_id,
            status="blocked",
            reason="environment_actor_config_role_eligibility_not_found",
            blockers=["environment_actor_config_role_eligibility_not_found"],
            evidence={
                **base_evidence,
                "eligible_role_count": len(eligible_roles),
            },
            eligible_roles=list(eligible_roles),
        )

    bindings: list[EnvironmentActorAdmissionRoleBindingSpec] = []
    try:
        for role in selected_roles:
            assignment = await identity_client.identity.assign_role.assign_role(
                _role_assignment_request_model()(
                    actor_id=actor_id,
                    role_config_id=role.role_config_id,
                    role_config_name=role.role_config_name,
                    class_instance_identity_id=request.class_instance_identity_id,
                    object_instance_graph_branch_key=(
                        request.object_instance_graph_branch_key or "all"
                    ),
                    object_instance_graph_branch_id=(
                        request.object_instance_graph_branch_id
                    ),
                    request_id=request.request_id,
                    reason=request.reason,
                    source_service="aware_environment_service.actor_admission",
                    grant_authority_kind="environment_profile_actor_config",
                    grant_authority_id=role.environment_profile_actor_config_id,
                    grant_context_kind="environment_profile_admission",
                    grant_context_id=request.environment_profile_id,
                    grant_context_ref=(
                        f"environment:{request.environment_id}:"
                        f"profile:{request.environment_profile_id}"
                    ),
                    grant_evidence={
                        "environment_id": str(request.environment_id),
                        "environment_profile_id": str(request.environment_profile_id),
                        "environment_profile_actor_config_id": str(
                            role.environment_profile_actor_config_id
                        ),
                        "actor_config_id": str(request.actor_config_id),
                        "actor_config_role_config_id": str(
                            role.actor_config_role_config_id
                        ),
                    },
                )
            )
            bindings.append(
                _admission_binding_from_identity(role=role, binding=assignment.binding)
            )
    except Exception as exc:
        return _blocked_response(
            request=request,
            actor_id=actor_id,
            status="blocked",
            reason="identity_role_assignment_failed",
            blockers=["identity_role_assignment_failed"],
            evidence={
                **base_evidence,
                "error": str(exc),
            },
            eligible_roles=list(eligible_roles),
            bindings=bindings,
        )

    receipt = EnvironmentActorAdmissionReceiptSpec(
        accepted=True,
        status="admitted",
        error=None,
        reason=request.reason,
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        environment_profile_actor_config_id=(
            selected_roles[0].environment_profile_actor_config_id
        ),
        actor_config_id=request.actor_config_id,
        class_instance_identity_id=request.class_instance_identity_id,
        object_instance_graph_branch_key=(
            request.object_instance_graph_branch_key or "all"
        ),
        object_instance_graph_branch_id=request.object_instance_graph_branch_id,
        requested_role_config_ids=list(request.requested_role_config_ids),
        requested_role_config_names=list(request.requested_role_config_names),
        eligible_roles=list(eligible_roles),
        bindings=bindings,
        evidence={
            **base_evidence,
            "selected_role_count": len(selected_roles),
            "binding_count": len(bindings),
        },
    )
    return AdmitEnvironmentActorResponseSpec(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        accepted=True,
        status="admitted",
        receipt=receipt,
        evidence=dict(receipt.evidence),
    )


def _build_identity_service_api_client(
    *,
    host_context: ServiceApiHostContext,
) -> IdentityRoleAssignmentApiClient | None:
    invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_IDENTITY_SERVICE_API_PACKAGE_NAME,
        actor_id=host_context.operation_context.actor_id,
        invocation_context=_host_invocation_context_payload(host_context),
    )
    if invoker is None:
        return None
    return cast(IdentityRoleAssignmentApiClient, _identity_api_client_model()(invoker))


def _identity_api_client_model() -> type[Any]:
    module = import_module("aware_" + "identity" + "_service_api")
    return cast(type[Any], getattr(module, "AwareIdentityServiceApiClient"))


def _role_assignment_request_model() -> type[Any]:
    module = import_module("aware_" + "identity" + "_service_dto.role.assignment")
    return cast(type[Any], getattr(module, "RoleAssignmentRequest"))


def _host_invocation_context_payload(
    host_context: ServiceApiHostContext,
) -> JsonObject | None:
    if host_context.invocation_context is None:
        return None
    return cast(JsonObject, dict(host_context.invocation_context))


def _basic_request_blocker(
    *,
    request: AdmitEnvironmentActorRequestSpec,
    actor_id: UUID | None,
) -> str | None:
    if actor_id is None:
        return "actor_id_missing"
    if request.environment_id is None:
        return "environment_id_missing"
    if request.environment_profile_id is None:
        return "environment_profile_id_missing"
    if request.actor_config_id is None:
        return "actor_config_id_missing"
    if request.class_instance_identity_id is None:
        return "class_instance_identity_id_missing"
    return None


def _select_requested_roles(
    *,
    eligible_roles: Sequence[EnvironmentActorAdmissionRoleEligibilitySpec],
    requested_role_config_ids: Sequence[UUID],
    requested_role_config_names: Sequence[str],
) -> tuple[EnvironmentActorAdmissionRoleEligibilitySpec, ...]:
    requested_ids = set(requested_role_config_ids)
    requested_names = {
        item.strip().casefold() for item in requested_role_config_names if item.strip()
    }
    if not requested_ids and not requested_names:
        return tuple(eligible_roles)
    selected = []
    for role in eligible_roles:
        if role.role_config_id in requested_ids:
            selected.append(role)
            continue
        if (
            role.role_config_name is not None
            and role.role_config_name.strip().casefold() in requested_names
        ):
            selected.append(role)
    return tuple(selected)


def _admission_binding_from_identity(
    *,
    role: EnvironmentActorAdmissionRoleEligibilitySpec,
    binding: object,
) -> EnvironmentActorAdmissionRoleBindingSpec:
    return EnvironmentActorAdmissionRoleBindingSpec(
        environment_profile_actor_config_id=role.environment_profile_actor_config_id,
        actor_config_role_config_id=role.actor_config_role_config_id,
        role_config_id=getattr(binding, "role_config_id"),
        role_config_name=role.role_config_name,
        actor_id=getattr(binding, "actor_id"),
        role_id=getattr(binding, "role_id"),
        actor_role_id=getattr(binding, "actor_role_id"),
        role_class_instance_id=getattr(binding, "role_class_instance_id"),
        class_instance_identity_id=getattr(binding, "class_instance_identity_id"),
        role_config_class_config_id=getattr(
            binding,
            "role_config_class_config_id",
        ),
        object_instance_graph_identity_id=getattr(
            binding,
            "object_instance_graph_identity_id",
        ),
        object_instance_graph_branch_key=getattr(
            binding,
            "object_instance_graph_branch_key",
        ),
        object_instance_graph_branch_id=getattr(
            binding,
            "object_instance_graph_branch_id",
        ),
    )


def _blocked_response(
    *,
    request: AdmitEnvironmentActorRequestSpec,
    actor_id: UUID | None,
    status: str,
    reason: str,
    blockers: list[str],
    evidence: dict[str, Any],
    eligible_roles: list[EnvironmentActorAdmissionRoleEligibilitySpec] | None = None,
    bindings: list[EnvironmentActorAdmissionRoleBindingSpec] | None = None,
) -> AdmitEnvironmentActorResponseSpec:
    receipt = EnvironmentActorAdmissionReceiptSpec(
        accepted=False,
        status=status,
        error=reason,
        reason=reason,
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        actor_config_id=request.actor_config_id,
        class_instance_identity_id=request.class_instance_identity_id,
        object_instance_graph_branch_key=(
            request.object_instance_graph_branch_key or "all"
        ),
        object_instance_graph_branch_id=request.object_instance_graph_branch_id,
        requested_role_config_ids=list(request.requested_role_config_ids),
        requested_role_config_names=list(request.requested_role_config_names),
        eligible_roles=eligible_roles or [],
        bindings=bindings or [],
        blockers=blockers,
        evidence=evidence,
    )
    return AdmitEnvironmentActorResponseSpec(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        accepted=False,
        status=status,
        error=reason,
        receipt=receipt,
        evidence=dict(receipt.evidence),
    )


__all__ = [
    "AdmitEnvironmentActorRequestSpec",
    "AdmitEnvironmentActorResponseSpec",
    "EnvironmentActorAdmissionBackend",
    "EnvironmentActorAdmissionReceiptSpec",
    "EnvironmentActorAdmissionRoleBindingSpec",
    "EnvironmentActorAdmissionRoleEligibilitySpec",
    "IdentityRoleAssignmentApiClient",
    "admit_environment_actor",
]

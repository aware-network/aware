from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, cast
from uuid import UUID

from aware_types import JsonObject
from aware_environment_service_dto.environment.environment import (
    AdmitEnvironmentActorRequest,
    AdmitEnvironmentActorResponse,
    EnvironmentActorAdmissionReceipt as DtoEnvironmentActorAdmissionReceipt,
    EnvironmentActorAdmissionRoleBinding as DtoEnvironmentActorAdmissionRoleBinding,
    EnvironmentActorAdmissionRoleEligibility as DtoEnvironmentActorAdmissionRoleEligibility,
)


class EnvironmentActorAdmissionError(RuntimeError):
    """Raised when Environment actor admission is rejected or fails closed."""

    def __init__(
        self,
        message: str,
        *,
        receipt: "EnvironmentActorAdmissionReceipt",
    ) -> None:
        super().__init__(message)
        self.receipt = receipt


class _EnvironmentActorAdmissionCapabilityClient(Protocol):
    async def admit_actor(
        self,
        request: AdmitEnvironmentActorRequest,
    ) -> AdmitEnvironmentActorResponse: ...


class _EnvironmentApiClient(Protocol):
    @property
    def actor_admission(self) -> _EnvironmentActorAdmissionCapabilityClient: ...


class EnvironmentActorAdmissionGeneratedApiClient(Protocol):
    @property
    def environment(self) -> _EnvironmentApiClient: ...


@dataclass(frozen=True, slots=True)
class EnvironmentActorAdmissionContext:
    actor_id: UUID
    environment_id: UUID

    @classmethod
    def from_object(cls, context: object) -> "EnvironmentActorAdmissionContext":
        return cls(
            actor_id=_required_uuid(
                getattr(context, "actor_id", None),
                field_name="actor_id",
            ),
            environment_id=_required_uuid(
                getattr(context, "environment_id", None),
                field_name="environment_id",
            ),
        )


@dataclass(frozen=True, slots=True)
class EnvironmentActorAdmissionRoleEligibility:
    environment_profile_actor_config_id: UUID
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentActorAdmissionRoleBinding:
    environment_profile_actor_config_id: UUID
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None
    actor_id: UUID
    role_id: UUID
    actor_role_id: UUID
    role_class_instance_id: UUID
    class_instance_identity_id: UUID
    role_config_class_config_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_key: str
    object_instance_graph_branch_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentActorAdmissionReceipt:
    accepted: bool
    status: str
    error: str | None
    reason: str | None
    actor_id: UUID | None
    environment_id: UUID
    environment_profile_id: UUID
    environment_profile_actor_config_id: UUID | None
    actor_config_id: UUID | None
    class_instance_identity_id: UUID | None
    object_instance_graph_branch_key: str
    object_instance_graph_branch_id: UUID | None
    requested_role_config_ids: tuple[UUID, ...]
    requested_role_config_names: tuple[str, ...]
    eligible_roles: tuple[EnvironmentActorAdmissionRoleEligibility, ...]
    bindings: tuple[EnvironmentActorAdmissionRoleBinding, ...]
    blockers: tuple[str, ...]
    eligible_role_count: int
    binding_count: int
    evidence: Mapping[str, object] = field(default_factory=dict)
    dto_receipt: DtoEnvironmentActorAdmissionReceipt | None = None
    raw_response: AdmitEnvironmentActorResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentActorAdmissionClient:
    api_client: EnvironmentActorAdmissionGeneratedApiClient
    context: EnvironmentActorAdmissionContext

    async def admit_actor(
        self,
        *,
        environment_profile_id: UUID | str,
        actor_config_id: UUID | str,
        class_instance_identity_id: UUID | str,
        request_id: UUID | str | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | str | None = None,
        requested_role_config_ids: Sequence[UUID | str] = (),
        requested_role_config_names: Sequence[str] = (),
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> EnvironmentActorAdmissionReceipt:
        response = await self.api_client.environment.actor_admission.admit_actor(
            AdmitEnvironmentActorRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                request_id=_optional_uuid(request_id),
                environment_profile_id=_required_uuid(
                    environment_profile_id,
                    field_name="environment_profile_id",
                ),
                actor_config_id=_required_uuid(
                    actor_config_id,
                    field_name="actor_config_id",
                ),
                class_instance_identity_id=_required_uuid(
                    class_instance_identity_id,
                    field_name="class_instance_identity_id",
                ),
                object_instance_graph_branch_key=(
                    object_instance_graph_branch_key or "all"
                ),
                object_instance_graph_branch_id=_optional_uuid(
                    object_instance_graph_branch_id
                ),
                requested_role_config_ids=[
                    _required_uuid(value, field_name="requested_role_config_id")
                    for value in requested_role_config_ids
                ],
                requested_role_config_names=[
                    str(value).strip()
                    for value in requested_role_config_names
                    if str(value).strip()
                ],
                reason=reason,
                evidence=cast(JsonObject, dict(evidence or {})),
            )
        )
        receipt = _receipt_from_response(response)
        if not receipt.accepted:
            raise EnvironmentActorAdmissionError(
                "Environment actor admission failed: "
                f"{receipt.error or receipt.status}",
                receipt=receipt,
            )
        return receipt


def _receipt_from_response(
    response: AdmitEnvironmentActorResponse,
) -> EnvironmentActorAdmissionReceipt:
    dto_receipt = response.receipt
    eligible_roles = tuple(
        _role_eligibility_from_dto(role) for role in dto_receipt.eligible_roles
    )
    bindings = tuple(
        _role_binding_from_dto(binding) for binding in dto_receipt.bindings
    )
    return EnvironmentActorAdmissionReceipt(
        accepted=response.accepted and dto_receipt.accepted,
        status=response.status or dto_receipt.status,
        error=response.error,
        reason=dto_receipt.reason,
        actor_id=dto_receipt.actor_id,
        environment_id=dto_receipt.environment_id,
        environment_profile_id=dto_receipt.environment_profile_id,
        environment_profile_actor_config_id=(
            dto_receipt.environment_profile_actor_config_id
        ),
        actor_config_id=dto_receipt.actor_config_id,
        class_instance_identity_id=dto_receipt.class_instance_identity_id,
        object_instance_graph_branch_key=(dto_receipt.object_instance_graph_branch_key),
        object_instance_graph_branch_id=(dto_receipt.object_instance_graph_branch_id),
        requested_role_config_ids=tuple(dto_receipt.requested_role_config_ids),
        requested_role_config_names=tuple(dto_receipt.requested_role_config_names),
        eligible_roles=eligible_roles,
        bindings=bindings,
        blockers=tuple(dto_receipt.blockers),
        eligible_role_count=len(eligible_roles),
        binding_count=len(bindings),
        evidence=dict(response.evidence) or dict(dto_receipt.evidence),
        dto_receipt=dto_receipt,
        raw_response=response,
    )


def _role_eligibility_from_dto(
    role: DtoEnvironmentActorAdmissionRoleEligibility,
) -> EnvironmentActorAdmissionRoleEligibility:
    return EnvironmentActorAdmissionRoleEligibility(
        environment_profile_actor_config_id=(role.environment_profile_actor_config_id),
        actor_config_role_config_id=role.actor_config_role_config_id,
        role_config_id=role.role_config_id,
        role_config_name=role.role_config_name,
    )


def _role_binding_from_dto(
    binding: DtoEnvironmentActorAdmissionRoleBinding,
) -> EnvironmentActorAdmissionRoleBinding:
    return EnvironmentActorAdmissionRoleBinding(
        environment_profile_actor_config_id=(
            binding.environment_profile_actor_config_id
        ),
        actor_config_role_config_id=binding.actor_config_role_config_id,
        role_config_id=binding.role_config_id,
        role_config_name=binding.role_config_name,
        actor_id=binding.actor_id,
        role_id=binding.role_id,
        actor_role_id=binding.actor_role_id,
        role_class_instance_id=binding.role_class_instance_id,
        class_instance_identity_id=binding.class_instance_identity_id,
        role_config_class_config_id=binding.role_config_class_config_id,
        object_instance_graph_identity_id=(binding.object_instance_graph_identity_id),
        object_instance_graph_branch_key=(binding.object_instance_graph_branch_key),
        object_instance_graph_branch_id=(binding.object_instance_graph_branch_id),
    )


def _required_uuid(value: object, *, field_name: str) -> UUID:
    resolved = _optional_uuid(value)
    if resolved is None:
        raise ValueError(f"{field_name} is required.")
    return resolved


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    text = str(value).strip()
    return UUID(text) if text else None


__all__ = [
    "EnvironmentActorAdmissionClient",
    "EnvironmentActorAdmissionContext",
    "EnvironmentActorAdmissionError",
    "EnvironmentActorAdmissionGeneratedApiClient",
    "EnvironmentActorAdmissionReceipt",
    "EnvironmentActorAdmissionRoleBinding",
    "EnvironmentActorAdmissionRoleEligibility",
]

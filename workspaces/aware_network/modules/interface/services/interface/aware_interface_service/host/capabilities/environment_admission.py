from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from aware_environment_service_api import AwareEnvironmentServiceApiClient
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt as DtoEnvironmentActorAdmissionReceipt,
)
from aware_environment_sdk import (
    EnvironmentActorAdmissionClient,
    EnvironmentActorAdmissionContext,
    EnvironmentActorAdmissionError,
    EnvironmentActorAdmissionReceipt,
)
from aware_interface_sdk.transport import InterfaceTransportSession

from aware_interface_service.models import (
    InterfaceExperienceSessionActorContext,
    InterfaceEnvironmentAdmissionRoleBindingState,
    InterfaceEnvironmentAdmissionRoleEligibilityState,
    InterfaceEnvironmentAdmissionState,
)


@dataclass(frozen=True, slots=True)
class ServiceApiInterfaceEnvironmentAdmissionResult:
    admission_state: InterfaceEnvironmentAdmissionState
    environment_admission_receipt: DtoEnvironmentActorAdmissionReceipt | None = None


@dataclass(frozen=True, slots=True)
class ServiceApiInterfaceEnvironmentAdmissionPort:
    transport_session: InterfaceTransportSession | None
    context_environment_id: UUID | None = None
    actor_context: InterfaceExperienceSessionActorContext | None = None

    async def admit_actor(
        self,
        *,
        environment_profile_id: UUID,
        actor_config_id: UUID,
        class_instance_identity_id: UUID,
        environment_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: Sequence[UUID] = (),
        requested_role_config_names: Sequence[str] = (),
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> ServiceApiInterfaceEnvironmentAdmissionResult:
        actor_id = _resolved_actor_id(
            transport_session=self.transport_session,
            actor_context=self.actor_context,
        )
        resolved_environment_id = environment_id or self.context_environment_id
        if self.transport_session is None:
            return ServiceApiInterfaceEnvironmentAdmissionResult(
                admission_state=_blocked_state(
                    blocker="interface_transport_unbound",
                    environment_id=resolved_environment_id,
                    environment_profile_id=environment_profile_id,
                    actor_config_id=actor_config_id,
                    class_instance_identity_id=class_instance_identity_id,
                    evidence=evidence,
                )
            )
        if actor_id is None:
            return ServiceApiInterfaceEnvironmentAdmissionResult(
                admission_state=_blocked_state(
                    blocker="interface_actor_unbound",
                    environment_id=resolved_environment_id,
                    environment_profile_id=environment_profile_id,
                    actor_config_id=actor_config_id,
                    class_instance_identity_id=class_instance_identity_id,
                    evidence=evidence,
                )
            )
        if resolved_environment_id is None:
            return ServiceApiInterfaceEnvironmentAdmissionResult(
                admission_state=_blocked_state(
                    blocker="interface_environment_unbound",
                    actor_id=actor_id,
                    environment_profile_id=environment_profile_id,
                    actor_config_id=actor_config_id,
                    class_instance_identity_id=class_instance_identity_id,
                    evidence=evidence,
                )
            )

        client = EnvironmentActorAdmissionClient(
            api_client=AwareEnvironmentServiceApiClient(self.transport_session.client),
            context=EnvironmentActorAdmissionContext(
                actor_id=actor_id,
                environment_id=resolved_environment_id,
            ),
        )
        try:
            receipt = await client.admit_actor(
                environment_profile_id=environment_profile_id,
                actor_config_id=actor_config_id,
                class_instance_identity_id=class_instance_identity_id,
                object_instance_graph_branch_key=object_instance_graph_branch_key,
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                requested_role_config_ids=requested_role_config_ids,
                requested_role_config_names=requested_role_config_names,
                reason=reason,
                evidence=_merged_evidence(evidence),
            )
            return ServiceApiInterfaceEnvironmentAdmissionResult(
                admission_state=_state_from_receipt(receipt, status="admitted"),
                environment_admission_receipt=receipt.dto_receipt,
            )
        except EnvironmentActorAdmissionError as exc:
            return ServiceApiInterfaceEnvironmentAdmissionResult(
                admission_state=_state_from_receipt(
                    exc.receipt,
                    status="blocked",
                    error=str(exc),
                ),
                environment_admission_receipt=exc.receipt.dto_receipt,
            )
        except Exception as exc:
            return ServiceApiInterfaceEnvironmentAdmissionResult(
                admission_state=_blocked_state(
                    blocker="environment_actor_admission_exception",
                    actor_id=actor_id,
                    environment_id=resolved_environment_id,
                    environment_profile_id=environment_profile_id,
                    actor_config_id=actor_config_id,
                    class_instance_identity_id=class_instance_identity_id,
                    error=str(exc),
                    evidence=evidence,
                    status="error",
                )
            )


def _resolved_actor_id(
    transport_session: InterfaceTransportSession | None,
    actor_context: InterfaceExperienceSessionActorContext | None,
) -> UUID | None:
    if actor_context is not None:
        return actor_context.actor_id
    binding = getattr(transport_session, "binding", None)
    value = getattr(binding, "actor_id", None)
    return value if isinstance(value, UUID) else None


def _state_from_receipt(
    receipt: EnvironmentActorAdmissionReceipt,
    *,
    status: str,
    error: str | None = None,
) -> InterfaceEnvironmentAdmissionState:
    return InterfaceEnvironmentAdmissionState(
        status=status if receipt.accepted else "blocked",
        accepted=receipt.accepted,
        actor_id=receipt.actor_id,
        environment_id=receipt.environment_id,
        environment_profile_id=receipt.environment_profile_id,
        environment_profile_actor_config_id=(
            receipt.environment_profile_actor_config_id
        ),
        actor_config_id=receipt.actor_config_id,
        class_instance_identity_id=receipt.class_instance_identity_id,
        object_instance_graph_branch_key=receipt.object_instance_graph_branch_key,
        object_instance_graph_branch_id=receipt.object_instance_graph_branch_id,
        requested_role_config_ids=tuple(receipt.requested_role_config_ids),
        requested_role_config_names=tuple(receipt.requested_role_config_names),
        eligible_role_count=receipt.eligible_role_count,
        binding_count=receipt.binding_count,
        eligible_roles=tuple(
            InterfaceEnvironmentAdmissionRoleEligibilityState(
                environment_profile_actor_config_id=(
                    role.environment_profile_actor_config_id
                ),
                actor_config_role_config_id=role.actor_config_role_config_id,
                role_config_id=role.role_config_id,
                role_config_name=role.role_config_name,
            )
            for role in receipt.eligible_roles
        ),
        bindings=tuple(
            InterfaceEnvironmentAdmissionRoleBindingState(
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
                object_instance_graph_identity_id=(
                    binding.object_instance_graph_identity_id
                ),
                object_instance_graph_branch_key=(
                    binding.object_instance_graph_branch_key
                ),
                object_instance_graph_branch_id=(
                    binding.object_instance_graph_branch_id
                ),
            )
            for binding in receipt.bindings
        ),
        blockers=tuple(receipt.blockers),
        error=error or receipt.error,
        reason=receipt.reason,
        updated_at=_utc_now_isoformat(),
        evidence=dict(receipt.evidence),
    )


def state_from_receipt(
    receipt: EnvironmentActorAdmissionReceipt,
    *,
    status: str,
    error: str | None = None,
) -> InterfaceEnvironmentAdmissionState:
    return _state_from_receipt(receipt, status=status, error=error)


def _blocked_state(
    *,
    blocker: str,
    actor_id: UUID | None = None,
    environment_id: UUID | None = None,
    environment_profile_id: UUID | None = None,
    actor_config_id: UUID | None = None,
    class_instance_identity_id: UUID | None = None,
    error: str | None = None,
    evidence: Mapping[str, object] | None = None,
    status: str = "blocked",
) -> InterfaceEnvironmentAdmissionState:
    return InterfaceEnvironmentAdmissionState(
        status=status,
        accepted=False,
        actor_id=actor_id,
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        actor_config_id=actor_config_id,
        class_instance_identity_id=class_instance_identity_id,
        blockers=(blocker,),
        error=error,
        updated_at=_utc_now_isoformat(),
        evidence=_merged_evidence(evidence),
    )


def _merged_evidence(evidence: Mapping[str, object] | None) -> dict[str, object]:
    merged = dict(evidence or {})
    merged.setdefault("source", "aware_interface_service.environment_admission")
    merged.setdefault("rail", "interface_environment_actor_admission")
    return merged


def _utc_now_isoformat() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = [
    "ServiceApiInterfaceEnvironmentAdmissionPort",
    "ServiceApiInterfaceEnvironmentAdmissionResult",
    "state_from_receipt",
]

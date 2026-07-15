from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from aware_environment_service_api import AwareEnvironmentServiceApiClient
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentNavigationCommitReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
    EnvironmentSessionView,
)
from aware_environment_sdk import (
    EnvironmentSessionClient,
    EnvironmentSessionContext,
    EnvironmentSessionError,
)
from aware_interface_sdk.transport import InterfaceTransportSession

from aware_interface_service.host.capabilities.experience_lens import (
    environment_navigation_state_from_context,
    environment_session_state_from_join_receipt,
)
from aware_interface_service.models import (
    InterfaceExperienceSessionActorContext,
    InterfaceEnvironmentAdmissionRoleBindingState,
    InterfaceEnvironmentAdmissionRoleEligibilityState,
    InterfaceEnvironmentAdmissionState,
    InterfaceEnvironmentEntryResult,
    InterfaceEnvironmentNavigationState,
    InterfaceEnvironmentSessionState,
    InterfaceHostServiceState,
)
import aware_interface_service.host.capabilities.environment_admission as environment_admission_capability_mod


@dataclass(frozen=True, slots=True)
class ServiceApiInterfaceEnvironmentEntry:
    environment_admission_state: InterfaceEnvironmentAdmissionState | None
    environment_session_state: InterfaceEnvironmentSessionState | None
    environment_navigation_state: InterfaceEnvironmentNavigationState | None
    environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None
    environment_session: EnvironmentSessionView | None = None
    environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = None
    environment_navigation_context: EnvironmentNavigationContextView | None = None
    default_navigation_receipt: EnvironmentNavigationCommitReceipt | None = None


@dataclass(frozen=True, slots=True)
class ServiceApiInterfaceEnvironmentEntryPort:
    transport_session: InterfaceTransportSession | None
    context_environment_id: UUID | None = None
    actor_context: InterfaceExperienceSessionActorContext | None = None

    async def enter_environment(
        self,
        *,
        environment_id: UUID | None = None,
        environment_profile_id: UUID | None = None,
        actor_config_id: UUID | None = None,
        class_instance_identity_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: Sequence[UUID] = (),
        requested_role_config_names: Sequence[str] = (),
        environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None,
        environment_session_id: UUID | None = None,
        environment_session_config_id: UUID | None = None,
        session_key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        source_kind: str | None = None,
        source_ref: str | None = None,
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> ServiceApiInterfaceEnvironmentEntry:
        updated_at = _utc_now_isoformat()
        actor_id = _resolved_actor_id(
            transport_session=self.transport_session,
            actor_context=self.actor_context,
        )
        resolved_admission_receipt = environment_admission_receipt
        resolved_environment_id = _resolve_environment_id(
            admission=resolved_admission_receipt,
            environment_id=environment_id,
            fallback=self.context_environment_id,
        )
        resolved_profile_id = _resolve_environment_profile_id(
            admission=resolved_admission_receipt,
            fallback=environment_profile_id,
        )
        admission_state = (
            _admission_state_from_receipt(
                resolved_admission_receipt,
                updated_at=updated_at,
            )
            if resolved_admission_receipt is not None
            else None
        )

        if resolved_admission_receipt is None:
            admission_blocker = _admission_input_blocker(
                environment_profile_id=environment_profile_id,
                actor_config_id=actor_config_id,
                class_instance_identity_id=class_instance_identity_id,
            )
            if admission_blocker is not None:
                return _blocked_entry(
                    blocker=admission_blocker,
                    actor_id=actor_id,
                    environment_id=resolved_environment_id,
                    environment_profile_id=resolved_profile_id,
                    updated_at=updated_at,
                    evidence=evidence,
                )
            admission_port = environment_admission_capability_mod.ServiceApiInterfaceEnvironmentAdmissionPort(
                transport_session=self.transport_session,
                context_environment_id=resolved_environment_id,
                actor_context=self.actor_context,
            )
            admission_result = await admission_port.admit_actor(
                environment_id=resolved_environment_id,
                environment_profile_id=environment_profile_id,
                actor_config_id=actor_config_id,
                class_instance_identity_id=class_instance_identity_id,
                object_instance_graph_branch_key=object_instance_graph_branch_key,
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                requested_role_config_ids=requested_role_config_ids,
                requested_role_config_names=requested_role_config_names,
                reason=reason,
                evidence={
                    "source": "interface_enter_environment.admission",
                    **_jsonish_mapping(evidence or {}),
                },
            )
            admission_state = admission_result.admission_state
            resolved_admission_receipt = admission_result.environment_admission_receipt
            resolved_environment_id = _resolve_environment_id(
                admission=resolved_admission_receipt,
                environment_id=environment_id,
                fallback=resolved_environment_id,
            )
            resolved_profile_id = _resolve_environment_profile_id(
                admission=resolved_admission_receipt,
                fallback=environment_profile_id,
            )

        if admission_state is not None and not admission_state.accepted:
            return ServiceApiInterfaceEnvironmentEntry(
                environment_admission_state=admission_state,
                environment_session_state=_blocked_session_state(
                    blocker="environment_admission_blocked",
                    actor_id=actor_id,
                    environment_id=resolved_environment_id,
                    environment_profile_id=resolved_profile_id,
                    environment_session_id=environment_session_id,
                    updated_at=updated_at,
                    evidence=evidence,
                ),
                environment_navigation_state=None,
                environment_admission_receipt=resolved_admission_receipt,
            )

        target_blocker = _session_target_blocker(
            environment_session_id=environment_session_id,
            environment_session_config_id=environment_session_config_id,
            session_key=session_key,
        )
        if target_blocker is not None:
            return ServiceApiInterfaceEnvironmentEntry(
                environment_admission_state=admission_state,
                environment_session_state=_blocked_session_state(
                    blocker=target_blocker,
                    actor_id=actor_id,
                    environment_id=resolved_environment_id,
                    environment_profile_id=resolved_profile_id,
                    environment_session_id=environment_session_id,
                    updated_at=updated_at,
                    evidence=evidence,
                ),
                environment_navigation_state=None,
                environment_admission_receipt=resolved_admission_receipt,
            )

        preflight_blocker = _session_preflight_blocker(
            transport_session=self.transport_session,
            actor_id=actor_id,
            environment_id=resolved_environment_id,
            environment_profile_id=resolved_profile_id,
            environment_admission_receipt=resolved_admission_receipt,
        )
        if preflight_blocker is not None:
            return ServiceApiInterfaceEnvironmentEntry(
                environment_admission_state=admission_state,
                environment_session_state=_blocked_session_state(
                    blocker=preflight_blocker,
                    actor_id=actor_id,
                    environment_id=resolved_environment_id,
                    environment_profile_id=resolved_profile_id,
                    environment_session_id=environment_session_id,
                    updated_at=updated_at,
                    evidence=evidence,
                ),
                environment_navigation_state=None,
                environment_admission_receipt=resolved_admission_receipt,
            )

        client = EnvironmentSessionClient(
            api_client=AwareEnvironmentServiceApiClient(self.transport_session.client),
            context=EnvironmentSessionContext(
                actor_id=actor_id,
                environment_id=resolved_environment_id,
            ),
        )
        try:
            if environment_session_id is not None:
                result = await client.join_session(
                    environment_profile_id=resolved_profile_id,
                    environment_session_id=environment_session_id,
                    admission_receipt=resolved_admission_receipt,
                    reason=reason,
                    resolve_default_navigation_context=True,
                    metadata={
                        "source": "interface_enter_environment.join_session",
                        **_jsonish_mapping(evidence or {}),
                    },
                )
                session = result.session.dto_session if result.session else None
                join_receipt = result.receipt.dto_receipt
                navigation_context = result.default_navigation_context
                default_navigation_receipt = result.default_navigation_receipt
            else:
                result = await client.start_session(
                    environment_profile_id=resolved_profile_id,
                    environment_session_config_id=environment_session_config_id,
                    admission_receipt=resolved_admission_receipt,
                    session_key=session_key,
                    title=title,
                    description=description,
                    purpose=purpose,
                    source_kind=source_kind,
                    source_ref=source_ref,
                    resolve_default_navigation_context=True,
                    metadata={
                        "source": "interface_enter_environment.start_session",
                        **_jsonish_mapping(evidence or {}),
                    },
                )
                session = result.session.dto_session if result.session else None
                join_receipt = result.join_receipt.dto_receipt
                navigation_context = result.default_navigation_context
                default_navigation_receipt = result.default_navigation_receipt

            return ServiceApiInterfaceEnvironmentEntry(
                environment_admission_state=admission_state,
                environment_session_state=(
                    environment_session_state_from_join_receipt(
                        receipt=join_receipt,
                        updated_at=updated_at,
                    )
                    if join_receipt is not None
                    else None
                ),
                environment_navigation_state=(
                    environment_navigation_state_from_context(
                        context=navigation_context,
                        actor_id=actor_id,
                        updated_at=updated_at,
                    )
                    if navigation_context is not None
                    else _navigation_state_from_receipt(
                        receipt=default_navigation_receipt,
                        actor_id=actor_id,
                        updated_at=updated_at,
                    )
                ),
                environment_admission_receipt=resolved_admission_receipt,
                environment_session=session,
                environment_session_join_receipt=join_receipt,
                environment_navigation_context=navigation_context,
                default_navigation_receipt=default_navigation_receipt,
            )
        except EnvironmentSessionError as exc:
            join_receipt = exc.receipt.dto_receipt if exc.receipt is not None else None
            return ServiceApiInterfaceEnvironmentEntry(
                environment_admission_state=admission_state,
                environment_session_state=(
                    environment_session_state_from_join_receipt(
                        receipt=join_receipt,
                        updated_at=updated_at,
                    )
                    if join_receipt is not None
                    else _blocked_session_state(
                        blocker="environment_session_entry_failed",
                        actor_id=actor_id,
                        environment_id=resolved_environment_id,
                        environment_profile_id=resolved_profile_id,
                        environment_session_id=environment_session_id,
                        error=str(exc),
                        updated_at=updated_at,
                        evidence=evidence,
                    )
                ),
                environment_navigation_state=None,
                environment_admission_receipt=resolved_admission_receipt,
                environment_session_join_receipt=join_receipt,
            )
        except Exception as exc:
            return ServiceApiInterfaceEnvironmentEntry(
                environment_admission_state=admission_state,
                environment_session_state=_blocked_session_state(
                    blocker="environment_session_entry_exception",
                    actor_id=actor_id,
                    environment_id=resolved_environment_id,
                    environment_profile_id=resolved_profile_id,
                    environment_session_id=environment_session_id,
                    error=str(exc),
                    updated_at=updated_at,
                    evidence=evidence,
                ),
                environment_navigation_state=None,
                environment_admission_receipt=resolved_admission_receipt,
            )


def result_with_state(
    *,
    state: InterfaceHostServiceState,
    entry: ServiceApiInterfaceEnvironmentEntry,
) -> InterfaceEnvironmentEntryResult:
    return InterfaceEnvironmentEntryResult(
        state=state,
        environment_session=entry.environment_session,
        environment_session_join_receipt=entry.environment_session_join_receipt,
        environment_navigation_context=entry.environment_navigation_context,
        default_navigation_receipt=entry.default_navigation_receipt,
    )


def _resolved_actor_id(
    *,
    transport_session: InterfaceTransportSession | None,
    actor_context: InterfaceExperienceSessionActorContext | None,
) -> UUID | None:
    if actor_context is not None:
        return actor_context.actor_id
    binding = getattr(transport_session, "binding", None)
    value = getattr(binding, "actor_id", None)
    return value if isinstance(value, UUID) else None


def _resolve_environment_id(
    *,
    admission: EnvironmentActorAdmissionReceipt | None,
    environment_id: UUID | None,
    fallback: UUID | None,
) -> UUID | None:
    if admission is not None:
        return admission.environment_id
    return environment_id or fallback


def _resolve_environment_profile_id(
    *,
    admission: EnvironmentActorAdmissionReceipt | None,
    fallback: UUID | None,
) -> UUID | None:
    if admission is not None:
        return admission.environment_profile_id
    return fallback


def _admission_input_blocker(
    *,
    environment_profile_id: UUID | None,
    actor_config_id: UUID | None,
    class_instance_identity_id: UUID | None,
) -> str | None:
    if environment_profile_id is None:
        return "environment_admission_receipt_or_profile_required"
    if actor_config_id is None:
        return "environment_admission_receipt_or_actor_config_required"
    if class_instance_identity_id is None:
        return "environment_admission_receipt_or_class_instance_identity_required"
    return None


def _session_target_blocker(
    *,
    environment_session_id: UUID | None,
    environment_session_config_id: UUID | None,
    session_key: str | None,
) -> str | None:
    if environment_session_id is not None and environment_session_config_id is not None:
        return "environment_entry_session_target_ambiguous"
    if environment_session_id is None and environment_session_config_id is None:
        return "environment_entry_session_target_required"
    if environment_session_config_id is not None and not (session_key or "").strip():
        return "environment_entry_session_key_required"
    return None


def _session_preflight_blocker(
    *,
    transport_session: InterfaceTransportSession | None,
    actor_id: UUID | None,
    environment_id: UUID | None,
    environment_profile_id: UUID | None,
    environment_admission_receipt: EnvironmentActorAdmissionReceipt | None,
) -> str | None:
    if transport_session is None:
        return "interface_transport_unbound"
    if actor_id is None:
        return "interface_actor_unbound"
    if environment_id is None:
        return "interface_environment_unbound"
    if environment_profile_id is None:
        return "environment_profile_required"
    if environment_admission_receipt is None:
        return "environment_admission_receipt_required"
    return None


def _blocked_entry(
    *,
    blocker: str,
    actor_id: UUID | None,
    environment_id: UUID | None,
    environment_profile_id: UUID | None,
    updated_at: str,
    evidence: Mapping[str, object] | None = None,
) -> ServiceApiInterfaceEnvironmentEntry:
    admission_state = InterfaceEnvironmentAdmissionState(
        status="blocked",
        accepted=False,
        actor_id=actor_id,
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        blockers=(blocker,),
        error=blocker,
        updated_at=updated_at,
        evidence={
            "source": "interface_enter_environment.admission",
            "blocker": blocker,
            **_jsonish_mapping(evidence or {}),
        },
    )
    return ServiceApiInterfaceEnvironmentEntry(
        environment_admission_state=admission_state,
        environment_session_state=_blocked_session_state(
            blocker=blocker,
            actor_id=actor_id,
            environment_id=environment_id,
            environment_profile_id=environment_profile_id,
            environment_session_id=None,
            updated_at=updated_at,
            evidence=evidence,
        ),
        environment_navigation_state=None,
    )


def _blocked_session_state(
    *,
    blocker: str,
    actor_id: UUID | None,
    environment_id: UUID | None,
    environment_profile_id: UUID | None,
    environment_session_id: UUID | None,
    error: str | None = None,
    updated_at: str,
    evidence: Mapping[str, object] | None = None,
) -> InterfaceEnvironmentSessionState:
    return InterfaceEnvironmentSessionState(
        status="blocked" if error is None else "error",
        accepted=False,
        actor_id=actor_id,
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        environment_session_id=environment_session_id,
        blockers=(blocker,),
        error=error or blocker,
        updated_at=updated_at,
        evidence={
            "source": "interface_enter_environment",
            "blocker": blocker,
            **_jsonish_mapping(evidence or {}),
        },
    )


def _navigation_state_from_receipt(
    *,
    receipt: EnvironmentNavigationCommitReceipt | None,
    actor_id: UUID | None,
    updated_at: str,
) -> InterfaceEnvironmentNavigationState | None:
    if receipt is None:
        return None
    return InterfaceEnvironmentNavigationState(
        status=receipt.status,
        accepted=receipt.accepted,
        actor_id=actor_id or receipt.actor_id,
        environment_id=receipt.environment_id,
        environment_session_id=receipt.environment_session_id,
        environment_navigation_context_id=receipt.environment_navigation_context_id,
        key=receipt.key,
        process_id=receipt.selected_process_id,
        thread_id=receipt.selected_thread_id,
        branch_id=receipt.branch_id,
        projection_hash=receipt.projection_hash,
        root_object_id=receipt.root_object_id,
        commit_id=receipt.commit_id,
        object_instance_graph_commit_id=receipt.object_instance_graph_commit_id,
        blockers=tuple(receipt.blockers),
        error=receipt.error,
        reason=receipt.reason,
        updated_at=updated_at,
        evidence={
            "source": "interface_enter_environment.default_navigation_receipt",
            **_jsonish_mapping(receipt.evidence),
        },
    )


def _admission_state_from_receipt(
    receipt: EnvironmentActorAdmissionReceipt,
    *,
    updated_at: str,
) -> InterfaceEnvironmentAdmissionState:
    return InterfaceEnvironmentAdmissionState(
        status=receipt.status if receipt.accepted else "blocked",
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
        eligible_role_count=len(receipt.eligible_roles),
        binding_count=len(receipt.bindings),
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
        error=receipt.error,
        reason=receipt.reason,
        updated_at=updated_at,
        evidence=_jsonish_mapping(receipt.evidence),
    )


def _utc_now_isoformat() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _jsonish_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {str(key): _jsonish_value(item) for key, item in value.items()}


def _jsonish_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonish_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonish_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


__all__ = [
    "ServiceApiInterfaceEnvironmentEntry",
    "ServiceApiInterfaceEnvironmentEntryPort",
    "result_with_state",
]

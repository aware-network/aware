from __future__ import annotations

from collections.abc import Mapping
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
    InterfaceEnvironmentNavigationState,
    InterfaceEnvironmentSessionJoinResult,
    InterfaceEnvironmentSessionState,
    InterfaceHostServiceState,
)


@dataclass(frozen=True, slots=True)
class ServiceApiInterfaceEnvironmentSessionJoin:
    environment_session_state: InterfaceEnvironmentSessionState | None
    environment_navigation_state: InterfaceEnvironmentNavigationState | None
    environment_session: EnvironmentSessionView | None = None
    environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = None
    environment_navigation_context: EnvironmentNavigationContextView | None = None
    default_navigation_receipt: EnvironmentNavigationCommitReceipt | None = None


@dataclass(frozen=True, slots=True)
class ServiceApiInterfaceEnvironmentSessionPort:
    transport_session: InterfaceTransportSession | None
    context_environment_id: UUID | None = None
    actor_context: InterfaceExperienceSessionActorContext | None = None

    async def join_session(
        self,
        *,
        environment_session_id: UUID,
        environment_profile_id: UUID | None = None,
        environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None,
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> ServiceApiInterfaceEnvironmentSessionJoin:
        updated_at = _utc_now_isoformat()
        actor_id = _resolved_actor_id(
            transport_session=self.transport_session,
            actor_context=self.actor_context,
        )
        resolved_environment_id = _resolve_environment_id(
            admission=environment_admission_receipt,
            fallback=self.context_environment_id,
        )
        resolved_profile_id = _resolve_environment_profile_id(
            admission=environment_admission_receipt,
            fallback=environment_profile_id,
        )
        if self.transport_session is None:
            return _blocked_join(
                blocker="interface_transport_unbound",
                actor_id=actor_id,
                environment_id=resolved_environment_id,
                environment_profile_id=resolved_profile_id,
                environment_session_id=environment_session_id,
                updated_at=updated_at,
                evidence=evidence,
            )
        if actor_id is None:
            return _blocked_join(
                blocker="interface_actor_unbound",
                environment_id=resolved_environment_id,
                environment_profile_id=resolved_profile_id,
                environment_session_id=environment_session_id,
                updated_at=updated_at,
                evidence=evidence,
            )
        if resolved_environment_id is None:
            return _blocked_join(
                blocker="interface_environment_unbound",
                actor_id=actor_id,
                environment_profile_id=resolved_profile_id,
                environment_session_id=environment_session_id,
                updated_at=updated_at,
                evidence=evidence,
            )
        if resolved_profile_id is None:
            return _blocked_join(
                blocker="environment_profile_required",
                actor_id=actor_id,
                environment_id=resolved_environment_id,
                environment_session_id=environment_session_id,
                updated_at=updated_at,
                evidence=evidence,
            )
        if environment_admission_receipt is None:
            return _blocked_join(
                blocker="environment_admission_receipt_required",
                actor_id=actor_id,
                environment_id=resolved_environment_id,
                environment_profile_id=resolved_profile_id,
                environment_session_id=environment_session_id,
                updated_at=updated_at,
                evidence=evidence,
            )

        client = EnvironmentSessionClient(
            api_client=AwareEnvironmentServiceApiClient(self.transport_session.client),
            context=EnvironmentSessionContext(
                actor_id=actor_id,
                environment_id=resolved_environment_id,
            ),
        )
        try:
            result = await client.join_session(
                environment_profile_id=resolved_profile_id,
                environment_session_id=environment_session_id,
                admission_receipt=environment_admission_receipt,
                reason=reason,
                resolve_default_navigation_context=True,
                metadata={
                    "source": "interface_join_environment_session",
                    **_jsonish_mapping(evidence or {}),
                },
            )
            session = result.session.dto_session if result.session is not None else None
            join_receipt = result.receipt.dto_receipt
            navigation_context = result.default_navigation_context
            default_navigation_receipt = result.default_navigation_receipt
            return ServiceApiInterfaceEnvironmentSessionJoin(
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
                environment_session=session,
                environment_session_join_receipt=join_receipt,
                environment_navigation_context=navigation_context,
                default_navigation_receipt=default_navigation_receipt,
            )
        except EnvironmentSessionError as exc:
            join_receipt = exc.receipt.dto_receipt if exc.receipt is not None else None
            return ServiceApiInterfaceEnvironmentSessionJoin(
                environment_session_state=(
                    environment_session_state_from_join_receipt(
                        receipt=join_receipt,
                        updated_at=updated_at,
                    )
                    if join_receipt is not None
                    else _blocked_session_state(
                        blocker="environment_session_join_failed",
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
                environment_session_join_receipt=join_receipt,
            )
        except Exception as exc:
            return _blocked_join(
                blocker="environment_session_join_exception",
                actor_id=actor_id,
                environment_id=resolved_environment_id,
                environment_profile_id=resolved_profile_id,
                environment_session_id=environment_session_id,
                error=str(exc),
                updated_at=updated_at,
                evidence=evidence,
            )


def result_with_state(
    *,
    state: InterfaceHostServiceState,
    join: ServiceApiInterfaceEnvironmentSessionJoin,
) -> InterfaceEnvironmentSessionJoinResult:
    return InterfaceEnvironmentSessionJoinResult(
        state=state,
        environment_session=join.environment_session,
        environment_session_join_receipt=join.environment_session_join_receipt,
        environment_navigation_context=join.environment_navigation_context,
        default_navigation_receipt=join.default_navigation_receipt,
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


def _resolve_environment_id(
    *,
    admission: EnvironmentActorAdmissionReceipt | None,
    fallback: UUID | None,
) -> UUID | None:
    if admission is not None:
        return admission.environment_id
    return fallback


def _resolve_environment_profile_id(
    *,
    admission: EnvironmentActorAdmissionReceipt | None,
    fallback: UUID | None,
) -> UUID | None:
    if admission is not None:
        return admission.environment_profile_id
    return fallback


def _blocked_join(
    *,
    blocker: str,
    actor_id: UUID | None = None,
    environment_id: UUID | None = None,
    environment_profile_id: UUID | None = None,
    environment_session_id: UUID | None = None,
    error: str | None = None,
    updated_at: str,
    evidence: Mapping[str, object] | None = None,
) -> ServiceApiInterfaceEnvironmentSessionJoin:
    return ServiceApiInterfaceEnvironmentSessionJoin(
        environment_session_state=_blocked_session_state(
            blocker=blocker,
            actor_id=actor_id,
            environment_id=environment_id,
            environment_profile_id=environment_profile_id,
            environment_session_id=environment_session_id,
            error=error,
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
            "source": "interface_join_environment_session",
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
            "source": "interface_join_environment_session.default_navigation_receipt",
            **_jsonish_mapping(receipt.evidence),
        },
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
    "ServiceApiInterfaceEnvironmentSessionJoin",
    "ServiceApiInterfaceEnvironmentSessionPort",
    "result_with_state",
]

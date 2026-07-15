from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from aware_environment_service_dto.environment.view import (
    EnvironmentNavigatorViewStateV1,
    ThreadLayoutViewStateV1,
)
from aware_environment_service_api import AwareEnvironmentServiceApiClient
from aware_environment_service_dto.environment.environment import (
    EnvironmentNavigationCommitReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
)
from aware_environment_sdk import (
    EnvironmentNavigationClient,
    EnvironmentNavigationClientContext,
    EnvironmentNavigationError,
)
from aware_environment_sdk.view_state_providers import (
    ENVIRONMENT_NAVIGATOR_API_VIEW_REF,
    ENVIRONMENT_NAVIGATOR_PROJECTION_VIEW_KEY,
    THREAD_LAYOUT_API_VIEW_REF,
    THREAD_LAYOUT_PROJECTION_VIEW_KEY,
    environment_navigator_view_state_from_input,
    environment_views_v1_provider_input_from_api,
    thread_layout_view_state_from_input,
)
from aware_interface import InterfaceMaterializedPaneState
from aware_interface_sdk.transport import InterfaceTransportSession

from aware_interface_service.host.capabilities.experience_lens import (
    environment_navigation_state_from_context,
)
from aware_interface_service.models import (
    InterfaceExperienceSessionActorContext,
    InterfaceEnvironmentNavigationSelectResult,
    InterfaceEnvironmentNavigationState,
    InterfaceHostServiceState,
)

_ENVIRONMENT_NAVIGATOR_PANE_STATE_KEY = (
    "shell:environment_navigation:environment_navigator"
)
_ENVIRONMENT_NAVIGATOR_WINDOW_KEY = "shell"
_ENVIRONMENT_NAVIGATOR_LAYOUT_KEY = "environment_navigation"
_ENVIRONMENT_NAVIGATOR_SECTION_KEY = "environment_navigator"
_ENVIRONMENT_NAVIGATOR_PANE_KIND = "environment_navigator"
_THREAD_LAYOUT_PANE_STATE_KEY = "shell:environment_navigation:thread_layout"
_THREAD_LAYOUT_WINDOW_KEY = "main"
_THREAD_LAYOUT_SECTION_KEY = "thread_layout"
_THREAD_LAYOUT_PANE_KIND = "thread_layout"
_ENVIRONMENT_NAVIGATOR_STATE_MODEL_REF = (
    "aware_environment_service_dto.environment.EnvironmentNavigatorViewStateV1"
)
_THREAD_LAYOUT_STATE_MODEL_REF = (
    "aware_environment_service_dto.environment.ThreadLayoutViewStateV1"
)


@dataclass(frozen=True, slots=True)
class ServiceApiInterfaceEnvironmentNavigationSelection:
    environment_navigation_state: InterfaceEnvironmentNavigationState | None
    environment_navigation_context: EnvironmentNavigationContextView | None = None
    environment_navigation_receipt: EnvironmentNavigationCommitReceipt | None = None


@dataclass(frozen=True, slots=True)
class ServiceApiInterfaceEnvironmentNavigationPort:
    transport_session: InterfaceTransportSession | None
    context_environment_id: UUID | None = None
    actor_context: InterfaceExperienceSessionActorContext | None = None

    async def select_target(
        self,
        *,
        environment_session_join_receipt: EnvironmentSessionJoinReceipt | None,
        active_navigation_state: InterfaceEnvironmentNavigationState | None,
        environment_navigation_context_id: UUID | None = None,
        selected_process_id: UUID | None = None,
        selected_thread_id: UUID | None = None,
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> ServiceApiInterfaceEnvironmentNavigationSelection:
        updated_at = _utc_now_isoformat()
        actor_id = _resolved_actor_id(
            transport_session=self.transport_session,
            actor_context=self.actor_context,
        )
        environment_id = _resolve_environment_id(
            receipt=environment_session_join_receipt,
            navigation=active_navigation_state,
            fallback=self.context_environment_id,
        )
        environment_session_id = _resolve_environment_session_id(
            receipt=environment_session_join_receipt,
            navigation=active_navigation_state,
        )
        resolved_context_id = environment_navigation_context_id or (
            active_navigation_state.environment_navigation_context_id
            if active_navigation_state is not None
            else None
        )

        blocker = _select_preflight_blocker(
            transport_session=self.transport_session,
            actor_id=actor_id,
            environment_id=environment_id,
            environment_session_id=environment_session_id,
            environment_navigation_context_id=resolved_context_id,
            environment_session_join_receipt=environment_session_join_receipt,
        )
        if blocker is not None:
            return ServiceApiInterfaceEnvironmentNavigationSelection(
                environment_navigation_state=_blocked_navigation_state(
                    blocker=blocker,
                    actor_id=actor_id,
                    environment_id=environment_id,
                    environment_session_id=environment_session_id,
                    environment_navigation_context_id=resolved_context_id,
                    process_id=selected_process_id,
                    thread_id=selected_thread_id,
                    reason=reason,
                    updated_at=updated_at,
                    evidence=evidence,
                )
            )

        client = EnvironmentNavigationClient(
            api_client=AwareEnvironmentServiceApiClient(self.transport_session.client),
            context=EnvironmentNavigationClientContext(
                actor_id=actor_id,
                environment_id=environment_id,
            ),
        )
        try:
            result = await client.select_navigation_target(
                environment_session_id=environment_session_id,
                environment_navigation_context_id=resolved_context_id,
                session_join_receipt=environment_session_join_receipt,
                selected_process_id=selected_process_id,
                selected_thread_id=selected_thread_id,
                reason=reason,
                metadata={
                    "source": "interface_select_environment_navigation_target",
                    **_jsonish_mapping(evidence or {}),
                },
            )
            context = result.context.dto_context if result.context is not None else None
            receipt = result.receipt.dto_receipt
            return ServiceApiInterfaceEnvironmentNavigationSelection(
                environment_navigation_state=(
                    environment_navigation_state_from_context(
                        context=context,
                        actor_id=actor_id,
                        updated_at=updated_at,
                    )
                    if context is not None
                    else _navigation_state_from_receipt(
                        receipt=receipt,
                        actor_id=actor_id,
                        updated_at=updated_at,
                    )
                ),
                environment_navigation_context=context,
                environment_navigation_receipt=receipt,
            )
        except EnvironmentNavigationError as exc:
            receipt = exc.receipt.dto_receipt if exc.receipt is not None else None
            return ServiceApiInterfaceEnvironmentNavigationSelection(
                environment_navigation_state=(
                    _navigation_state_from_receipt(
                        receipt=receipt,
                        actor_id=actor_id,
                        updated_at=updated_at,
                    )
                    if receipt is not None
                    else _blocked_navigation_state(
                        blocker="environment_navigation_select_failed",
                        actor_id=actor_id,
                        environment_id=environment_id,
                        environment_session_id=environment_session_id,
                        environment_navigation_context_id=resolved_context_id,
                        process_id=selected_process_id,
                        thread_id=selected_thread_id,
                        reason=reason,
                        error=str(exc),
                        updated_at=updated_at,
                        evidence=evidence,
                    )
                ),
                environment_navigation_receipt=receipt,
            )
        except Exception as exc:
            return ServiceApiInterfaceEnvironmentNavigationSelection(
                environment_navigation_state=_blocked_navigation_state(
                    blocker="environment_navigation_select_exception",
                    actor_id=actor_id,
                    environment_id=environment_id,
                    environment_session_id=environment_session_id,
                    environment_navigation_context_id=resolved_context_id,
                    process_id=selected_process_id,
                    thread_id=selected_thread_id,
                    reason=reason,
                    error=str(exc),
                    updated_at=updated_at,
                    evidence=evidence,
                )
            )


def result_with_state(
    *,
    state: InterfaceHostServiceState,
    selection: ServiceApiInterfaceEnvironmentNavigationSelection,
) -> InterfaceEnvironmentNavigationSelectResult:
    return InterfaceEnvironmentNavigationSelectResult(
        state=state,
        environment_navigation_context=selection.environment_navigation_context,
        environment_navigation_receipt=selection.environment_navigation_receipt,
    )


async def environment_navigator_materialized_pane_state(
    *,
    transport_session: InterfaceTransportSession | None,
    navigation_state: InterfaceEnvironmentNavigationState | None,
) -> InterfaceMaterializedPaneState | None:
    if transport_session is None or navigation_state is None:
        return None
    actor_id = _transport_actor_id(transport_session)
    environment_id = navigation_state.environment_id
    if actor_id is None or environment_id is None:
        return None

    try:
        provider_input = await environment_views_v1_provider_input_from_api(
            api_client=AwareEnvironmentServiceApiClient(transport_session.client),
            environment_id=environment_id,
            actor_id=actor_id,
            process_id=navigation_state.process_id,
            thread_id=navigation_state.thread_id,
            branch_id=navigation_state.branch_id,
            projection_hash=navigation_state.projection_hash,
        )
        view_state = environment_navigator_view_state_from_input(provider_input)
        state_payload = view_state.model_dump(mode="json")
        status = str(state_payload.get("status") or navigation_state.status)
        error = None
    except Exception as exc:
        view_state = EnvironmentNavigatorViewStateV1(
            environment_id=str(environment_id),
            title="Environment",
            status="blocked",
            ready=False,
            selected_process_id=(
                str(navigation_state.process_id)
                if navigation_state.process_id is not None
                else None
            ),
            selected_thread_id=(
                str(navigation_state.thread_id)
                if navigation_state.thread_id is not None
                else None
            ),
            empty_message="Environment navigator view is unavailable.",
            provenance={
                "source": "interface_host_environment_navigation",
                "blocker": "environment_navigator_view_unavailable",
            },
        )
        state_payload = view_state.model_dump(mode="json")
        status = "blocked"
        error = str(exc)

    return InterfaceMaterializedPaneState(
        pane_state_key=_ENVIRONMENT_NAVIGATOR_PANE_STATE_KEY,
        window_key=_ENVIRONMENT_NAVIGATOR_WINDOW_KEY,
        layout_key=_ENVIRONMENT_NAVIGATOR_LAYOUT_KEY,
        section_key=_ENVIRONMENT_NAVIGATOR_SECTION_KEY,
        pane_kind=_ENVIRONMENT_NAVIGATOR_PANE_KIND,
        branch_id=navigation_state.branch_id,
        projection_view_id=ENVIRONMENT_NAVIGATOR_PROJECTION_VIEW_KEY,
        projection_hash=navigation_state.projection_hash,
        status=status,
        head_commit_id=(
            str(navigation_state.object_instance_graph_commit_id)
            if navigation_state.object_instance_graph_commit_id is not None
            else None
        ),
        materialized_at=_utc_now_isoformat(),
        state=state_payload,
        provenance={
            "source": "interface_host_environment_navigation",
            "view_ref": ENVIRONMENT_NAVIGATOR_API_VIEW_REF,
            "projection_view_key": ENVIRONMENT_NAVIGATOR_PROJECTION_VIEW_KEY,
            "state_model_ref": _ENVIRONMENT_NAVIGATOR_STATE_MODEL_REF,
        },
        error=error,
    )


async def environment_thread_layout_materialized_pane_state(
    *,
    transport_session: InterfaceTransportSession | None,
    navigation_state: InterfaceEnvironmentNavigationState | None,
) -> InterfaceMaterializedPaneState | None:
    if (
        transport_session is None
        or navigation_state is None
        or navigation_state.thread_id is None
    ):
        return None
    actor_id = _transport_actor_id(transport_session)
    environment_id = navigation_state.environment_id
    if actor_id is None or environment_id is None:
        return None

    layout_key = "thread_layout"
    try:
        provider_input = await environment_views_v1_provider_input_from_api(
            api_client=AwareEnvironmentServiceApiClient(transport_session.client),
            environment_id=environment_id,
            actor_id=actor_id,
            process_id=navigation_state.process_id,
            thread_id=navigation_state.thread_id,
            branch_id=navigation_state.branch_id,
            projection_hash=navigation_state.projection_hash,
        )
        view_state = thread_layout_view_state_from_input(provider_input)
        state_payload = view_state.model_dump(mode="json")
        status = str(state_payload.get("status") or navigation_state.status)
        layout_key = str(state_payload.get("active_layout_key") or layout_key)
        error = None
    except Exception as exc:
        view_state = ThreadLayoutViewStateV1(
            environment_id=str(environment_id),
            process_id=(
                str(navigation_state.process_id)
                if navigation_state.process_id is not None
                else None
            ),
            thread_id=str(navigation_state.thread_id),
            title="Thread",
            status="blocked",
            empty_message="Thread layout view is unavailable.",
            provenance={
                "source": "interface_host_environment_navigation",
                "blocker": "thread_layout_view_unavailable",
            },
        )
        state_payload = view_state.model_dump(mode="json")
        status = "blocked"
        error = str(exc)

    return InterfaceMaterializedPaneState(
        pane_state_key=_THREAD_LAYOUT_PANE_STATE_KEY,
        window_key=_THREAD_LAYOUT_WINDOW_KEY,
        layout_key=layout_key,
        section_key=_THREAD_LAYOUT_SECTION_KEY,
        pane_kind=_THREAD_LAYOUT_PANE_KIND,
        branch_id=navigation_state.branch_id,
        projection_view_id=THREAD_LAYOUT_PROJECTION_VIEW_KEY,
        projection_hash=navigation_state.projection_hash,
        status=status,
        head_commit_id=(
            str(navigation_state.object_instance_graph_commit_id)
            if navigation_state.object_instance_graph_commit_id is not None
            else None
        ),
        materialized_at=_utc_now_isoformat(),
        state=state_payload,
        provenance={
            "source": "interface_host_environment_navigation",
            "view_ref": THREAD_LAYOUT_API_VIEW_REF,
            "projection_view_key": THREAD_LAYOUT_PROJECTION_VIEW_KEY,
            "state_model_ref": _THREAD_LAYOUT_STATE_MODEL_REF,
        },
        error=error,
    )


def _select_preflight_blocker(
    *,
    transport_session: InterfaceTransportSession | None,
    actor_id: UUID | None,
    environment_id: UUID | None,
    environment_session_id: UUID | None,
    environment_navigation_context_id: UUID | None,
    environment_session_join_receipt: EnvironmentSessionJoinReceipt | None,
) -> str | None:
    if transport_session is None:
        return "interface_transport_unbound"
    if actor_id is None:
        return "interface_actor_unbound"
    if environment_id is None:
        return "interface_environment_unbound"
    if environment_session_id is None:
        return "environment_session_required"
    if environment_navigation_context_id is None:
        return "environment_navigation_context_required"
    if environment_session_join_receipt is None:
        return "environment_session_join_receipt_required"
    if not environment_session_join_receipt.accepted:
        return "environment_session_join_not_accepted"
    if environment_session_join_receipt.actor_id != actor_id:
        return "environment_session_actor_mismatch"
    if environment_session_join_receipt.environment_id != environment_id:
        return "environment_session_environment_mismatch"
    if (
        environment_session_join_receipt.environment_session_id
        != environment_session_id
    ):
        return "environment_session_scope_mismatch"
    return None


def _transport_actor_id(
    transport_session: InterfaceTransportSession | None,
) -> UUID | None:
    binding = getattr(transport_session, "binding", None)
    value = getattr(binding, "actor_id", None)
    return value if isinstance(value, UUID) else None


def _resolved_actor_id(
    *,
    transport_session: InterfaceTransportSession | None,
    actor_context: InterfaceExperienceSessionActorContext | None,
) -> UUID | None:
    if actor_context is not None:
        return actor_context.actor_id
    return _transport_actor_id(transport_session)


def _resolve_environment_id(
    *,
    receipt: EnvironmentSessionJoinReceipt | None,
    navigation: InterfaceEnvironmentNavigationState | None,
    fallback: UUID | None,
) -> UUID | None:
    if receipt is not None:
        return receipt.environment_id
    if navigation is not None:
        return navigation.environment_id
    return fallback


def _resolve_environment_session_id(
    *,
    receipt: EnvironmentSessionJoinReceipt | None,
    navigation: InterfaceEnvironmentNavigationState | None,
) -> UUID | None:
    if receipt is not None:
        return receipt.environment_session_id
    if navigation is not None:
        return navigation.environment_session_id
    return None


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
            "source": "interface_select_environment_navigation_target.receipt",
            **_jsonish_mapping(receipt.evidence),
        },
    )


def _blocked_navigation_state(
    *,
    blocker: str,
    actor_id: UUID | None,
    environment_id: UUID | None,
    environment_session_id: UUID | None,
    environment_navigation_context_id: UUID | None,
    process_id: UUID | None,
    thread_id: UUID | None,
    reason: str | None,
    error: str | None = None,
    updated_at: str,
    evidence: Mapping[str, object] | None = None,
) -> InterfaceEnvironmentNavigationState:
    return InterfaceEnvironmentNavigationState(
        status="blocked" if error is None else "error",
        accepted=False,
        actor_id=actor_id,
        environment_id=environment_id,
        environment_session_id=environment_session_id,
        environment_navigation_context_id=environment_navigation_context_id,
        process_id=process_id,
        thread_id=thread_id,
        blockers=(blocker,),
        error=error or blocker,
        reason=reason,
        updated_at=updated_at,
        evidence={
            "source": "interface_select_environment_navigation_target",
            "blocker": blocker,
            **_jsonish_mapping(evidence or {}),
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
    "ServiceApiInterfaceEnvironmentNavigationPort",
    "ServiceApiInterfaceEnvironmentNavigationSelection",
    "environment_navigator_materialized_pane_state",
    "environment_thread_layout_materialized_pane_state",
    "result_with_state",
]

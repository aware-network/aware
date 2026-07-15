from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from typing import Protocol, cast
from uuid import UUID

from aware_experience_sdk import build_experience_sdk_client
from aware_types import JsonObject
from aware_experience_service_api import AwareExperienceServiceApiClient
from aware_experience_service_dto.experience.session_handoff.models import (
    ExperienceSessionHandoffActorContext,
    ExperienceSessionHandoffFeatureSpec,
    ExperienceSessionHandoffScope,
)
from aware_experience_service_dto.experience.session_context.models import (
    ExperienceSessionAttentionResolutionRequest,
)
from aware_experience_service_dto.experience.session_view_frame.service_operation import (
    ResolveExperienceSessionViewFrameRequest,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_interface import (
    InterfaceAttentionFocusTargetState,
    InterfaceResolvedPaneDescriptor,
    InterfaceRuntimeFocusState,
    InterfaceRuntimeSectionRepresentationState,
    InterfaceRuntimeState,
    InterfaceNavigationContextLayoutTargetState,
    InterfaceWindowLayoutState,
)
from aware_interface_sdk.transport import (
    InterfaceTransportBindingState,
    InterfaceTransportSession,
)

from aware_interface_service.models import (
    InterfaceExperienceSessionActorContext,
    InterfaceExperienceSessionFeatureDeclaration,
    InterfaceExperienceSessionHandoffRequest,
    InterfaceExperienceSessionHandoffResult,
    InterfaceExperienceSessionNarrationEventState,
    InterfaceExperienceSessionScope,
    InterfaceHostServiceExperienceSessionHandoffState,
    InterfaceHostServiceExperienceSessionNarrationState,
)


REACTIVITY_TRANSITION_DISPATCH_FEATURE_KEY = "reactivity_transition_dispatch"
EXPERIENCE_SESSION_NARRATOR_FEATURE_KEY = "experience_session_narrator"


class ExperienceSessionHandoffProvider(Protocol):
    async def ensure_experience_session_handoff(
        self,
        request: InterfaceExperienceSessionHandoffRequest,
    ) -> InterfaceExperienceSessionHandoffResult: ...

    async def get_experience_session_narration(
        self,
        request: InterfaceExperienceSessionHandoffRequest,
    ) -> InterfaceHostServiceExperienceSessionNarrationState: ...


class ExperienceSessionHandoffSdk(Protocol):
    async def ensure_session_handoff(
        self,
        *,
        session_scope: ExperienceSessionHandoffScope,
        actor_context: ExperienceSessionHandoffActorContext,
        environment_admission: EnvironmentActorAdmissionReceipt | None = None,
        environment_session_join: EnvironmentSessionJoinReceipt | None = None,
        experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None,
        experience_identity_session_config_id: UUID | None = None,
        feature: ExperienceSessionHandoffFeatureSpec,
        idempotency_key: str,
        evidence: Mapping[str, object],
    ) -> object: ...

    async def get_session_handoff_status(
        self,
        *,
        session_scope: ExperienceSessionHandoffScope,
        feature_key: str | None = None,
        lease_key: str | None = None,
        include_health: bool = True,
        evidence: Mapping[str, object],
    ) -> object: ...


class ExperienceSdkSessionHandoffProvider:
    def __init__(self, *, sdk: ExperienceSessionHandoffSdk) -> None:
        self._sdk = sdk

    @classmethod
    def from_transport_session(
        cls,
        transport_session: InterfaceTransportSession,
    ) -> "ExperienceSdkSessionHandoffProvider":
        api_client = AwareExperienceServiceApiClient(transport_session.client)
        return cls(
            sdk=cast(
                ExperienceSessionHandoffSdk,
                cast(object, build_experience_sdk_client(api_client)),
            )
        )

    async def ensure_experience_session_handoff(
        self,
        request: InterfaceExperienceSessionHandoffRequest,
    ) -> InterfaceExperienceSessionHandoffResult:
        response = await self._sdk.ensure_session_handoff(
            session_scope=_experience_session_handoff_scope(request),
            actor_context=_experience_session_handoff_actor_context(request),
            environment_admission=request.environment_admission,
            environment_session_join=request.environment_session_join,
            experience_actor_admission=request.experience_actor_admission,
            experience_identity_session_config_id=(
                request.experience_identity_session_config_id
            ),
            feature=_experience_session_handoff_feature(request),
            idempotency_key=request.idempotency_key,
            evidence=_jsonish_mapping(request.evidence),
        )
        return _interface_handoff_result_from_experience_response(
            request=request,
            response=response,
        )

    async def get_experience_session_narration(
        self,
        request: InterfaceExperienceSessionHandoffRequest,
    ) -> InterfaceHostServiceExperienceSessionNarrationState:
        response = await self._sdk.get_session_handoff_status(
            session_scope=_experience_session_handoff_scope(request),
            feature_key=EXPERIENCE_SESSION_NARRATOR_FEATURE_KEY,
            lease_key=request.idempotency_key,
            include_health=True,
            evidence={
                "source": "interface_experience_session_narration",
                "handoff_feature_key": request.feature.feature_key,
            },
        )
        return narration_state_from_status_response(
            request=request,
            response=response,
        )


def build_experience_sdk_session_handoff_provider(
    *,
    transport_session: InterfaceTransportSession | None,
) -> ExperienceSessionHandoffProvider | None:
    if transport_session is None:
        return None
    client = getattr(transport_session, "client", None)
    if client is None:
        return None
    return ExperienceSdkSessionHandoffProvider.from_transport_session(transport_session)


def build_experience_session_handoff_request(
    *,
    namespace: str,
    authenticated: bool,
    interface_admitted: bool,
    transport_binding: InterfaceTransportBindingState | None,
    actor_context: InterfaceExperienceSessionActorContext | None = None,
    runtime_state: InterfaceRuntimeState | None,
    window_layout: InterfaceWindowLayoutState | None,
    active_focus: InterfaceRuntimeFocusState | None,
    section_representations: tuple[InterfaceRuntimeSectionRepresentationState, ...],
    environment_admission: EnvironmentActorAdmissionReceipt | None = None,
    environment_session_join: EnvironmentSessionJoinReceipt | None = None,
    environment_navigation_context: EnvironmentNavigationContextView | None = None,
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None,
    experience_identity_session_config_id: UUID | None = None,
    host_environment_id: UUID | None = None,
    feature_key: str = REACTIVITY_TRANSITION_DISPATCH_FEATURE_KEY,
) -> InterfaceExperienceSessionHandoffRequest | None:
    if not interface_admitted:
        return None
    actor = actor_context or _actor_context_from_transport_binding(transport_binding)
    actor_id = actor.actor_id if actor is not None else None
    if actor_id is None or runtime_state is None or window_layout is None:
        return None
    if active_focus is None:
        return None
    section_key = _optional_text(active_focus.section_key)
    observable_id = _as_uuid(active_focus.observable_id)
    if section_key is None or observable_id is None:
        return None

    representation = _active_representation(
        active_focus=active_focus,
        section_representations=section_representations,
    )
    if representation is None:
        return None
    view_ref = _optional_text(representation.view_ref)
    experience_name = _experience_name_from_view_ref(view_ref)
    if view_ref is None or experience_name is None:
        return None

    navigation_context_layout_target = runtime_state.navigation_context_layout_target
    focus_target = active_focus.focus_target
    scope = InterfaceExperienceSessionScope(
        namespace=namespace,
        experience_name=experience_name,
        view_ref=view_ref,
        window_key=window_layout.window_key,
        layout_key=active_focus.layout_key or window_layout.layout_key,
        layout_config_id=(
            active_focus.layout_config_id
            or window_layout.layout_config_id
            or representation.layout_config_id
        ),
        section_key=section_key,
        layout_config_section_config_id=(
            active_focus.layout_config_section_config_id
            or representation.layout_config_section_config_id
        ),
        layout_section_id=active_focus.layout_section_id,
        section_focus_scope_id=active_focus.section_focus_scope_id,
        focus_scope_id=active_focus.focus_scope_id,
        focus_id=active_focus.focus_id,
        observable_id=observable_id,
        projection_view_key=_optional_text(representation.projection_view_key),
        environment_session_id=(
            environment_navigation_context.environment_session_id
            if environment_navigation_context is not None
            else (
                environment_session_join.environment_session_id
                if environment_session_join is not None
                else None
            )
        ),
        environment_navigation_context_id=(
            environment_navigation_context.environment_navigation_context_id
            if environment_navigation_context is not None
            else None
        ),
        section_graph_binding_key=_optional_text(
            representation.section_graph_binding_key
        ),
        projection_experience_graph_identity_id=(
            representation.projection_experience_graph_identity_id
            or _focus_projection_experience_graph_identity_id(focus_target)
        ),
        object_projection_graph_identity_id=(
            representation.object_projection_graph_identity_id
            or _focus_object_projection_graph_identity_id(focus_target)
        ),
        object_instance_graph_branch_id=(
            focus_target.object_instance_graph_branch_id
            if focus_target is not None
            else None
        ),
        projection_hash=(
            focus_target.projection_hash if focus_target is not None else None
        ),
        environment_id=_scope_environment_id(
            runtime_state=runtime_state,
            navigation_context_layout_target=navigation_context_layout_target,
            environment_navigation_context=environment_navigation_context,
            host_environment_id=host_environment_id,
        ),
        process_id=(
            environment_navigation_context.selected_process_id
            if environment_navigation_context is not None
            else (
                navigation_context_layout_target.process_id
                if navigation_context_layout_target is not None
                else None
            )
        ),
        thread_id=(
            environment_navigation_context.selected_thread_id
            if environment_navigation_context is not None
            else (
                navigation_context_layout_target.thread_id
                if navigation_context_layout_target is not None
                else None
            )
        ),
        thread_layout_id=(
            navigation_context_layout_target.thread_layout_id
            if navigation_context_layout_target is not None
            else None
        ),
        profile_key=_thread_layout_evidence_text(
            navigation_context_layout_target,
            "profile_key",
            "experience_profile_key",
            "environment_experience_profile_key",
        ),
        topology_seed_key=_thread_layout_evidence_text(
            navigation_context_layout_target,
            "topology_seed_key",
        ),
    )
    feature = InterfaceExperienceSessionFeatureDeclaration(
        feature_key=feature_key,
        config={
            "source": "interface_runtime_focus",
            "window_key": window_layout.window_key,
            "section_key": section_key,
            "observable_id": str(observable_id),
            "view_ref": view_ref,
        },
    )
    return InterfaceExperienceSessionHandoffRequest(
        actor=actor,
        scope=scope,
        feature=feature,
        idempotency_key=_request_idempotency_key(
            actor=actor,
            scope=scope,
            feature=feature,
        ),
        environment_admission=environment_admission,
        environment_session_join=environment_session_join,
        experience_actor_admission=experience_actor_admission,
        experience_identity_session_config_id=experience_identity_session_config_id,
        evidence=_request_evidence(
            runtime_state=runtime_state,
            navigation_context_layout_target=navigation_context_layout_target,
            environment_navigation_context=environment_navigation_context,
            focus_target=focus_target,
            representation=representation,
        ),
    )


def build_experience_session_view_frame_request_for_pane(
    *,
    namespace: str,
    authenticated: bool,
    interface_admitted: bool,
    transport_binding: InterfaceTransportBindingState | None,
    actor_context: InterfaceExperienceSessionActorContext | None = None,
    runtime_state: InterfaceRuntimeState | None,
    pane: InterfaceResolvedPaneDescriptor,
    active_focus: InterfaceRuntimeFocusState | None,
    section_representations: tuple[InterfaceRuntimeSectionRepresentationState, ...],
    environment_admission: EnvironmentActorAdmissionReceipt | None = None,
    environment_session_join: EnvironmentSessionJoinReceipt | None = None,
    environment_navigation_context: EnvironmentNavigationContextView | None = None,
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None,
    experience_identity_session_config_id: UUID | None = None,
    host_environment_id: UUID | None = None,
) -> ResolveExperienceSessionViewFrameRequest | None:
    _ = authenticated
    if (
        not interface_admitted
        or runtime_state is None
        or environment_admission is None
        or environment_session_join is None
        or environment_navigation_context is None
        or experience_actor_admission is None
        or experience_identity_session_config_id is None
    ):
        return None
    actor = actor_context or _actor_context_from_transport_binding(transport_binding)
    actor_id = actor.actor_id if actor is not None else None
    if actor is None or actor_id is None:
        return None
    view_ref = _optional_text(getattr(pane, "view_ref", None))
    experience_name = _experience_name_from_view_ref(view_ref)
    section_key = _optional_text(getattr(pane, "section_key", None))
    if view_ref is None or experience_name is None or section_key is None:
        return None

    navigation_context_layout_target = runtime_state.navigation_context_layout_target
    active_representation = (
        _active_representation(
            active_focus=active_focus,
            section_representations=section_representations,
        )
        if active_focus is not None
        else None
    )
    active_for_pane = _pane_matches_active_focus(
        pane=pane,
        active_focus=active_focus,
        representation=active_representation,
    )
    focus = active_focus if active_for_pane else None
    focus_target = focus.focus_target if focus is not None else None
    representation = active_representation if active_for_pane else None
    observable_id = _pane_observable_id(
        pane=pane,
        active_focus=focus,
        representation=representation,
    )
    if observable_id is None:
        return None

    scope = InterfaceExperienceSessionScope(
        namespace=namespace,
        experience_name=experience_name,
        view_ref=view_ref,
        window_key=str(getattr(pane, "window_key", "") or ""),
        layout_key=(
            (focus.layout_key if focus is not None else None)
            or _optional_text(getattr(pane, "layout_key", None))
        ),
        layout_config_id=(
            (focus.layout_config_id if focus is not None else None)
            or _as_uuid(getattr(pane, "layout_config_id", None))
            or (representation.layout_config_id if representation is not None else None)
        ),
        section_key=section_key,
        layout_config_section_config_id=(
            (
                focus.layout_config_section_config_id
                if focus is not None
                else None
            )
            or _as_uuid(getattr(pane, "layout_config_section_config_id", None))
            or (
                representation.layout_config_section_config_id
                if representation is not None
                else None
            )
        ),
        layout_section_id=(
            (focus.layout_section_id if focus is not None else None)
            or _as_uuid(getattr(pane, "layout_section_id", None))
        ),
        section_focus_scope_id=(
            (focus.section_focus_scope_id if focus is not None else None)
            or _as_uuid(getattr(pane, "section_focus_scope_id", None))
        ),
        focus_scope_id=(
            (focus.focus_scope_id if focus is not None else None)
            or _as_uuid(getattr(pane, "focus_scope_id", None))
        ),
        focus_id=focus.focus_id if focus is not None else None,
        observable_id=observable_id,
        projection_view_key=_optional_text(getattr(pane, "projection_view_key", None)),
        environment_session_id=(
            environment_navigation_context.environment_session_id
            or environment_session_join.environment_session_id
        ),
        environment_navigation_context_id=(
            environment_navigation_context.environment_navigation_context_id
        ),
        section_graph_binding_key=(
            _optional_text(getattr(pane, "section_graph_binding_key", None))
            or (
                representation.section_graph_binding_key
                if representation is not None
                else None
            )
        ),
        projection_experience_graph_identity_id=(
            _as_uuid(getattr(pane, "projection_experience_graph_identity_id", None))
            or (
                representation.projection_experience_graph_identity_id
                if representation is not None
                else None
            )
            or _focus_projection_experience_graph_identity_id(focus_target)
        ),
        object_projection_graph_identity_id=(
            _as_uuid(getattr(pane, "object_projection_graph_identity_id", None))
            or (
                representation.object_projection_graph_identity_id
                if representation is not None
                else None
            )
            or _focus_object_projection_graph_identity_id(focus_target)
        ),
        object_instance_graph_branch_id=(
            focus_target.object_instance_graph_branch_id
            if focus_target is not None
            else None
        ),
        projection_hash=(
            focus_target.projection_hash
            if focus_target is not None
            else environment_navigation_context.projection_hash
        ),
        environment_id=_scope_environment_id(
            runtime_state=runtime_state,
            navigation_context_layout_target=navigation_context_layout_target,
            environment_navigation_context=environment_navigation_context,
            host_environment_id=host_environment_id,
        ),
        process_id=(
            environment_navigation_context.selected_process_id
            or (
                navigation_context_layout_target.process_id
                if navigation_context_layout_target is not None
                else None
            )
        ),
        thread_id=(
            environment_navigation_context.selected_thread_id
            or (
                navigation_context_layout_target.thread_id
                if navigation_context_layout_target is not None
                else None
            )
        ),
        thread_layout_id=(
            navigation_context_layout_target.thread_layout_id
            if navigation_context_layout_target is not None
            else None
        ),
        profile_key=_thread_layout_evidence_text(
            navigation_context_layout_target,
            "profile_key",
            "experience_profile_key",
            "environment_experience_profile_key",
        ),
        topology_seed_key=_thread_layout_evidence_text(
            navigation_context_layout_target,
            "topology_seed_key",
        ),
        source_kind="interface_runtime_pane",
    )
    pane_state_key = _pane_state_key_for_scope(scope=scope, pane=pane)
    return ResolveExperienceSessionViewFrameRequest(
        session_scope=_experience_session_scope(scope=scope, actor_id=actor_id),
        actor_context=_experience_actor_context(actor),
        environment_admission=environment_admission,
        environment_session_join=environment_session_join,
        experience_actor_admission=experience_actor_admission,
        experience_identity_session_config_id=experience_identity_session_config_id,
        environment_attention=ExperienceSessionAttentionResolutionRequest(
            environment_navigation_context_id=(
                environment_navigation_context.environment_navigation_context_id
            ),
            expected_focus_scope_id=scope.focus_scope_id,
            expected_projection_hash=scope.projection_hash,
            include_attention_session=True,
            include_transition_list=True,
            transition_limit=50,
            metadata={
                "source": "interface_runtime_pane_view_state_watch",
                "pane_state_key": pane_state_key,
                "active_for_pane": active_for_pane,
            },
        ),
        idempotency_key=_request_idempotency_key(
            actor=actor,
            scope=scope,
            feature=InterfaceExperienceSessionFeatureDeclaration(
                feature_key="view_state_watch",
                reason="interface_runtime_pane",
            ),
        ),
        evidence={
            "source": "interface_runtime_pane_view_state_watch",
            "pane_state_key": pane_state_key,
            "active_for_pane": active_for_pane,
        },
    )


def experience_session_handoff_blocker(
    request: InterfaceExperienceSessionHandoffRequest,
) -> str | None:
    admission = request.environment_admission
    if admission is None:
        return "environment_admission_required"
    if not admission.accepted or admission.status != "admitted":
        return "environment_admission_not_admitted"
    if not admission.bindings:
        return "environment_admission_has_no_role_bindings"
    if admission.actor_id != request.actor.actor_id:
        return "environment_admission_actor_scope_mismatch"
    if admission.environment_id != request.scope.environment_id:
        return "environment_admission_environment_scope_mismatch"
    session_join = request.environment_session_join
    if session_join is None:
        return "environment_session_join_required"
    if not session_join.accepted or session_join.status not in {"joined", "started"}:
        return "environment_session_join_not_accepted"
    if session_join.actor_id != request.actor.actor_id:
        return "environment_session_actor_scope_mismatch"
    if session_join.environment_id != request.scope.environment_id:
        return "environment_session_environment_scope_mismatch"
    if session_join.environment_session_id != request.scope.environment_session_id:
        return "environment_session_id_scope_mismatch"
    actor_admission = request.experience_actor_admission
    if actor_admission is None:
        return "experience_actor_admission_required"
    if not actor_admission.accepted or actor_admission.status != "admitted":
        return "experience_actor_admission_not_admitted"
    if actor_admission.actor_id != request.actor.actor_id:
        return "experience_actor_admission_actor_scope_mismatch"
    if actor_admission.experience_name != request.scope.experience_name:
        return "experience_actor_admission_experience_scope_mismatch"
    if not actor_admission.bindings:
        return "experience_actor_admission_has_no_role_bindings"
    if request.experience_identity_session_config_id is None:
        return "experience_identity_session_config_required"
    if request.scope.environment_navigation_context_id is None:
        return "environment_navigation_context_required"
    return None


def environment_admission_blocker(
    request: InterfaceExperienceSessionHandoffRequest,
) -> str | None:
    return experience_session_handoff_blocker(request)


def handoff_state_from_blocker(
    *,
    request: InterfaceExperienceSessionHandoffRequest,
    blocker: str,
) -> InterfaceHostServiceExperienceSessionHandoffState:
    return InterfaceHostServiceExperienceSessionHandoffState(
        status="blocked",
        feature_key=request.feature.feature_key,
        experience_name=request.scope.experience_name,
        view_ref=request.scope.view_ref,
        actor_id=request.actor.actor_id,
        admitted=False,
        feature_enabled=False,
        idempotency_key=request.idempotency_key,
        error=blocker,
        evidence={
            "source": "interface_runtime_focus",
            "blocker": blocker,
            "environment_admission_required": True,
        },
    )


def handoff_state_from_result(
    result: InterfaceExperienceSessionHandoffResult,
) -> InterfaceHostServiceExperienceSessionHandoffState:
    request = result.request
    return InterfaceHostServiceExperienceSessionHandoffState(
        status=result.status,
        feature_key=request.feature.feature_key,
        experience_name=request.scope.experience_name,
        view_ref=request.scope.view_ref,
        actor_id=request.actor.actor_id,
        experience_session_id=result.experience_session_id,
        identity_session_id=result.identity_session_id,
        identity_member_id=result.identity_member_id,
        actor_admission_id=result.actor_admission_id,
        feature_lease_id=result.feature_lease_id,
        admitted=result.admitted,
        feature_enabled=result.feature_enabled,
        idempotency_key=request.idempotency_key,
        error=result.error,
        evidence=dict(result.evidence),
    )


def handoff_state_from_failure(
    *,
    request: InterfaceExperienceSessionHandoffRequest,
    error: BaseException,
) -> InterfaceHostServiceExperienceSessionHandoffState:
    return InterfaceHostServiceExperienceSessionHandoffState(
        status="failed",
        feature_key=request.feature.feature_key,
        experience_name=request.scope.experience_name,
        view_ref=request.scope.view_ref,
        actor_id=request.actor.actor_id,
        admitted=False,
        feature_enabled=False,
        idempotency_key=request.idempotency_key,
        error=str(error),
        evidence={
            "source": "interface_runtime_focus",
            "error_type": type(error).__name__,
        },
    )


def narration_state_from_result(
    result: InterfaceExperienceSessionHandoffResult,
) -> InterfaceHostServiceExperienceSessionNarrationState:
    request = result.request
    return InterfaceHostServiceExperienceSessionNarrationState(
        status=result.status,
        feature_key=request.feature.feature_key,
        experience_name=request.scope.experience_name,
        view_ref=request.scope.view_ref,
        actor_id=request.actor.actor_id,
        feature_lease_id=result.feature_lease_id,
        error=result.error,
        evidence=dict(result.evidence),
    )


def narration_state_from_blocker(
    *,
    request: InterfaceExperienceSessionHandoffRequest,
    blocker: str,
) -> InterfaceHostServiceExperienceSessionNarrationState:
    return InterfaceHostServiceExperienceSessionNarrationState(
        status="blocked",
        feature_key=request.feature.feature_key,
        experience_name=request.scope.experience_name,
        view_ref=request.scope.view_ref,
        actor_id=request.actor.actor_id,
        error=blocker,
        evidence={
            "source": "interface_experience_session_narration",
            "blocker": blocker,
        },
    )


def narration_state_from_status_response(
    *,
    request: InterfaceExperienceSessionHandoffRequest,
    response: object,
) -> InterfaceHostServiceExperienceSessionNarrationState:
    receipt = getattr(response, "receipt", None)
    lease = getattr(receipt, "feature_lease", None)
    health = _object_mapping(getattr(lease, "health_payload", None))
    events = tuple(
        _narration_event_state(item) for item in _mapping_sequence(health.get("events"))
    )
    last_commit_id = _as_uuid(health.get("last_commit_id"))
    return InterfaceHostServiceExperienceSessionNarrationState(
        status=str(getattr(receipt, "status", None) or getattr(response, "status", "")),
        feature_key=(
            str(getattr(lease, "feature_key", None))
            if getattr(lease, "feature_key", None) is not None
            else request.feature.feature_key
        ),
        experience_name=request.scope.experience_name,
        view_ref=request.scope.view_ref,
        actor_id=request.actor.actor_id,
        feature_lease_id=getattr(lease, "lease_key", None),
        event_count=_int_value(health.get("event_count")) or len(events),
        last_commit_id=last_commit_id,
        events=events,
        error=getattr(response, "error", None) or getattr(receipt, "error", None),
        evidence={
            "provider": "experience_sdk",
            "receipt": _object_mapping(getattr(receipt, "evidence", None)),
            "health": health,
        },
    )


def narration_state_from_failure(
    *,
    request: InterfaceExperienceSessionHandoffRequest,
    error: BaseException,
) -> InterfaceHostServiceExperienceSessionNarrationState:
    return InterfaceHostServiceExperienceSessionNarrationState(
        status="failed",
        feature_key=request.feature.feature_key,
        experience_name=request.scope.experience_name,
        view_ref=request.scope.view_ref,
        actor_id=request.actor.actor_id,
        error=str(error),
        evidence={
            "source": "interface_experience_session_narration",
            "error_type": type(error).__name__,
        },
    )


def _experience_session_handoff_scope(
    request: InterfaceExperienceSessionHandoffRequest,
) -> ExperienceSessionHandoffScope:
    return _experience_session_scope(scope=request.scope, actor_id=request.actor.actor_id)


def _experience_session_scope(
    *,
    scope: InterfaceExperienceSessionScope,
    actor_id: UUID,
) -> ExperienceSessionHandoffScope:
    return ExperienceSessionHandoffScope(
        namespace=scope.namespace,
        experience_name=scope.experience_name,
        profile_key=scope.profile_key,
        environment_id=scope.environment_id,
        actor_id=actor_id,
        process_id=scope.process_id,
        thread_id=scope.thread_id,
        environment_session_id=scope.environment_session_id,
        workspace_session_id=(
            str(scope.thread_layout_id) if scope.thread_layout_id is not None else None
        ),
        projection_hash=scope.projection_hash,
        view_ref=scope.view_ref,
        window_key=scope.window_key,
        layout_key=scope.layout_key,
        layout_config_id=scope.layout_config_id,
        section_key=scope.section_key,
        layout_config_section_config_id=scope.layout_config_section_config_id,
        layout_section_id=scope.layout_section_id,
        section_focus_scope_id=scope.section_focus_scope_id,
        focus_scope_id=scope.focus_scope_id,
        focus_id=scope.focus_id,
        observable_id=scope.observable_id,
        projection_view_key=scope.projection_view_key,
        section_graph_binding_key=scope.section_graph_binding_key,
        projection_experience_graph_identity_id=(
            scope.projection_experience_graph_identity_id
        ),
        object_projection_graph_identity_id=scope.object_projection_graph_identity_id,
        object_instance_graph_branch_id=scope.object_instance_graph_branch_id,
        topology_seed_key=scope.topology_seed_key,
        source_kind=scope.source_kind,
        evidence=cast(
            JsonObject,
            {
                "source": "interface_experience_session_handoff_scope",
                "environment_session_id": (
                    str(scope.environment_session_id)
                    if scope.environment_session_id is not None
                    else None
                ),
                "environment_navigation_context_id": (
                    str(scope.environment_navigation_context_id)
                    if scope.environment_navigation_context_id is not None
                    else None
                ),
                "thread_layout_id": (
                    str(scope.thread_layout_id)
                    if scope.thread_layout_id is not None
                    else None
                ),
            },
        ),
    )


def _experience_session_handoff_actor_context(
    request: InterfaceExperienceSessionHandoffRequest,
) -> ExperienceSessionHandoffActorContext:
    return _experience_actor_context(request.actor)


def _experience_actor_context(
    actor: InterfaceExperienceSessionActorContext,
) -> ExperienceSessionHandoffActorContext:
    return ExperienceSessionHandoffActorContext(
        status="ready",
        kind=actor.actor_kind,
        source=actor.actor_source,
        actor_id=actor.actor_id,
        identity_id=actor.interface_system_identity_id,
        provider_key="interface",
        provider_session_id=(
            str(actor.interface_session_id)
            if actor.interface_session_id is not None
            else None
        ),
        execution_id=actor.session_label,
        evidence=cast(
            JsonObject,
            {
                "interface_id": (
                    str(actor.interface_id) if actor.interface_id is not None else None
                ),
                "actor_kind": actor.actor_kind,
                "actor_source": actor.actor_source,
                "interface_system_identity_id": (
                    str(actor.interface_system_identity_id)
                    if actor.interface_system_identity_id is not None
                    else None
                ),
                "interface_session_id": (
                    str(actor.interface_session_id)
                    if actor.interface_session_id is not None
                    else None
                ),
                "capabilities": list(actor.capabilities),
            },
        ),
    )


def _actor_context_from_transport_binding(
    transport_binding: InterfaceTransportBindingState | None,
) -> InterfaceExperienceSessionActorContext | None:
    actor_id = _as_uuid(getattr(transport_binding, "actor_id", None))
    if actor_id is None:
        return None
    return InterfaceExperienceSessionActorContext(
        actor_id=actor_id,
        actor_kind="agent_operator",
        actor_source="transport_binding",
        interface_id=_as_uuid(getattr(transport_binding, "interface_id", None)),
        interface_session_id=_as_uuid(
            getattr(transport_binding, "interface_session_id", None)
        ),
        session_label=_optional_text(getattr(transport_binding, "session_label", None)),
        capabilities=tuple(
            str(item)
            for item in tuple(getattr(transport_binding, "capabilities", ()) or ())
            if str(item).strip()
        ),
    )


def _experience_session_handoff_feature(
    request: InterfaceExperienceSessionHandoffRequest,
) -> ExperienceSessionHandoffFeatureSpec:
    return ExperienceSessionHandoffFeatureSpec(
        feature_key=request.feature.feature_key,
        reason=request.feature.reason,
        lease_key=request.idempotency_key,
        config=cast(JsonObject, _jsonish_mapping(request.feature.config)),
    )


def _interface_handoff_result_from_experience_response(
    *,
    request: InterfaceExperienceSessionHandoffRequest,
    response: object,
) -> InterfaceExperienceSessionHandoffResult:
    receipt = getattr(response, "receipt", None)
    feature_lease = getattr(receipt, "feature_lease", None)
    identity_evidence = getattr(receipt, "identity_evidence", None)
    experience_identity_session = (
        getattr(identity_evidence, "experience_identity_session", None)
        if identity_evidence is not None
        else None
    )
    experience_identity_member = (
        getattr(identity_evidence, "experience_identity_member", None)
        if identity_evidence is not None
        else None
    )
    evidence = {
        "provider": "experience_sdk",
        **_object_mapping(getattr(response, "evidence", None)),
        "receipt": _object_mapping(getattr(receipt, "evidence", None)),
    }
    return InterfaceExperienceSessionHandoffResult(
        request=request,
        status=str(getattr(receipt, "status", None) or getattr(response, "status", "")),
        admitted=bool(
            getattr(receipt, "admitted", getattr(response, "accepted", False))
        ),
        feature_enabled=bool(
            getattr(receipt, "feature_enabled", getattr(response, "accepted", False))
        ),
        identity_session_id=_as_uuid(
            getattr(experience_identity_session, "session_id", None)
        ),
        identity_member_id=_as_uuid(
            getattr(experience_identity_member, "session_member_id", None)
        ),
        feature_lease_id=getattr(feature_lease, "lease_key", None),
        error=getattr(response, "error", None) or getattr(receipt, "error", None),
        evidence=evidence,
    )


def _active_representation(
    *,
    active_focus: InterfaceRuntimeFocusState,
    section_representations: tuple[InterfaceRuntimeSectionRepresentationState, ...],
) -> InterfaceRuntimeSectionRepresentationState | None:
    section_key = _optional_text(active_focus.section_key)
    observable_id = _as_uuid(active_focus.observable_id)
    if section_key is None or observable_id is None:
        return None
    candidates = tuple(
        item
        for item in section_representations
        if item.section_key.strip().casefold() == section_key.casefold()
        and item.observable_id == observable_id
    )
    if not candidates:
        focus_target = active_focus.focus_target
        object_projection_graph_identity_id = _focus_object_projection_graph_identity_id(
            focus_target
        )
        if object_projection_graph_identity_id is not None:
            candidates = tuple(
                item
                for item in section_representations
                if item.section_key.strip().casefold() == section_key.casefold()
                and item.object_projection_graph_identity_id
                == object_projection_graph_identity_id
            )
    if not candidates:
        return None
    active = next((item for item in candidates if item.is_active), None)
    return active or candidates[0]


def _pane_matches_active_focus(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    active_focus: InterfaceRuntimeFocusState | None,
    representation: InterfaceRuntimeSectionRepresentationState | None,
) -> bool:
    if active_focus is None:
        return False
    section_key = _optional_text(active_focus.section_key)
    pane_section_key = _optional_text(getattr(pane, "section_key", None))
    if section_key is None or pane_section_key is None:
        return False
    if section_key.casefold() != pane_section_key.casefold():
        return False
    pane_view_ref = _optional_text(getattr(pane, "view_ref", None))
    representation_view_ref = (
        _optional_text(representation.view_ref) if representation is not None else None
    )
    if pane_view_ref is not None and representation_view_ref is not None:
        return pane_view_ref == representation_view_ref
    pane_observable_id = _as_uuid(
        getattr(pane, "object_projection_graph_observable_id", None)
    )
    if pane_observable_id is not None and active_focus.observable_id is not None:
        return pane_observable_id == active_focus.observable_id
    return True


def _pane_observable_id(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    active_focus: InterfaceRuntimeFocusState | None,
    representation: InterfaceRuntimeSectionRepresentationState | None,
) -> UUID | None:
    return (
        _as_uuid(getattr(pane, "object_projection_graph_observable_id", None))
        or (representation.observable_id if representation is not None else None)
        or (active_focus.observable_id if active_focus is not None else None)
        or _as_uuid(getattr(pane, "projection_experience_view_instance_id", None))
    )


def _pane_state_key_for_scope(
    *,
    scope: InterfaceExperienceSessionScope,
    pane: InterfaceResolvedPaneDescriptor,
) -> str:
    return ":".join(
        (
            scope.window_key,
            scope.layout_key or "",
            scope.section_key,
            getattr(pane, "pane_kind", None) or "",
            str(getattr(pane, "pane_config_id", None) or ""),
            getattr(pane, "state_projection_hash", None) or "",
        )
    )


def _experience_name_from_view_ref(view_ref: str | None) -> str | None:
    normalized = _optional_text(view_ref)
    if normalized is None:
        return None
    value = normalized.split(".", 1)[0].strip()
    return value or None


def _scope_environment_id(
    *,
    runtime_state: InterfaceRuntimeState,
    navigation_context_layout_target: (
        InterfaceNavigationContextLayoutTargetState | None
    ),
    environment_navigation_context: EnvironmentNavigationContextView | None,
    host_environment_id: UUID | None,
) -> UUID | None:
    if environment_navigation_context is not None:
        return environment_navigation_context.environment_id
    if navigation_context_layout_target is not None:
        return navigation_context_layout_target.environment_id
    if host_environment_id is not None:
        return host_environment_id
    return runtime_state.backend.environment_id


def _thread_layout_evidence_text(
    navigation_context_layout_target: (
        InterfaceNavigationContextLayoutTargetState | None
    ),
    *keys: str,
) -> str | None:
    if navigation_context_layout_target is None:
        return None
    evidence = navigation_context_layout_target.evidence
    for key in keys:
        value = evidence.get(key)
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _request_evidence(
    *,
    runtime_state: InterfaceRuntimeState,
    navigation_context_layout_target: (
        InterfaceNavigationContextLayoutTargetState | None
    ),
    environment_navigation_context: EnvironmentNavigationContextView | None,
    focus_target: InterfaceAttentionFocusTargetState | None,
    representation: InterfaceRuntimeSectionRepresentationState,
) -> dict[str, object]:
    evidence: dict[str, object] = {
        "source": "interface_runtime_focus",
        "runtime_backend_available": runtime_state.backend.available,
        "representation_id": str(representation.representation_id),
        "pane_kind": representation.pane_kind,
        "pane_name": representation.pane_name,
    }
    if navigation_context_layout_target is not None:
        evidence["thread_layout_source_kind"] = (
            navigation_context_layout_target.source_kind
        )
        evidence["thread_layout_evidence"] = _jsonish_mapping(
            navigation_context_layout_target.evidence
        )
    if environment_navigation_context is not None:
        evidence["environment_navigation_context_id"] = str(
            environment_navigation_context.environment_navigation_context_id
        )
        evidence["environment_session_id"] = str(
            environment_navigation_context.environment_session_id
        )
    if focus_target is not None:
        evidence["focus_target_kind"] = focus_target.kind
        evidence["focus_target_type"] = focus_target.target_type
    return evidence


def _request_idempotency_key(
    *,
    actor: InterfaceExperienceSessionActorContext,
    scope: InterfaceExperienceSessionScope,
    feature: InterfaceExperienceSessionFeatureDeclaration,
) -> str:
    raw = "|".join(
        (
            str(actor.actor_id),
            str(actor.interface_session_id or ""),
            scope.namespace,
            scope.experience_name,
            scope.view_ref,
            str(scope.environment_id or ""),
            str(scope.process_id or ""),
            str(scope.thread_id or ""),
            str(scope.thread_layout_id or ""),
            scope.window_key,
            str(scope.layout_config_id or ""),
            scope.layout_key or "",
            scope.section_key,
            str(scope.observable_id),
            feature.feature_key,
        )
    )
    return f"interface-experience-session:{sha256(raw.encode('utf-8')).hexdigest()}"


def _jsonish_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {str(key): _jsonish_value(item) for key, item in value.items()}


def _jsonish_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonish_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_jsonish_value(item) for item in value]
    return value


def _object_mapping(value: object | None) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return _jsonish_mapping(value)
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="json", exclude_none=True)
        if isinstance(payload, Mapping):
            return _jsonish_mapping(payload)
    if isinstance(value, dict):
        return _jsonish_mapping(value)
    return {"value": _jsonish_value(value)}


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _narration_event_state(
    value: Mapping[str, object],
) -> InterfaceExperienceSessionNarrationEventState:
    return InterfaceExperienceSessionNarrationEventState(
        commit_id=_as_uuid(value.get("commit_id")),
        branch_id=_as_uuid(value.get("branch_id")),
        projection_hash=_optional_text(value.get("projection_hash")),
        narration_lines=tuple(
            str(item)
            for item in tuple(value.get("narration_lines") or ())
            if str(item).strip()
        ),
        operation_label=_optional_text(value.get("operation_label")),
        graph_hash_post=_optional_text(value.get("graph_hash_post")),
        object_instance_graph_identity_id=_as_uuid(
            value.get("object_instance_graph_identity_id")
        ),
        object_instance_graph_branch_id=_as_uuid(
            value.get("object_instance_graph_branch_id")
        ),
        object_instance_graph_commit_id=_as_uuid(
            value.get("object_instance_graph_commit_id")
        ),
        projection_experience_graph_identity_id=_as_uuid(
            value.get("projection_experience_graph_identity_id")
        ),
        object_projection_graph_identity_id=_as_uuid(
            value.get("object_projection_graph_identity_id")
        ),
        semantics=_object_mapping(value.get("semantics")),
        evidence=_object_mapping(value.get("evidence")),
    )


def _int_value(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _focus_projection_experience_graph_identity_id(
    focus_target: InterfaceAttentionFocusTargetState | None,
) -> UUID | None:
    if focus_target is None:
        return None
    return focus_target.projection_experience_graph_identity_id


def _focus_object_projection_graph_identity_id(
    focus_target: InterfaceAttentionFocusTargetState | None,
) -> UUID | None:
    if focus_target is None:
        return None
    return focus_target.object_projection_graph_identity_id


def _as_uuid(value: object | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "EXPERIENCE_SESSION_NARRATOR_FEATURE_KEY",
    "ExperienceSessionHandoffProvider",
    "ExperienceSdkSessionHandoffProvider",
    "REACTIVITY_TRANSITION_DISPATCH_FEATURE_KEY",
    "build_experience_sdk_session_handoff_provider",
    "build_experience_session_handoff_request",
    "build_experience_session_view_frame_request_for_pane",
    "environment_admission_blocker",
    "handoff_state_from_blocker",
    "handoff_state_from_failure",
    "handoff_state_from_result",
    "narration_state_from_blocker",
    "narration_state_from_failure",
    "narration_state_from_result",
    "narration_state_from_status_response",
]

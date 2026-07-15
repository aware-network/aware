from __future__ import annotations

import asyncio
import hashlib
import json
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar, cast
from uuid import UUID

from aware_interface import (
    InterfaceBackendState,
    InterfaceGateState,
    InterfaceGateStep,
    InterfaceMaterializedPaneState,
    InterfaceRuntimeFocusState,
    InterfaceRuntimePaneRenderSpecState,
    InterfaceRuntimeSectionRepresentationState,
    InterfaceRuntimeLayoutState,
    InterfaceRuntimeWindowState,
    InterfaceRuntimeWindowNavigationContextState,
    InterfaceResolvedPaneDescriptor,
    InterfaceResolvedView,
    InterfaceRuntimeState,
    InterfaceWindowLayoutSectionState,
    InterfaceWindowLayoutState,
)
from aware_code.types import JsonObject
from aware_code.types.json import JsonValue
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActionRequest,
    InterfaceActionResponse,
    InterfaceApiEventNotification,
    InterfaceApiStreamClosedNotification,
    InterfaceAdmitEnvironmentActorRequest,
    InterfaceAdmitEnvironmentActorResponse,
    InterfaceApplyAttentionLayoutTransitionRequest,
    InterfaceApplyAttentionLayoutTransitionResponse,
    InterfaceApplyAttentionLayoutTopologyTransitionRequest,
    InterfaceApplyAttentionLayoutTopologyTransitionResponse,
    InterfaceFollowRequest,
    InterfaceFollowResponse,
    InterfaceActivateRuntimeFocusRequest,
    InterfaceActivateRuntimeFocusResponse,
    InterfaceInvokeApiRequest,
    InterfaceInvokeApiResponse,
    InterfaceJoinEnvironmentSessionRequest,
    InterfaceJoinEnvironmentSessionResponse,
    InterfaceSelectEnvironmentNavigationTargetRequest,
    InterfaceSelectEnvironmentNavigationTargetResponse,
    InterfaceControlPlaneOperation,
    InterfaceControlPlaneNotification,
    InterfaceControlPlaneRequest,
    InterfaceControlPlaneResponse,
    InterfaceEnterEnvironmentRequest,
    InterfaceEnterEnvironmentResponse,
    InterfaceEnterAppScreenRequest,
    InterfaceEnterAppScreenResponse,
    InterfaceReportRendererCapabilitiesRequest,
    InterfaceReportRendererCapabilitiesResponse,
    InterfaceRequestWindowLayoutRequest,
    InterfaceRequestWindowLayoutResponse,
    InterfaceResolveExperienceLensRequest,
    InterfaceResolveExperienceLensResponse,
    InterfaceSelectRuntimeLayoutRequest,
    InterfaceSelectRuntimeLayoutResponse,
    InterfaceStateNotification,
    InterfaceStreamApiRequest,
    InterfaceStreamApiResponse,
    InterfaceStatusRequest,
    InterfaceStatusResponse,
    InterfaceSelectStepRequest,
    InterfaceSelectProfileRequest,
    InterfaceSelectProfileResponse,
    InterfaceSelectStepResponse,
    InterfaceStopRequest,
    InterfaceStopResponse,
    InterfaceSyncViewStateCursorRequest,
    InterfaceSyncViewStateCursorResponse,
    NamespaceEnsureRequest,
    NamespaceEnsureResponse,
    NamespaceListRequest,
    NamespaceListResponse,
    PingRequest,
    PingResponse,
)
from aware_interface_service_dto.comms.models.hosted_interface_namespace import (
    HostedInterfaceNamespace,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceAllowedAction as ApiInterfaceAllowedAction,
    InterfaceControlPlaneProfileState as ApiInterfaceControlPlaneProfileState,
    InterfaceControlPlaneProfilesState as ApiInterfaceControlPlaneProfilesState,
    InterfaceBackendState as ApiInterfaceBackendState,
    InterfaceControlPlaneOrchestrationStep as ApiInterfaceControlPlaneOrchestrationStep,
    InterfaceControlPlaneTraceEntry as ApiInterfaceControlPlaneTraceEntry,
    InterfaceControlPlaneTraceGroup as ApiInterfaceControlPlaneTraceGroup,
    InterfaceControlPlaneWorkspaceState as ApiInterfaceControlPlaneWorkspaceState,
    InterfaceCurrentScreen as ApiInterfaceCurrentScreen,
    InterfaceGateState as ApiInterfaceGateState,
    InterfaceGateStep as ApiInterfaceGateStep,
    InterfaceHostRecoveryCapabilityState as ApiInterfaceHostRecoveryCapabilityState,
    InterfaceEnvironmentAdmissionRoleBindingState as ApiInterfaceEnvironmentAdmissionRoleBindingState,
    InterfaceEnvironmentAdmissionRoleEligibilityState as ApiInterfaceEnvironmentAdmissionRoleEligibilityState,
    InterfaceEnvironmentAdmissionState as ApiInterfaceEnvironmentAdmissionState,
    InterfaceEnvironmentNavigationState as ApiInterfaceEnvironmentNavigationState,
    InterfaceEnvironmentSessionState as ApiInterfaceEnvironmentSessionState,
    InterfaceExperienceLensActionState as ApiInterfaceExperienceLensActionState,
    InterfaceExperienceLensState as ApiInterfaceExperienceLensState,
    InterfaceAppScreenState as ApiInterfaceAppScreenState,
    InterfaceHostState,
    InterfaceHostedServiceRequirementState as ApiInterfaceHostedServiceRequirementState,
    InterfaceHostedRuntimeServiceState as ApiInterfaceHostedRuntimeServiceState,
    InterfaceHostedRuntimeState as ApiInterfaceHostedRuntimeState,
    InterfaceHostedServicesState as ApiInterfaceHostedServicesState,
    InterfaceLaneSyncState,
    InterfaceLocalNodeRuntimeState as ApiInterfaceLocalNodeRuntimeState,
    InterfaceLocalServiceHostState as ApiInterfaceLocalServiceHostState,
    InterfaceMaterializedPaneState as ApiInterfaceMaterializedPaneState,
    InterfaceOperationState as ApiInterfaceOperationState,
    InterfaceOperationTargetState as ApiInterfaceOperationTargetState,
    InterfaceRendererCacheCapabilityState as ApiInterfaceRendererCacheCapabilityState,
    InterfaceRendererCapabilitiesState as ApiInterfaceRendererCapabilitiesState,
    InterfaceRendererPanePackageCapabilityState as ApiInterfaceRendererPanePackageCapabilityState,
    InterfaceRendererViewCapabilityState as ApiInterfaceRendererViewCapabilityState,
    InterfaceHostViewStateCursorState as ApiInterfaceHostViewStateCursorState,
    InterfaceHostViewStateDigestEntryState as ApiInterfaceHostViewStateDigestEntryState,
    InterfaceAttentionFocusTargetState as ApiInterfaceAttentionFocusTargetState,
    InterfaceResolvedView as ApiInterfaceResolvedView,
    InterfaceResolvedPaneDescriptor as ApiInterfaceResolvedPaneDescriptor,
    InterfaceRuntimeFocusState as ApiInterfaceRuntimeFocusState,
    InterfaceRuntimePaneRenderSpecState as ApiInterfaceRuntimePaneRenderSpecState,
    InterfaceRuntimePackageApiState as ApiInterfaceRuntimePackageApiState,
    InterfaceRuntimePackageState as ApiInterfaceRuntimePackageState,
    InterfaceRuntimeSectionRepresentationState as ApiInterfaceRuntimeSectionRepresentationState,
    InterfaceRuntimeLayoutState as ApiInterfaceRuntimeLayoutState,
    InterfaceRuntimeWindowState as ApiInterfaceRuntimeWindowState,
    InterfaceRuntimeWindowNavigationContextState as ApiInterfaceRuntimeWindowNavigationContextState,
    InterfaceRuntimeState as ApiInterfaceRuntimeState,
    InterfaceWindowLayoutSectionState as ApiInterfaceWindowLayoutSectionState,
    InterfaceWindowLayoutState as ApiInterfaceWindowLayoutState,
    InterfaceSelectedSemanticPackageState as ApiInterfaceSelectedSemanticPackageState,
    InterfaceSelectedWorkspaceState as ApiInterfaceSelectedWorkspaceState,
    InterfaceTransportState,
    InterfaceWorkspaceCandidate as ApiInterfaceWorkspaceCandidate,
    InterfaceWorkspaceCommittedSemanticPackageFamilyState as ApiInterfaceWorkspaceCommittedSemanticPackageFamilyState,
    InterfaceWorkspaceCommittedSemanticPackageState as ApiInterfaceWorkspaceCommittedSemanticPackageState,
    InterfaceWorkspaceDiscoveryState as ApiInterfaceWorkspaceDiscoveryState,
    InterfaceWorkspaceLifecycleState as ApiInterfaceWorkspaceLifecycleState,
    InterfaceWorkspaceMaterializationStateRef as ApiInterfaceWorkspaceMaterializationStateRef,
    InterfaceWorkspaceSemanticObjectConfigGraphPreviewState as ApiInterfaceWorkspaceSemanticPreviewState,
    InterfaceWorkspaceSemanticPackageState as ApiInterfaceWorkspaceSemanticPackageState,
    InterfaceWorkspaceSemanticSourceState as ApiInterfaceWorkspaceSemanticState,
)
from aware_service_service_dto.comms.models.service import (
    RequestStatus,
    StreamLifecycle,
)
from aware_service_runtime.duplex import (
    ServiceDuplexStreamEventEnvelope,
    ServiceDuplexStreamEventKind,
)
from aware_service_runtime.duplex_client import ServiceHostDuplexRequestHandle
from aware_utils.logging import logger

from aware_interface_service.app import (
    InterfaceHostServiceConfig,
    build_namespaced_service_config,
)
from aware_interface_service.dogfood_persistence import InterfaceHostDogfoodStore
from aware_interface_service.models import (
    InterfaceEnvironmentAdmissionRoleBindingState,
    InterfaceEnvironmentAdmissionRoleEligibilityState,
    InterfaceEnvironmentAdmissionState,
    InterfaceEnvironmentNavigationState,
    InterfaceEnvironmentSessionState,
    InterfaceExperienceLensActionState,
    InterfaceExperienceLensState,
    InterfaceHostedNamespaceState,
    InterfaceHostServiceAllowedAction,
    InterfaceHostServiceControlPlaneProfileState,
    InterfaceHostServiceControlPlaneProfilesState,
    InterfaceHostServiceControlPlaneOrchestrationStep,
    InterfaceHostServiceControlPlaneTraceEntry,
    InterfaceHostServiceControlPlaneTraceGroup,
    InterfaceHostServiceControlPlaneWorkspaceState,
    InterfaceHostServiceCurrentScreen,
    InterfaceHostServiceHostedServiceRequirementState,
    InterfaceHostServiceHostedRuntimeServiceState,
    InterfaceHostServiceHostedRuntimeState,
    InterfaceHostServiceHostedServicesState,
    InterfaceHostServiceLaneSyncState,
    InterfaceHostServiceLocalNodeRuntimeState,
    InterfaceHostServiceLocalServiceHostState,
    InterfaceHostServiceOperationState,
    InterfaceHostServiceOperationTargetState,
    InterfaceHostServiceRecoveryCapabilityState,
    InterfaceHostServiceRendererCacheCapabilityState,
    InterfaceHostServiceRendererCapabilitiesState,
    InterfaceHostServiceRendererPanePackageCapabilityState,
    InterfaceHostServiceRendererViewCapabilityState,
    InterfaceHostServiceSelectedSemanticPackageState,
    InterfaceHostServiceSelectedWorkspaceState,
    InterfaceHostServiceState,
    InterfaceHostServiceTransportState,
    InterfaceHostServiceWorkspaceMaterializationStateRef,
    InterfaceHostServiceWorkspaceCandidate,
    InterfaceHostServiceWorkspaceCommittedSemanticPackageFamilyState,
    InterfaceHostServiceWorkspaceCommittedSemanticPackageState,
    InterfaceHostServiceWorkspaceDiscoveryState,
    InterfaceHostServiceWorkspaceLifecycleState,
    InterfaceHostServiceWorkspaceSemanticObjectConfigGraphPreviewState,
    InterfaceHostServiceWorkspaceSemanticPackageState,
    InterfaceHostServiceWorkspaceSemanticSourceState,
)
from aware_interface_service.host.capabilities.attention import (
    AttentionLayoutIntentSection,
    AttentionLayoutTopologyIntentSection,
)
from aware_interface_service.namespace_registry import InterfaceNamespaceRegistry
from aware_interface_service.fingerprint import compute_daemon_source_fingerprint
from aware_interface_service.host.actions import (
    InterfaceActionTarget,
    interface_action_target_from_request_payload,
)


_ResponseT = TypeVar("_ResponseT", bound=InterfaceControlPlaneResponse)


@dataclass(frozen=True, slots=True)
class InterfaceDaemonMetadata:
    daemon_instance_id: UUID
    daemon_started_at: str
    daemon_source_fingerprint: str
    repository_root: Path
    state_home: Path
    default_endpoint: str | None


def _optional_uuid(value: UUID | str | None) -> UUID | None:
    if value is None or isinstance(value, UUID):
        return value
    normalized = str(value).strip()
    if not normalized:
        return None
    return UUID(normalized)


def _public_actor_id(value: UUID | None) -> UUID | None:
    if value is None or value.int == 0:
        return None
    return value


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("Interface resolved-view payload keys must be strings")
            normalized[key] = _json_value(item)
        return normalized
    return str(value)


def _json_object(value: dict[str, object]) -> JsonObject:
    normalized: dict[str, JsonValue] = {}
    for key, item in value.items():
        normalized[key] = _json_value(item)
    return JsonObject(normalized)


def _stable_digest(value: object) -> str:
    encoded = json.dumps(
        _json_value(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _utc_now_isoformat() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _string_from_json_object(value: dict[str, object], key: str) -> str | None:
    raw = value.get(key)
    if not isinstance(raw, str):
        return None
    normalized = raw.strip()
    return normalized or None


def _interface_action_target_from_request(
    request: InterfaceControlPlaneRequest,
) -> InterfaceActionTarget | None:
    if not isinstance(request, InterfaceActionRequest):
        return None
    return interface_action_target_from_request_payload(
        cast(dict[str, object], request.model_dump(mode="python"))
    )


def _interface_invocation_context(*, namespace: str) -> dict[str, object]:
    return {"interface": {"namespace": namespace}}


def _materialized_pane_state_digest_payload(
    state: InterfaceMaterializedPaneState,
) -> dict[str, object]:
    # Host wall-clock materialized_at is intentionally excluded: commit,
    # projection, state, and provenance fields are the semantic cache boundary.
    return {
        "pane_state_key": state.pane_state_key,
        "window_key": state.window_key,
        "layout_key": state.layout_key,
        "section_key": state.section_key,
        "pane_kind": state.pane_kind,
        "pane_config_id": state.pane_config_id,
        "pane_package_id": state.pane_package_id,
        "focus_scope_id": state.focus_scope_id,
        "branch_id": state.branch_id,
        "projection_experience_view_id": state.projection_experience_view_id,
        "projection_view_id": state.projection_view_id,
        "state_model_id": state.state_model_id,
        "projection_hash": state.projection_hash,
        "status": state.status,
        "head_commit_id": state.head_commit_id,
        "graph_hash_post": state.graph_hash_post,
        "state": dict(state.state),
        "provenance": dict(state.provenance),
        "error": state.error,
    }


def _view_state_digest_entry_model(
    state: InterfaceMaterializedPaneState,
) -> ApiInterfaceHostViewStateDigestEntryState:
    return ApiInterfaceHostViewStateDigestEntryState(
        pane_state_key=state.pane_state_key,
        digest=_stable_digest(_materialized_pane_state_digest_payload(state)),
        view_ref=_string_from_json_object(state.provenance, "view_ref"),
        projection_view_key=_string_from_json_object(
            state.provenance,
            "projection_view_key",
        ),
        projection_hash=state.projection_hash,
        head_commit_id=state.head_commit_id,
        graph_hash_post=state.graph_hash_post,
    )


def _runtime_view_state_cursor_model(
    state: InterfaceRuntimeState,
) -> ApiInterfaceHostViewStateCursorState:
    entries = sorted(
        (
            _view_state_digest_entry_model(item)
            for item in state.materialized_pane_states
        ),
        key=lambda item: (item.pane_state_key, item.digest),
    )
    digest = _stable_digest(
        {
            "entry_digests": [
                item.model_dump(mode="json", exclude_none=True) for item in entries
            ],
        }
    )
    return ApiInterfaceHostViewStateCursorState(
        cursor=f"view-state:{digest}",
        digest=digest,
        materialized_entry_count=len(entries),
        entry_digests=entries,
        computed_at=_utc_now_isoformat(),
    )


def _view_state_cursor_changed(
    *,
    cursor: ApiInterfaceHostViewStateCursorState | None,
    known_cursor: str | None,
    known_digest: str | None,
) -> bool:
    if cursor is None:
        return True
    normalized_cursor = known_cursor.strip() if known_cursor is not None else ""
    normalized_digest = known_digest.strip() if known_digest is not None else ""
    if normalized_cursor and normalized_cursor == cursor.cursor:
        return False
    if normalized_digest and normalized_digest == cursor.digest:
        return False
    return True


def _evaluate_daemon_freshness(
    *,
    daemon_metadata: InterfaceDaemonMetadata,
) -> tuple[str | None, bool, str | None]:
    expected_source_fingerprint = compute_daemon_source_fingerprint(
        repository_root=daemon_metadata.repository_root,
    )
    daemon_source_fingerprint = daemon_metadata.daemon_source_fingerprint.strip()
    if not daemon_source_fingerprint:
        return (
            expected_source_fingerprint,
            True,
            "daemon is missing source-fingerprint metadata",
        )
    if daemon_source_fingerprint != expected_source_fingerprint:
        return (
            expected_source_fingerprint,
            True,
            "daemon source fingerprint differs from the current workspace",
        )
    return (expected_source_fingerprint, False, None)


class InterfaceControlPlane:
    def __init__(
        self,
        *,
        base_config: InterfaceHostServiceConfig,
        socket_path: Path,
        registry: InterfaceNamespaceRegistry,
        daemon_metadata: InterfaceDaemonMetadata,
    ) -> None:
        self._base_config = base_config
        self._socket_path = socket_path.resolve()
        self._registry = registry
        self._daemon_metadata = daemon_metadata
        self._dogfood_store = InterfaceHostDogfoodStore(
            state_home=daemon_metadata.state_home,
        )

    async def handle_request(
        self,
        request: InterfaceControlPlaneRequest,
        *,
        action_target: InterfaceActionTarget | None = None,
        committed_app_screen_resolver: object | None = None,
    ) -> InterfaceControlPlaneResponse:
        try:
            if isinstance(request, PingRequest):
                (
                    expected_source_fingerprint,
                    restart_recommended,
                    restart_reason,
                ) = _evaluate_daemon_freshness(
                    daemon_metadata=self._daemon_metadata,
                )
                return PingResponse(
                    request_id=request.request_id,
                    socket_path=str(self._socket_path),
                    daemon_instance_id=self._daemon_metadata.daemon_instance_id,
                    daemon_started_at=self._daemon_metadata.daemon_started_at,
                    daemon_source_fingerprint=self._daemon_metadata.daemon_source_fingerprint,
                    repository_root=str(self._daemon_metadata.repository_root),
                    state_home=str(self._daemon_metadata.state_home),
                    default_endpoint=self._daemon_metadata.default_endpoint,
                    expected_source_fingerprint=expected_source_fingerprint,
                    restart_recommended=restart_recommended,
                    restart_reason=restart_reason,
                    namespaces=[
                        _hosted_namespace_model(namespace_state)
                        for namespace_state in self._registry.list_namespaces()
                    ],
                )
            if isinstance(request, NamespaceEnsureRequest):
                config = build_namespaced_service_config(
                    self._base_config,
                    namespace=request.namespace,
                    host_label=request.host_label,
                    endpoint=request.endpoint,
                    auth_token=request.auth_token,
                    environment_config_id=request.environment_config_id,
                    interface_package_name=request.interface_package_name,
                )
                state = await self._registry.ensure_namespace(config=config)
                return self._persist_response_host_state(
                    NamespaceEnsureResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        host_state=_host_state_model(state),
                    )
                )
            if isinstance(request, NamespaceListRequest):
                return NamespaceListResponse(
                    request_id=request.request_id,
                    namespaces=[
                        _hosted_namespace_model(namespace_state)
                        for namespace_state in self._registry.list_namespaces()
                    ],
                )
            if isinstance(request, InterfaceStatusRequest):
                try:
                    return self._persist_response_host_state(
                        InterfaceStatusResponse(
                            request_id=request.request_id,
                            namespace=request.namespace,
                            host_state=_host_state_model(
                                await self._registry.status(
                                    namespace=request.namespace, refresh=True
                                ),
                            ),
                        ),
                    )
                except Exception as exc:
                    fallback = self._last_good_host_state(
                        namespace=request.namespace,
                        error=str(exc),
                    )
                    if fallback is not None:
                        return InterfaceStatusResponse(
                            request_id=request.request_id,
                            namespace=request.namespace,
                            host_state=fallback,
                        )
                    raise
            if isinstance(request, InterfaceAdmitEnvironmentActorRequest):
                state = await self._registry.admit_environment_actor(
                    namespace=request.namespace,
                    environment_id=request.environment_id,
                    environment_profile_id=request.environment_profile_id,
                    actor_config_id=request.actor_config_id,
                    class_instance_identity_id=request.class_instance_identity_id,
                    object_instance_graph_branch_key=(
                        request.object_instance_graph_branch_key
                    ),
                    object_instance_graph_branch_id=(
                        request.object_instance_graph_branch_id
                    ),
                    requested_role_config_ids=tuple(request.requested_role_config_ids),
                    requested_role_config_names=tuple(
                        request.requested_role_config_names
                    ),
                    reason=request.reason,
                    evidence=dict(request.evidence),
                )
                host_state = _host_state_model(state)
                self._save_host_state(host_state)
                return InterfaceAdmitEnvironmentActorResponse(
                    request_id=request.request_id,
                    namespace=request.namespace,
                    environment_admission=host_state.environment_admission,
                    environment_admission_receipt=(
                        host_state.environment_admission_receipt
                    ),
                    host_state=host_state,
                )
            if isinstance(request, InterfaceEnterAppScreenRequest):
                result = await self._registry.enter_app_screen(
                    namespace=request.namespace,
                    app_package_id=request.app_package_id,
                    app_package_branch_id=request.app_package_branch_id,
                    app_package_object_instance_graph_commit_id=(
                        request.app_package_object_instance_graph_commit_id
                    ),
                    app_config_screen_config_id=(request.app_config_screen_config_id),
                    reason=request.reason,
                    evidence=dict(request.evidence),
                    committed_app_screen_resolver=(committed_app_screen_resolver),
                )
                host_state = _host_state_model(result.state)
                self._save_host_state(host_state)
                return InterfaceEnterAppScreenResponse(
                    request_id=request.request_id,
                    success=result.app_screen.accepted,
                    error=result.app_screen.error,
                    namespace=request.namespace,
                    app_screen=host_state.app_screen,
                    host_state=host_state,
                )
            if isinstance(request, InterfaceEnterEnvironmentRequest):
                result = await self._registry.enter_environment(
                    namespace=request.namespace,
                    environment_id=request.environment_id,
                    environment_profile_id=request.environment_profile_id,
                    actor_config_id=request.actor_config_id,
                    class_instance_identity_id=request.class_instance_identity_id,
                    object_instance_graph_branch_key=(
                        request.object_instance_graph_branch_key
                    ),
                    object_instance_graph_branch_id=(
                        request.object_instance_graph_branch_id
                    ),
                    requested_role_config_ids=tuple(request.requested_role_config_ids),
                    requested_role_config_names=tuple(
                        request.requested_role_config_names
                    ),
                    environment_admission_receipt=(
                        request.environment_admission_receipt
                    ),
                    environment_session_id=request.environment_session_id,
                    environment_session_config_id=(
                        request.environment_session_config_id
                    ),
                    session_key=request.session_key,
                    title=request.title,
                    description=request.description,
                    purpose=request.purpose,
                    source_kind=request.source_kind,
                    source_ref=request.source_ref,
                    reason=request.reason,
                    evidence=dict(request.evidence),
                )
                host_state = _host_state_model(result.state)
                self._save_host_state(host_state)
                return InterfaceEnterEnvironmentResponse(
                    request_id=request.request_id,
                    namespace=request.namespace,
                    environment_admission=host_state.environment_admission,
                    environment_admission_receipt=(
                        host_state.environment_admission_receipt
                    ),
                    environment_session=result.environment_session,
                    environment_session_join_receipt=(
                        result.environment_session_join_receipt
                    ),
                    environment_navigation_context=(
                        result.environment_navigation_context
                    ),
                    default_navigation_receipt=result.default_navigation_receipt,
                    environment_session_state=host_state.environment_session,
                    environment_navigation_state=host_state.environment_navigation,
                    host_state=host_state,
                )
            if isinstance(request, InterfaceJoinEnvironmentSessionRequest):
                result = await self._registry.join_environment_session(
                    namespace=request.namespace,
                    environment_session_id=request.environment_session_id,
                    environment_profile_id=request.environment_profile_id,
                    environment_admission_receipt=(
                        request.environment_admission_receipt
                    ),
                    reason=request.reason,
                    evidence=dict(request.evidence),
                )
                host_state = _host_state_model(result.state)
                self._save_host_state(host_state)
                return InterfaceJoinEnvironmentSessionResponse(
                    request_id=request.request_id,
                    namespace=request.namespace,
                    environment_session=result.environment_session,
                    environment_session_join_receipt=(
                        result.environment_session_join_receipt
                    ),
                    environment_navigation_context=(
                        result.environment_navigation_context
                    ),
                    default_navigation_receipt=result.default_navigation_receipt,
                    environment_session_state=host_state.environment_session,
                    environment_navigation_state=host_state.environment_navigation,
                    host_state=host_state,
                )
            if isinstance(request, InterfaceSelectEnvironmentNavigationTargetRequest):
                result = await self._registry.select_environment_navigation_target(
                    namespace=request.namespace,
                    environment_navigation_context_id=(
                        request.environment_navigation_context_id
                    ),
                    selected_process_id=request.selected_process_id,
                    selected_thread_id=request.selected_thread_id,
                    reason=request.reason,
                    evidence=dict(request.evidence),
                )
                host_state = _host_state_model(result.state)
                self._save_host_state(host_state)
                return InterfaceSelectEnvironmentNavigationTargetResponse(
                    request_id=request.request_id,
                    namespace=request.namespace,
                    environment_navigation_context=(
                        result.environment_navigation_context
                    ),
                    environment_navigation_receipt=(
                        result.environment_navigation_receipt
                    ),
                    environment_navigation_state=host_state.environment_navigation,
                    host_state=host_state,
                )
            if isinstance(request, InterfaceResolveExperienceLensRequest):
                state = await self._registry.resolve_experience_lens(
                    namespace=request.namespace,
                    environment_session_join_receipt=(
                        request.environment_session_join_receipt
                    ),
                    environment_navigation_context=(
                        request.environment_navigation_context
                    ),
                    experience_actor_admission=request.experience_actor_admission,
                    experience_identity_session_config_id=(
                        request.experience_identity_session_config_id
                    ),
                    reason=request.reason,
                    evidence=dict(request.evidence),
                )
                host_state = _host_state_model(state)
                self._save_host_state(host_state)
                return InterfaceResolveExperienceLensResponse(
                    request_id=request.request_id,
                    namespace=request.namespace,
                    environment_session=host_state.environment_session,
                    environment_navigation=host_state.environment_navigation,
                    experience_lens=host_state.experience_lens,
                    host_state=host_state,
                )
            if isinstance(request, InterfaceInvokeApiRequest):
                response = await self._registry.invoke_api(
                    namespace=request.namespace,
                    endpoint_ref=request.endpoint_ref,
                    discriminant=request.discriminant,
                    request_payload=dict(request.request_payload),
                    invocation_context=_interface_invocation_context(
                        namespace=request.namespace,
                    ),
                )
                invoke_response = InterfaceInvokeApiResponse(
                    request_id=request.request_id,
                    success=response.status is RequestStatus.succeeded,
                    error=response.error,
                    namespace=request.namespace,
                    endpoint_ref=request.endpoint_ref,
                    discriminant=request.discriminant,
                    service_status=response.status.value,
                    response_payload=response.response_payload,
                )
                self._append_action_receipt(
                    request_id=request.request_id,
                    namespace=request.namespace,
                    operation_kind="api_invoke",
                    action_key=request.endpoint_ref,
                    status=response.status.value,
                    error=response.error,
                    service_status=response.status.value,
                    endpoint_ref=request.endpoint_ref,
                    discriminant=request.discriminant,
                )
                return invoke_response
            if isinstance(request, InterfaceActionRequest):
                try:
                    effective_action_target = (
                        action_target or _interface_action_target_from_request(request)
                    )
                    if effective_action_target is not None:
                        service_state = await self._registry.perform_action(
                            namespace=request.namespace,
                            pane_ref=request.pane_ref,
                            action_key=request.action_key,
                            action_target=effective_action_target,
                            payload=dict(request.payload),
                        )
                    else:
                        service_state = await self._registry.perform_action(
                            namespace=request.namespace,
                            pane_ref=request.pane_ref,
                            action_key=request.action_key,
                            payload=dict(request.payload),
                        )
                    host_state = _host_state_model(service_state)
                    self._save_host_state(host_state)
                    action_status = (
                        host_state.current_operation.status
                        if host_state.current_operation is not None
                        else "succeeded"
                    )
                    self._append_action_receipt(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        operation_kind="pane_action",
                        pane_ref=request.pane_ref,
                        action_key=request.action_key,
                        status=action_status,
                        error=(
                            host_state.current_operation.error
                            if host_state.current_operation is not None
                            else None
                        ),
                        host_state=host_state,
                    )
                    return InterfaceActionResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        pane_ref=request.pane_ref,
                        action_key=request.action_key,
                        host_state=host_state,
                    )
                except Exception as exc:
                    self._append_action_receipt(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        operation_kind="pane_action",
                        pane_ref=request.pane_ref,
                        action_key=request.action_key,
                        status="failed",
                        error=str(exc),
                    )
                    raise
            if isinstance(request, InterfaceSelectStepRequest):
                return self._persist_response_host_state(
                    InterfaceSelectStepResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        step_id=request.step_id,
                        host_state=_host_state_model(
                            await self._registry.select_control_plane_step(
                                namespace=request.namespace,
                                step_id=request.step_id,
                            )
                        ),
                    )
                )
            if isinstance(request, InterfaceSelectProfileRequest):
                return self._persist_response_host_state(
                    InterfaceSelectProfileResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        profile_id=request.profile_id,
                        host_state=_host_state_model(
                            await self._registry.select_control_plane_profile(
                                namespace=request.namespace,
                                profile_id=request.profile_id,
                            )
                        ),
                    )
                )
            if isinstance(request, InterfaceSelectRuntimeLayoutRequest):
                state = await self._registry.select_control_plane_runtime_layout(
                    namespace=request.namespace,
                    layout_config_id=request.layout_config_id,
                )
                return self._persist_response_host_state(
                    InterfaceSelectRuntimeLayoutResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        layout_config_id=(
                            state.runtime.active_layout_config_id
                            if state.runtime is not None
                            else None
                        ),
                        host_state=_host_state_model(state),
                    )
                )
            if isinstance(request, InterfaceActivateRuntimeFocusRequest):
                state = await self._registry.activate_control_plane_runtime_focus(
                    namespace=request.namespace,
                    representation_id=request.representation_id,
                )
                runtime_state = state.runtime
                return self._persist_response_host_state(
                    InterfaceActivateRuntimeFocusResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        representation_id=_active_runtime_representation_id(state),
                        layout_config_id=(
                            runtime_state.active_layout_config_id
                            if runtime_state is not None
                            else None
                        ),
                        host_state=_host_state_model(state),
                    )
                )
            if isinstance(request, InterfaceRequestWindowLayoutRequest):
                state = await self._registry.request_interface_window_layout(
                    namespace=request.namespace,
                    interface_package_id=request.interface_package_id,
                    interface_package_name=request.interface_package_name,
                    window_key=request.window_key,
                    layout_config_id=request.layout_config_id,
                    layout_key=request.layout_key,
                    section_key=request.section_key,
                    observable_id=request.observable_id,
                    representation_id=request.representation_id,
                    requested_by_service=request.requested_by_service,
                    requested_by_operation=request.requested_by_operation,
                    reason=request.reason,
                    idempotency_key=request.idempotency_key,
                )
                runtime_state = state.runtime
                active_focus = (
                    runtime_state.active_focus if runtime_state is not None else None
                )
                window_layout = (
                    runtime_state.window_layout if runtime_state is not None else None
                )
                resolved_view = (
                    runtime_state.resolved_view if runtime_state is not None else None
                )
                return self._persist_response_host_state(
                    InterfaceRequestWindowLayoutResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        interface_package_id=(
                            request.interface_package_id
                            or (
                                resolved_view.interface_package_id
                                if resolved_view is not None
                                else None
                            )
                        ),
                        interface_package_name=(
                            request.interface_package_name
                            or (
                                resolved_view.interface_package_name
                                if resolved_view is not None
                                else None
                            )
                        ),
                        window_key=(
                            window_layout.window_key
                            if window_layout is not None
                            else request.window_key
                        ),
                        layout_config_id=(
                            active_focus.layout_config_id
                            if active_focus is not None
                            else (
                                runtime_state.active_layout_config_id
                                if runtime_state is not None
                                else request.layout_config_id
                            )
                        ),
                        layout_key=(
                            active_focus.layout_key
                            if active_focus is not None
                            else (
                                window_layout.layout_key
                                if window_layout is not None
                                else request.layout_key
                            )
                        ),
                        section_key=(
                            active_focus.section_key
                            if active_focus is not None
                            else request.section_key
                        ),
                        observable_id=(
                            active_focus.observable_id
                            if active_focus is not None
                            else request.observable_id
                        ),
                        representation_id=_active_runtime_representation_id(state),
                        requested_by_service=request.requested_by_service,
                        requested_by_operation=request.requested_by_operation,
                        reason=request.reason,
                        idempotency_key=request.idempotency_key,
                        host_state=_host_state_model(state),
                    )
                )
            if isinstance(request, InterfaceApplyAttentionLayoutTransitionRequest):
                result = await self._registry.apply_attention_layout_transition(
                    namespace=request.namespace,
                    client_intent_id=request.client_intent_id,
                    expected_previous_layout_transition_id=(
                        request.expected_previous_layout_transition_id
                    ),
                    topology_transition_id=request.topology_transition_id,
                    section_states=tuple(
                        AttentionLayoutIntentSection(
                            layout_config_section_config_id=(
                                section.layout_config_section_config_id
                            ),
                            order=section.order,
                            weight_micros=section.weight_micros,
                            is_visible=section.is_visible,
                            is_collapsed=section.is_collapsed,
                        )
                        for section in request.section_states
                    ),
                )
                return self._persist_response_host_state(
                    InterfaceApplyAttentionLayoutTransitionResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        outcome=result.outcome,
                        conflict_reason=result.conflict_reason,
                        active_layout_transition_id=(
                            result.active_layout_transition_id
                        ),
                        active_topology_transition_id=(
                            result.active_topology_transition_id
                        ),
                        object_instance_graph_commit_id=(
                            result.object_instance_graph_commit_id
                        ),
                        graph_hash_post=result.graph_hash_post,
                        host_state=_host_state_model(result.state),
                    )
                )
            if isinstance(
                request,
                InterfaceApplyAttentionLayoutTopologyTransitionRequest,
            ):
                result = (
                    await self._registry.apply_attention_layout_topology_transition(
                        namespace=request.namespace,
                        client_intent_id=request.client_intent_id,
                        expected_previous_topology_transition_id=(
                            request.expected_previous_topology_transition_id
                        ),
                        section_states=tuple(
                            AttentionLayoutTopologyIntentSection(
                                layout_config_section_config_id=(
                                    section.layout_config_section_config_id
                                ),
                                order=section.order,
                            )
                            for section in request.section_states
                        ),
                    )
                )
                return self._persist_response_host_state(
                    InterfaceApplyAttentionLayoutTopologyTransitionResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        outcome=result.outcome,
                        conflict_reason=result.conflict_reason,
                        active_topology_transition_id=(
                            result.active_topology_transition_id
                        ),
                        object_instance_graph_commit_id=(
                            result.object_instance_graph_commit_id
                        ),
                        graph_hash_post=result.graph_hash_post,
                        host_state=_host_state_model(result.state),
                    )
                )
            if isinstance(request, InterfaceReportRendererCapabilitiesRequest):
                state = await self._registry.report_renderer_capabilities(
                    namespace=request.namespace,
                    renderer_capabilities=_service_renderer_capabilities_state(
                        request.renderer_capabilities,
                    ),
                )
                return self._persist_response_host_state(
                    InterfaceReportRendererCapabilitiesResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        host_state=_host_state_model(state),
                    )
                )
            if isinstance(request, InterfaceSyncViewStateCursorRequest):
                state = await self._registry.status(
                    namespace=request.namespace,
                    refresh=False,
                )
                cursor = (
                    _runtime_view_state_cursor_model(state.runtime)
                    if state.runtime is not None
                    else None
                )
                return self._persist_response_host_state(
                    InterfaceSyncViewStateCursorResponse(
                        request_id=request.request_id,
                        namespace=request.namespace,
                        changed=_view_state_cursor_changed(
                            cursor=cursor,
                            known_cursor=request.known_cursor,
                            known_digest=request.known_digest,
                        ),
                        view_state_cursor=cursor,
                        host_state=_host_state_model(state, view_state_cursor=cursor),
                    )
                )
            if isinstance(request, InterfaceStopRequest):
                return InterfaceStopResponse(
                    request_id=request.request_id,
                    namespace=request.namespace,
                    hosted_namespace=_hosted_namespace_model(
                        await self._registry.stop_namespace(
                            namespace=request.namespace
                        ),
                    ),
                )
            raise ValueError(
                f"Unsupported control-plane method: {request.operation or '<empty>'}"
            )
        except Exception as exc:
            return InterfaceControlPlaneResponse(
                operation=request.operation,
                request_id=request.request_id,
                success=False,
                error=str(exc),
            )

    def _persist_response_host_state(self, response: _ResponseT) -> _ResponseT:
        host_state = getattr(response, "host_state", None)
        if isinstance(host_state, InterfaceHostState):
            self._save_host_state(host_state)
        return response

    def _persist_host_state_model(
        self,
        state: InterfaceHostServiceState,
    ) -> InterfaceHostState:
        host_state = _host_state_model(state)
        self._save_host_state(host_state)
        return host_state

    def _save_host_state(self, host_state: InterfaceHostState) -> None:
        try:
            self._dogfood_store.save_host_state(host_state)
        except Exception as exc:
            logger.warning(
                "aware_interface_service failed to persist host snapshot namespace=%s: %s",
                host_state.namespace,
                exc,
            )

    def _last_good_host_state(
        self,
        *,
        namespace: str,
        error: str,
    ) -> InterfaceHostState | None:
        host_state = self._dogfood_store.read_host_state(namespace=namespace)
        if host_state is None:
            return None
        warnings = [
            *host_state.warnings,
            "last_good_host_state",
            "live_host_unavailable",
            f"live_host_error:{error}",
        ]
        return host_state.model_copy(
            update={
                "started": False,
                "warnings": warnings,
            }
        )

    def _append_action_receipt(
        self,
        *,
        request_id: UUID | None,
        namespace: str,
        operation_kind: str,
        action_key: str,
        status: str,
        error: str | None,
        pane_ref: str | None = None,
        host_state: InterfaceHostState | None = None,
        service_status: str | None = None,
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
    ) -> None:
        try:
            self._dogfood_store.append_action_receipt(
                request_id=str(request_id) if request_id is not None else None,
                namespace=namespace,
                operation_kind=operation_kind,
                pane_ref=pane_ref,
                action_key=action_key,
                status=status,
                error=error,
                host_state=host_state,
                service_status=service_status,
                endpoint_ref=endpoint_ref,
                discriminant=discriminant,
            )
        except Exception as exc:
            logger.warning(
                "aware_interface_service failed to persist action receipt namespace=%s action=%s: %s",
                namespace,
                action_key,
                exc,
            )

    async def initial_follow_state(
        self,
        request: InterfaceFollowRequest,
    ) -> InterfaceHostServiceState:
        return await self._registry.status(namespace=request.namespace, refresh=True)

    async def open_api_stream(
        self,
        request: InterfaceStreamApiRequest,
    ) -> ServiceHostDuplexRequestHandle:
        return await self._registry.open_api_stream(
            namespace=request.namespace,
            endpoint_ref=request.endpoint_ref,
            discriminant=request.discriminant,
            request_payload=dict(request.request_payload),
        )

    async def follow_notifications(
        self,
        request: InterfaceFollowRequest,
        *,
        last_state: InterfaceHostServiceState,
        should_stop,
    ):
        async for state in self._registry.follow_namespace(
            namespace=request.namespace,
            poll_interval_s=max(request.poll_interval_ms / 1000.0, 0.25),
            last_state=last_state,
            should_stop=should_stop,
        ):
            yield InterfaceStateNotification(
                namespace=request.namespace,
                host_state=self._persist_host_state_model(state),
            )

    async def api_stream_notifications(
        self,
        request: InterfaceStreamApiRequest,
        *,
        handle: ServiceHostDuplexRequestHandle,
        should_stop,
    ):
        try:
            async for event in handle.events:
                if should_stop():
                    return
                if (
                    event.kind is not ServiceDuplexStreamEventKind.RESPONSE
                    or event.response is None
                ):
                    continue
                response = event.response.to_contract()
                if response.stream_lifecycle is not StreamLifecycle.started:
                    continue
                if response.response_payload is None:
                    continue
                envelope = ServiceDuplexStreamEventEnvelope.model_validate(
                    response.response_payload
                ).to_contract()
                yield InterfaceApiEventNotification(
                    namespace=request.namespace,
                    endpoint_ref=request.endpoint_ref,
                    discriminant=request.discriminant,
                    event_kind=envelope.kind.value,
                    sequence=envelope.sequence,
                    item_key=envelope.item_key,
                    payload=cast(JsonValue, envelope.payload),
                )
            if should_stop():
                return
            terminal_response = await handle.response
            yield InterfaceApiStreamClosedNotification(
                namespace=request.namespace,
                endpoint_ref=request.endpoint_ref,
                discriminant=request.discriminant,
                service_status=terminal_response.status.value,
                response_payload=terminal_response.response_payload,
                error=terminal_response.error,
            )
        except Exception as exc:
            if should_stop():
                return
            yield InterfaceApiStreamClosedNotification(
                namespace=request.namespace,
                endpoint_ref=request.endpoint_ref,
                discriminant=request.discriminant,
                service_status=RequestStatus.failed.value,
                error=str(exc),
            )
        finally:
            await handle.close()


class InterfaceControlPlaneServer:
    def __init__(
        self,
        *,
        socket_path: Path,
        control_plane: InterfaceControlPlane,
    ) -> None:
        self.socket_path = socket_path.resolve()
        self.control_plane = control_plane
        self._server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        with suppress(FileNotFoundError):
            self.socket_path.unlink()
        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=str(self.socket_path),
        )

    async def serve_forever(self) -> None:
        if self._server is None:
            raise RuntimeError("Interface control-plane server is not started.")
        async with self._server:
            await self._server.serve_forever()

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        with suppress(FileNotFoundError):
            self.socket_path.unlink()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                raw = line.decode("utf-8").strip()
                if not raw:
                    continue
                try:
                    operation = InterfaceControlPlaneOperation.model_validate_json(raw)
                    request = operation.request
                    if request is None:
                        raise ValueError(
                            "Control-plane request must carry a request envelope."
                        )
                except Exception as exc:
                    response = InterfaceControlPlaneOperation(
                        response=InterfaceControlPlaneResponse(
                            operation="invalid_request",
                            success=False,
                            error=str(exc),
                        )
                    )
                else:
                    if isinstance(request, InterfaceFollowRequest):
                        try:
                            initial_state = (
                                await self.control_plane.initial_follow_state(request)
                            )
                        except Exception as exc:
                            response = InterfaceControlPlaneOperation(
                                response=InterfaceControlPlaneResponse(
                                    operation=request.operation,
                                    request_id=request.request_id,
                                    success=False,
                                    error=str(exc),
                                )
                            )
                            writer.write(
                                response.model_dump_json(exclude_none=True).encode(
                                    "utf-8"
                                )
                                + b"\n"
                            )
                            await writer.drain()
                            continue
                        response = InterfaceControlPlaneOperation(
                            response=InterfaceFollowResponse(
                                request_id=request.request_id,
                                namespace=request.namespace,
                                host_state=_host_state_model(initial_state),
                            )
                        )
                        writer.write(
                            response.model_dump_json(exclude_none=True).encode("utf-8")
                            + b"\n"
                        )
                        await writer.drain()
                        async for (
                            notification
                        ) in self.control_plane.follow_notifications(
                            request,
                            last_state=initial_state,
                            should_stop=lambda: reader.at_eof() or writer.is_closing(),
                        ):
                            writer.write(
                                InterfaceControlPlaneOperation(
                                    notification=cast(
                                        InterfaceControlPlaneNotification,
                                        notification,
                                    )
                                )
                                .model_dump_json(exclude_none=True)
                                .encode("utf-8")
                                + b"\n"
                            )
                            await writer.drain()
                        continue
                    if isinstance(request, InterfaceStreamApiRequest):
                        try:
                            handle = await self.control_plane.open_api_stream(request)
                        except Exception as exc:
                            response = InterfaceControlPlaneOperation(
                                response=InterfaceControlPlaneResponse(
                                    operation=request.operation,
                                    request_id=request.request_id,
                                    success=False,
                                    error=str(exc),
                                )
                            )
                            writer.write(
                                response.model_dump_json(exclude_none=True).encode(
                                    "utf-8"
                                )
                                + b"\n"
                            )
                            await writer.drain()
                            continue
                        response = InterfaceControlPlaneOperation(
                            response=InterfaceStreamApiResponse(
                                request_id=request.request_id,
                                namespace=request.namespace,
                                endpoint_ref=request.endpoint_ref,
                                discriminant=request.discriminant,
                            )
                        )
                        writer.write(
                            response.model_dump_json(exclude_none=True).encode("utf-8")
                            + b"\n"
                        )
                        await writer.drain()
                        async for (
                            notification
                        ) in self.control_plane.api_stream_notifications(
                            request,
                            handle=handle,
                            should_stop=lambda: reader.at_eof() or writer.is_closing(),
                        ):
                            writer.write(
                                InterfaceControlPlaneOperation(
                                    notification=cast(
                                        InterfaceControlPlaneNotification,
                                        notification,
                                    )
                                )
                                .model_dump_json(exclude_none=True)
                                .encode("utf-8")
                                + b"\n"
                            )
                            await writer.drain()
                        continue
                    response = InterfaceControlPlaneOperation(
                        response=await self.control_plane.handle_request(request)
                    )
                writer.write(
                    response.model_dump_json(exclude_none=True).encode("utf-8") + b"\n"
                )
                await writer.drain()
        finally:
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()


def _transport_state_model(
    state: InterfaceHostServiceTransportState,
) -> InterfaceTransportState:
    return InterfaceTransportState(
        available=state.available,
        registered=state.registered,
        authenticated=state.authenticated,
        actor_id=_public_actor_id(state.actor_id),
        interface_id=state.interface_id,
        interface_system_actor_id=state.interface_system_actor_id,
        interface_system_identity_id=state.interface_system_identity_id,
        interface_session_id=state.interface_session_id,
        session_label=state.session_label,
        capabilities=list(state.capabilities),
        protocol_version=state.protocol_version,
        last_seen_at=state.last_seen_at,
        interface_identity_network_node_id=state.interface_identity_network_node_id,
        interface_session_network_binding_id=state.interface_session_network_binding_id,
    )


def _lane_sync_state_model(
    state: InterfaceHostServiceLaneSyncState,
) -> InterfaceLaneSyncState:
    return InterfaceLaneSyncState(
        enabled=state.enabled,
        watching=state.watching,
        window_key=state.window_key,
        lane_id=_optional_uuid(state.lane_id),
        branch_id=state.branch_id,
        projection_hash=state.projection_hash,
        last_commit_id=_optional_uuid(state.last_commit_id),
        last_graph_hash_post=state.last_graph_hash_post,
        updates_received=state.updates_received,
        advanced_count=state.advanced_count,
        last_synced_at=state.last_synced_at,
        error=state.error,
    )


def _environment_admission_role_eligibility_model(
    state: InterfaceEnvironmentAdmissionRoleEligibilityState,
) -> ApiInterfaceEnvironmentAdmissionRoleEligibilityState:
    return ApiInterfaceEnvironmentAdmissionRoleEligibilityState(
        environment_profile_actor_config_id=(state.environment_profile_actor_config_id),
        actor_config_role_config_id=state.actor_config_role_config_id,
        role_config_id=state.role_config_id,
        role_config_name=state.role_config_name,
    )


def _environment_admission_role_binding_model(
    state: InterfaceEnvironmentAdmissionRoleBindingState,
) -> ApiInterfaceEnvironmentAdmissionRoleBindingState:
    return ApiInterfaceEnvironmentAdmissionRoleBindingState(
        environment_profile_actor_config_id=(state.environment_profile_actor_config_id),
        actor_config_role_config_id=state.actor_config_role_config_id,
        role_config_id=state.role_config_id,
        role_config_name=state.role_config_name,
        actor_id=state.actor_id,
        role_id=state.role_id,
        actor_role_id=state.actor_role_id,
        role_class_instance_id=state.role_class_instance_id,
        class_instance_identity_id=state.class_instance_identity_id,
        role_config_class_config_id=state.role_config_class_config_id,
        object_instance_graph_identity_id=state.object_instance_graph_identity_id,
        object_instance_graph_branch_key=state.object_instance_graph_branch_key,
        object_instance_graph_branch_id=state.object_instance_graph_branch_id,
    )


def _environment_admission_state_model(
    state: InterfaceEnvironmentAdmissionState,
) -> ApiInterfaceEnvironmentAdmissionState:
    return ApiInterfaceEnvironmentAdmissionState(
        status=state.status,
        source_kind=state.source_kind,
        accepted=state.accepted,
        actor_id=_public_actor_id(state.actor_id),
        environment_id=state.environment_id,
        environment_profile_id=state.environment_profile_id,
        environment_profile_actor_config_id=(state.environment_profile_actor_config_id),
        actor_config_id=state.actor_config_id,
        class_instance_identity_id=state.class_instance_identity_id,
        object_instance_graph_branch_key=state.object_instance_graph_branch_key,
        object_instance_graph_branch_id=state.object_instance_graph_branch_id,
        requested_role_config_ids=list(state.requested_role_config_ids),
        requested_role_config_names=list(state.requested_role_config_names),
        eligible_role_count=state.eligible_role_count,
        binding_count=state.binding_count,
        eligible_roles=[
            _environment_admission_role_eligibility_model(item)
            for item in state.eligible_roles
        ],
        bindings=[
            _environment_admission_role_binding_model(item) for item in state.bindings
        ],
        blockers=list(state.blockers),
        error=state.error,
        reason=state.reason,
        updated_at=state.updated_at,
        evidence=_json_object(dict(state.evidence)),
    )


def _environment_navigation_state_model(
    state: InterfaceEnvironmentNavigationState,
) -> ApiInterfaceEnvironmentNavigationState:
    return ApiInterfaceEnvironmentNavigationState(
        status=state.status,
        source_kind=state.source_kind,
        accepted=state.accepted,
        actor_id=_public_actor_id(state.actor_id),
        environment_id=state.environment_id,
        environment_session_id=state.environment_session_id,
        environment_navigation_context_id=state.environment_navigation_context_id,
        key=state.key,
        process_id=state.process_id,
        thread_id=state.thread_id,
        branch_id=state.branch_id,
        projection_hash=state.projection_hash,
        root_object_id=state.root_object_id,
        commit_id=state.commit_id,
        object_instance_graph_commit_id=state.object_instance_graph_commit_id,
        blockers=list(state.blockers),
        error=state.error,
        reason=state.reason,
        updated_at=state.updated_at,
        evidence=_json_object(dict(state.evidence)),
    )


def _environment_session_state_model(
    state: InterfaceEnvironmentSessionState,
) -> ApiInterfaceEnvironmentSessionState:
    return ApiInterfaceEnvironmentSessionState(
        status=state.status,
        source_kind=state.source_kind,
        accepted=state.accepted,
        actor_id=_public_actor_id(state.actor_id),
        environment_id=state.environment_id,
        environment_profile_id=state.environment_profile_id,
        environment_session_id=state.environment_session_id,
        environment_session_key=state.environment_session_key,
        identity_session_id=state.identity_session_id,
        identity_member_id=state.identity_member_id,
        identity_actor_role_count=state.identity_actor_role_count,
        blockers=list(state.blockers),
        error=state.error,
        reason=state.reason,
        updated_at=state.updated_at,
        evidence=_json_object(dict(state.evidence)),
    )


def _experience_lens_action_state_model(
    state: InterfaceExperienceLensActionState,
) -> ApiInterfaceExperienceLensActionState:
    return ApiInterfaceExperienceLensActionState(
        action_key=state.action_key,
        action_kind=state.action_kind,
        target_ref=state.target_ref,
        label=state.label,
        view_invocation_action_config_id=state.view_invocation_action_config_id,
        experience_invocation_action_config_id=(
            state.experience_invocation_action_config_id
        ),
        api_capability_endpoint_id=state.api_capability_endpoint_id,
        sdk_operation_id=state.sdk_operation_id,
    )


def _experience_lens_state_model(
    state: InterfaceExperienceLensState,
) -> ApiInterfaceExperienceLensState:
    return ApiInterfaceExperienceLensState(
        status=state.status,
        source_kind=state.source_kind,
        accepted=state.accepted,
        actor_id=_public_actor_id(state.actor_id),
        environment_id=state.environment_id,
        environment_session_id=state.environment_session_id,
        environment_navigation_context_id=state.environment_navigation_context_id,
        experience_name=state.experience_name,
        view_ref=state.view_ref,
        section_key=state.section_key,
        observable_id=state.observable_id,
        section_graph_binding_key=state.section_graph_binding_key,
        projection_experience_view_instance_id=(
            state.projection_experience_view_instance_id
        ),
        projection_experience_graph_identity_id=(
            state.projection_experience_graph_identity_id
        ),
        object_projection_graph_identity_id=state.object_projection_graph_identity_id,
        focus_scope_id=state.focus_scope_id,
        focus_id=state.focus_id,
        action_count=state.action_count,
        actions=[_experience_lens_action_state_model(item) for item in state.actions],
        blockers=list(state.blockers),
        error=state.error,
        reason=state.reason,
        updated_at=state.updated_at,
        evidence=_json_object(dict(state.evidence)),
    )


def _app_screen_state_model(
    state: InterfaceAppScreenState,
) -> ApiInterfaceAppScreenState:
    return ApiInterfaceAppScreenState(
        status=state.status,
        accepted=state.accepted,
        app_package_id=state.app_package_id,
        app_package_branch_id=state.app_package_branch_id,
        app_package_object_instance_graph_commit_id=(
            state.app_package_object_instance_graph_commit_id
        ),
        app_config_id=state.app_config_id,
        app_config_object_instance_graph_commit_id=(
            state.app_config_object_instance_graph_commit_id
        ),
        app_config_screen_config_id=state.app_config_screen_config_id,
        screen_key=state.screen_key,
        projection_experience_id=state.projection_experience_id,
        projection_experience_branch_id=state.projection_experience_branch_id,
        projection_experience_head_commit_id=(
            state.projection_experience_head_commit_id
        ),
        projection_experience_layout_graph_binding_id=(
            state.projection_experience_layout_graph_binding_id
        ),
        experience_name=state.experience_name,
        layout_binding_key=state.layout_binding_key,
        blockers=list(state.blockers),
        error=state.error,
        reason=state.reason,
        updated_at=state.updated_at,
        evidence=_json_object(dict(state.evidence)),
    )


def _renderer_pane_package_capability_model(
    state: InterfaceHostServiceRendererPanePackageCapabilityState,
) -> ApiInterfaceRendererPanePackageCapabilityState:
    return ApiInterfaceRendererPanePackageCapabilityState(
        pane_package_id=state.pane_package_id,
        pane_package_name=state.pane_package_name,
        pane_kind=state.pane_kind,
    )


def _renderer_view_capability_model(
    state: InterfaceHostServiceRendererViewCapabilityState,
) -> ApiInterfaceRendererViewCapabilityState:
    return ApiInterfaceRendererViewCapabilityState(
        view_ref=state.view_ref,
        projection_view_key=state.projection_view_key,
        pane_kind=state.pane_kind,
        has_decoder=state.has_decoder,
    )


def _renderer_cache_capability_model(
    state: InterfaceHostServiceRendererCacheCapabilityState,
) -> ApiInterfaceRendererCacheCapabilityState:
    return ApiInterfaceRendererCacheCapabilityState(
        store_kind=state.store_kind,
        supports_namespace_replace=state.supports_namespace_replace,
        supports_persistent_storage=state.supports_persistent_storage,
        supports_cursor_lookup=state.supports_cursor_lookup,
    )


def _renderer_capabilities_model(
    state: InterfaceHostServiceRendererCapabilitiesState,
) -> ApiInterfaceRendererCapabilitiesState:
    return ApiInterfaceRendererCapabilitiesState(
        renderer_id=state.renderer_id,
        renderer_kind=state.renderer_kind,
        renderer_version=state.renderer_version,
        interface_package_id=state.interface_package_id,
        interface_package_name=state.interface_package_name,
        experience_keys=list(state.experience_keys),
        pane_packages=[
            _renderer_pane_package_capability_model(item)
            for item in state.pane_packages
        ],
        view_capabilities=[
            _renderer_view_capability_model(item) for item in state.view_capabilities
        ],
        cache=(
            _renderer_cache_capability_model(state.cache)
            if state.cache is not None
            else None
        ),
        reported_at=state.reported_at,
    )


def _service_renderer_pane_package_capability_state(
    state: ApiInterfaceRendererPanePackageCapabilityState,
) -> InterfaceHostServiceRendererPanePackageCapabilityState:
    return InterfaceHostServiceRendererPanePackageCapabilityState(
        pane_package_id=state.pane_package_id,
        pane_package_name=state.pane_package_name,
        pane_kind=state.pane_kind,
    )


def _service_renderer_view_capability_state(
    state: ApiInterfaceRendererViewCapabilityState,
) -> InterfaceHostServiceRendererViewCapabilityState:
    return InterfaceHostServiceRendererViewCapabilityState(
        view_ref=state.view_ref,
        projection_view_key=state.projection_view_key,
        pane_kind=state.pane_kind,
        has_decoder=state.has_decoder,
    )


def _service_renderer_cache_capability_state(
    state: ApiInterfaceRendererCacheCapabilityState,
) -> InterfaceHostServiceRendererCacheCapabilityState:
    return InterfaceHostServiceRendererCacheCapabilityState(
        store_kind=state.store_kind,
        supports_namespace_replace=state.supports_namespace_replace,
        supports_persistent_storage=state.supports_persistent_storage,
        supports_cursor_lookup=state.supports_cursor_lookup,
    )


def _service_renderer_capabilities_state(
    state: ApiInterfaceRendererCapabilitiesState,
) -> InterfaceHostServiceRendererCapabilitiesState:
    return InterfaceHostServiceRendererCapabilitiesState(
        renderer_id=state.renderer_id,
        renderer_kind=state.renderer_kind,
        renderer_version=state.renderer_version,
        interface_package_id=state.interface_package_id,
        interface_package_name=state.interface_package_name,
        experience_keys=tuple(state.experience_keys),
        pane_packages=tuple(
            _service_renderer_pane_package_capability_state(item)
            for item in state.pane_packages
        ),
        view_capabilities=tuple(
            _service_renderer_view_capability_state(item)
            for item in state.view_capabilities
        ),
        cache=(
            _service_renderer_cache_capability_state(state.cache)
            if state.cache is not None
            else None
        ),
        reported_at=state.reported_at,
    )


def _local_service_host_state_model(
    state: InterfaceHostServiceLocalServiceHostState,
) -> ApiInterfaceLocalServiceHostState:
    return ApiInterfaceLocalServiceHostState(
        managed=state.managed,
        supported=state.supported,
        socket_path=state.socket_path,
        available=state.available,
        ready=state.ready,
        status=state.status,
        host_id=state.host_id,
        host_version=state.host_version,
        protocol_version=state.protocol_version,
        capabilities=list(state.capabilities),
        error=state.error,
        probe_duration_ms=state.probe_duration_ms,
        last_checked_at=state.last_checked_at,
    )


def _local_node_runtime_state_model(
    state: InterfaceHostServiceLocalNodeRuntimeState,
) -> ApiInterfaceLocalNodeRuntimeState:
    return ApiInterfaceLocalNodeRuntimeState(
        managed=state.managed,
        available=state.available,
        ready=state.ready,
        phase=state.phase,
        active_target_id=state.active_target_id,
        target_key=state.target_key,
        display_name=state.display_name,
        backend_kind=state.backend_kind,
        is_active=state.is_active,
        is_healthy=state.is_healthy,
        node_base_url=state.node_base_url,
        node_websocket_path=state.node_websocket_path,
        summary=state.summary,
        error=state.error,
        updated_at=state.updated_at,
        recent_log_lines=list(state.recent_log_lines),
        target_statuses=[
            _operation_target_state_model(item) for item in state.target_statuses
        ],
    )


def _hosted_runtime_service_state_model(
    state: InterfaceHostServiceHostedRuntimeServiceState,
) -> ApiInterfaceHostedRuntimeServiceState:
    return ApiInterfaceHostedRuntimeServiceState(
        service_name=state.service_name,
        endpoint_refs=list(state.endpoint_refs),
        stream_endpoint_refs=list(state.stream_endpoint_refs),
    )


def _hosted_service_requirement_state_model(
    state: InterfaceHostServiceHostedServiceRequirementState,
) -> ApiInterfaceHostedServiceRequirementState:
    return ApiInterfaceHostedServiceRequirementState(
        service_name=state.service_name,
        service_label=state.service_label,
        is_required=state.is_required,
        status=state.status,
        source_kind=state.source_kind,
        summary=state.summary,
        error=state.error,
        matched_runtime_host_id=state.matched_runtime_host_id,
        endpoint_refs=list(state.endpoint_refs),
        stream_endpoint_refs=list(state.stream_endpoint_refs),
    )


def _hosted_runtime_state_model(
    state: InterfaceHostServiceHostedRuntimeState,
) -> ApiInterfaceHostedRuntimeState:
    return ApiInterfaceHostedRuntimeState(
        host_id=state.host_id,
        host_version=state.host_version,
        protocol_version=state.protocol_version,
        readiness_status=state.readiness_status,
        is_ready=state.is_ready,
        is_alive=state.is_alive,
        supports_stream_events=state.supports_stream_events,
        summary=state.summary,
        error=state.error,
        updated_at=state.updated_at,
        probe_duration_ms=state.probe_duration_ms,
        services=[_hosted_runtime_service_state_model(item) for item in state.services],
    )


def _hosted_services_state_model(
    state: InterfaceHostServiceHostedServicesState,
) -> ApiInterfaceHostedServicesState:
    return ApiInterfaceHostedServicesState(
        available=state.available,
        source_kind=state.source_kind,
        updated_at=state.updated_at,
        error=state.error,
        refresh_duration_ms=state.refresh_duration_ms,
        runtime_count=state.runtime_count,
        service_count=state.service_count,
        required_service_count=state.required_service_count,
        satisfied_service_count=state.satisfied_service_count,
        service_requirements=[
            _hosted_service_requirement_state_model(item)
            for item in state.service_requirements
        ],
        runtimes=[_hosted_runtime_state_model(item) for item in state.runtimes],
    )


def _backend_state_model(state: InterfaceBackendState) -> ApiInterfaceBackendState:
    return ApiInterfaceBackendState(
        available=state.available,
        manifest_path=(
            str(state.manifest_path) if state.manifest_path is not None else None
        ),
        registry_path=(
            str(state.registry_path) if state.registry_path is not None else None
        ),
        database_path=(
            str(state.database_path) if state.database_path is not None else None
        ),
        database_exists=state.database_exists,
        environment_id=state.environment_id,
        opg_count=state.opg_count,
        projection_bundle_available=state.projection_bundle_available,
        projection_plan_count=state.projection_plan_count,
        table_count=state.table_count,
        reason=state.reason,
    )


def _current_screen_model(
    state: InterfaceHostServiceCurrentScreen,
) -> ApiInterfaceCurrentScreen:
    return ApiInterfaceCurrentScreen(
        screen_kind=state.screen_kind,
        screen_key=state.screen_key,
        source_kind=state.source_kind,
        title=state.title,
        message=state.message,
        window_id=state.window_id,
        section_id=state.section_id,
        focus_scope_id=state.focus_scope_id,
        focus_id=state.focus_id,
        branch_id=state.branch_id,
        projection_view_id=state.projection_view_id,
        pane_key=state.pane_key,
    )


def _allowed_action_model(
    state: InterfaceHostServiceAllowedAction,
) -> ApiInterfaceAllowedAction:
    return ApiInterfaceAllowedAction(
        action_key=state.action_key,
        label=state.label,
        enabled=state.enabled,
        reason=state.reason,
        payload_schema_hint=state.payload_schema_hint,
    )


def _recovery_capability_state_model(
    state: InterfaceHostServiceRecoveryCapabilityState,
) -> ApiInterfaceHostRecoveryCapabilityState:
    return ApiInterfaceHostRecoveryCapabilityState(
        key=state.key,
        label=state.label,
        enabled=state.enabled,
        reason=state.reason,
        action_key=state.action_key,
    )


def _control_plane_trace_entry_model(
    state: InterfaceHostServiceControlPlaneTraceEntry,
) -> ApiInterfaceControlPlaneTraceEntry:
    return ApiInterfaceControlPlaneTraceEntry(
        step_id=state.step_id,
        source_key=state.source_key,
        source_label=state.source_label,
        message=state.message,
        step_label=state.step_label,
    )


def _control_plane_trace_group_model(
    state: InterfaceHostServiceControlPlaneTraceGroup,
) -> ApiInterfaceControlPlaneTraceGroup:
    return ApiInterfaceControlPlaneTraceGroup(
        step_id=state.step_id,
        step_title=state.step_title,
        status=state.status,
        current=state.current,
        selected=state.selected,
        entries=[_control_plane_trace_entry_model(item) for item in state.entries],
    )


def _control_plane_step_model(
    state: InterfaceHostServiceControlPlaneOrchestrationStep,
) -> ApiInterfaceControlPlaneOrchestrationStep:
    return ApiInterfaceControlPlaneOrchestrationStep(
        step_id=state.step_id,
        title=state.title,
        kind=state.kind,
        status=state.status,
        phase=state.phase,
        summary=state.summary,
        current=state.current,
        selected=state.selected,
        trace_preview=[
            _control_plane_trace_entry_model(item) for item in state.trace_preview
        ],
    )


def _control_plane_workspace_model(
    state: InterfaceHostServiceControlPlaneWorkspaceState,
) -> ApiInterfaceControlPlaneWorkspaceState:
    return ApiInterfaceControlPlaneWorkspaceState(
        selected_step_id=state.selected_step_id,
        current_step_id=state.current_step_id,
        orchestration_steps=[
            _control_plane_step_model(item) for item in state.orchestration_steps
        ],
        grouped_trace_preview=[
            _control_plane_trace_group_model(item)
            for item in state.grouped_trace_preview
        ],
    )


def _control_plane_profile_model(
    state: InterfaceHostServiceControlPlaneProfileState,
) -> ApiInterfaceControlPlaneProfileState:
    return ApiInterfaceControlPlaneProfileState(
        profile_id=state.profile_id,
        title=state.title,
        kind=state.kind,
        summary=state.summary,
        selected=state.selected,
        gate_keys=list(state.gate_keys),
        current_gate_key=state.current_gate_key,
    )


def _control_plane_profiles_model(
    state: InterfaceHostServiceControlPlaneProfilesState,
) -> ApiInterfaceControlPlaneProfilesState:
    return ApiInterfaceControlPlaneProfilesState(
        active_profile_id=state.active_profile_id,
        profiles=[_control_plane_profile_model(item) for item in state.profiles],
    )


def _workspace_candidate_model(
    state: InterfaceHostServiceWorkspaceCandidate,
) -> ApiInterfaceWorkspaceCandidate:
    return ApiInterfaceWorkspaceCandidate(
        selector_key=state.selector_key,
        label=state.label,
        workspace_root=str(state.workspace_root),
        registry_source=state.registry_source,
        compatibility_mode=state.compatibility_mode,
        workspace_toml_path=(
            str(state.workspace_toml_path)
            if state.workspace_toml_path is not None
            else None
        ),
        summary=state.summary,
        environment_count=state.environment_count,
        api_count=state.api_count,
        service_count=state.service_count,
        experience_count=state.experience_count,
        interface_count=state.interface_count,
        lifecycle=(
            _workspace_lifecycle_state_model(state.lifecycle)
            if state.lifecycle is not None
            else None
        ),
    )


def _workspace_lifecycle_state_model(
    state: InterfaceHostServiceWorkspaceLifecycleState,
) -> ApiInterfaceWorkspaceLifecycleState:
    return ApiInterfaceWorkspaceLifecycleState(
        status=state.status,
        summary=state.summary,
        error=state.error,
        joined=state.joined,
        attached_namespace_count=state.attached_namespace_count,
        joinable=state.joinable,
        startable=state.startable,
        recoverable=state.recoverable,
        leaveable=state.leaveable,
        stoppable=state.stoppable,
        safety_reason=state.safety_reason,
    )


def _workspace_semantic_package_state_model(
    state: InterfaceHostServiceWorkspaceSemanticPackageState,
) -> ApiInterfaceWorkspaceSemanticPackageState:
    return ApiInterfaceWorkspaceSemanticPackageState(
        package_kind=state.package_kind,
        package_name=state.package_name,
        manifest_path=state.manifest_path,
        workspace_relative_path=state.workspace_relative_path,
        title=state.title,
        fqn_prefix=state.fqn_prefix,
        object_config_graph_id=state.object_config_graph_id,
        object_config_graph_package_id=state.object_config_graph_package_id,
        semantic_branch_id=state.semantic_branch_id,
    )


def _workspace_committed_semantic_package_state_model(
    state: InterfaceHostServiceWorkspaceCommittedSemanticPackageState,
) -> ApiInterfaceWorkspaceCommittedSemanticPackageState:
    return ApiInterfaceWorkspaceCommittedSemanticPackageState(
        selector_key=state.selector_key,
        family_key=state.family_key,
        family_title=state.family_title,
        package_kind=state.package_kind,
        label=state.label,
        module_name=state.module_name,
        package_name=state.package_name,
        aware_toml_path=state.aware_toml_path,
        manifest_relative_path=state.manifest_relative_path,
        package_root=state.package_root,
        sources_root=state.sources_root,
        fqn_prefix=state.fqn_prefix,
        object_config_graph_id=state.object_config_graph_id,
        object_config_graph_package_id=state.object_config_graph_package_id,
    )


def _workspace_committed_semantic_package_family_model(
    state: InterfaceHostServiceWorkspaceCommittedSemanticPackageFamilyState,
) -> ApiInterfaceWorkspaceCommittedSemanticPackageFamilyState:
    return ApiInterfaceWorkspaceCommittedSemanticPackageFamilyState(
        family_key=state.family_key,
        title=state.title,
        members=[
            _workspace_committed_semantic_package_state_model(item)
            for item in state.members
        ],
    )


def _workspace_semantic_preview_model(
    state: InterfaceHostServiceWorkspaceSemanticObjectConfigGraphPreviewState,
) -> ApiInterfaceWorkspaceSemanticPreviewState:
    return ApiInterfaceWorkspaceSemanticPreviewState(
        package_kind=state.package_kind,
        package_name=state.package_name,
        manifest_path=state.manifest_path,
        object_config_graph_id=state.object_config_graph_id,
        materialization=(
            _workspace_materialization_state_ref_model(state.materialization)
            if state.materialization is not None
            else None
        ),
        materialize_invocation_id=state.materialize_invocation_id,
        materialize_receipt_path=state.materialize_receipt_path,
        lane_branch_id=state.lane_branch_id,
        object_config_graph=_json_object(state.object_config_graph),
    )


def _workspace_semantic_source_model(
    state: InterfaceHostServiceWorkspaceSemanticSourceState,
) -> ApiInterfaceWorkspaceSemanticState:
    return ApiInterfaceWorkspaceSemanticState(
        source_mode=state.source_mode,
        summary=state.summary,
        error=state.error,
        materialization=(
            _workspace_materialization_state_ref_model(state.materialization)
            if state.materialization is not None
            else None
        ),
        materialize_invocation_id=state.materialize_invocation_id,
        materialize_receipt_path=state.materialize_receipt_path,
        semantic_packages=[
            _workspace_semantic_package_state_model(item)
            for item in state.semantic_packages
        ],
        committed_semantic_packages=[
            _workspace_committed_semantic_package_state_model(item)
            for item in state.committed_semantic_packages
        ],
        committed_semantic_package_families=[
            _workspace_committed_semantic_package_family_model(item)
            for item in state.committed_semantic_package_families
        ],
        preview_graph=(
            _workspace_semantic_preview_model(state.preview_graph)
            if state.preview_graph is not None
            else None
        ),
    )


def _workspace_materialization_state_ref_model(
    state: InterfaceHostServiceWorkspaceMaterializationStateRef,
) -> ApiInterfaceWorkspaceMaterializationStateRef:
    return ApiInterfaceWorkspaceMaterializationStateRef(
        source_kind=state.source_kind,
        status=state.status,
        invocation_id=state.invocation_id,
        receipt_path=state.receipt_path,
        latest_path=state.latest_path,
        workspace_materialization_id=state.workspace_materialization_id,
        workspace_materialization_commit_id=state.workspace_materialization_commit_id,
        workspace_materialization_head_commit_id=(
            state.workspace_materialization_head_commit_id
        ),
    )


def _selected_semantic_package_state_model(
    state: InterfaceHostServiceSelectedSemanticPackageState,
) -> ApiInterfaceSelectedSemanticPackageState:
    return ApiInterfaceSelectedSemanticPackageState(
        package=_workspace_committed_semantic_package_state_model(state.package),
        preview_status=state.preview_status,
        summary=state.summary,
        error=state.error,
        preview_graph=(
            _workspace_semantic_preview_model(state.preview_graph)
            if state.preview_graph is not None
            else None
        ),
    )


def _workspace_discovery_state_model(
    state: InterfaceHostServiceWorkspaceDiscoveryState,
) -> ApiInterfaceWorkspaceDiscoveryState:
    return ApiInterfaceWorkspaceDiscoveryState(
        selection_required=state.selection_required,
        selected_selector_key=state.selected_selector_key,
        candidates=[_workspace_candidate_model(item) for item in state.candidates],
        error=state.error,
    )


def _selected_workspace_state_model(
    state: InterfaceHostServiceSelectedWorkspaceState,
) -> ApiInterfaceSelectedWorkspaceState:
    return ApiInterfaceSelectedWorkspaceState(
        selector_key=state.selector_key,
        label=state.label,
        workspace_root=str(state.workspace_root),
        registry_source=state.registry_source,
        compatibility_mode=state.compatibility_mode,
        workspace_toml_path=(
            str(state.workspace_toml_path)
            if state.workspace_toml_path is not None
            else None
        ),
        summary=state.summary,
        environment_count=state.environment_count,
        api_count=state.api_count,
        service_count=state.service_count,
        experience_count=state.experience_count,
        interface_count=state.interface_count,
        lifecycle=(
            _workspace_lifecycle_state_model(state.lifecycle)
            if state.lifecycle is not None
            else None
        ),
        semantic_source=(
            _workspace_semantic_source_model(state.semantic_source)
            if state.semantic_source is not None
            else None
        ),
    )


def _operation_target_state_model(
    state: InterfaceHostServiceOperationTargetState,
) -> ApiInterfaceOperationTargetState:
    return ApiInterfaceOperationTargetState(
        target_id=state.target_id,
        display_name=state.display_name,
        kind=state.kind,
        endpoint=state.endpoint,
        phase=state.phase,
        is_active=state.is_active,
        is_healthy=state.is_healthy,
        summary=state.summary,
        error=state.error,
        detail_lines=list(state.detail_lines),
    )


def _operation_state_model(
    state: InterfaceHostServiceOperationState,
) -> ApiInterfaceOperationState:
    return ApiInterfaceOperationState(
        operation_key=state.operation_key,
        title=state.title,
        status=state.status,
        phase=state.phase,
        current_target_id=state.current_target_id,
        current_target_title=state.current_target_title,
        summary=state.summary,
        error=state.error,
        running=state.running,
        retryable=state.retryable,
        updated_at=state.updated_at,
        recent_activity=list(state.recent_activity),
        target_statuses=[
            _operation_target_state_model(item) for item in state.target_statuses
        ],
    )


def _gate_step_model(step: InterfaceGateStep) -> ApiInterfaceGateStep:
    return ApiInterfaceGateStep(
        key=step.key,
        status=step.status,
        title=step.title,
        description=step.description,
    )


def _gate_state_model(state: InterfaceGateState) -> ApiInterfaceGateState:
    return ApiInterfaceGateState(
        destination_key=state.destination_key,
        active_step_key=state.active_step_key,
        blocked=state.blocked,
        steps=[_gate_step_model(step) for step in state.steps],
        reason=state.reason,
    )


def _resolved_view_model(state: InterfaceResolvedView) -> ApiInterfaceResolvedView:
    return ApiInterfaceResolvedView(
        experience_key=state.experience_key,
        interface_package_id=state.interface_package_id,
        interface_package_name=state.interface_package_name,
        projection_view_id=state.projection_view_id,
        host_payload=_json_object(state.host_payload),
    )


def _resolved_pane_descriptor_model(
    state: InterfaceResolvedPaneDescriptor,
) -> ApiInterfaceResolvedPaneDescriptor:
    return ApiInterfaceResolvedPaneDescriptor(
        window_key=state.window_key,
        layout_key=state.layout_key,
        section_key=state.section_key,
        layout_config_section_config_id=state.layout_config_section_config_id,
        layout_section_id=state.layout_section_id,
        section_focus_scope_id=state.section_focus_scope_id,
        focus_scope_id=state.focus_scope_id,
        focus_id=state.focus_id,
        branch_id=state.branch_id,
        focus_target=(
            _attention_focus_target_state_model(state.focus_target)
            if state.focus_target is not None
            else None
        ),
        pane_kind=state.pane_kind,
        pane_config_id=state.pane_config_id,
        pane_package_id=state.pane_package_id,
        pane_package_name=state.pane_package_name,
        object_projection_graph_observable_id=state.object_projection_graph_observable_id,
        projection_experience_graph_identity_id=(
            state.projection_experience_graph_identity_id
        ),
        object_projection_graph_identity_id=state.object_projection_graph_identity_id,
        section_graph_binding_key=state.section_graph_binding_key,
        projection_experience_view_id=state.projection_experience_view_id,
        projection_view_id=state.projection_view_id,
        view_ref=state.view_ref,
        projection_view_key=state.projection_view_key,
        state_model_id=state.state_model_id,
        title=state.title,
        summary=state.summary,
        narrative_key=state.narrative_key,
        state_source_kind=state.state_source_kind,
        state_projection_hash=state.state_projection_hash,
        action_keys=list(state.action_keys),
    )


def _materialized_pane_state_model(
    state: InterfaceMaterializedPaneState,
) -> ApiInterfaceMaterializedPaneState:
    return ApiInterfaceMaterializedPaneState(
        pane_state_key=state.pane_state_key,
        window_key=state.window_key,
        layout_key=state.layout_key,
        section_key=state.section_key,
        pane_kind=state.pane_kind,
        pane_config_id=state.pane_config_id,
        pane_package_id=state.pane_package_id,
        focus_scope_id=state.focus_scope_id,
        branch_id=state.branch_id,
        projection_experience_view_id=state.projection_experience_view_id,
        projection_view_id=state.projection_view_id,
        state_model_id=state.state_model_id,
        projection_hash=state.projection_hash,
        status=state.status,
        head_commit_id=state.head_commit_id,
        graph_hash_post=state.graph_hash_post,
        materialized_at=state.materialized_at,
        state=_json_object(state.state),
        provenance=_json_object(state.provenance),
        error=state.error,
    )


def _runtime_pane_render_spec_state_model(
    state: InterfaceRuntimePaneRenderSpecState,
) -> ApiInterfaceRuntimePaneRenderSpecState:
    return ApiInterfaceRuntimePaneRenderSpecState(
        source_kind=state.source_kind,
        branch_id=state.branch_id,
        projection_hash=state.projection_hash,
        last_commit_id=state.last_commit_id,
        object_instance_graph_commit_id=state.object_instance_graph_commit_id,
        pane_render_spec_id=state.pane_render_spec_id,
        pane_config_id=(state.pane_config_id),
        render_spec_content_hash_sha256=state.render_spec_content_hash_sha256,
        payload=_json_object(state.payload),
    )


def _runtime_layout_state_model(
    state: InterfaceRuntimeLayoutState,
) -> ApiInterfaceRuntimeLayoutState:
    return ApiInterfaceRuntimeLayoutState(
        layout_config_id=state.layout_config_id,
        layout_key=state.layout_key,
        label=state.label,
        is_default=state.is_default,
        is_active=state.is_active,
    )


def _runtime_focus_state_model(
    state: InterfaceRuntimeFocusState,
) -> ApiInterfaceRuntimeFocusState:
    return ApiInterfaceRuntimeFocusState(
        layout_config_id=state.layout_config_id,
        layout_key=state.layout_key,
        section_key=state.section_key,
        layout_config_section_config_id=state.layout_config_section_config_id,
        layout_section_id=state.layout_section_id,
        section_focus_scope_id=state.section_focus_scope_id,
        focus_scope_id=state.focus_scope_id,
        focus_id=state.focus_id,
        observable_id=state.observable_id,
        focus_target=(
            _attention_focus_target_state_model(state.focus_target)
            if state.focus_target is not None
            else None
        ),
    )


def _attention_focus_target_state_model(
    state: object,
) -> ApiInterfaceAttentionFocusTargetState:
    return ApiInterfaceAttentionFocusTargetState(
        kind=getattr(state, "kind"),
        focus_id=getattr(state, "focus_id"),
        focus_scope_id=getattr(state, "focus_scope_id"),
        projection_experience_graph_identity_id=getattr(
            state,
            "projection_experience_graph_identity_id",
        ),
        object_projection_graph_identity_id=getattr(
            state,
            "object_projection_graph_identity_id",
        ),
        object_instance_graph_branch_id=getattr(
            state,
            "object_instance_graph_branch_id",
        ),
        projection_hash=getattr(state, "projection_hash"),
        target_type=getattr(state, "target_type"),
        target_id=getattr(state, "target_id"),
        description=getattr(state, "description"),
    )


def _runtime_section_representation_state_model(
    state: InterfaceRuntimeSectionRepresentationState,
) -> ApiInterfaceRuntimeSectionRepresentationState:
    return ApiInterfaceRuntimeSectionRepresentationState(
        representation_id=state.representation_id,
        window_key=state.window_key,
        layout_config_id=state.layout_config_id,
        layout_key=state.layout_key,
        section_key=state.section_key,
        layout_config_section_config_id=state.layout_config_section_config_id,
        pane_name=state.pane_name,
        pane_kind=state.pane_kind,
        label=state.label,
        observable_id=state.observable_id,
        projection_experience_graph_identity_id=(
            state.projection_experience_graph_identity_id
        ),
        object_projection_graph_identity_id=state.object_projection_graph_identity_id,
        section_graph_binding_key=state.section_graph_binding_key,
        view_ref=state.view_ref,
        projection_view_key=state.projection_view_key,
        is_active=state.is_active,
    )


def _runtime_package_state_model(
    state: InterfaceRuntimeState,
    *,
    resolved_view: InterfaceResolvedView | None,
    interface_config_bundle: InterfaceConfigBundle,
) -> ApiInterfaceRuntimePackageState:
    experience_key = (
        resolved_view.experience_key.strip()
        if resolved_view is not None and resolved_view.experience_key.strip()
        else None
    )
    warnings: list[str] = []
    if (
        resolved_view is not None
        and resolved_view.interface_package_id is not None
        and resolved_view.interface_package_id
        != interface_config_bundle.interface_package_id
    ):
        warnings.append("interface_package_runtime_id_mismatch")
    if (
        resolved_view is not None
        and resolved_view.interface_package_name is not None
        and resolved_view.interface_package_name.strip().casefold()
        != interface_config_bundle.interface_package_name.strip().casefold()
    ):
        warnings.append("interface_package_runtime_name_mismatch")
    return ApiInterfaceRuntimePackageState(
        source_kind="interface_host_config_bundle",
        interface_package_id=interface_config_bundle.interface_package_id,
        interface_package_name=interface_config_bundle.interface_package_name,
        experience_keys=[experience_key] if experience_key is not None else [],
        layouts=[_runtime_layout_state_model(item) for item in state.layout_states],
        section_representations=[
            _runtime_section_representation_state_model(item)
            for item in state.section_representations
        ],
        apis=[
            ApiInterfaceRuntimePackageApiState(
                interface_name=interface_config_bundle.name,
                interface_config_id=interface_config_bundle.interface_config_id,
                interface_config_api_id=item.interface_config_api_id,
                api_id=item.api_id,
                api_ref=item.api_ref,
            )
            for item in interface_config_bundle.apis
        ],
        dynamic_pane_render_specs=[
            _runtime_pane_render_spec_state_model(item)
            for item in state.dynamic_pane_render_specs
        ],
        warnings=warnings,
    )


def _window_layout_section_state_model(
    state: InterfaceWindowLayoutSectionState,
) -> ApiInterfaceWindowLayoutSectionState:
    return ApiInterfaceWindowLayoutSectionState.model_validate(
        {
            "section_key": state.section_key,
            "layout_config_section_config_id": (state.layout_config_section_config_id),
            "layout_section_id": state.layout_section_id,
            "attention_session_section_id": state.attention_session_section_id,
            "title": state.title,
            "description": state.description,
            "order": state.order,
            "flex": state.flex,
            "weight_micros": state.weight_micros,
            "is_visible": state.is_visible,
            "is_collapsed": state.is_collapsed,
            "projection_view_id": state.projection_view_id,
            "pane_key": state.pane_key,
        }
    )


def _window_layout_state_model(
    state: InterfaceWindowLayoutState,
) -> ApiInterfaceWindowLayoutState:
    return ApiInterfaceWindowLayoutState.model_validate(
        {
            "source_kind": state.source_kind,
            "window_key": state.window_key,
            "layout_key": state.layout_key,
            "layout_config_id": state.layout_config_id,
            "attention_session_id": state.attention_session_id,
            "attention_session_layout_id": state.attention_session_layout_id,
            "active_layout_transition_id": state.active_layout_transition_id,
            "active_topology_transition_id": state.active_topology_transition_id,
            "object_instance_graph_commit_id": (state.object_instance_graph_commit_id),
            "graph_hash_post": state.graph_hash_post,
            "title": state.title,
            "description": state.description,
            "frame_mode": state.frame_mode,
            "version_hash": state.version_hash,
            "resolved_at": state.resolved_at,
            "stale": state.stale,
            "admitted_sections": [
                _window_layout_section_state_model(item)
                for item in state.admitted_sections
            ],
            "sections": [
                _window_layout_section_state_model(item) for item in state.sections
            ],
        }
    )


def _window_layout_state_payload(
    state: InterfaceWindowLayoutState,
) -> JsonObject:
    return _json_object(_window_layout_state_model(state).model_dump(mode="json"))


def _runtime_window_navigation_context_state_model(
    state: InterfaceRuntimeWindowNavigationContextState,
) -> ApiInterfaceRuntimeWindowNavigationContextState:
    return ApiInterfaceRuntimeWindowNavigationContextState(
        source_kind=state.source_kind,
        environment_navigation_context_id=state.environment_navigation_context_id,
        thread_id=state.thread_id,
        interface_window_navigation_context_id=state.interface_window_navigation_context_id,
        interface_environment_id=state.interface_environment_id,
        environment_id=state.environment_id,
        process_id=state.process_id,
        evidence=_json_object(state.evidence),
    )


def _runtime_window_state_model(
    state: InterfaceRuntimeWindowState,
) -> ApiInterfaceRuntimeWindowState:
    return ApiInterfaceRuntimeWindowState(
        source_kind=state.source_kind,
        window_key=state.window_key,
        active=state.active,
        interface_id=state.interface_id,
        interface_window_id=state.interface_window_id,
        window_id=state.window_id,
        title=state.title,
        active_navigation_context=(
            _runtime_window_navigation_context_state_model(
                state.active_navigation_context
            )
            if state.active_navigation_context is not None
            else None
        ),
        active_layout_id=state.active_layout_id,
        active_layout_config_id=state.active_layout_config_id,
        active_layout_key=state.active_layout_key,
        active_layout_source_kind=state.active_layout_source_kind,
        interface_projection_hash=state.interface_projection_hash,
        window_projection_hash=state.window_projection_hash,
        interface_head_commit_id=state.interface_head_commit_id,
        window_head_commit_id=state.window_head_commit_id,
        evidence=_json_object(state.evidence),
    )


def _runtime_state_model(
    state: InterfaceRuntimeState,
    *,
    interface_config_bundle: InterfaceConfigBundle | None = None,
    view_state_cursor: ApiInterfaceHostViewStateCursorState | None = None,
) -> ApiInterfaceRuntimeState:
    resolved_view = state.resolved_view
    if state.window_layout is not None:
        payload = dict(resolved_view.host_payload) if resolved_view is not None else {}
        payload["window_layout"] = _window_layout_state_payload(state.window_layout)
        resolved_view = InterfaceResolvedView(
            experience_key=(
                resolved_view.experience_key
                if resolved_view is not None
                else "aware.interface.bootstrap"
            ),
            interface_package_id=(
                resolved_view.interface_package_id
                if resolved_view is not None
                else None
            ),
            interface_package_name=(
                resolved_view.interface_package_name
                if resolved_view is not None
                else None
            ),
            projection_view_id=(
                resolved_view.projection_view_id
                if resolved_view is not None
                else "entry.control-plane"
            ),
            host_payload=payload,
        )
    return ApiInterfaceRuntimeState(
        backend=_backend_state_model(state.backend),
        gate_state=(
            _gate_state_model(state.gate_state)
            if state.gate_state is not None
            else None
        ),
        resolved_view=(
            _resolved_view_model(resolved_view) if resolved_view is not None else None
        ),
        window_layout=(
            _window_layout_state_model(state.window_layout)
            if state.window_layout is not None
            else None
        ),
        active_window=(
            _runtime_window_state_model(state.active_window)
            if state.active_window is not None
            else None
        ),
        windows=[_runtime_window_state_model(item) for item in state.windows],
        active_layout_config_id=state.active_layout_config_id,
        layout_states=[
            _runtime_layout_state_model(item) for item in state.layout_states
        ],
        active_focus=(
            _runtime_focus_state_model(state.active_focus)
            if state.active_focus is not None
            else None
        ),
        interface_package_runtime=(
            _runtime_package_state_model(
                state,
                resolved_view=resolved_view,
                interface_config_bundle=interface_config_bundle,
            )
            if interface_config_bundle is not None
            else None
        ),
        section_representations=[
            _runtime_section_representation_state_model(item)
            for item in state.section_representations
        ],
        resolved_panes=[
            _resolved_pane_descriptor_model(item) for item in state.resolved_panes
        ],
        view_state_cursor=view_state_cursor or _runtime_view_state_cursor_model(state),
        materialized_pane_states=[
            _materialized_pane_state_model(item)
            for item in state.materialized_pane_states
        ],
        dynamic_pane_render_specs=[
            _runtime_pane_render_spec_state_model(item)
            for item in state.dynamic_pane_render_specs
        ],
        warnings=list(state.warnings),
    )


def _active_runtime_representation_id(
    state: InterfaceHostServiceState,
) -> UUID | None:
    runtime_state = state.runtime
    if runtime_state is None:
        return None
    active_representation = next(
        (item for item in runtime_state.section_representations if item.is_active),
        None,
    )
    if active_representation is not None:
        return active_representation.representation_id
    active_focus = runtime_state.active_focus
    if active_focus is None:
        return None
    return next(
        (
            item.representation_id
            for item in runtime_state.section_representations
            if item.observable_id == active_focus.observable_id
            and item.section_key.strip().casefold()
            == (active_focus.section_key or "").strip().casefold()
        ),
        None,
    )


def _host_state_model(
    state: InterfaceHostServiceState,
    *,
    view_state_cursor: ApiInterfaceHostViewStateCursorState | None = None,
) -> InterfaceHostState:
    return InterfaceHostState(
        host_label=state.host_label,
        namespace=state.namespace,
        endpoint=state.endpoint,
        environment_id=state.environment_id,
        environment_config_id=state.environment_config_id,
        started=state.started,
        transport=_transport_state_model(state.transport),
        renderer_capabilities=(
            _renderer_capabilities_model(state.renderer_capabilities)
            if state.renderer_capabilities is not None
            else None
        ),
        local_service_host=(
            _local_service_host_state_model(state.local_service_host)
            if state.local_service_host is not None
            else None
        ),
        local_node_runtime=(
            _local_node_runtime_state_model(state.local_node_runtime)
            if state.local_node_runtime is not None
            else None
        ),
        hosted_services=(
            _hosted_services_state_model(state.hosted_services)
            if state.hosted_services is not None
            else None
        ),
        lane_sync=(
            _lane_sync_state_model(state.lane_sync)
            if state.lane_sync is not None
            else None
        ),
        environment_admission=(
            _environment_admission_state_model(state.environment_admission)
            if state.environment_admission is not None
            else None
        ),
        environment_session=(
            _environment_session_state_model(state.environment_session)
            if state.environment_session is not None
            else None
        ),
        environment_navigation=(
            _environment_navigation_state_model(state.environment_navigation)
            if state.environment_navigation is not None
            else None
        ),
        environment_admission_receipt=state.environment_admission_receipt,
        environment_session_join_receipt=state.environment_session_join_receipt,
        experience_lens=(
            _experience_lens_state_model(state.experience_lens)
            if state.experience_lens is not None
            else None
        ),
        app_screen=(
            _app_screen_state_model(state.app_screen)
            if state.app_screen is not None
            else None
        ),
        runtime=(
            _runtime_state_model(
                state.runtime,
                interface_config_bundle=state.interface_config_bundle,
                view_state_cursor=view_state_cursor,
            )
            if state.runtime is not None
            else None
        ),
        control_plane_profiles=(
            _control_plane_profiles_model(state.control_plane_profiles)
            if state.control_plane_profiles is not None
            else None
        ),
        control_plane_workspace=(
            _control_plane_workspace_model(state.control_plane_workspace)
            if state.control_plane_workspace is not None
            else None
        ),
        workspace_discovery=(
            _workspace_discovery_state_model(state.workspace_discovery)
            if state.workspace_discovery is not None
            else None
        ),
        selected_workspace=(
            _selected_workspace_state_model(state.selected_workspace)
            if state.selected_workspace is not None
            else None
        ),
        selected_semantic_package=(
            _selected_semantic_package_state_model(state.selected_semantic_package)
            if state.selected_semantic_package is not None
            else None
        ),
        current_screen=(
            _current_screen_model(state.current_screen)
            if state.current_screen is not None
            else None
        ),
        current_operation=(
            _operation_state_model(state.current_operation)
            if state.current_operation is not None
            else None
        ),
        allowed_actions=[
            _allowed_action_model(action) for action in state.allowed_actions
        ],
        recovery_capabilities=[
            _recovery_capability_state_model(capability)
            for capability in state.recovery_capabilities
        ],
        warnings=list(state.warnings),
    )


def _hosted_namespace_model(
    state: InterfaceHostedNamespaceState,
) -> HostedInterfaceNamespace:
    return HostedInterfaceNamespace(
        namespace=state.namespace,
        host_label=state.host_label,
        started=state.started,
        actor_id=_public_actor_id(state.actor_id),
        interface_id=state.interface_id,
        interface_session_id=state.interface_session_id,
        environment_id=state.environment_id,
        environment_config_id=state.environment_config_id,
        warnings=list(state.warnings),
    )


__all__ = [
    "InterfaceControlPlane",
    "InterfaceControlPlaneServer",
]

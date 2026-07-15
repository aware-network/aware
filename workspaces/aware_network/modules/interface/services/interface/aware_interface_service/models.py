from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentNavigationCommitReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
    EnvironmentSessionView,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_interface import InterfaceRuntimeState
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)


JsonObject = dict[str, object]


@dataclass(frozen=True, slots=True)
class InterfaceHostAttentionLayoutTransitionResult:
    outcome: str
    state: "InterfaceHostServiceState"
    conflict_reason: str | None = None
    active_layout_transition_id: UUID | None = None
    active_topology_transition_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    graph_hash_post: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostAttentionLayoutTopologyTransitionResult:
    outcome: str
    state: "InterfaceHostServiceState"
    conflict_reason: str | None = None
    active_topology_transition_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    graph_hash_post: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceCurrentScreen:
    screen_kind: str
    screen_key: str
    source_kind: str
    title: str | None = None
    message: str | None = None
    window_id: UUID | None = None
    section_id: UUID | None = None
    focus_scope_id: UUID | None = None
    focus_id: UUID | None = None
    branch_id: UUID | None = None
    projection_view_id: str | None = None
    pane_key: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceAllowedAction:
    action_key: str
    label: str
    enabled: bool = True
    reason: str | None = None
    payload_schema_hint: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceRecoveryCapabilityState:
    key: str
    label: str
    enabled: bool = False
    reason: str | None = None
    action_key: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceWorkspaceCandidate:
    selector_key: str
    label: str
    workspace_root: Path
    registry_source: str
    compatibility_mode: bool = False
    workspace_toml_path: Path | None = None
    summary: str | None = None
    environment_count: int = 0
    api_count: int = 0
    service_count: int = 0
    experience_count: int = 0
    interface_count: int = 0
    lifecycle: "InterfaceHostServiceWorkspaceLifecycleState | None" = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceWorkspaceDiscoveryState:
    selection_required: bool = False
    selected_selector_key: str | None = None
    candidates: tuple[InterfaceHostServiceWorkspaceCandidate, ...] = ()
    error: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceSelectedWorkspaceState:
    selector_key: str
    label: str
    workspace_root: Path
    registry_source: str
    compatibility_mode: bool = False
    workspace_toml_path: Path | None = None
    summary: str | None = None
    environment_count: int = 0
    api_count: int = 0
    service_count: int = 0
    experience_count: int = 0
    interface_count: int = 0
    lifecycle: "InterfaceHostServiceWorkspaceLifecycleState | None" = None
    semantic_source: "InterfaceHostServiceWorkspaceSemanticSourceState | None" = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceWorkspaceLifecycleState:
    status: str = "unknown"
    summary: str | None = None
    error: str | None = None
    joined: bool = False
    attached_namespace_count: int = 0
    joinable: bool = False
    startable: bool = False
    recoverable: bool = False
    leaveable: bool = False
    stoppable: bool = False
    safety_reason: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceWorkspaceSemanticPackageState:
    package_kind: str
    package_name: str
    manifest_path: str
    workspace_relative_path: str | None = None
    title: str | None = None
    fqn_prefix: str | None = None
    object_config_graph_id: str | None = None
    object_config_graph_package_id: str | None = None
    semantic_branch_id: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceWorkspaceCommittedSemanticPackageState:
    selector_key: str
    family_key: str
    family_title: str
    package_kind: str
    label: str
    module_name: str
    package_name: str
    aware_toml_path: str
    manifest_relative_path: str
    package_root: str
    sources_root: str | None = None
    fqn_prefix: str = ""
    object_config_graph_id: str = ""
    object_config_graph_package_id: str = ""


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceWorkspaceCommittedSemanticPackageFamilyState:
    family_key: str
    title: str
    members: tuple[
        "InterfaceHostServiceWorkspaceCommittedSemanticPackageState", ...
    ] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceWorkspaceMaterializationStateRef:
    source_kind: str
    status: str | None = None
    invocation_id: str | None = None
    receipt_path: str | None = None
    latest_path: str | None = None
    workspace_materialization_id: str | None = None
    workspace_materialization_commit_id: str | None = None
    workspace_materialization_head_commit_id: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceWorkspaceSemanticObjectConfigGraphPreviewState:
    package_kind: str
    package_name: str
    manifest_path: str
    object_config_graph_id: str
    materialize_invocation_id: str
    materialize_receipt_path: str
    lane_branch_id: str
    object_config_graph: dict[str, object]
    materialization: "InterfaceHostServiceWorkspaceMaterializationStateRef | None" = (
        None
    )


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceWorkspaceSemanticSourceState:
    source_mode: str = "bundle_backed"
    summary: str | None = None
    error: str | None = None
    materialization: "InterfaceHostServiceWorkspaceMaterializationStateRef | None" = (
        None
    )
    materialize_invocation_id: str | None = None
    materialize_receipt_path: str | None = None
    semantic_packages: tuple[
        "InterfaceHostServiceWorkspaceSemanticPackageState",
        ...,
    ] = ()
    committed_semantic_packages: tuple[
        "InterfaceHostServiceWorkspaceCommittedSemanticPackageState",
        ...,
    ] = ()
    committed_semantic_package_families: tuple[
        "InterfaceHostServiceWorkspaceCommittedSemanticPackageFamilyState",
        ...,
    ] = ()
    preview_graph: (
        "InterfaceHostServiceWorkspaceSemanticObjectConfigGraphPreviewState | None"
    ) = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceSelectedSemanticPackageState:
    package: "InterfaceHostServiceWorkspaceCommittedSemanticPackageState"
    preview_status: str = "none"
    summary: str | None = None
    error: str | None = None
    preview_graph: (
        "InterfaceHostServiceWorkspaceSemanticObjectConfigGraphPreviewState | None"
    ) = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceOperationTargetState:
    target_id: str
    display_name: str
    kind: str | None = None
    endpoint: str | None = None
    phase: str = "idle"
    is_active: bool = False
    is_healthy: bool = False
    summary: str | None = None
    error: str | None = None
    detail_lines: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceOperationState:
    operation_key: str
    title: str | None = None
    status: str = "idle"
    phase: str | None = None
    current_target_id: str | None = None
    current_target_title: str | None = None
    summary: str | None = None
    error: str | None = None
    running: bool = False
    retryable: bool = False
    updated_at: str | None = None
    recent_activity: tuple[str, ...] = ()
    target_statuses: tuple[InterfaceHostServiceOperationTargetState, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceControlPlaneTraceEntry:
    step_id: str | None
    source_key: str
    source_label: str
    message: str
    step_label: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceControlPlaneTraceGroup:
    step_id: str
    step_title: str
    status: str
    current: bool = False
    selected: bool = False
    entries: tuple[InterfaceHostServiceControlPlaneTraceEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceControlPlaneOrchestrationStep:
    step_id: str
    title: str
    kind: str | None = None
    status: str = "idle"
    phase: str | None = None
    summary: str | None = None
    current: bool = False
    selected: bool = False
    trace_preview: tuple[InterfaceHostServiceControlPlaneTraceEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceControlPlaneWorkspaceState:
    selected_step_id: str | None = None
    current_step_id: str | None = None
    orchestration_steps: tuple[
        InterfaceHostServiceControlPlaneOrchestrationStep, ...
    ] = ()
    grouped_trace_preview: tuple[InterfaceHostServiceControlPlaneTraceGroup, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceControlPlaneProfileState:
    profile_id: str
    title: str
    kind: str
    summary: str | None = None
    selected: bool = False
    gate_keys: tuple[str, ...] = ()
    current_gate_key: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceControlPlaneProfilesState:
    active_profile_id: str
    profiles: tuple[InterfaceHostServiceControlPlaneProfileState, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceLocalServiceHostState:
    managed: bool = False
    supported: bool = False
    socket_path: str | None = None
    available: bool = False
    ready: bool = False
    status: str = "absent"
    host_id: str | None = None
    host_version: str | None = None
    protocol_version: str | None = None
    capabilities: tuple[str, ...] = ()
    error: str | None = None
    recent_log_lines: tuple[str, ...] = ()
    probe_duration_ms: int | None = None
    last_checked_at: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceLocalNodeRuntimeState:
    managed: bool = False
    available: bool = False
    ready: bool = False
    phase: str = "idle"
    active_target_id: str | None = None
    target_key: str | None = None
    display_name: str | None = None
    backend_kind: str | None = None
    is_active: bool = False
    is_healthy: bool = False
    node_base_url: str | None = None
    node_websocket_path: str | None = None
    summary: str | None = None
    error: str | None = None
    updated_at: str | None = None
    recent_log_lines: tuple[str, ...] = ()
    target_statuses: tuple[InterfaceHostServiceOperationTargetState, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceTransportState:
    available: bool
    registered: bool
    authenticated: bool
    actor_id: UUID | None = None
    interface_id: UUID | None = None
    interface_system_actor_id: UUID | None = None
    interface_system_identity_id: UUID | None = None
    interface_session_id: UUID | None = None
    session_label: str | None = None
    capabilities: tuple[str, ...] = ()
    protocol_version: int | None = None
    last_seen_at: str | None = None
    interface_identity_network_node_id: UUID | None = None
    interface_session_network_binding_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceRendererPanePackageCapabilityState:
    pane_package_id: UUID | None = None
    pane_package_name: str | None = None
    pane_kind: str = ""


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceRendererViewCapabilityState:
    view_ref: str | None = None
    projection_view_key: str | None = None
    pane_kind: str | None = None
    has_decoder: bool = False


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceRendererCacheCapabilityState:
    store_kind: str = "memory"
    supports_namespace_replace: bool = True
    supports_persistent_storage: bool = False
    supports_cursor_lookup: bool = False


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceRendererCapabilitiesState:
    renderer_id: str
    renderer_kind: str = "flutter"
    renderer_version: str | None = None
    interface_package_id: UUID | None = None
    interface_package_name: str | None = None
    experience_keys: tuple[str, ...] = ()
    pane_packages: tuple[
        InterfaceHostServiceRendererPanePackageCapabilityState,
        ...,
    ] = ()
    view_capabilities: tuple[
        InterfaceHostServiceRendererViewCapabilityState,
        ...,
    ] = ()
    cache: InterfaceHostServiceRendererCacheCapabilityState | None = None
    reported_at: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceLaneSyncState:
    enabled: bool
    watching: bool
    window_key: str | None = None
    lane_id: str | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    last_commit_id: str | None = None
    last_graph_hash_post: str | None = None
    updates_received: int = 0
    advanced_count: int = 0
    last_synced_at: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceEnvironmentAdmissionRoleEligibilityState:
    environment_profile_actor_config_id: UUID
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceEnvironmentAdmissionRoleBindingState:
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
class InterfaceEnvironmentAdmissionState:
    status: str = "inactive"
    source_kind: str = "environment_sdk_actor_admission"
    accepted: bool = False
    actor_id: UUID | None = None
    environment_id: UUID | None = None
    environment_profile_id: UUID | None = None
    environment_profile_actor_config_id: UUID | None = None
    actor_config_id: UUID | None = None
    class_instance_identity_id: UUID | None = None
    object_instance_graph_branch_key: str | None = None
    object_instance_graph_branch_id: UUID | None = None
    requested_role_config_ids: tuple[UUID, ...] = ()
    requested_role_config_names: tuple[str, ...] = ()
    eligible_role_count: int = 0
    binding_count: int = 0
    eligible_roles: tuple[InterfaceEnvironmentAdmissionRoleEligibilityState, ...] = ()
    bindings: tuple[InterfaceEnvironmentAdmissionRoleBindingState, ...] = ()
    blockers: tuple[str, ...] = ()
    error: str | None = None
    reason: str | None = None
    updated_at: str | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceEnvironmentNavigationState:
    status: str = "inactive"
    source_kind: str = "environment_attention_navigation"
    accepted: bool = False
    actor_id: UUID | None = None
    environment_id: UUID | None = None
    environment_session_id: UUID | None = None
    environment_navigation_context_id: UUID | None = None
    key: str | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    root_object_id: UUID | None = None
    commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    blockers: tuple[str, ...] = ()
    error: str | None = None
    reason: str | None = None
    updated_at: str | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceEnvironmentSessionState:
    status: str = "inactive"
    source_kind: str = "environment_session_join"
    accepted: bool = False
    actor_id: UUID | None = None
    environment_id: UUID | None = None
    environment_profile_id: UUID | None = None
    environment_session_id: UUID | None = None
    environment_session_key: str | None = None
    identity_session_id: UUID | None = None
    identity_member_id: UUID | None = None
    identity_actor_role_count: int = 0
    blockers: tuple[str, ...] = ()
    error: str | None = None
    reason: str | None = None
    updated_at: str | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceEnvironmentSessionJoinResult:
    state: "InterfaceHostServiceState"
    environment_session: EnvironmentSessionView | None = None
    environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = None
    environment_navigation_context: EnvironmentNavigationContextView | None = None
    default_navigation_receipt: EnvironmentNavigationCommitReceipt | None = None


@dataclass(frozen=True, slots=True)
class InterfaceEnvironmentEntryResult:
    state: "InterfaceHostServiceState"
    environment_session: EnvironmentSessionView | None = None
    environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = None
    environment_navigation_context: EnvironmentNavigationContextView | None = None
    default_navigation_receipt: EnvironmentNavigationCommitReceipt | None = None


@dataclass(frozen=True, slots=True)
class InterfaceEnvironmentNavigationSelectResult:
    state: "InterfaceHostServiceState"
    environment_navigation_context: EnvironmentNavigationContextView | None = None
    environment_navigation_receipt: EnvironmentNavigationCommitReceipt | None = None


@dataclass(frozen=True, slots=True)
class InterfaceExperienceLensActionState:
    action_key: str
    view_invocation_action_config_id: UUID
    action_kind: str | None = None
    target_ref: str | None = None
    label: str | None = None
    experience_invocation_action_config_id: UUID | None = None
    api_capability_endpoint_id: UUID | None = None
    sdk_operation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class InterfaceExperienceLensState:
    status: str = "inactive"
    source_kind: str = "experience_section_graph_binding"
    accepted: bool = False
    actor_id: UUID | None = None
    environment_id: UUID | None = None
    environment_session_id: UUID | None = None
    environment_navigation_context_id: UUID | None = None
    experience_name: str | None = None
    view_ref: str | None = None
    section_key: str | None = None
    observable_id: UUID | None = None
    section_graph_binding_key: str | None = None
    projection_experience_view_instance_id: UUID | None = None
    projection_experience_graph_identity_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    focus_scope_id: UUID | None = None
    focus_id: UUID | None = None
    action_count: int = 0
    actions: tuple[InterfaceExperienceLensActionState, ...] = ()
    blockers: tuple[str, ...] = ()
    error: str | None = None
    reason: str | None = None
    updated_at: str | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceAppScreenState:
    status: str = "inactive"
    accepted: bool = False
    app_package_id: UUID | None = None
    app_package_branch_id: UUID | None = None
    app_package_object_instance_graph_commit_id: UUID | None = None
    app_config_id: UUID | None = None
    app_config_object_instance_graph_commit_id: UUID | None = None
    app_config_screen_config_id: UUID | None = None
    screen_key: str | None = None
    projection_experience_id: UUID | None = None
    projection_experience_branch_id: UUID | None = None
    projection_experience_head_commit_id: UUID | None = None
    projection_experience_layout_graph_binding_id: UUID | None = None
    experience_name: str | None = None
    layout_binding_key: str | None = None
    blockers: tuple[str, ...] = ()
    error: str | None = None
    reason: str | None = None
    updated_at: str | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceAppScreenEntryResult:
    state: "InterfaceHostServiceState"
    app_screen: InterfaceAppScreenState


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceHostedRuntimeServiceState:
    service_name: str
    endpoint_refs: tuple[str, ...] = ()
    stream_endpoint_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceHostedServiceRequirementState:
    service_name: str
    service_label: str | None = None
    is_required: bool = True
    status: str = "missing"
    source_kind: str = "host_requirement"
    summary: str | None = None
    error: str | None = None
    matched_runtime_host_id: str | None = None
    endpoint_refs: tuple[str, ...] = ()
    stream_endpoint_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceHostedRuntimeState:
    host_id: str
    host_version: str | None = None
    protocol_version: str | None = None
    readiness_status: str = "unknown"
    is_ready: bool = False
    is_alive: bool = False
    supports_stream_events: bool = False
    summary: str | None = None
    error: str | None = None
    updated_at: str | None = None
    probe_duration_ms: int | None = None
    services: tuple[InterfaceHostServiceHostedRuntimeServiceState, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceHostedServicesState:
    available: bool = False
    source_kind: str = "node_control_plane"
    updated_at: str | None = None
    error: str | None = None
    refresh_duration_ms: int | None = None
    runtime_count: int = 0
    service_count: int = 0
    required_service_count: int | None = None
    satisfied_service_count: int | None = None
    service_requirements: tuple[
        InterfaceHostServiceHostedServiceRequirementState, ...
    ] = ()
    runtimes: tuple[InterfaceHostServiceHostedRuntimeState, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostedNamespaceState:
    namespace: str
    host_label: str
    started: bool
    actor_id: UUID | None = None
    interface_id: UUID | None = None
    interface_session_id: UUID | None = None
    environment_id: UUID | None = None
    environment_config_id: UUID | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class InterfaceExperienceSessionActorContext:
    actor_id: UUID
    actor_kind: str = "agent_operator"
    actor_source: str = "transport_binding"
    interface_id: UUID | None = None
    interface_system_identity_id: UUID | None = None
    interface_session_id: UUID | None = None
    session_label: str | None = None
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceExperienceSessionScope:
    namespace: str
    experience_name: str
    view_ref: str
    window_key: str
    layout_key: str | None
    section_key: str
    observable_id: UUID
    environment_id: UUID | None = None
    environment_session_id: UUID | None = None
    environment_navigation_context_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    thread_layout_id: UUID | None = None
    layout_config_id: UUID | None = None
    layout_config_section_config_id: UUID | None = None
    layout_section_id: UUID | None = None
    section_focus_scope_id: UUID | None = None
    focus_scope_id: UUID | None = None
    focus_id: UUID | None = None
    projection_view_key: str | None = None
    section_graph_binding_key: str | None = None
    projection_experience_graph_identity_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    object_instance_graph_branch_id: UUID | None = None
    projection_hash: str | None = None
    profile_key: str | None = None
    topology_seed_key: str | None = None
    source_kind: str = "interface_runtime_focus"


@dataclass(frozen=True, slots=True)
class InterfaceExperienceSessionFeatureDeclaration:
    feature_key: str
    reason: str = "interface_runtime_focus"
    config: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceExperienceSessionHandoffRequest:
    actor: InterfaceExperienceSessionActorContext
    scope: InterfaceExperienceSessionScope
    feature: InterfaceExperienceSessionFeatureDeclaration
    idempotency_key: str
    environment_admission: EnvironmentActorAdmissionReceipt | None = None
    environment_session_join: EnvironmentSessionJoinReceipt | None = None
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None
    experience_identity_session_config_id: UUID | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceExperienceSessionHandoffResult:
    request: InterfaceExperienceSessionHandoffRequest
    status: str
    admitted: bool = False
    feature_enabled: bool = False
    experience_session_id: str | None = None
    identity_session_id: UUID | None = None
    identity_member_id: UUID | None = None
    actor_admission_id: str | None = None
    feature_lease_id: str | None = None
    error: str | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceExperienceSessionHandoffState:
    status: str = "inactive"
    feature_key: str | None = None
    experience_name: str | None = None
    view_ref: str | None = None
    actor_id: UUID | None = None
    experience_session_id: str | None = None
    identity_session_id: UUID | None = None
    identity_member_id: UUID | None = None
    actor_admission_id: str | None = None
    feature_lease_id: str | None = None
    admitted: bool = False
    feature_enabled: bool = False
    idempotency_key: str | None = None
    error: str | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceExperienceSessionNarrationEventState:
    commit_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    narration_lines: tuple[str, ...] = ()
    operation_label: str | None = None
    graph_hash_post: str | None = None
    object_instance_graph_identity_id: UUID | None = None
    object_instance_graph_branch_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    projection_experience_graph_identity_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    semantics: JsonObject = field(default_factory=dict)
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceExperienceSessionNarrationState:
    status: str = "inactive"
    feature_key: str | None = None
    experience_name: str | None = None
    view_ref: str | None = None
    actor_id: UUID | None = None
    feature_lease_id: str | None = None
    event_count: int = 0
    last_commit_id: UUID | None = None
    events: tuple[InterfaceExperienceSessionNarrationEventState, ...] = ()
    error: str | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceState:
    host_label: str
    repository_root: Path
    state_home: Path | None
    namespace: str
    endpoint: str | None
    environment_id: UUID | None
    environment_config_id: UUID | None
    started: bool
    transport: InterfaceHostServiceTransportState
    renderer_capabilities: InterfaceHostServiceRendererCapabilitiesState | None = None
    local_service_host: InterfaceHostServiceLocalServiceHostState | None = None
    local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None = None
    hosted_services: InterfaceHostServiceHostedServicesState | None = None
    lane_sync: InterfaceHostServiceLaneSyncState | None = None
    environment_admission: InterfaceEnvironmentAdmissionState | None = None
    environment_session: InterfaceEnvironmentSessionState | None = None
    environment_navigation: InterfaceEnvironmentNavigationState | None = None
    environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None
    environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = None
    experience_lens: InterfaceExperienceLensState | None = None
    app_screen: InterfaceAppScreenState | None = None
    runtime: InterfaceRuntimeState | None = None
    interface_config_bundle: InterfaceConfigBundle | None = None
    control_plane_profiles: InterfaceHostServiceControlPlaneProfilesState | None = None
    control_plane_workspace: InterfaceHostServiceControlPlaneWorkspaceState | None = (
        None
    )
    workspace_discovery: InterfaceHostServiceWorkspaceDiscoveryState | None = None
    selected_workspace: InterfaceHostServiceSelectedWorkspaceState | None = None
    selected_semantic_package: (
        InterfaceHostServiceSelectedSemanticPackageState | None
    ) = None
    current_screen: InterfaceHostServiceCurrentScreen | None = None
    current_operation: InterfaceHostServiceOperationState | None = None
    allowed_actions: tuple[InterfaceHostServiceAllowedAction, ...] = field(
        default_factory=tuple
    )
    recovery_capabilities: tuple[InterfaceHostServiceRecoveryCapabilityState, ...] = (
        field(default_factory=tuple)
    )
    experience_session_handoff: (
        InterfaceHostServiceExperienceSessionHandoffState | None
    ) = None
    experience_session_narration: (
        InterfaceHostServiceExperienceSessionNarrationState | None
    ) = None
    warnings: tuple[str, ...] = field(default_factory=tuple)


__all__ = [
    "InterfaceAppScreenEntryResult",
    "InterfaceAppScreenState",
    "InterfaceEnvironmentAdmissionRoleBindingState",
    "InterfaceEnvironmentAdmissionRoleEligibilityState",
    "InterfaceEnvironmentAdmissionState",
    "InterfaceEnvironmentEntryResult",
    "InterfaceEnvironmentNavigationSelectResult",
    "InterfaceEnvironmentNavigationState",
    "InterfaceEnvironmentSessionJoinResult",
    "InterfaceEnvironmentSessionState",
    "InterfaceExperienceLensActionState",
    "InterfaceExperienceLensState",
    "InterfaceExperienceSessionActorContext",
    "InterfaceExperienceSessionFeatureDeclaration",
    "InterfaceExperienceSessionHandoffRequest",
    "InterfaceExperienceSessionHandoffResult",
    "InterfaceExperienceSessionNarrationEventState",
    "InterfaceExperienceSessionScope",
    "InterfaceHostServiceAllowedAction",
    "InterfaceHostServiceControlPlaneProfileState",
    "InterfaceHostServiceControlPlaneProfilesState",
    "InterfaceHostServiceControlPlaneOrchestrationStep",
    "InterfaceHostServiceControlPlaneTraceEntry",
    "InterfaceHostServiceControlPlaneTraceGroup",
    "InterfaceHostServiceControlPlaneWorkspaceState",
    "InterfaceHostServiceCurrentScreen",
    "InterfaceHostServiceHostedRuntimeServiceState",
    "InterfaceHostServiceHostedServiceRequirementState",
    "InterfaceHostServiceHostedRuntimeState",
    "InterfaceHostServiceHostedServicesState",
    "InterfaceHostedNamespaceState",
    "InterfaceHostServiceLaneSyncState",
    "InterfaceHostServiceLocalNodeRuntimeState",
    "InterfaceHostServiceLocalServiceHostState",
    "InterfaceHostServiceOperationState",
    "InterfaceHostServiceOperationTargetState",
    "InterfaceHostServiceRecoveryCapabilityState",
    "InterfaceHostServiceRendererCacheCapabilityState",
    "InterfaceHostServiceRendererCapabilitiesState",
    "InterfaceHostServiceRendererPanePackageCapabilityState",
    "InterfaceHostServiceRendererViewCapabilityState",
    "InterfaceHostServiceSelectedSemanticPackageState",
    "InterfaceHostServiceExperienceSessionHandoffState",
    "InterfaceHostServiceExperienceSessionNarrationState",
    "InterfaceHostServiceState",
    "InterfaceHostServiceTransportState",
    "InterfaceHostServiceSelectedWorkspaceState",
    "InterfaceHostServiceWorkspaceCommittedSemanticPackageFamilyState",
    "InterfaceHostServiceWorkspaceCommittedSemanticPackageState",
    "InterfaceHostServiceWorkspaceSemanticObjectConfigGraphPreviewState",
    "InterfaceHostServiceWorkspaceSemanticPackageState",
    "InterfaceHostServiceWorkspaceSemanticSourceState",
    "InterfaceHostServiceWorkspaceLifecycleState",
    "InterfaceHostServiceWorkspaceCandidate",
    "InterfaceHostServiceWorkspaceDiscoveryState",
]

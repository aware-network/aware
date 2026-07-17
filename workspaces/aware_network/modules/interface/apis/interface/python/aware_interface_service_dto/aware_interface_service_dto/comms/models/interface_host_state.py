from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Environment Service Dto
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionJoinReceipt,
)

# Types
from aware_types import JsonObject


class InterfaceTransportState(BaseModel):
    """
    Transport-facing state snapshots exposed by the local Interface daemon.
    These DTOs are not SSOT graph entities. They are local control-plane read
    models that summarize the live host service state for renderer and CLI clients.
    """

    # Attributes
    available: bool
    registered: bool
    authenticated: bool
    actor_id: UUID | None = Field(default=None)
    interface_id: UUID | None = Field(default=None)
    interface_system_actor_id: UUID | None = Field(default=None)
    interface_system_identity_id: UUID | None = Field(default=None)
    interface_session_id: UUID | None = Field(default=None)
    session_label: str | None = Field(default=None)
    capabilities: list[str] = Field(default_factory=list)
    protocol_version: int | None = Field(default=None)
    last_seen_at: str | None = Field(default=None)
    interface_identity_network_node_id: UUID | None = Field(default=None)
    interface_session_network_binding_id: UUID | None = Field(default=None)


class InterfaceRendererPanePackageCapabilityState(BaseModel):
    # Attributes
    pane_package_id: UUID | None = Field(default=None)
    pane_package_name: str | None = Field(default=None)
    pane_kind: str


class InterfaceRendererViewCapabilityState(BaseModel):
    # Attributes
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    pane_kind: str | None = Field(default=None)
    has_decoder: bool = Field(default=False)


class InterfaceRendererCacheCapabilityState(BaseModel):
    # Attributes
    store_kind: str = Field(default="memory")
    supports_namespace_replace: bool = Field(default=True)
    supports_persistent_storage: bool = Field(default=False)
    supports_cursor_lookup: bool = Field(default=False)


class InterfaceRendererCapabilitiesState(BaseModel):
    # Attributes
    renderer_id: str
    renderer_kind: str = Field(default="flutter")
    renderer_version: str | None = Field(default=None)
    interface_package_id: UUID | None = Field(default=None)
    interface_package_name: str | None = Field(default=None)
    experience_keys: list[str] = Field(default_factory=list)
    pane_packages: list[InterfaceRendererPanePackageCapabilityState] = Field(default_factory=list)
    view_capabilities: list[InterfaceRendererViewCapabilityState] = Field(default_factory=list)
    cache: InterfaceRendererCacheCapabilityState | None = Field(default=None)
    reported_at: str | None = Field(default=None)


class InterfaceHostViewStateDigestEntryState(BaseModel):
    # Attributes
    pane_state_key: str
    digest: str
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    head_commit_id: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)


class InterfaceHostViewStateCursorState(BaseModel):
    # Attributes
    cursor: str
    digest: str
    materialized_entry_count: int = Field(default=0)
    entry_digests: list[InterfaceHostViewStateDigestEntryState] = Field(default_factory=list)
    computed_at: str | None = Field(default=None)


class InterfaceLaneSyncState(BaseModel):
    # Attributes
    enabled: bool
    watching: bool
    window_key: str | None = Field(default=None)
    lane_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    last_commit_id: UUID | None = Field(default=None)
    last_graph_hash_post: str | None = Field(default=None)
    updates_received: int = Field(default=0)
    advanced_count: int = Field(default=0)
    last_synced_at: str | None = Field(default=None)
    error: str | None = Field(default=None)


class InterfaceEnvironmentAdmissionRoleEligibilityState(BaseModel):
    # Attributes
    environment_profile_actor_config_id: UUID
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = Field(default=None)


class InterfaceEnvironmentAdmissionRoleBindingState(BaseModel):
    # Attributes
    environment_profile_actor_config_id: UUID
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = Field(default=None)
    actor_id: UUID
    role_id: UUID
    actor_role_id: UUID
    role_class_instance_id: UUID
    class_instance_identity_id: UUID
    role_config_class_config_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_key: str
    object_instance_graph_branch_id: UUID | None = Field(default=None)


class InterfaceEnvironmentAdmissionState(BaseModel):
    # Attributes
    status: str = Field(default="inactive")
    source_kind: str = Field(default="environment_sdk_actor_admission")
    accepted: bool = Field(default=False)
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    environment_profile_actor_config_id: UUID | None = Field(default=None)
    actor_config_id: UUID | None = Field(default=None)
    class_instance_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_key: str | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    requested_role_config_ids: list[UUID] = Field(default_factory=list)
    requested_role_config_names: list[str] = Field(default_factory=list)
    eligible_role_count: int = Field(default=0)
    binding_count: int = Field(default=0)
    eligible_roles: list[InterfaceEnvironmentAdmissionRoleEligibilityState] = Field(default_factory=list)
    bindings: list[InterfaceEnvironmentAdmissionRoleBindingState] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    error: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceEnvironmentNavigationState(BaseModel):
    # Attributes
    status: str = Field(default="inactive")
    source_kind: str = Field(default="environment_attention_navigation")
    accepted: bool = Field(default=False)
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_session_id: UUID | None = Field(default=None)
    environment_navigation_context_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    error: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceEnvironmentSessionState(BaseModel):
    # Attributes
    status: str = Field(default="inactive")
    source_kind: str = Field(default="environment_session_join")
    accepted: bool = Field(default=False)
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    environment_session_id: UUID | None = Field(default=None)
    environment_session_key: str | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    identity_member_id: UUID | None = Field(default=None)
    identity_actor_role_count: int = Field(default=0)
    blockers: list[str] = Field(default_factory=list)
    error: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceExperienceLensActionState(BaseModel):
    # Attributes
    action_key: str
    action_kind: str | None = Field(default=None)
    target_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    view_invocation_action_config_id: UUID
    experience_invocation_action_config_id: UUID | None = Field(default=None)
    api_capability_endpoint_id: UUID | None = Field(default=None)
    sdk_operation_id: UUID | None = Field(default=None)


class InterfaceExperienceLensState(BaseModel):
    # Attributes
    status: str = Field(default="inactive")
    source_kind: str = Field(default="experience_section_graph_binding")
    accepted: bool = Field(default=False)
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_session_id: UUID | None = Field(default=None)
    environment_navigation_context_id: UUID | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    section_key: str | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    section_graph_binding_key: str | None = Field(default=None)
    projection_experience_view_instance_id: UUID | None = Field(default=None)
    projection_experience_graph_identity_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    action_count: int = Field(default=0)
    actions: list[InterfaceExperienceLensActionState] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    error: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceAppScreenState(BaseModel):
    # Attributes
    status: str = Field(default="inactive")
    accepted: bool = Field(default=False)
    app_package_id: UUID | None = Field(default=None)
    app_package_branch_id: UUID | None = Field(default=None)
    app_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    app_config_id: UUID | None = Field(default=None)
    app_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    app_config_screen_config_id: UUID | None = Field(default=None)
    screen_key: str | None = Field(default=None)
    projection_experience_id: UUID | None = Field(default=None)
    projection_experience_branch_id: UUID | None = Field(default=None)
    projection_experience_head_commit_id: UUID | None = Field(default=None)
    projection_experience_layout_graph_binding_id: UUID | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    layout_binding_key: str | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    error: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceExperienceSessionNarrationEventState(BaseModel):
    # Attributes
    commit_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    narration_lines: list[str] = Field(default_factory=list)
    operation_label: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    projection_experience_graph_identity_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    semantics: JsonObject = Field(default_factory=JsonObject)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceExperienceSessionNarrationState(BaseModel):
    # Attributes
    status: str = Field(default="inactive")
    feature_key: str | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    feature_lease_id: str | None = Field(default=None)
    event_count: int = Field(default=0)
    last_commit_id: UUID | None = Field(default=None)
    events: list[InterfaceExperienceSessionNarrationEventState] = Field(default_factory=list)
    error: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceBackendState(BaseModel):
    # Attributes
    available: bool
    manifest_path: str | None = Field(default=None)
    registry_path: str | None = Field(default=None)
    database_path: str | None = Field(default=None)
    database_exists: bool
    environment_id: UUID | None = Field(default=None)
    opg_count: int
    projection_bundle_available: bool
    projection_plan_count: int
    table_count: int
    reason: str | None = Field(default=None)


class InterfaceLocalServiceHostState(BaseModel):
    # Attributes
    managed: bool = Field(default=False)
    supported: bool = Field(default=False)
    socket_path: str | None = Field(default=None)
    available: bool = Field(default=False)
    ready: bool = Field(default=False)
    status: str = Field(default="absent")
    host_id: str | None = Field(default=None)
    host_version: str | None = Field(default=None)
    protocol_version: str | None = Field(default=None)
    capabilities: list[str] = Field(default_factory=list)
    error: str | None = Field(default=None)
    probe_duration_ms: int | None = Field(default=None)
    last_checked_at: str | None = Field(default=None)


class InterfaceLocalNodeRuntimeState(BaseModel):
    # Attributes
    managed: bool = Field(default=False)
    available: bool = Field(default=False)
    ready: bool = Field(default=False)
    phase: str = Field(default="idle")
    active_target_id: str | None = Field(default=None)
    target_key: str | None = Field(default=None)
    display_name: str | None = Field(default=None)
    backend_kind: str | None = Field(default=None)
    is_active: bool = Field(default=False)
    is_healthy: bool = Field(default=False)
    node_base_url: str | None = Field(default=None)
    node_websocket_path: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    recent_log_lines: list[str] = Field(default_factory=list)
    target_statuses: list[InterfaceOperationTargetState] = Field(default_factory=list)


class InterfaceHostedRuntimeServiceState(BaseModel):
    # Attributes
    service_name: str
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)


class InterfaceHostedServiceRequirementState(BaseModel):
    # Attributes
    service_name: str
    service_label: str | None = Field(default=None)
    is_required: bool = Field(default=True)
    status: str = Field(default="missing")
    source_kind: str = Field(default="host_requirement")
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    matched_runtime_host_id: str | None = Field(default=None)
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)


class InterfaceHostedRuntimeState(BaseModel):
    # Attributes
    host_id: str
    host_version: str | None = Field(default=None)
    protocol_version: str | None = Field(default=None)
    readiness_status: str = Field(default="unknown")
    is_ready: bool = Field(default=False)
    is_alive: bool = Field(default=False)
    supports_stream_events: bool = Field(default=False)
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    probe_duration_ms: int | None = Field(default=None)
    services: list[InterfaceHostedRuntimeServiceState] = Field(default_factory=list)


class InterfaceHostedServicesState(BaseModel):
    # Attributes
    available: bool = Field(default=False)
    source_kind: str = Field(default="node_control_plane")
    updated_at: str | None = Field(default=None)
    error: str | None = Field(default=None)
    refresh_duration_ms: int | None = Field(default=None)
    runtime_count: int = Field(default=0)
    service_count: int = Field(default=0)
    required_service_count: int | None = Field(default=None)
    satisfied_service_count: int | None = Field(default=None)
    service_requirements: list[InterfaceHostedServiceRequirementState] = Field(default_factory=list)
    runtimes: list[InterfaceHostedRuntimeState] = Field(default_factory=list)


class InterfaceCurrentScreen(BaseModel):
    # Attributes
    screen_kind: str
    screen_key: str
    source_kind: str
    title: str | None = Field(default=None)
    message: str | None = Field(default=None)
    window_id: UUID | None = Field(default=None)
    section_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_view_id: str | None = Field(default=None)
    pane_key: str | None = Field(default=None)


class InterfaceAllowedAction(BaseModel):
    # Attributes
    action_key: str
    label: str
    enabled: bool = Field(default=True)
    reason: str | None = Field(default=None)
    payload_schema_hint: str | None = Field(default=None)


class InterfaceHostRecoveryCapabilityState(BaseModel):
    # Attributes
    key: str
    label: str
    enabled: bool = Field(default=False)
    reason: str | None = Field(default=None)
    action_key: str | None = Field(default=None)


class InterfaceWorkspaceCandidate(BaseModel):
    # Attributes
    selector_key: str
    label: str
    workspace_root: str
    registry_source: str
    compatibility_mode: bool = Field(default=False)
    workspace_toml_path: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    environment_count: int = Field(default=0)
    api_count: int = Field(default=0)
    service_count: int = Field(default=0)
    experience_count: int = Field(default=0)
    interface_count: int = Field(default=0)
    lifecycle: InterfaceWorkspaceLifecycleState | None = Field(default=None)


class InterfaceWorkspaceDiscoveryState(BaseModel):
    # Attributes
    selection_required: bool = Field(default=False)
    selected_selector_key: str | None = Field(default=None)
    candidates: list[InterfaceWorkspaceCandidate] = Field(default_factory=list)
    error: str | None = Field(default=None)


class InterfaceSelectedWorkspaceState(BaseModel):
    # Attributes
    selector_key: str
    label: str
    workspace_root: str
    registry_source: str
    compatibility_mode: bool = Field(default=False)
    workspace_toml_path: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    environment_count: int = Field(default=0)
    api_count: int = Field(default=0)
    service_count: int = Field(default=0)
    experience_count: int = Field(default=0)
    interface_count: int = Field(default=0)
    lifecycle: InterfaceWorkspaceLifecycleState | None = Field(default=None)
    semantic_source: InterfaceWorkspaceSemanticSourceState | None = Field(default=None)


class InterfaceWorkspaceLifecycleState(BaseModel):
    # Attributes
    status: str = Field(default="unknown")
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    joined: bool = Field(default=False)
    attached_namespace_count: int = Field(default=0)
    joinable: bool = Field(default=False)
    startable: bool = Field(default=False)
    recoverable: bool = Field(default=False)
    leaveable: bool = Field(default=False)
    stoppable: bool = Field(default=False)
    safety_reason: str | None = Field(default=None)


class InterfaceWorkspaceSemanticPackageState(BaseModel):
    # Attributes
    package_kind: str
    package_name: str
    manifest_path: str
    workspace_relative_path: str | None = Field(default=None)
    title: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    object_config_graph_id: str | None = Field(default=None)
    object_config_graph_package_id: str | None = Field(default=None)
    semantic_branch_id: str | None = Field(default=None)


class InterfaceWorkspaceCommittedSemanticPackageState(BaseModel):
    # Attributes
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
    sources_root: str | None = Field(default=None)
    fqn_prefix: str
    object_config_graph_id: str
    object_config_graph_package_id: str


class InterfaceWorkspaceCommittedSemanticPackageFamilyState(BaseModel):
    # Attributes
    family_key: str
    title: str
    members: list[InterfaceWorkspaceCommittedSemanticPackageState] = Field(default_factory=list)


class InterfaceWorkspaceMaterializationStateRef(BaseModel):
    # Attributes
    source_kind: str
    status: str | None = Field(default=None)
    invocation_id: str | None = Field(default=None)
    receipt_path: str | None = Field(default=None)
    latest_path: str | None = Field(default=None)
    workspace_materialization_id: str | None = Field(default=None)
    workspace_materialization_commit_id: str | None = Field(default=None)
    workspace_materialization_head_commit_id: str | None = Field(default=None)


class InterfaceWorkspaceSemanticObjectConfigGraphPreviewState(BaseModel):
    # Attributes
    package_kind: str
    package_name: str
    manifest_path: str
    object_config_graph_id: str
    materialization: InterfaceWorkspaceMaterializationStateRef | None = Field(default=None)
    materialize_invocation_id: str
    materialize_receipt_path: str
    lane_branch_id: str
    object_config_graph: JsonObject


class InterfaceWorkspaceSemanticSourceState(BaseModel):
    # Attributes
    source_mode: str = Field(default="bundle_backed")
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    materialization: InterfaceWorkspaceMaterializationStateRef | None = Field(default=None)
    materialize_invocation_id: str | None = Field(default=None)
    materialize_receipt_path: str | None = Field(default=None)
    semantic_packages: list[InterfaceWorkspaceSemanticPackageState] = Field(default_factory=list)
    committed_semantic_packages: list[InterfaceWorkspaceCommittedSemanticPackageState] = Field(default_factory=list)
    committed_semantic_package_families: list[InterfaceWorkspaceCommittedSemanticPackageFamilyState] = Field(
        default_factory=list
    )
    preview_graph: InterfaceWorkspaceSemanticObjectConfigGraphPreviewState | None = Field(default=None)


class InterfaceSelectedSemanticPackageState(BaseModel):
    # Attributes
    package: InterfaceWorkspaceCommittedSemanticPackageState
    preview_status: str = Field(default="none")
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    preview_graph: InterfaceWorkspaceSemanticObjectConfigGraphPreviewState | None = Field(default=None)


class InterfaceOperationTargetState(BaseModel):
    # Attributes
    target_id: str
    display_name: str
    kind: str | None = Field(default=None)
    endpoint: str | None = Field(default=None)
    phase: str = Field(default="idle")
    is_active: bool = Field(default=False)
    is_healthy: bool = Field(default=False)
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    detail_lines: list[str] = Field(default_factory=list)


class InterfaceOperationState(BaseModel):
    # Attributes
    operation_key: str
    title: str | None = Field(default=None)
    status: str
    phase: str | None = Field(default=None)
    current_target_id: str | None = Field(default=None)
    current_target_title: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    running: bool = Field(default=False)
    retryable: bool = Field(default=False)
    updated_at: str | None = Field(default=None)
    recent_activity: list[str] = Field(default_factory=list)
    target_statuses: list[InterfaceOperationTargetState] = Field(default_factory=list)


class InterfaceControlPlaneTraceEntry(BaseModel):
    # Attributes
    step_id: str | None = Field(default=None)
    source_key: str
    source_label: str
    message: str
    step_label: str | None = Field(default=None)


class InterfaceControlPlaneTraceGroup(BaseModel):
    # Attributes
    step_id: str
    step_title: str
    status: str
    current: bool = Field(default=False)
    selected: bool = Field(default=False)
    entries: list[InterfaceControlPlaneTraceEntry] = Field(default_factory=list)


class InterfaceControlPlaneOrchestrationStep(BaseModel):
    # Attributes
    step_id: str
    title: str
    kind: str | None = Field(default=None)
    status: str
    phase: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    current: bool = Field(default=False)
    selected: bool = Field(default=False)
    trace_preview: list[InterfaceControlPlaneTraceEntry] = Field(default_factory=list)


class InterfaceControlPlaneWorkspaceState(BaseModel):
    # Attributes
    selected_step_id: str | None = Field(default=None)
    current_step_id: str | None = Field(default=None)
    orchestration_steps: list[InterfaceControlPlaneOrchestrationStep] = Field(default_factory=list)
    grouped_trace_preview: list[InterfaceControlPlaneTraceGroup] = Field(default_factory=list)


class InterfaceControlPlaneProfileState(BaseModel):
    # Attributes
    profile_id: str
    title: str
    kind: str
    summary: str | None = Field(default=None)
    selected: bool = Field(default=False)
    gate_keys: list[str] = Field(default_factory=list)
    current_gate_key: str | None = Field(default=None)


class InterfaceControlPlaneProfilesState(BaseModel):
    # Attributes
    active_profile_id: str
    profiles: list[InterfaceControlPlaneProfileState] = Field(default_factory=list)


class InterfaceGateStep(BaseModel):
    # Attributes
    key: str
    status: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)


class InterfaceGateState(BaseModel):
    # Attributes
    destination_key: str | None = Field(default=None)
    active_step_key: str | None = Field(default=None)
    blocked: bool = Field(default=False)
    steps: list[InterfaceGateStep] = Field(default_factory=list)
    reason: str | None = Field(default=None)


class InterfaceResolvedView(BaseModel):
    # Attributes
    experience_key: str
    interface_package_id: UUID | None = Field(default=None)
    interface_package_name: str | None = Field(default=None)
    projection_view_id: str | None = Field(default=None)
    host_payload: JsonObject = Field(default_factory=JsonObject)


class InterfaceRuntimeLayoutState(BaseModel):
    # Attributes
    layout_config_id: UUID | None = Field(default=None)
    layout_key: str
    label: str
    is_active: bool = Field(default=False)


class InterfaceAttentionFocusTargetState(BaseModel):
    # Attributes
    kind: str = Field(default="constructor")
    focus_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    projection_experience_graph_identity_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    target_type: str | None = Field(default=None)
    target_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None)


class InterfaceRuntimeFocusState(BaseModel):
    # Attributes
    layout_config_id: UUID | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    section_key: str | None = Field(default=None)
    layout_config_section_config_id: UUID | None = Field(default=None)
    layout_section_id: UUID | None = Field(default=None)
    section_focus_scope_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    focus_target: InterfaceAttentionFocusTargetState | None = Field(default=None)


class InterfaceRuntimeSectionRepresentationState(BaseModel):
    # Attributes
    representation_id: UUID
    window_key: str
    layout_config_id: UUID | None = Field(default=None)
    layout_key: str
    section_key: str
    layout_config_section_config_id: UUID | None = Field(default=None)
    pane_name: str
    pane_kind: str
    label: str
    observable_id: UUID
    projection_experience_graph_identity_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    section_graph_binding_key: str | None = Field(default=None)
    view_ref: str
    projection_view_key: str | None = Field(default=None)
    is_active: bool = Field(default=False)


class InterfaceResolvedPaneDescriptor(BaseModel):
    # Attributes
    window_key: str
    layout_key: str
    section_key: str
    layout_config_section_config_id: UUID | None = Field(default=None)
    layout_section_id: UUID | None = Field(default=None)
    section_focus_scope_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    focus_target: InterfaceAttentionFocusTargetState | None = Field(default=None)
    pane_kind: str
    pane_config_id: UUID | None = Field(default=None)
    pane_package_id: UUID | None = Field(default=None)
    pane_package_name: str | None = Field(default=None)
    object_projection_graph_observable_id: UUID | None = Field(default=None)
    projection_experience_graph_identity_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    section_graph_binding_key: str | None = Field(default=None)
    projection_experience_view_id: UUID | None = Field(default=None)
    projection_view_id: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    state_model_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    narrative_key: str | None = Field(default=None)
    state_source_kind: str
    state_projection_hash: str | None = Field(default=None)
    action_keys: list[str] = Field(default_factory=list)


class InterfaceMaterializedPaneState(BaseModel):
    # Attributes
    pane_state_key: str
    window_key: str
    layout_key: str
    section_key: str
    pane_kind: str
    pane_config_id: UUID | None = Field(default=None)
    pane_package_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_experience_view_id: UUID | None = Field(default=None)
    projection_view_id: str | None = Field(default=None)
    state_model_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    status: str = Field(default="unknown")
    head_commit_id: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    materialized_at: str | None = Field(default=None)
    state: JsonObject = Field(default_factory=JsonObject)
    provenance: JsonObject = Field(default_factory=JsonObject)
    error: str | None = Field(default=None)


class InterfaceRuntimePaneRenderSpecState(BaseModel):
    # Attributes
    source_kind: str = Field(default="committed_oig")
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    last_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    pane_render_spec_id: UUID
    pane_config_id: UUID
    render_spec_content_hash_sha256: str | None = Field(default=None)
    payload: JsonObject = Field(default_factory=JsonObject)


class InterfaceRuntimePackageApiPackageState(BaseModel):
    # Attributes
    api_package_id: UUID | None = Field(default=None)
    api_package_name: str


class InterfaceRuntimePackageApiState(BaseModel):
    # Attributes
    interface_name: str | None = Field(default=None)
    interface_config_id: UUID | None = Field(default=None)
    interface_config_api_id: UUID | None = Field(default=None)
    api_id: UUID | None = Field(default=None)
    api_ref: str


class InterfaceRuntimePackageRenderComponentState(BaseModel):
    # Attributes
    component_ref: str
    display_name: str | None = Field(default=None)


class InterfaceRuntimePackageState(BaseModel):
    # Attributes
    source_kind: str = Field(default="interface_api")
    interface_package_id: UUID | None = Field(default=None)
    interface_package_name: str
    experience_keys: list[str] = Field(default_factory=list)
    layouts: list[InterfaceRuntimeLayoutState] = Field(default_factory=list)
    section_representations: list[InterfaceRuntimeSectionRepresentationState] = Field(default_factory=list)
    api_packages: list[InterfaceRuntimePackageApiPackageState] = Field(default_factory=list)
    apis: list[InterfaceRuntimePackageApiState] = Field(default_factory=list)
    dynamic_pane_render_specs: list[InterfaceRuntimePaneRenderSpecState] = Field(default_factory=list)
    render_components: list[InterfaceRuntimePackageRenderComponentState] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class InterfaceWindowLayoutSectionState(BaseModel):
    # Attributes
    section_key: str
    layout_config_section_config_id: UUID | None = Field(default=None)
    layout_section_id: UUID | None = Field(default=None)
    attention_session_section_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    weight_micros: int | None = Field(default=None)
    is_visible: bool = Field(default=True)
    is_collapsed: bool = Field(default=False)
    projection_view_id: str | None = Field(default=None)
    pane_key: str | None = Field(default=None)


class InterfaceWindowLayoutState(BaseModel):
    # Attributes
    source_kind: str
    window_key: str
    layout_key: str
    layout_config_id: UUID | None = Field(default=None)
    attention_session_id: UUID | None = Field(default=None)
    attention_session_layout_id: UUID | None = Field(default=None)
    active_layout_transition_id: UUID | None = Field(default=None)
    active_topology_transition_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    frame_mode: str = Field(default="vertical")
    version_hash: str | None = Field(default=None)
    resolved_at: str | None = Field(default=None)
    stale: bool = Field(default=False)
    admitted_sections: list[InterfaceWindowLayoutSectionState] = Field(
        default_factory=list,
        description="Stable admitted catalog; rows remain present when topology makes them inactive.",
    )
    sections: list[InterfaceWindowLayoutSectionState] = Field(
        default_factory=list, description="Active ordered membership rendered by the current topology."
    )


class InterfaceRuntimeWindowNavigationContextState(BaseModel):
    # Attributes
    source_kind: str
    environment_navigation_context_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    interface_window_navigation_context_id: UUID | None = Field(default=None)
    interface_environment_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceRuntimeWindowState(BaseModel):
    # Attributes
    source_kind: str
    window_key: str
    active: bool = Field(default=False)
    interface_id: UUID | None = Field(default=None)
    interface_window_id: UUID | None = Field(default=None)
    window_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    active_navigation_context: InterfaceRuntimeWindowNavigationContextState | None = Field(default=None)
    active_layout_id: UUID | None = Field(default=None)
    active_layout_config_id: UUID | None = Field(default=None)
    active_layout_key: str | None = Field(default=None)
    active_layout_source_kind: str | None = Field(default=None)
    interface_projection_hash: str | None = Field(default=None)
    window_projection_hash: str | None = Field(default=None)
    interface_head_commit_id: str | None = Field(default=None)
    window_head_commit_id: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceRuntimeState(BaseModel):
    # Attributes
    backend: InterfaceBackendState
    gate_state: InterfaceGateState | None = Field(default=None)
    resolved_view: InterfaceResolvedView | None = Field(default=None)
    window_layout: InterfaceWindowLayoutState | None = Field(default=None)
    active_window: InterfaceRuntimeWindowState | None = Field(default=None)
    windows: list[InterfaceRuntimeWindowState] = Field(default_factory=list)
    active_layout_config_id: UUID | None = Field(default=None)
    layout_states: list[InterfaceRuntimeLayoutState] = Field(default_factory=list)
    active_focus: InterfaceRuntimeFocusState | None = Field(default=None)
    interface_package_runtime: InterfaceRuntimePackageState | None = Field(default=None)
    section_representations: list[InterfaceRuntimeSectionRepresentationState] = Field(default_factory=list)
    resolved_panes: list[InterfaceResolvedPaneDescriptor] = Field(default_factory=list)
    view_state_cursor: InterfaceHostViewStateCursorState | None = Field(default=None)
    materialized_pane_states: list[InterfaceMaterializedPaneState] = Field(default_factory=list)
    dynamic_pane_render_specs: list[InterfaceRuntimePaneRenderSpecState] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class InterfaceHostState(BaseModel):
    # Attributes
    host_label: str
    namespace: str
    endpoint: str | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_config_id: UUID | None = Field(default=None)
    started: bool
    transport: InterfaceTransportState
    renderer_capabilities: InterfaceRendererCapabilitiesState | None = Field(default=None)
    local_service_host: InterfaceLocalServiceHostState | None = Field(default=None)
    local_node_runtime: InterfaceLocalNodeRuntimeState | None = Field(default=None)
    hosted_services: InterfaceHostedServicesState | None = Field(default=None)
    lane_sync: InterfaceLaneSyncState | None = Field(default=None)
    environment_admission: InterfaceEnvironmentAdmissionState | None = Field(default=None)
    environment_session: InterfaceEnvironmentSessionState | None = Field(default=None)
    environment_navigation: InterfaceEnvironmentNavigationState | None = Field(default=None)
    environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = Field(default=None)
    environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = Field(default=None)
    experience_lens: InterfaceExperienceLensState | None = Field(default=None)
    app_screen: InterfaceAppScreenState | None = Field(default=None)
    experience_session_narration: InterfaceExperienceSessionNarrationState | None = Field(default=None)
    runtime: InterfaceRuntimeState | None = Field(default=None)
    control_plane_profiles: InterfaceControlPlaneProfilesState | None = Field(default=None)
    control_plane_workspace: InterfaceControlPlaneWorkspaceState | None = Field(default=None)
    workspace_discovery: InterfaceWorkspaceDiscoveryState | None = Field(default=None)
    selected_workspace: InterfaceSelectedWorkspaceState | None = Field(default=None)
    selected_semantic_package: InterfaceSelectedSemanticPackageState | None = Field(default=None)
    current_screen: InterfaceCurrentScreen | None = Field(default=None)
    current_operation: InterfaceOperationState | None = Field(default=None)
    allowed_actions: list[InterfaceAllowedAction] = Field(default_factory=list)
    recovery_capabilities: list[InterfaceHostRecoveryCapabilityState] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

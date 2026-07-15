from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID


JsonObject = dict[str, object]


@dataclass(frozen=True, slots=True)
class InterfaceBackendState:
    available: bool
    manifest_path: Path | None
    registry_path: Path | None
    database_path: Path | None
    database_exists: bool
    environment_id: UUID | None
    opg_count: int
    projection_bundle_available: bool
    projection_plan_count: int
    table_count: int
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceGateStep:
    key: str
    status: str
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceGateState:
    destination_key: str | None = None
    active_step_key: str | None = None
    blocked: bool = False
    steps: tuple[InterfaceGateStep, ...] = ()
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceResolvedView:
    experience_key: str
    interface_package_id: UUID | None = None
    interface_package_name: str | None = None
    projection_view_id: str | None = None
    host_payload: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceNavigationContextLayoutTargetState:
    source_kind: str
    environment_id: UUID
    thread_id: UUID
    thread_layout_id: UUID
    window_key: str = "main"
    process_id: UUID | None = None
    environment_navigation_context_id: UUID | None = None
    layout_id: UUID | None = None
    layout_config_id: UUID | None = None
    layout_key: str | None = None
    interface_environment_id: UUID | None = None
    interface_window_navigation_context_id: UUID | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceRuntimeLayoutState:
    layout_key: str
    label: str
    layout_config_id: UUID | None = None
    is_default: bool = False
    is_active: bool = False


@dataclass(frozen=True, slots=True)
class InterfaceRuntimeFocusTarget:
    layout_key: str
    label: str
    layout_config_id: UUID | None = None
    section_key: str | None = None
    layout_config_section_config_id: UUID | None = None
    observable_id: UUID | None = None
    view_ref: str | None = None
    projection_view_key: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceAttentionFocusTargetState:
    object_projection_graph_identity_id: UUID
    kind: str = "constructor"
    focus_id: UUID | None = None
    focus_scope_id: UUID | None = None
    projection_experience_graph_identity_id: UUID | None = None
    object_instance_graph_branch_id: UUID | None = None
    projection_hash: str | None = None
    target_type: str | None = None
    target_id: UUID | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceRuntimeFocusState:
    layout_config_id: UUID | None = None
    layout_key: str | None = None
    section_key: str | None = None
    layout_config_section_config_id: UUID | None = None
    layout_section_id: UUID | None = None
    section_focus_scope_id: UUID | None = None
    focus_scope_id: UUID | None = None
    focus_id: UUID | None = None
    observable_id: UUID | None = None
    focus_target: InterfaceAttentionFocusTargetState | None = None


@dataclass(frozen=True, slots=True)
class InterfaceRuntimeSectionRepresentationState:
    representation_id: UUID
    window_key: str
    layout_key: str
    section_key: str
    pane_name: str
    pane_kind: str
    label: str
    observable_id: UUID
    view_ref: str
    projection_experience_graph_identity_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    section_graph_binding_key: str | None = None
    layout_config_id: UUID | None = None
    layout_config_section_config_id: UUID | None = None
    projection_view_key: str | None = None
    is_active: bool = False


@dataclass(frozen=True, slots=True)
class InterfaceResolvedSectionStateAddress:
    section_key: str
    layout_section_id: UUID | None = None
    section_focus_scope_id: UUID | None = None
    focus_scope_id: UUID | None = None
    focus_id: UUID | None = None
    observable_id: UUID | None = None
    branch_id: UUID | None = None
    state_projection_hash: str | None = None
    focus_target: InterfaceAttentionFocusTargetState | None = None


@dataclass(frozen=True, slots=True)
class InterfaceResolvedPaneActionTarget:
    action_key: str
    action_kind: str
    target_ref: str
    view_invocation_action_config_id: UUID | None = None
    label: str | None = None
    receipt_policy: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceResolvedPaneDescriptor:
    window_key: str
    layout_key: str
    section_key: str
    pane_kind: str
    layout_config_section_config_id: UUID | None = None
    layout_section_id: UUID | None = None
    section_focus_scope_id: UUID | None = None
    focus_scope_id: UUID | None = None
    focus_id: UUID | None = None
    branch_id: UUID | None = None
    focus_target: InterfaceAttentionFocusTargetState | None = None
    pane_config_id: UUID | None = None
    pane_package_id: UUID | None = None
    pane_package_name: str | None = None
    object_projection_graph_observable_id: UUID | None = None
    projection_experience_graph_identity_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    section_graph_binding_key: str | None = None
    projection_experience_view_instance_id: UUID | None = None
    projection_experience_view_id: UUID | None = None
    projection_view_id: str | None = None
    view_ref: str | None = None
    projection_view_key: str | None = None
    state_model_id: UUID | None = None
    state_provider_ref: str | None = None
    state_provider_kind: str | None = None
    title: str | None = None
    summary: str | None = None
    narrative_key: str | None = None
    state_source_kind: str = "unknown"
    state_projection_hash: str | None = None
    action_keys: tuple[str, ...] = ()
    action_targets: tuple[InterfaceResolvedPaneActionTarget, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceMaterializedPaneState:
    pane_state_key: str
    window_key: str
    layout_key: str
    section_key: str
    pane_kind: str
    pane_config_id: UUID | None = None
    pane_package_id: UUID | None = None
    focus_scope_id: UUID | None = None
    branch_id: UUID | None = None
    projection_experience_view_id: UUID | None = None
    projection_view_id: str | None = None
    state_model_id: UUID | None = None
    projection_hash: str | None = None
    status: str = "unknown"
    head_commit_id: str | None = None
    graph_hash_post: str | None = None
    materialized_at: str | None = None
    state: JsonObject = field(default_factory=dict)
    provenance: JsonObject = field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceRuntimePaneRenderSpecState:
    pane_render_spec_id: UUID
    pane_config_id: UUID
    source_kind: str = "committed_oig"
    branch_id: UUID | None = None
    projection_hash: str | None = None
    last_commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    render_spec_content_hash_sha256: str | None = None
    payload: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceWindowLayoutSectionState:
    section_key: str
    layout_config_section_config_id: UUID | None = None
    layout_section_id: UUID | None = None
    attention_session_section_id: UUID | None = None
    title: str | None = None
    description: str | None = None
    order: int = 0
    flex: float = 1.0
    weight_micros: int | None = None
    is_visible: bool = True
    is_collapsed: bool = False
    projection_view_id: str | None = None
    pane_key: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceWindowLayoutState:
    source_kind: str
    window_key: str
    layout_key: str
    layout_config_id: UUID | None = None
    attention_session_id: UUID | None = None
    attention_session_layout_id: UUID | None = None
    active_layout_transition_id: UUID | None = None
    active_topology_transition_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    graph_hash_post: str | None = None
    title: str | None = None
    description: str | None = None
    frame_mode: str = "vertical"
    version_hash: str | None = None
    resolved_at: str | None = None
    stale: bool = False
    admitted_sections: tuple[InterfaceWindowLayoutSectionState, ...] = ()
    sections: tuple[InterfaceWindowLayoutSectionState, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceRuntimeWindowNavigationContextState:
    source_kind: str
    environment_navigation_context_id: UUID | None = None
    thread_id: UUID | None = None
    interface_window_navigation_context_id: UUID | None = None
    interface_environment_id: UUID | None = None
    environment_id: UUID | None = None
    process_id: UUID | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceRuntimeWindowState:
    source_kind: str
    window_key: str
    active: bool = False
    interface_id: UUID | None = None
    interface_window_id: UUID | None = None
    window_id: UUID | None = None
    title: str | None = None
    active_navigation_context: InterfaceRuntimeWindowNavigationContextState | None = (
        None
    )
    active_layout_id: UUID | None = None
    active_layout_config_id: UUID | None = None
    active_layout_key: str | None = None
    active_layout_source_kind: str | None = None
    interface_projection_hash: str | None = None
    window_projection_hash: str | None = None
    interface_head_commit_id: str | None = None
    window_head_commit_id: str | None = None
    evidence: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceActionRequest:
    action_key: str
    payload: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceActionReceipt:
    status: str
    receipt_id: str | None = None
    payload: JsonObject = field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceRuntimeState:
    backend: InterfaceBackendState
    gate_state: InterfaceGateState | None = None
    resolved_view: InterfaceResolvedView | None = None
    navigation_context_layout_target: (
        InterfaceNavigationContextLayoutTargetState | None
    ) = None
    window_layout: InterfaceWindowLayoutState | None = None
    active_window: InterfaceRuntimeWindowState | None = None
    windows: tuple[InterfaceRuntimeWindowState, ...] = ()
    active_layout_config_id: UUID | None = None
    layout_states: tuple[InterfaceRuntimeLayoutState, ...] = ()
    active_focus: InterfaceRuntimeFocusState | None = None
    available_focus_targets: tuple[InterfaceRuntimeFocusTarget, ...] = ()
    section_representations: tuple[InterfaceRuntimeSectionRepresentationState, ...] = ()
    resolved_panes: tuple[InterfaceResolvedPaneDescriptor, ...] = ()
    materialized_pane_states: tuple[InterfaceMaterializedPaneState, ...] = ()
    dynamic_pane_render_specs: tuple[InterfaceRuntimePaneRenderSpecState, ...] = ()
    warnings: tuple[str, ...] = ()


__all__ = [
    "InterfaceActionReceipt",
    "InterfaceActionRequest",
    "InterfaceAttentionFocusTargetState",
    "InterfaceBackendState",
    "InterfaceGateState",
    "InterfaceGateStep",
    "InterfaceRuntimeFocusState",
    "InterfaceRuntimePaneRenderSpecState",
    "InterfaceRuntimeSectionRepresentationState",
    "InterfaceRuntimeFocusTarget",
    "InterfaceRuntimeLayoutState",
    "InterfaceRuntimeWindowState",
    "InterfaceRuntimeWindowNavigationContextState",
    "InterfaceNavigationContextLayoutTargetState",
    "InterfaceMaterializedPaneState",
    "InterfaceResolvedPaneDescriptor",
    "InterfaceResolvedSectionStateAddress",
    "InterfaceResolvedView",
    "InterfaceRuntimeState",
    "InterfaceWindowLayoutSectionState",
    "InterfaceWindowLayoutState",
]

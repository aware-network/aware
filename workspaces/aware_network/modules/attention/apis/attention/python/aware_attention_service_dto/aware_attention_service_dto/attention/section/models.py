from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_service_dto.attention.session.models import AttentionLayoutTopologyTransitionPin
    from aware_attention_service_dto.attention.session.models import AttentionLayoutTransitionPin


class AttentionSectionFocusTarget(BaseModel):
    """
    Canonical DTOs for Attention-owned section focus-scope observable state.
    Ownership:
    - Attention API owns the stable transport DTO boundary.
    - Attention runtime/service own the committed section -> focus_scope -> observable truth.
    - Interface later consumes this boundary and resolves experience views + panes on top.
    SSOT: `attention-service-dto` generated from `workspaces/aware_network/modules/attention/apis/attention/dto`.
    """

    # Attributes
    kind: str = Field(
        default="constructor",
        description='Canonical token values:\n- "constructor": branchless focus over projection identity.\n- "materialized": focus has a committed ObjectInstanceGraphBranch.',
    )
    focus_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    target_type: str | None = Field(default=None)
    target_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None)


class AttentionSectionSnapshot(BaseModel):
    # Attributes
    section_id: UUID
    section_key: str
    section_title: str | None = Field(default=None)
    section_description: str | None = Field(default=None)
    exists: bool = Field(default=False)
    section_focus_scope_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    focus_scope_title: str | None = Field(default=None)
    focus_scope_description: str | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    focus_target: AttentionSectionFocusTarget | None = Field(default=None)
    is_active: bool = Field(default=False)


class AttentionFocusScopeCommitPin(BaseModel):
    """
    Commit pointer observed while one Attention focus scope was active.
    This intentionally carries only graph commit pointers. Observation time is the
    create commit time of the underlying FocusScopeCommit object, not a DTO scalar.
    """

    # Attributes
    focus_scope_commit_id: UUID
    focus_scope_id: UUID
    focus_id: UUID
    object_instance_graph_commit_id: UUID


class AttentionRuntimeMountSectionRequest(BaseModel):
    """One section request inside a bundle-backed runtime mount snapshot read."""

    # Attributes
    layout_config_section_config_id: UUID | None = Field(default=None)
    layout_section_id: UUID | None = Field(default=None)
    section_id: UUID | None = Field(default=None)
    section_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    order: int | None = Field(default=None)
    flex: float | None = Field(default=None)
    is_visible: bool | None = Field(default=None)
    default_observable_id: UUID | None = Field(default=None)
    default_rationale: str | None = Field(default=None)


class AttentionRuntimeMountLayoutRequest(BaseModel):
    """One layout candidate inside a bundle-backed runtime mount read."""

    # Attributes
    layout_config_id: UUID | None = Field(default=None)
    layout_id: UUID | None = Field(default=None)
    layout_key: str
    is_default: bool = Field(default=False)
    sections: list[AttentionRuntimeMountSectionRequest] = Field(default_factory=list)


class AttentionRuntimeLayoutSectionState(BaseModel):
    """Runtime layout-section truth for one Attention-selected layout section."""

    # Attributes
    source_kind: str = Field(default="runtime_mount_request")
    layout_config_id: UUID | None = Field(default=None)
    layout_id: UUID | None = Field(default=None)
    layout_config_section_config_id: UUID | None = Field(default=None)
    layout_section_id: UUID | None = Field(default=None)
    attention_session_section_id: UUID | None = Field(default=None)
    section_id: UUID | None = Field(default=None)
    section_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    weight_micros: int | None = Field(default=None)
    is_visible: bool = Field(default=True)
    is_collapsed: bool = Field(default=False)


class AttentionEnvironmentRuntimeTarget(BaseModel):
    """
    Environment-owned runtime target that Attention must echo when resolving focus.
    This is a service/API DTO copy of Environment runtime receipt truth. Attention uses it
    only to bind focus reads to a concrete Environment Process/Thread/ThreadLayout target;
    it does not mutate Environment and does not import Environment runtime internals.
    """

    # Attributes
    environment_id: UUID
    environment_experience_profile_id: UUID | None = Field(default=None)
    environment_experience_profile_mount_id: UUID | None = Field(default=None)
    mount_key: str | None = Field(default=None)
    topology_seed_key: str | None = Field(default=None)
    process_config_id: UUID | None = Field(default=None)
    process_key: str | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_config_id: UUID | None = Field(default=None)
    thread_key: str | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    thread_layout_config_id: UUID | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    layout_id: UUID | None = Field(default=None)
    thread_layout_id: UUID | None = Field(default=None)
    activate_on_seed: bool = Field(default=False)
    status: str | None = Field(default=None)


class AttentionRuntimeMountSnapshot(BaseModel):
    """Batch snapshot of section-scoped Attention state for one Attention-selected runtime layout."""

    # Attributes
    window_key: str | None = Field(default=None)
    environment_target: AttentionEnvironmentRuntimeTarget | None = Field(default=None)
    attention_session_id: UUID | None = Field(default=None)
    attention_session_layout_id: UUID | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    layout_id: UUID | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    active_section_key: str | None = Field(default=None)
    active_observable_id: UUID | None = Field(default=None)
    active_layout_transition: AttentionLayoutTransitionPin | None = Field(default=None)
    active_layout_topology_transition: AttentionLayoutTopologyTransitionPin | None = Field(default=None)
    admitted_layout_sections: list[AttentionRuntimeLayoutSectionState] = Field(
        default_factory=list,
        description="Full stable admitted catalog. Unlike `layout_sections`, these rows are\nnot filtered by the active topology transition.",
    )
    layout_sections: list[AttentionRuntimeLayoutSectionState] = Field(
        default_factory=list, description="Active ordered membership after topology and geometry overlays."
    )
    section_snapshots: list[AttentionSectionSnapshot] = Field(default_factory=list)


class AttentionRuntimeMountSnapshotEvent(BaseModel):
    """One streamed runtime-mount snapshot event emitted by the Attention service."""

    # Attributes
    kind: str = Field(default="snapshot")
    runtime_mount: AttentionRuntimeMountSnapshot

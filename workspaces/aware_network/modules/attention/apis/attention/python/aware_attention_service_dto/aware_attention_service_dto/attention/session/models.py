from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class AttentionSessionPin(BaseModel):
    """
    Canonical DTOs for Attention session transition reads.
    Ownership:
    - Attention API owns the transport read models.
    - Attention ontology owns persisted AttentionSession and
    AttentionFocusTransition truth.
    - Identity owns actor membership/subscription checks.
    """

    # Attributes
    attention_session_id: UUID
    identity_session_id: UUID
    active_layout_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class AttentionSessionLayoutPin(BaseModel):
    # Attributes
    attention_session_layout_id: UUID
    attention_session_id: UUID
    layout_id: UUID
    layout_config_id: UUID | None = Field(default=None)
    active_section_id: UUID | None = Field(default=None)
    active_layout_transition_id: UUID | None = Field(default=None)
    active_topology_transition_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)


class AttentionLayoutTopologyTransitionSectionInput(BaseModel):
    """One stable admitted section anchor supplied in a complete topology intent."""

    # Attributes
    attention_session_section_id: UUID
    order: int


class AttentionLayoutTopologyTransitionSectionState(BaseModel):
    """Committed active-membership state for one stable admitted section anchor."""

    # Attributes
    attention_layout_topology_transition_section_id: UUID
    attention_layout_topology_transition_id: UUID
    attention_session_section_id: UUID
    layout_section_id: UUID | None = Field(default=None)
    section_id: UUID | None = Field(default=None)
    section_key: str | None = Field(default=None)
    order: int


class AttentionLayoutTopologyTransitionPin(BaseModel):
    """
    Immutable full-vector topology transition committed on an
    AttentionSessionLayout lane.
    """

    # Attributes
    attention_layout_topology_transition_id: UUID
    attention_session_layout_id: UUID
    previous_topology_transition_id: UUID | None = Field(default=None)
    client_intent_id: str
    sequence: int = Field(default=0)
    transition_kind: str = Field(default="topology")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    section_states: list[AttentionLayoutTopologyTransitionSectionState] = Field(default_factory=list)


class AttentionSessionSectionPin(BaseModel):
    # Attributes
    attention_session_section_id: UUID
    attention_session_layout_id: UUID
    layout_section_id: UUID
    section_id: UUID
    active_transition_id: UUID | None = Field(default=None)
    section_key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)


class AttentionFocusTransitionPin(BaseModel):
    """
    Read pin for one AttentionFocusTransition plus its parent session chain.
    This is a DTO projection over Attention ontology rows. It is not a second
    persisted frame model.
    """

    # Attributes
    attention_focus_transition_id: UUID
    attention_session_section_id: UUID
    attention_session_layout_id: UUID | None = Field(default=None)
    attention_session_id: UUID | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    layout_section_id: UUID | None = Field(default=None)
    section_id: UUID | None = Field(default=None)
    section_key: str | None = Field(default=None)
    layout_id: UUID | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    previous_transition_id: UUID | None = Field(default=None)
    focus_scope_id: UUID
    focus_id: UUID | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    transition_key: str
    sequence: int = Field(default=0)
    projection_hash: str | None = Field(default=None)
    transition_kind: str = Field(default="focus")
    rationale: str | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class AttentionTransitionValidationResult(BaseModel):
    # Attributes
    exists: bool = Field(default=False)
    valid: bool = Field(default=False)
    failure_reasons: list[str] = Field(default_factory=list)
    transition: AttentionFocusTransitionPin | None = Field(default=None)


class AttentionLayoutTransitionSectionInput(BaseModel):
    """
    One typed section row supplied by a consumer in a full-vector layout intent.
    Pixels and floating-point flex values are intentionally absent. Shared
    geometry crosses the Attention boundary only as exact integer micros.
    """

    # Attributes
    attention_session_section_id: UUID
    order: int
    weight_micros: int
    is_visible: bool = Field(default=True)
    is_collapsed: bool = Field(default=False)


class AttentionLayoutTransitionSectionState(BaseModel):
    """Committed shared geometry for one mounted AttentionSessionSection."""

    # Attributes
    attention_layout_transition_section_id: UUID
    attention_layout_transition_id: UUID
    attention_session_section_id: UUID
    layout_section_id: UUID | None = Field(default=None)
    section_id: UUID | None = Field(default=None)
    section_key: str | None = Field(default=None)
    order: int
    weight_micros: int
    is_visible: bool = Field(default=True)
    is_collapsed: bool = Field(default=False)


class AttentionLayoutTransitionPin(BaseModel):
    """
    Immutable full-vector shared-layout transition committed on an
    AttentionSession lane.
    """

    # Attributes
    attention_layout_transition_id: UUID
    attention_session_layout_id: UUID
    previous_transition_id: UUID | None = Field(default=None)
    topology_transition_id: UUID | None = Field(default=None)
    client_intent_id: str
    sequence: int = Field(default=0)
    transition_kind: str = Field(default="layout")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    section_states: list[AttentionLayoutTransitionSectionState] = Field(default_factory=list)

from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.focus.focus import Focus
    from aware_attention_ontology_orm_models.focus.focus_scope import FocusScope
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_identity import (
        ObjectProjectionGraphIdentity,
    )
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_observable import (
        ObjectProjectionGraphObservable,
    )


class AttentionFocusTransition(ORMModel):
    """
    Replayable Attention focus transition under one AttentionSessionSection.
    Contract:
    - This is the ontology source event for session replay.
    - It is grounded by parent AttentionSessionSection, which is grounded by
    AttentionSessionLayout and AttentionSession.
    - It records focus/observable/graph coordinates, not a consumer snapshot.
    """

    # Relationships
    previous_transition: AttentionFocusTransition | None = Field(default=None)
    focus_scope: FocusScope | None = Field(default=None)
    focus: Focus | None = Field(default=None)
    observable: ObjectProjectionGraphObservable | None = Field(default=None)
    object_projection_graph_identity: ObjectProjectionGraphIdentity | None = Field(default=None)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    transition_key: str
    sequence: int = Field(default=0)
    projection_hash: str | None = Field(default=None)
    transition_kind: str = Field(default="focus")
    rationale: str | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    attention_session_section_id: UUID = Field(description="Foreign key for AttentionSessionSection.transitions")
    previous_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionFocusTransition.previous_transition"
    )
    focus_scope_id: UUID = Field(description="Foreign key for AttentionFocusTransition.focus_scope")
    focus_id: UUID | None = Field(default=None, description="Foreign key for AttentionFocusTransition.focus")
    observable_id: UUID | None = Field(default=None, description="Foreign key for AttentionFocusTransition.observable")
    object_projection_graph_identity_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionFocusTransition.object_projection_graph_identity"
    )
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionFocusTransition.object_instance_graph_branch"
    )
    object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionFocusTransition.object_instance_graph_commit"
    )

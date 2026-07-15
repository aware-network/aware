from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_ontology_dto.focus.focus import Focus
    from aware_attention_ontology_dto.focus.focus_scope import FocusScope
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_identity import ObjectProjectionGraphIdentity
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_observable import (
        ObjectProjectionGraphObservable,
    )


class AttentionFocusTransition(BaseModel):
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

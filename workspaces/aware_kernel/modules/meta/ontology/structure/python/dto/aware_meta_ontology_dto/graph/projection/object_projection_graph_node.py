from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.graph.projection.object_projection_graph_enums import ObjectProjectionGraphNodeSelection

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_meta_ontology_dto.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_node_key import ObjectProjectionGraphNodeKey


class ObjectProjectionGraphNode(BaseModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None)
    object_projection_graph_node_keys: list[ObjectProjectionGraphNodeKey] = Field(default_factory=list)
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None, description="Reverse view for ObjectProjectionGraph.object_projection_graph_nodes"
    )

    # Attributes
    is_root: bool
    policy_refs: list[str] = Field(default_factory=list)
    required_for_validity: bool = Field(default=False)
    selection: ObjectProjectionGraphNodeSelection = Field(default=ObjectProjectionGraphNodeSelection.all)
    selector_condition_id: UUID | None = Field(default=None)
    top_n: int | None = Field(default=None)

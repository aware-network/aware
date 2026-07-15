from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )
    from aware_experience_ontology_dto.projection.projection_experience_node_key import ProjectionExperienceNodeKey
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ProjectionExperienceNode(BaseModel):
    """
    ProjectionExperience node contract edge.
    Contract:
    - Anchors one ProjectionExperience to one structural projection node.
    - Owns human-stable identity names for that node.
    - Consumes canonical resolver key schema from Meta `ObjectProjectionGraphNodeKey`.
    """

    # Relationships
    object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None)
    projection_experience_node_identities: list[ProjectionExperienceNodeIdentity] = Field(default_factory=list)
    projection_experience_node_keys: list[ProjectionExperienceNodeKey] = Field(default_factory=list)

    # Attributes
    key: str

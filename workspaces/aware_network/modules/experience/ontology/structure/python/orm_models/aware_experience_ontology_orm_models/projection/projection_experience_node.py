from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_node_key import (
        ProjectionExperienceNodeKey,
    )
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ProjectionExperienceNode(ORMModel):
    """
    ProjectionExperience node contract edge.
    Contract:
    - Anchors one ProjectionExperience to one structural projection node.
    - Owns human-stable identity names for that node.
    - Consumes canonical resolver key schema from Meta `ObjectProjectionGraphNodeKey`.
    """

    # Relationships
    object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None, exclude=True)
    projection_experience_node_identities: list[ProjectionExperienceNodeIdentity] = Field(
        default_factory=list, exclude=True
    )
    projection_experience_node_keys: list[ProjectionExperienceNodeKey] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_nodes"
    )
    object_projection_graph_node_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNode.object_projection_graph_node"
    )

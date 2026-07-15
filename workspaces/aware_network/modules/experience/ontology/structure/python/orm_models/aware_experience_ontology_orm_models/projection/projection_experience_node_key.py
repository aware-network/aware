from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_node_key import (
        ObjectProjectionGraphNodeKey,
    )


class ProjectionExperienceNodeKey(ORMModel):
    """
    ProjectionExperience node key compatibility wrapper.
    Contract:
    - Declares one deterministic ProjectionKey consumer row under ProjectionExperienceNode.
    - Canonical key schema is owned by Meta `ObjectProjectionGraphNodeKey`.
    """

    # Relationships
    object_projection_graph_node_key: ObjectProjectionGraphNodeKey | None = Field(default=None, exclude=True)

    # Foreign Keys
    projection_experience_node_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNode.projection_experience_node_keys"
    )
    object_projection_graph_node_key_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeKey.object_projection_graph_node_key"
    )

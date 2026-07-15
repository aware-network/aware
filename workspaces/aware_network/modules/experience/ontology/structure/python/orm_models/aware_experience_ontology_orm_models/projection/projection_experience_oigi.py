from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_node_class_identity import (
        ProjectionExperienceNodeClassIdentity,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_node_class_identity_edge import (
        ProjectionExperienceNodeClassIdentityEdge,
    )
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class ProjectionExperienceOIGI(ORMModel):
    """
    ProjectionExperience -> ObjectInstanceGraphIdentity bridge.
    Contract:
    - Owns ProjectionExperience semantic-to-runtime identity topology.
    - Environment/Thread bind to this object; they do not own node/edge topology.
    """

    # Relationships
    node_class_identities: list[ProjectionExperienceNodeClassIdentity] = Field(default_factory=list, exclude=True)
    node_class_identity_edges: list[ProjectionExperienceNodeClassIdentityEdge] = Field(
        default_factory=list, exclude=True
    )
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_oigis"
    )
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceOIGI.object_instance_graph_identity"
    )

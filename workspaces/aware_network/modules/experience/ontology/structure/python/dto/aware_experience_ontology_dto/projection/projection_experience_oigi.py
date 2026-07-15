from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_node_class_identity import (
        ProjectionExperienceNodeClassIdentity,
    )
    from aware_experience_ontology_dto.projection.projection_experience_node_class_identity_edge import (
        ProjectionExperienceNodeClassIdentityEdge,
    )
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class ProjectionExperienceOIGI(BaseModel):
    """
    ProjectionExperience -> ObjectInstanceGraphIdentity bridge.
    Contract:
    - Owns ProjectionExperience semantic-to-runtime identity topology.
    - Environment/Thread bind to this object; they do not own node/edge topology.
    """

    # Relationships
    node_class_identities: list[ProjectionExperienceNodeClassIdentity] = Field(default_factory=list)
    node_class_identity_edges: list[ProjectionExperienceNodeClassIdentityEdge] = Field(default_factory=list)
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)

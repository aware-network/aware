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
    from aware_meta_ontology_dto.class_.class_instance_relationship_identity import ClassInstanceRelationshipIdentity


class ProjectionExperienceNodeClassIdentityEdge(BaseModel):
    """
    Environment-scoped binding edge for semantic node-class anchors.
    Contract:
    - Explicitly encodes parent -> child chain between two node-class anchors.
    - ClassInstanceRelationshipIdentity is required and is the only traversal truth.
    """

    # Relationships
    child_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(default=None)
    parent_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(default=None)
    class_instance_relationship_identity: ClassInstanceRelationshipIdentity | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)

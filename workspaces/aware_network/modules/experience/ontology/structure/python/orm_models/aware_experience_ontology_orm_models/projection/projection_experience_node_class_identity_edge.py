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
    from aware_meta_ontology_orm_models.class_.class_instance_relationship_identity import (
        ClassInstanceRelationshipIdentity,
    )


class ProjectionExperienceNodeClassIdentityEdge(ORMModel):
    """
    Environment-scoped binding edge for semantic node-class anchors.
    Contract:
    - Explicitly encodes parent -> child chain between two node-class anchors.
    - ClassInstanceRelationshipIdentity is required and is the only traversal truth.
    """

    # Relationships
    child_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(default=None, exclude=True)
    parent_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(default=None, exclude=True)
    class_instance_relationship_identity: ClassInstanceRelationshipIdentity | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_oigi_id: UUID = Field(
        description="Foreign key for ProjectionExperienceOIGI.node_class_identity_edges"
    )
    child_node_class_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentityEdge.child_node_class_identity"
    )
    parent_node_class_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentityEdge.parent_node_class_identity"
    )
    class_instance_relationship_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentityEdge.class_instance_relationship_identity"
    )

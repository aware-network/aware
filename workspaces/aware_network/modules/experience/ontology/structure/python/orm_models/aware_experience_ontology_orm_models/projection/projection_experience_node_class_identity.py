from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_node_class_identity_key_binding import (
        ProjectionExperienceNodeClassIdentityKeyBinding,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )
    from aware_meta_ontology_orm_models.class_.class_instance_identity import ClassInstanceIdentity


class ProjectionExperienceNodeClassIdentity(ORMModel):
    """
    Shared semantic node identity -> runtime class identity bridge.
    Contract:
    - Bridges one ProjectionExperienceNodeIdentity to one Meta ClassInstanceIdentity.
    - Traversal context is expressed via ProjectionExperienceNodeClassIdentityEdge.
    - Key bindings live under this edge as mapping data.
    """

    # Relationships
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None, exclude=True)
    class_instance_identity: ClassInstanceIdentity | None = Field(default=None, exclude=True)
    key_bindings: list[ProjectionExperienceNodeClassIdentityKeyBinding] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str

    # Foreign Keys
    projection_experience_oigi_id: UUID = Field(
        description="Foreign key for ProjectionExperienceOIGI.node_class_identities"
    )
    projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentity.projection_experience_node_identity"
    )
    class_instance_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentity.class_instance_identity"
    )

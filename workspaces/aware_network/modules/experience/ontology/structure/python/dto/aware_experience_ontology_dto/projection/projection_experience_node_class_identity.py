from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_node_class_identity_key_binding import (
        ProjectionExperienceNodeClassIdentityKeyBinding,
    )
    from aware_experience_ontology_dto.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )
    from aware_meta_ontology_dto.class_.class_instance_identity import ClassInstanceIdentity


class ProjectionExperienceNodeClassIdentity(BaseModel):
    """
    Shared semantic node identity -> runtime class identity bridge.
    Contract:
    - Bridges one ProjectionExperienceNodeIdentity to one Meta ClassInstanceIdentity.
    - Traversal context is expressed via ProjectionExperienceNodeClassIdentityEdge.
    - Key bindings live under this edge as mapping data.
    """

    # Relationships
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None)
    class_instance_identity: ClassInstanceIdentity | None = Field(default=None)
    key_bindings: list[ProjectionExperienceNodeClassIdentityKeyBinding] = Field(default_factory=list)

    # Attributes
    key: str

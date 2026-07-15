from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_graph_identity_profile import (
        ProjectionExperienceGraphIdentityProfile,
    )
    from aware_experience_ontology_dto.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )


class ProjectionExperienceGraphIdentity(BaseModel):
    """
    Graph occurrence identity under ProjectionExperienceGraph.
    Contract:
    - Binds one graph occurrence handle to one ProjectionExperienceNodeIdentity.
    - `is_root` marks the canonical root occurrence for deterministic path derivation.
    """

    # Relationships
    projection_experience_graph_identity_profile: ProjectionExperienceGraphIdentityProfile | None = Field(default=None)
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None)

    # Attributes
    is_root: bool = Field(default=False)
    key: str

from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_node_key import (
        ProjectionExperienceNodeKey,
    )


class ProjectionExperienceNodeClassIdentityKeyBinding(ORMModel):
    """
    ProjectionKey payload row under ProjectionExperienceNodeClassIdentity.
    Contract:
    - Binds one consumed ProjectionExperienceNodeKey to one concrete payload used for resolution proof.
    """

    # Relationships
    projection_experience_node_key: ProjectionExperienceNodeKey | None = Field(default=None, exclude=True)

    # Attributes
    value: JsonObject | None = Field(default=None)

    # Foreign Keys
    projection_experience_node_class_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentity.key_bindings"
    )
    projection_experience_node_key_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentityKeyBinding.projection_experience_node_key"
    )

from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.role.role_enums import AccessLevelType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config_relationship import ClassConfigRelationship


class RoleConfigClassConfigRelationship(ORMModel):
    # Relationships
    class_config_relationship: ClassConfigRelationship | None = Field(
        default=None, exclude=True, description="Association target reference to ClassConfigRelationship"
    )

    # Attributes
    access_level: AccessLevelType

    # Foreign Keys
    class_config_relationship_id: UUID = Field(description="Join FK to ClassConfigRelationship")
    role_config_id: UUID = Field(description="Join FK to RoleConfig")

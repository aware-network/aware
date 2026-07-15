from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.class_.class_config_relationship_enums import (
    ClassConfigRelationshipSideLoadingStrategy,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig


class ClassConfigRelationshipAssociation(ORMModel):
    # Relationships
    class_config: ClassConfig | None = Field(
        default=None, exclude=True, description="Association target reference to ClassConfig"
    )

    # Attributes
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)

    # Foreign Keys
    class_config_id: UUID = Field(description="Join FK to ClassConfig")
    class_config_relationship_id: UUID = Field(description="Join FK to ClassConfigRelationship")

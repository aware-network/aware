from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig


class ClassConfigRelationshipAttribute(ORMModel):
    """
    Relationship attribute representation.
    This models how a `ClassConfigRelationship` is represented via one or more
    `AttributeConfig`s (e.g. REFERENCE attribute, FOREIGN_KEY attribute, AUXILIARY).
    NOTE: OCG is general-purpose. Canonical constraints (e.g. emitting exactly one
    REFERENCE+FORWARD attribute) are enforced by builders/transformers, not the schema.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    direction: ClassConfigRelationshipDirection
    role: ClassConfigRelationshipAttributeRole

    # Foreign Keys
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ClassConfigRelationship.class_config_relationship_attributes"
    )
    attribute_config_id: UUID = Field(description="Foreign key for ClassConfigRelationshipAttribute.attribute_config")

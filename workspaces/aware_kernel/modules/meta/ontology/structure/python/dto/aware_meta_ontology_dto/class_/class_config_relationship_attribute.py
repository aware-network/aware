from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig


class ClassConfigRelationshipAttribute(BaseModel):
    """
    Relationship attribute representation.
    This models how a `ClassConfigRelationship` is represented via one or more
    `AttributeConfig`s (e.g. REFERENCE attribute, FOREIGN_KEY attribute, AUXILIARY).
    NOTE: OCG is general-purpose. Canonical constraints (e.g. emitting exactly one
    REFERENCE+FORWARD attribute) are enforced by builders/transformers, not the schema.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None)

    # Attributes
    direction: ClassConfigRelationshipDirection
    role: ClassConfigRelationshipAttributeRole

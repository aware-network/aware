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
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_meta_ontology_dto.class_.class_config_relationship_association import ClassConfigRelationshipAssociation
    from aware_meta_ontology_dto.class_.class_config_relationship_attribute import ClassConfigRelationshipAttribute


class ClassConfigRelationship(BaseModel):
    """
    Canonical relationship SSOT.
    A relationship is declared by exactly one class attribute (single-sided). Any "backref"
    attribute is treated as a separate relationship in canonical mode.
    This model stores:
    - Declaring endpoints (ClassConfig ↔ ClassConfig) for augmentation honesty
    - Optional association edge container
    - Loading semantics (forward/reverse) derived from annotations
    """

    # Relationships
    target_class_config: ClassConfig | None = Field(default=None)
    class_config_relationship_attributes: list[ClassConfigRelationshipAttribute] = Field(default_factory=list)
    reified_from_relationship: ClassConfigRelationship | None = Field(default=None)

    # Attributes
    relationship_key: str
    relationship_type: ClassConfigRelationshipType
    identity_rail: ClassConfigRelationshipIdentityRail | None = Field(default=None)
    forward_required: bool
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reified_role: ClassConfigRelationshipReifiedRole | None = Field(default=None)

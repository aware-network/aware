from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.class_.class_config_relationship_enums import (
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_meta_ontology_orm_models.class_.class_config_relationship_association import (
        ClassConfigRelationshipAssociation,
    )
    from aware_meta_ontology_orm_models.class_.class_config_relationship_attribute import (
        ClassConfigRelationshipAttribute,
    )


class ClassConfigRelationship(ORMModel):
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
    target_class_config: ClassConfig | None = Field(default=None, exclude=True)
    class_config_relationship_attributes: list[ClassConfigRelationshipAttribute] = Field(default_factory=list)
    reified_from_relationship: ClassConfigRelationship | None = Field(default=None, exclude=True)

    # Attributes
    relationship_key: str
    relationship_type: ClassConfigRelationshipType
    identity_rail: ClassConfigRelationshipIdentityRail | None = Field(default=None)
    forward_required: bool
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reified_role: ClassConfigRelationshipReifiedRole | None = Field(default=None)

    # Foreign Keys
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_relationships")
    target_class_config_id: UUID = Field(description="Foreign key for ClassConfigRelationship.target_class_config")
    reified_from_relationship_id: UUID | None = Field(
        default=None, description="Foreign key for ClassConfigRelationship.reified_from_relationship"
    )

    # Edges
    class_config_relationship_association_edge: ClassConfigRelationshipAssociation | None = Field(
        default=None, description="Edge association helper for class_config_relationship_association"
    )

    @property
    def class_config_relationship_association(self) -> ClassConfig | None:
        return (
            self.class_config_relationship_association_edge.class_config
            if self.class_config_relationship_association_edge is not None
            and self.class_config_relationship_association_edge.class_config is not None
            else None
        )

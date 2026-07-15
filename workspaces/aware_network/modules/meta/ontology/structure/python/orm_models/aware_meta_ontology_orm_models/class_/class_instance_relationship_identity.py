from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_instance_relationship import ClassInstanceRelationship


class ClassInstanceRelationshipIdentity(ORMModel):
    """
    Stable identity rail for ClassInstanceRelationship truth.
    Contract:
    - One identity id maps to one logical class-instance relationship worldline.
    - Commits/receipts should reference this id for parent-chain attribution truth.
    """

    # Relationships
    class_instance_relationship: ClassInstanceRelationship | None = Field(default=None, exclude=True)

    # Attributes
    label: str | None = Field(default=None)

    # Foreign Keys
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.class_instance_relationship_identities"
    )
    class_instance_relationship_id: UUID = Field(
        description="Foreign key for ClassInstanceRelationshipIdentity.class_instance_relationship"
    )

from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_instance_relationship import ClassInstanceRelationship


class ClassInstanceRelationshipIdentity(BaseModel):
    """
    Stable identity rail for ClassInstanceRelationship truth.
    Contract:
    - One identity id maps to one logical class-instance relationship worldline.
    - Commits/receipts should reference this id for parent-chain attribution truth.
    """

    # Relationships
    class_instance_relationship: ClassInstanceRelationship | None = Field(default=None)

    # Attributes
    label: str | None = Field(default=None)

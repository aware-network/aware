from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_instance import ClassInstance


class ClassInstanceIdentity(BaseModel):
    """
    Stable identity rail for ClassInstance truth.
    Contract:
    - One identity id maps to one logical class-instance worldline.
    - Commits/receipts should reference this id for attribution truth.
    """

    # Relationships
    class_instance: ClassInstance | None = Field(default=None)

    # Attributes
    label: str | None = Field(default=None)

from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_instance import ClassInstance


class ClassInstanceIdentity(ORMModel):
    """
    Stable identity rail for ClassInstance truth.
    Contract:
    - One identity id maps to one logical class-instance worldline.
    - Commits/receipts should reference this id for attribution truth.
    """

    # Relationships
    class_instance: ClassInstance | None = Field(default=None, exclude=True)

    # Attributes
    label: str | None = Field(default=None)

    # Foreign Keys
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.class_instance_identities"
    )
    class_instance_id: UUID = Field(description="Foreign key for ClassInstanceIdentity.class_instance")

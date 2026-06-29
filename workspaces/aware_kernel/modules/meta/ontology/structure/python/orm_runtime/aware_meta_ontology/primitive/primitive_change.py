from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology.change.change import Change


class PrimitiveChange(ORMModel):
    # Relationships
    change: Change | None = Field(default=None, exclude=True)

    # Foreign Keys
    primitive_id: UUID = Field(description="Foreign key for Primitive.primitive_changes")
    change_id: UUID = Field(description="Foreign key for PrimitiveChange.change")


FUNCTIONS = {
    "PrimitiveChange": {},
}

__all__ = [
    "PrimitiveChange",
    "FUNCTIONS",
]

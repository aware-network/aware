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
    from aware_meta_ontology.attribute.attribute_change import AttributeChange


class ClassInstanceChange(ORMModel):
    # Relationships
    attribute_changes: list[AttributeChange] = Field(default_factory=list)
    change: Change

    # Foreign Keys
    class_instance_id: UUID = Field(description="Foreign key for ClassInstance.class_instance_changes")
    change_id: UUID | None = Field(default=None, description="Foreign key for ClassInstanceChange.change")


FUNCTIONS = {
    "ClassInstanceChange": {},
}

__all__ = [
    "ClassInstanceChange",
    "FUNCTIONS",
]

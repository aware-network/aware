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
    from aware_meta_ontology.enum.enum_option import EnumOption


class EnumChange(ORMModel):
    # Relationships
    change: Change | None = Field(default=None, exclude=True)
    enum_option: EnumOption | None = Field(default=None, exclude=True)

    # Foreign Keys
    enum_id: UUID = Field(description="Foreign key for Enum.enum_changes")
    change_id: UUID = Field(description="Foreign key for EnumChange.change")
    enum_option_id: UUID = Field(description="Foreign key for EnumChange.enum_option")


FUNCTIONS = {
    "EnumChange": {},
}

__all__ = [
    "EnumChange",
    "FUNCTIONS",
]

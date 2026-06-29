from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology.enum.enum_change import EnumChange
    from aware_meta_ontology.enum.enum_config import EnumConfig
    from aware_meta_ontology.enum.enum_option import EnumOption


class Enum(ORMModel):
    # Relationships
    enum_changes: list[EnumChange] = Field(default_factory=list, exclude=True)
    enum_config: EnumConfig | None = Field(default=None, exclude=True)
    enum_option: EnumOption

    # Foreign Keys
    enum_config_id: UUID = Field(description="Foreign key for Enum.enum_config")
    enum_option_id: UUID | None = Field(default=None, description="Foreign key for Enum.enum_option")


FUNCTIONS = {
    "Enum": {},
}

__all__ = [
    "Enum",
    "FUNCTIONS",
]

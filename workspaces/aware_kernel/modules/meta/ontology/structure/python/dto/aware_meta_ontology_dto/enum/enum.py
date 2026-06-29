from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.enum.enum_change import EnumChange
    from aware_meta_ontology_dto.enum.enum_config import EnumConfig
    from aware_meta_ontology_dto.enum.enum_option import EnumOption


class Enum(BaseModel):
    # Relationships
    enum_changes: list[EnumChange] = Field(default_factory=list)
    enum_config: EnumConfig | None = Field(default=None)
    enum_option: EnumOption

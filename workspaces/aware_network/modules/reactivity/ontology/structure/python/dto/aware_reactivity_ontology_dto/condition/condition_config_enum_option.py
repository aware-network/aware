from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.enum.enum_option import EnumOption


class ConditionConfigEnumOption(BaseModel):
    # Relationships
    enum_option: EnumOption | None = Field(default=None)

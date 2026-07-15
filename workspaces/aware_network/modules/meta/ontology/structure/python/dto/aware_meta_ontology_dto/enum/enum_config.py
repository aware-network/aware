from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.enum.code_section_enum import CodeSectionEnum
    from aware_meta_ontology_dto.enum.enum_option import EnumOption


class EnumConfig(BaseModel):
    # Relationships
    enum_options: list[EnumOption] = Field(default_factory=list)
    code_section_enum: CodeSectionEnum | None = Field(default=None)

    # Attributes
    enum_fqn: str
    name: str
    description: str | None = Field(default=None)

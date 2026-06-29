from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.attribute.code_section_attribute import CodeSectionAttribute


class CodeSectionClassAttribute(BaseModel):
    # Relationships
    code_section_attribute: CodeSectionAttribute = Field(
        description="Association target reference to CodeSectionAttribute"
    )

    # Attributes
    position: int = Field(default=0)

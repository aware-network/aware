from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.function.code_section_function import CodeSectionFunction


class CodeSectionClassFunction(BaseModel):
    # Relationships
    code_section_function: CodeSectionFunction = Field(
        description="Association target reference to CodeSectionFunction"
    )

    # Attributes
    position: int = Field(default=0)

from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_section import CodeSection


class CodeSectionAnnotation(BaseModel):
    # Relationships
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_annotation")

    # Attributes
    path: str
    verb: str
    args: list[str] = Field(default_factory=list)

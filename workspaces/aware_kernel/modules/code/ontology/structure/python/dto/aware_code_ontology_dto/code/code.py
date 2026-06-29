from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_section import CodeSection
    from aware_code_ontology_dto.code.code_test import CodeTest
    from aware_content_ontology_dto.part.content_part_text import ContentPartText


class Code(BaseModel):
    # Relationships
    code_sections: list[CodeSection] = Field(default_factory=list)
    content_part_text: ContentPartText
    tests: list[CodeTest] = Field(default_factory=list)

    # Attributes
    relative_path: str
    language: CodeLanguage | None = Field(default=None)

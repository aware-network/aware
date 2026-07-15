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
    from aware_code_ontology_dto.import_.code_section_import_name import CodeSectionImportName
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionImport(BaseModel):
    # Relationships
    code_section_import_names: list[CodeSectionImportName] = Field(default_factory=list)
    module_segment: ContentPartTextSegment
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_import")

    # Attributes
    module_text: str
    is_from_import: bool
    is_star_import: bool
    relative_level: int = Field(default=0)

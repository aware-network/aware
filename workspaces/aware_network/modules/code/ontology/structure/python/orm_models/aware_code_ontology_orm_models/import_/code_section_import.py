from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_section import CodeSection
    from aware_code_ontology_orm_models.import_.code_section_import_name import CodeSectionImportName
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionImport(ORMModel):
    # Relationships
    code_section_import_names: list[CodeSectionImportName] = Field(default_factory=list)
    module_segment: ContentPartTextSegment
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_import")

    # Attributes
    module_text: str
    is_from_import: bool
    is_star_import: bool
    relative_level: int = Field(default=0)

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_import")
    module_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionImport.module_segment")

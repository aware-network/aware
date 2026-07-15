from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionImportName(ORMModel):
    # Relationships
    name_segment: ContentPartTextSegment
    alias_segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    name_text: str
    alias_text: str | None = Field(default=None)

    # Foreign Keys
    code_section_import_id: UUID = Field(description="Foreign key for CodeSectionImport.code_section_import_names")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionImportName.name_segment")
    alias_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionImportName.alias_segment"
    )

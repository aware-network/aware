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
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionMirror(ORMModel):
    """
    Canonical mirror directive (API transport allowlist).
    Mirrors are explicit, file-level statements that mark which ontology symbols
    are copied into an API OCG for DTO materialization.
    """

    # Relationships
    target_segment: ContentPartTextSegment
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_mirror")

    # Attributes
    target_text: str

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_mirror")
    target_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionMirror.target_segment")

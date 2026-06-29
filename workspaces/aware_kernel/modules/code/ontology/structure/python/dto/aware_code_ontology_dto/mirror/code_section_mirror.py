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
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionMirror(BaseModel):
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

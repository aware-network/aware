from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.comment.code_section_comment_enums import CodeSectionCommentType

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_section import CodeSection
    from aware_code_ontology_dto.comment.code_section_comment_content import CodeSectionCommentContent


class CodeSectionComment(BaseModel):
    # Relationships
    code_section_comment_contents: list[CodeSectionCommentContent] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_comment")

    # Attributes
    type: CodeSectionCommentType

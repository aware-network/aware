from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionCommentContent(ORMModel):
    # Relationships
    content_part_text_segment: ContentPartTextSegment

    # Attributes
    position: int

    # Foreign Keys
    code_section_comment_id: UUID = Field(
        description="Foreign key for CodeSectionComment.code_section_comment_contents"
    )
    content_part_text_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionCommentContent.content_part_text_segment"
    )

    @classmethod
    async def build_via_code_section_comment(
        cls, code_section_comment_id: UUID, position: int
    ) -> CodeSectionCommentContent:
        """Build an ordered comment-content item under a comment."""

        payload = {"code_section_comment_id": code_section_comment_id, "position": position}
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_code_section_comment", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionCommentContent):
            return value
        return CodeSectionCommentContent.validate_invocation_value(value)


class CodeSectionCommentContentBuildViaCodeSectionCommentInput(BaseModel):
    code_section_comment_id: UUID = Field(
        description="Foreign key for CodeSectionComment.code_section_comment_contents"
    )
    position: int


class CodeSectionCommentContentBuildViaCodeSectionCommentOutput(BaseModel):
    value: CodeSectionCommentContent


FUNCTIONS = {
    "CodeSectionCommentContent": {
        "build_via_code_section_comment": {
            "canonical": {
                "name": "build_via_code_section_comment",
                "description": "Build an ordered comment-content item under a comment.",
                "is_constructor": True,
            },
            "input": CodeSectionCommentContentBuildViaCodeSectionCommentInput,
            "output": CodeSectionCommentContentBuildViaCodeSectionCommentOutput,
        },
    },
}

__all__ = [
    "CodeSectionCommentContent",
    "CodeSectionCommentContentBuildViaCodeSectionCommentInput",
    "CodeSectionCommentContentBuildViaCodeSectionCommentOutput",
    "FUNCTIONS",
]

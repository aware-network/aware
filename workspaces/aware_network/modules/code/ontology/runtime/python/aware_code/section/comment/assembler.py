"""Assembler helpers for CodeSectionComment objects (free-function driven)."""

# Content
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Code
from aware_code_ontology.code.code_section import CodeSection

# Comment
from aware_code_ontology.comment.code_section_comment import CodeSectionComment
from aware_code_ontology.comment.code_section_comment_content import (
    CodeSectionCommentContent,
)
from aware_code_ontology.comment.code_section_comment_enums import (
    CodeSectionCommentType,
)

from aware_code.section.comment.segments import CodeSectionCommentSegment


def assemble_comment(
    *,
    code_section: CodeSection,
    segments: dict[str, ContentPartTextSegment | list[ContentPartTextSegment]],
    comment_type: CodeSectionCommentType = CodeSectionCommentType.line,
) -> CodeSectionComment:
    """Assemble a `CodeSectionComment` from explicit section inputs (no metadata contract)."""
    if CodeSectionCommentSegment.CONTENT.value not in segments:
        raise ValueError(f"Comment assembler requires a '{CodeSectionCommentSegment.CONTENT.value}' segment")

    content_segment = segments[CodeSectionCommentSegment.CONTENT.value]
    if not isinstance(content_segment, ContentPartTextSegment):
        raise ValueError(f"Comment content segment must be a ContentPartTextSegment, got {type(content_segment)}")

    comment_section = CodeSectionComment(
        code_section=code_section,
        type=comment_type,
    )
    comment_section.code_section_comment_contents.append(
        CodeSectionCommentContent(
            code_section_comment_id=comment_section.id,
            position=0,
            content_part_text_segment=content_segment,
            content_part_text_segment_id=content_segment.id,
        )
    )
    code_section.code_section_comment = comment_section
    return comment_section

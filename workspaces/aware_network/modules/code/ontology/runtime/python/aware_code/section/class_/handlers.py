# Aware Relationship Imports
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.comment.code_section_comment_enums import (
    CodeSectionCommentType,
)
from aware_code_ontology.class_.code_section_class import CodeSectionClass

from aware_code.section.class_.segments import CodeSectionClassSegment


def get_segment(class_: CodeSectionClass, kind: CodeSectionClassSegment) -> ContentPartTextSegment | None:
    """
    Get a segment by its enum type.

    Args:
        kind: The segment enum value (e.g., CodeSectionClassSegment.NAME)

    Returns:
        The ContentPartTextSegment if found, None otherwise
    """
    # TODO: Get Base segments from code_section_class_base_base_class_list -> segment.

    mapping = {
        CodeSectionClassSegment.NAME: class_.name_segment,
        CodeSectionClassSegment.KEYWORD: class_.keyword_segment,
        CodeSectionClassSegment.MODIFIERS: class_.modifiers_segment,
        CodeSectionClassSegment.DESCRIPTION_COMMENT: _first_doc_comment_raw_segment(
            class_,
        ),
        # Note: BASES and BODY segments are not currently stored as individual segments
        # They would need to be added to the database schema and model if needed
    }
    return mapping.get(kind)


def _first_doc_comment_raw_segment(
    class_: CodeSectionClass,
) -> ContentPartTextSegment | None:
    for comment in sorted(
        class_.code_section_comments,
        key=lambda item: 0 if item.type == CodeSectionCommentType.doc else 1,
    ):
        if comment.type != CodeSectionCommentType.doc:
            continue
        return comment.code_section.content_part_text_segment
    return None

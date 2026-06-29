# Kernel Graph Ontology
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

from aware_code.section.comment.handlers import get_first_doc_comment_segment
from aware_code.section.function.segments import CodeSectionFunctionSegment


def get_segment(function: CodeSectionFunction, kind: CodeSectionFunctionSegment) -> ContentPartTextSegment | None:
    """
    Get a segment by its enum type.

    Args:
        kind: The segment enum value (e.g., CodeSectionFunctionSegment.NAME)

    Returns:
        The ContentPartTextSegment if found, None otherwise
    """
    mapping = {
        CodeSectionFunctionSegment.NAME: function.name_segment,
        CodeSectionFunctionSegment.SIGNATURE: function.signature_segment,
        CodeSectionFunctionSegment.RETURN_TYPE: function.return_type_segment,
        CodeSectionFunctionSegment.BODY: function.body_segment,
        CodeSectionFunctionSegment.DESCRIPTION_COMMENT: (
            get_first_doc_comment_segment(function.code_section_comments)
        ),
        # Note: IS_ASYNC is not stored as an individual durable segment.
    }
    return mapping.get(kind)

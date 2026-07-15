# Content
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.enum.code_section_enum import CodeSectionEnum

from aware_code.section.enum.segments import CodeSectionEnumSegment


def get_segment(enum: CodeSectionEnum, kind: CodeSectionEnumSegment) -> ContentPartTextSegment | None:
    """
    Get a segment by its enum type.

    Args:
        kind: The segment enum value (e.g., CodeSectionEnumSegment.NAME)

    Returns:
        The ContentPartTextSegment if found, None otherwise
    """
    mapping = {
        CodeSectionEnumSegment.NAME: enum.name_segment,
        # Note: VALUES segment would need to be added to database schema if needed
    }
    return mapping.get(kind)

from aware_code_ontology.decorator.code_section_decorator import CodeSectionDecorator
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

from aware_code.section.decorator.segments import CodeSectionDecoratorSegment


def get_segment(decorator: CodeSectionDecorator, kind: CodeSectionDecoratorSegment) -> ContentPartTextSegment | None:
    """
    Get a segment by its enum type.

    Args:
        kind: The segment enum value (e.g., CodeSectionDecoratorSegment.NAME)

    Returns:
        The ContentPartTextSegment if found, None if not found
    """
    mapping = {
        CodeSectionDecoratorSegment.NAME: decorator.name_segment,
        # Note: ARGUMENTS segment would need to be added to database schema if needed
    }
    return mapping.get(kind)

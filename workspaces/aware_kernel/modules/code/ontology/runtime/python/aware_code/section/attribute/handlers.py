# Kernel Graph Ontology
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Code Runtime
from aware_code.section.attribute.segments import CodeSectionAttributeSegment


def get_segment(attribute: CodeSectionAttribute, kind: CodeSectionAttributeSegment) -> ContentPartTextSegment | None:
    """
    Get a segment by its enum type.

    Args:
        kind: The segment enum value (e.g., CodeSectionAttributeSegment.NAME)

    Returns:
        The ContentPartTextSegment if found, None otherwise
    """
    mapping = {
        CodeSectionAttributeSegment.NAME: attribute.name_segment,
        CodeSectionAttributeSegment.TYPE: attribute.type_segment,
        CodeSectionAttributeSegment.DEFAULT_VALUE: attribute.default_value_segment,
    }
    return mapping.get(kind)

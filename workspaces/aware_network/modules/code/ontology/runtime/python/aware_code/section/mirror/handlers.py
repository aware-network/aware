# Kernel Graph Ontology
from aware_code_ontology.mirror.code_section_mirror import CodeSectionMirror
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Code Runtime
from aware_code.section.mirror.segments import CodeSectionMirrorSegment


def get_segment(mirror: CodeSectionMirror, kind: CodeSectionMirrorSegment) -> ContentPartTextSegment | None:
    """
    Get a segment by its enum type.

    Args:
        kind: The segment enum value (e.g., CodeSectionMirrorSegment.TARGET)

    Returns:
        The ContentPartTextSegment if found, None otherwise
    """
    mapping = {
        CodeSectionMirrorSegment.TARGET: mirror.target_segment,
    }
    return mapping.get(kind)

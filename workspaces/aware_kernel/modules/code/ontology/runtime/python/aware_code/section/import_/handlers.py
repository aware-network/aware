# Kernel Graph Ontology
from aware_code_ontology.import_.code_section_import import CodeSectionImport
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Code Runtime
from aware_code.section.import_.segments import CodeSectionImportSegment


def get_segment(import_: CodeSectionImport, kind: CodeSectionImportSegment) -> ContentPartTextSegment | None:
    """
    Get a segment by its enum type.

    Args:
        kind: The segment enum value (e.g., CodeSectionImportSegment.MODULE)

    Returns:
        The ContentPartTextSegment if found, None otherwise
    """
    mapping = {
        CodeSectionImportSegment.MODULE: import_.module_segment,
        # !! TODO: add support for segment list
        # CodeSectionImportSegment.NAMES: self.code_section_import_name_list,
    }
    return mapping.get(kind)

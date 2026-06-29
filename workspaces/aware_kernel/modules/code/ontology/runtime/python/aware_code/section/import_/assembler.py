"""Assembler helpers for CodeSectionImport objects (free-function driven)."""

from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.import_.code_section_import import (
    CodeSectionImport,
)
from aware_code_ontology.import_.code_section_import_name import (
    CodeSectionImportName,
)

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.section.import_.segments import CodeSectionImportSegment

# Aware Storage
from aware_storage.blob_store import BlobStore


def assemble_import(
    *,
    code_section: CodeSection,
    segments: dict[str, ContentPartTextSegment | list[ContentPartTextSegment]],
    blob_store: BlobStore | None = None,
) -> CodeSectionImport:
    """Assemble a `CodeSectionImport` from explicit section inputs (no metadata contract)."""
    if CodeSectionImportSegment.MODULE.value not in segments:
        raise ValueError(f"Import assembler requires a '{CodeSectionImportSegment.MODULE.value}' segment")

    module_segment = segments[CodeSectionImportSegment.MODULE.value]
    if not isinstance(module_segment, ContentPartTextSegment):
        raise ValueError(f"Module segment must be a ContentPartTextSegment, got {type(module_segment)}")
    module_text = get_segment_text(content_part_text_segment=module_segment, blob_store=blob_store)
    import_section = CodeSectionImport(
        code_section=code_section,
        module_segment=module_segment,
        module_text=module_text,
        module_segment_id=module_segment.id,
        is_from_import=True,
        is_star_import=False,
        relative_level=0,
    )
    code_section.code_section_import = import_section
    return import_section


def add_import_name(
    import_section: CodeSectionImport,
    name_segment: ContentPartTextSegment,
    alias_segment: ContentPartTextSegment | None = None,
    blob_store: BlobStore | None = None,
) -> CodeSectionImportName:
    """
    Add an import name to an import statement.

    Args:
        import_section: The import section to add to
        name_segment: The segment containing the imported name
        alias_segment: Optional segment containing the alias (for "as" imports)

    Returns:
        The created import name relationship
    """
    name_text = get_segment_text(content_part_text_segment=name_segment, blob_store=blob_store)
    alias_text = None
    if alias_segment:
        alias_text = get_segment_text(content_part_text_segment=alias_segment, blob_store=blob_store)
    # Create the import name
    import_name = CodeSectionImportName(
        code_section_import_id=import_section.id,
        name_segment=name_segment,
        name_segment_id=name_segment.id,
        name_text=name_text,
        alias_segment=alias_segment,
        alias_segment_id=alias_segment.id if alias_segment else None,
        alias_text=alias_text,
    )

    # Add to the import's name list
    import_section.code_section_import_names.append(import_name)
    return import_name

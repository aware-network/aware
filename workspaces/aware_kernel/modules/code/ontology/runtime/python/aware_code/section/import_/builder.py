"""Builder for constructing CodeSectionImport instances from source code."""

# Kernel Graph Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.import_.code_section_import import CodeSectionImport
from aware_code_ontology.import_.code_section_import_name import CodeSectionImportName
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Code Runtime
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.section.import_.adapter import CodeSectionImportAdapter
from aware_code.symbol_table import CodeSymbolTable


# Aware Storage
from aware_storage.blob_store import BlobStore


def build_import_section(
    adapter: CodeSectionImportAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    symbol_table: CodeSymbolTable,
    blob_store: BlobStore | None = None,
) -> CodeSectionImport:
    """
    Build a CodeSectionImport instance from the provided node.

    Args:
        adapter: The adapter to use
        code: The code object containing the source
        code_section: The code section to build
        node: The node to build from
        symbol_table: The symbol table to use

    Returns:
        Constructed CodeSectionImport instance
    """
    code_section_segment = code_section.content_part_text_segment

    # Get the module name
    module_node = adapter.get_module_name(node)
    module_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=module_node.byte_start,
        byte_end=module_node.byte_end,
        parent_id=code_section_segment.id,
    )
    module_text = get_segment_text(content_part_text_segment=module_segment, blob_store=blob_store)

    # Create the import section
    import_section = CodeSectionImport(
        code_section=code_section,
        module_segment=module_segment,
        module_segment_id=module_segment.id,
        module_text=module_text,
        is_from_import=adapter.is_from_import(node),
        is_star_import=adapter.is_star_import(node),
        relative_level=adapter.get_relative_level(node),
    )

    # Process the imported names
    for name_node, alias_node in adapter.get_import_names(node):
        # Create text segment for name
        name_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=name_node.byte_start,
            byte_end=name_node.byte_end,
            parent_id=code_section_segment.id,
        )
        name_text = get_segment_text(content_part_text_segment=name_segment, blob_store=blob_store)

        # Create alias segment if present
        alias_segment = None
        alias_text = None
        if alias_node:
            alias_segment = ContentPartTextSegment(
                content_part_text=code.content_part_text,
                byte_start=alias_node.byte_start,
                byte_end=alias_node.byte_end,
                parent_id=code_section_segment.id,
            )
            alias_text = get_segment_text(content_part_text_segment=alias_segment, blob_store=blob_store)

        # Create import name entry
        import_name = CodeSectionImportName(
            code_section_import_id=import_section.id,
            name_segment=name_segment,
            name_segment_id=name_segment.id,
            name_text=name_text,
            alias_segment=alias_segment,
            alias_segment_id=alias_segment.id if alias_segment else None,
            alias_text=alias_text,
        )
        import_section.code_section_import_names.append(import_name)

    # Add alias bindings from this import to the symbol table
    for alias, fully_qualified in adapter.get_alias_bindings(node):
        # Use setdefault to avoid overwriting existing bindings
        _ = symbol_table.bindings.setdefault(alias, fully_qualified)

    return import_section

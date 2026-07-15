"""Builder for constructing CodeSectionEnum instances from source code."""

from __future__ import annotations

# Kernel Graph Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.enum.code_section_enum import CodeSectionEnum
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.section.builder import build_section_from_code
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.enum.adapter import CodeSectionEnumAdapter
from aware_code.section.enum_value.adapter import CodeSectionEnumValueAdapter
from aware_code.section.enum_value.builder import build_enum_value_section

# Aware Storage
from aware_storage.blob_store import BlobStore


def build_enum_section(
    *,
    adapter: CodeSectionEnumAdapter[T_Node],
    enum_value_adapter: CodeSectionEnumValueAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    source: bytes,
    section_index: CodeSectionBuilderIndex,
    blob_store: BlobStore | None = None,
) -> tuple[CodeSectionEnum, list[CodeSection]]:
    """
    Build a CodeSectionEnum instance from the provided source code.

    Args:
        adapter: The CodeSectionEnumAdapter instance
        enum_value_adapter: The CodeSectionEnumValueAdapter instance
        code: The code object
        code_section: The code section to build
        node: The node to build the section from
        source: The source code bytes
        section_index: The section builder index
        blob_store: The blob store

    Returns:
        Tuple of (constructed CodeSectionEnum, child CodeSections)
    """
    section_segment = code_section.content_part_text_segment

    # Get the enum name
    name_node = adapter.get_name(node)
    name_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=name_node.byte_start,
        byte_end=name_node.byte_end,
        parent_id=section_segment.id,
    )
    name = get_segment_text(name_segment, blob_store=blob_store)

    # Create the enum section
    enum_section = CodeSectionEnum(
        code_section=code_section,
        name_segment=name_segment,
        name=name,
    )
    code_section.code_section_enum = enum_section

    # Process enum values as child CodeSections
    child_sections: list[CodeSection] = []

    value_nodes = list(enum_value_adapter.match_nodes(node.node, source))
    value_nodes.sort(key=lambda n: (n.byte_start, n.byte_end))

    for position, value_node in enumerate(value_nodes):
        value_code_section = build_section_from_code(
            adapter=enum_value_adapter,
            code_section_type=CodeSectionType.enum_value,
            source=source,
            code=code,
            node=value_node,
            section_index=section_index,
            parent=code_section.qualname,
            parent_id=section_segment.id,
        )
        enum_value = build_enum_value_section(
            adapter=enum_value_adapter,
            code=code,
            code_section=value_code_section,
            node=value_node,
            code_section_enum_id=enum_section.id,
            position=position,
            blob_store=blob_store,
        )
        enum_section.code_section_enum_values.append(enum_value)
        child_sections.append(value_code_section)

    return enum_section, child_sections

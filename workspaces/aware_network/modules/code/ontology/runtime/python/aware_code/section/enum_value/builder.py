"""Builder for constructing CodeSectionEnumValue instances from source code."""

from uuid import UUID

# Kernel Graph Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.enum.code_section_enum_value import CodeSectionEnumValue
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.section.enum_value.adapter import CodeSectionEnumValueAdapter

# Aware Storage
from aware_storage.blob_store import BlobStore


def build_enum_value_section(
    *,
    adapter: CodeSectionEnumValueAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    code_section_enum_id: UUID,
    position: int,
    blob_store: BlobStore | None = None,
) -> CodeSectionEnumValue:
    """
    Build a CodeSectionEnumValue instance from the provided code section and node.
    """
    section_segment = code_section.content_part_text_segment

    name_node = adapter.get_name(node)
    value_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=name_node.byte_start,
        byte_end=name_node.byte_end,
        parent_id=section_segment.id,
    )
    value = get_segment_text(content_part_text_segment=value_segment, blob_store=blob_store)

    enum_value = CodeSectionEnumValue(
        code_section=code_section,
        code_section_enum_id=code_section_enum_id,
        value=value,
        value_segment=value_segment,
        position=position,
    )
    code_section.code_section_enum_value = enum_value
    return enum_value

"""Builder for constructing CodeSectionAttribute instances from source code."""

from uuid import UUID

# Kernel Graph Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.node.node import T_Node, CodeNode
from aware_code.section.attribute.adapter import CodeSectionAttributeAdapter
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.builder import build_section_from_code_by_identity

# Aware Storage
from aware_storage.blob_store import BlobStore


def build_section_from_code_with_param_discriminator(
    adapter: CodeSectionAttributeAdapter[T_Node],
    source: bytes,
    code: Code,
    node: CodeNode[T_Node],
    section_index: CodeSectionBuilderIndex,
    is_parameter: bool,
    discriminator: str | None = None,
    parent_ref: str | None = None,
    parent_id: UUID | None = None,
) -> CodeSection:
    """
    Build a CodeSectionAttribute instance from the provided node with a parameter discriminator.
    """
    qualname = adapter.qualname_for_role(node, is_parameter=is_parameter, parent=parent_ref)
    body_bytes = adapter.body_bytes(node, source)
    if is_parameter:
        # Discriminator to avoid collisions with class attributes of same name.
        # Default: "param" for input params. For outputs, callers should pass discriminator="out".
        label = discriminator or "param"
        qualname = f"{qualname} ({label})"
        body_bytes = f"{label}:".encode("utf-8") + body_bytes

    # Get optional reference string for lookup
    reference = adapter.reference_string_for_role(node, is_parameter=is_parameter, parent=parent_ref)
    if is_parameter and discriminator and discriminator != "param" and reference:
        # Avoid reference collisions between input/output params that share the same base ref.
        reference = f"{reference} ({discriminator})"

    # Create the code section
    code_section = build_section_from_code_by_identity(
        code_section_type=adapter.section_type,
        code=code,
        node=node,
        qualname=qualname,
        body_bytes=body_bytes,
        reference=reference,
        parent_id=parent_id,
        section_index=section_index,
    )
    return code_section


def build_attribute_section(
    adapter: CodeSectionAttributeAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    is_parameter: bool,
    blob_store: BlobStore | None = None,
) -> CodeSectionAttribute:
    """
    Build a CodeSectionAttribute instance from the provided code section and node.

    Args:
        code: The code object
        code_section: The code section to build the attribute for
        node: The node to create a section for
        is_parameter: Whether this is a function parameter

    Returns:
        The created CodeSectionAttribute instance
    """
    section_segment = code_section.content_part_text_segment

    # Get the name node
    name_node = adapter.get_name(node, is_parameter)
    name_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=name_node.byte_start,
        byte_end=name_node.byte_end,
        parent_id=section_segment.id,
    )
    name = get_segment_text(content_part_text_segment=name_segment, blob_store=blob_store)

    # Get the type node
    type_segment: ContentPartTextSegment | None = None
    type_node = adapter.get_type(node, is_parameter)
    if type_node:
        type_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=type_node.byte_start,
            byte_end=type_node.byte_end,
            parent_id=section_segment.id,
        )
    type_text = (
        get_segment_text(content_part_text_segment=type_segment, blob_store=blob_store) if type_segment else None
    )

    # Get the default value node if present
    default_value_segment: ContentPartTextSegment | None = None
    default_value_node = adapter.get_default_value(node, is_parameter)
    if default_value_node:
        default_value_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=default_value_node.byte_start,
            byte_end=default_value_node.byte_end,
            parent_id=section_segment.id,
        )

    # Determine properties
    is_public = adapter.is_public(node, is_parameter)
    is_primary = adapter.is_primary(node, is_parameter)
    is_required = adapter.is_required(node, is_parameter) or is_primary
    is_unique = adapter.has_unique(node, is_parameter) or is_primary
    default_value_node = adapter.get_default_value(node, is_parameter)

    # Parse the default value properly from the node text
    default_value_text: str | None = None
    if default_value_node:
        default_value_text = default_value_node.node_text()

    # Relationship SSOT (optional; only some languages support these constructs)
    edge_spec_name = adapter.get_edge_spec(node, is_parameter)
    is_many_to_many = adapter.is_many_to_many(node, is_parameter)

    # Create the attribute section
    attribute_section = CodeSectionAttribute(
        code_section=code_section,
        name_segment=name_segment,
        name_segment_id=name_segment.id,
        type_segment=type_segment,
        default_value_segment=default_value_segment,
        name=name,
        type_text=type_text,
        default_value_text=default_value_text,
        is_required=is_required,
        is_public=is_public,
        is_unique=is_unique,
        is_primary=is_primary,
        is_many_to_many=is_many_to_many,
        edge_spec_name=edge_spec_name,
    )
    code_section.code_section_attribute = attribute_section

    return attribute_section

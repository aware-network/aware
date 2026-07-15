"""Builder for constructing CodeSectionComment instances from source code."""

from __future__ import annotations

# Kernel Graph Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.comment.code_section_comment import CodeSectionComment
from aware_code_ontology.comment.code_section_comment_content import (
    CodeSectionCommentContent,
)
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.builder import make_identity_hash
from aware_code.section.attribute.adapter import CodeSectionAttributeAdapter
from aware_code.section.enum.adapter import CodeSectionEnumAdapter
from aware_code.section.class_.adapter import CodeSectionClassAdapter
from aware_code.section.comment.adapter import CodeSectionCommentAdapter
from aware_code.section.function.adapter import CodeSectionFunctionAdapter
from aware_code.section.projection.adapter import CodeSectionProjectionAdapter

# Logging
from aware_utils.logging import logger


def build_comment_section(
    adapter: CodeSectionCommentAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    source: bytes,
    section_index: CodeSectionBuilderIndex,
    enum_adapter: CodeSectionEnumAdapter[T_Node] | None = None,
    class_adapter: CodeSectionClassAdapter[T_Node] | None = None,
    function_adapter: CodeSectionFunctionAdapter[T_Node] | None = None,
    attribute_adapter: CodeSectionAttributeAdapter[T_Node] | None = None,
    projection_adapter: CodeSectionProjectionAdapter[T_Node] | None = None,
) -> CodeSectionComment:
    """
    Build a CodeSectionComment instance from the provided node.

    Args:
        adapter: The adapter for the comment section
        code: The code object containing the source
        code_section: The code section to build
        node: The node to build from
        source: Source code bytes
        section_index: Shared index for cross-references

    Returns:
        Constructed CodeSectionComment instance
    """
    # Get the comment type
    comment_type = adapter.get_comment_type(node)

    # Create the comment section
    comment_section = CodeSectionComment(
        code_section=code_section,
        type=comment_type,
    )
    code_section.code_section_comment = comment_section

    # Get content segments and create CodeSectionCommentContent records
    content_segments = list(adapter.get_content_segments(node, source))
    for position, segment_node in enumerate(content_segments):
        # Create content part text segment for each segment
        segment_content = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=segment_node.byte_start,
            byte_end=segment_node.byte_end,
            parent_id=code_section.id,
        )

        # Create the comment content link
        comment_content = CodeSectionCommentContent(
            code_section_comment_id=comment_section.id,
            position=position,
            content_part_text_segment=segment_content,
        )

        # Add to the comment's content list
        comment_section.code_section_comment_contents.append(comment_content)

    # Find the target section for the comment
    assoc_node = adapter.get_associated_node(node, source)
    if assoc_node:
        target_sec = find_target_section(
            adapter=adapter,
            comment_node=node,
            associated_node=assoc_node,
            source=source,
            code=code,
            section_index=section_index,
            enum_adapter=enum_adapter,
            class_adapter=class_adapter,
            function_adapter=function_adapter,
            attribute_adapter=attribute_adapter,
            projection_adapter=projection_adapter,
        )
        if target_sec:
            if target_sec.type is CodeSectionType.class_:
                if target_sec.code_section_class is None:
                    raise ValueError(f"Class section {target_sec.id} has no associated class")
                target_sec.code_section_class.code_section_comments.append(comment_section)
                comment_section.code_section_class_id = target_sec.code_section_class.id
            elif target_sec.type is CodeSectionType.function:
                if target_sec.code_section_function is None:
                    raise ValueError(f"Function section {target_sec.id} has no associated function")
                target_sec.code_section_function.code_section_comments.append(comment_section)
                comment_section.code_section_function_id = target_sec.code_section_function.id
            elif target_sec.type is CodeSectionType.enum:
                if target_sec.code_section_enum is None:
                    raise ValueError(f"Enum section {target_sec.id} has no associated enum")
                target_sec.code_section_enum.code_section_comments.append(comment_section)
                comment_section.code_section_enum_id = target_sec.code_section_enum.id
            elif target_sec.type is CodeSectionType.enum_value:
                if target_sec.code_section_enum_value is None:
                    raise ValueError(f"Enum value section {target_sec.id} has no associated enum value")
                target_sec.code_section_enum_value.code_section_comments.append(comment_section)
                comment_section.code_section_enum_value_id = target_sec.code_section_enum_value.id
            elif target_sec.type is CodeSectionType.attribute:
                if target_sec.code_section_attribute is None:
                    raise ValueError(f"Attribute section {target_sec.id} has no associated attribute")
                target_sec.code_section_attribute.code_section_comments.append(comment_section)
                comment_section.code_section_attribute_id = target_sec.code_section_attribute.id
            elif target_sec.type is CodeSectionType.projection:
                if target_sec.code_section_projection is None:
                    raise ValueError(f"Projection section {target_sec.id} has no associated projection")
                target_sec.code_section_projection.code_section_comments.append(comment_section)
                comment_section.code_section_projection_id = target_sec.code_section_projection.id
    return comment_section


def find_target_section(
    adapter: CodeSectionCommentAdapter[T_Node],
    comment_node: CodeNode[T_Node],
    associated_node: CodeNode[T_Node],
    source: bytes,
    code: Code,
    section_index: CodeSectionBuilderIndex,
    enum_adapter: CodeSectionEnumAdapter[T_Node] | None = None,
    class_adapter: CodeSectionClassAdapter[T_Node] | None = None,
    function_adapter: CodeSectionFunctionAdapter[T_Node] | None = None,
    attribute_adapter: CodeSectionAttributeAdapter[T_Node] | None = None,
    projection_adapter: CodeSectionProjectionAdapter[T_Node] | None = None,
) -> CodeSection | None:
    """
    Find a section in the index that corresponds to the associated node.

    Args:
        comment_node: The node this comment is associated with
        associated_node: The node this comment is associated with
        source: Source bytes for content extraction
        code: The code object containing the source
        section_index: Shared index of code sections

    Returns:
        The matching section or None if not found
    """
    # If the adapter has a section lookup key, use it
    key = adapter.section_lookup_key(associated_node)
    if key:
        code_section_type, reference = key
        sec = section_index.get_by_ref(code_section_type, reference)
        if sec:
            return sec
        logger.debug(
            "Comment section lookup key did not resolve; falling back to generic "
            f"target lookup for {code_section_type} {reference}"
        )

    # Determine if this is a class, function, or attribute
    # Try each adapter using the identity hash to see which one recognizes this node
    node_adapters: list[CodeNodeAdapter[T_Node]] = []
    if enum_adapter is not None:
        node_adapters.append(enum_adapter)
    if class_adapter is not None:
        node_adapters.append(class_adapter)
    if function_adapter is not None:
        node_adapters.append(function_adapter)
    if attribute_adapter is not None:
        node_adapters.append(attribute_adapter)
    if projection_adapter is not None:
        node_adapters.append(projection_adapter)

    for node_adapter in node_adapters:
        target_section = get_target_section(
            adapter=node_adapter,
            associated_node=associated_node,
            source=source,
            code=code,
            section_index=section_index,
            section_type=node_adapter.section_type,
        )
        if target_section:
            return target_section
    logger.debug(f"Could not find target section for comment: {comment_node.node_text()}")
    logger.debug(f"Associated node: {associated_node.node_text()}")
    return None


def get_target_section(
    adapter: CodeNodeAdapter[T_Node],
    associated_node: CodeNode[T_Node],
    source: bytes,
    code: Code,
    section_index: CodeSectionBuilderIndex,
    section_type: CodeSectionType,
) -> CodeSection | None:
    # Try to get qualified name and body bytes using this adapter
    try:
        qualname = adapter.qualname(associated_node)
        body_bytes = adapter.body_bytes(associated_node, source)
        # Create identity hash
        identity_hash = make_identity_hash(
            code_section_type=section_type,
            code_id=code.id,
            qualname=qualname,
            body_bytes=body_bytes,
        )
        # Look up in section index
        target_section = section_index.get_by_hash(section_type, identity_hash)
        if target_section:
            return target_section
    except Exception:
        # NOTE: Expected if the adapter doesn't recognize the node
        pass
    return None

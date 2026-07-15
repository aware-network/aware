"""Builder for constructing CodeSectionMirror instances from source code."""

# Kernel Graph Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.mirror.code_section_mirror import CodeSectionMirror
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Code Runtime
from aware_content.builder import get_segment_text
from aware_code.node.node import CodeNode, T_Node
from aware_code.section.mirror.adapter import CodeSectionMirrorAdapter

# Storage
from aware_storage.blob_store import BlobStore


def build_mirror_section(
    adapter: CodeSectionMirrorAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    blob_store: BlobStore | None = None,
) -> CodeSectionMirror:
    """
    Build a CodeSectionMirror instance from the provided node.

    Args:
        adapter: The adapter to use
        code: The code object containing the source
        code_section: The code section to build
        node: The node to build from
        blob_store: Optional blob store to use for loading segment text

    Returns:
        Constructed CodeSectionMirror instance
    """
    code_section_segment = code_section.content_part_text_segment
    target_node = adapter.get_target(node)

    target_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=target_node.byte_start,
        byte_end=target_node.byte_end,
        parent_id=code_section_segment.id,
    )
    target_text = get_segment_text(content_part_text_segment=target_segment, blob_store=blob_store)

    mirror_section = CodeSectionMirror(
        code_section=code_section,
        target_segment=target_segment,
        target_segment_id=target_segment.id,
        target_text=target_text,
    )

    return mirror_section

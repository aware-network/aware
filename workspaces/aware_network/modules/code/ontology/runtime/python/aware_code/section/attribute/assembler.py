"""Assembler helpers for CodeSectionAttribute objects (free-function driven)."""

# Kernel Graph Ontology
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.attribute.code_section_attribute import (
    CodeSectionAttribute,
)

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.section.attribute.segments import CodeSectionAttributeSegment

# Aware Storage
from aware_storage.blob_store import BlobStore


def assemble_attribute(
    *,
    code_section: CodeSection,
    segments: dict[str, ContentPartTextSegment | list[ContentPartTextSegment]],
    is_required: bool,
    is_public: bool,
    is_unique: bool,
    is_primary: bool,
    is_many_to_many: bool = False,
    edge_spec_name: str | None = None,
    blob_store: BlobStore | None = None,
) -> CodeSectionAttribute:
    """Assemble a `CodeSectionAttribute` with explicit semantics (no metadata dict contract)."""
    if CodeSectionAttributeSegment.NAME.value not in segments:
        raise ValueError(f"Attribute assembler requires a '{CodeSectionAttributeSegment.NAME.value}' segment")

    name_segment = segments[CodeSectionAttributeSegment.NAME.value]
    if not isinstance(name_segment, ContentPartTextSegment):
        raise ValueError(f"Name segment must be a ContentPartTextSegment, got {type(name_segment)}")

    name = get_segment_text(content_part_text_segment=name_segment, blob_store=blob_store)
    type_segment = segments.get(CodeSectionAttributeSegment.TYPE.value)
    default_segment = segments.get(CodeSectionAttributeSegment.DEFAULT_VALUE.value)

    type_text: str | None = None
    if isinstance(type_segment, ContentPartTextSegment):
        type_text = get_segment_text(content_part_text_segment=type_segment, blob_store=blob_store)

    default_value_text: str | None = None
    if isinstance(default_segment, ContentPartTextSegment):
        default_value_text = get_segment_text(content_part_text_segment=default_segment, blob_store=blob_store)

    attribute_section = CodeSectionAttribute(
        code_section=code_section,
        name=name,
        type_text=type_text,
        default_value_text=default_value_text,
        is_required=is_required,
        is_public=is_public,
        is_unique=is_unique,
        is_primary=is_primary,
        is_many_to_many=is_many_to_many,
        edge_spec_name=edge_spec_name,
        name_segment=name_segment,
        name_segment_id=name_segment.id,
        type_segment=(type_segment if isinstance(type_segment, ContentPartTextSegment) else None),
        default_value_segment=(default_segment if isinstance(default_segment, ContentPartTextSegment) else None),
        type_segment_id=(type_segment.id if isinstance(type_segment, ContentPartTextSegment) else None),
        default_value_segment_id=(default_segment.id if isinstance(default_segment, ContentPartTextSegment) else None),
    )

    code_section.code_section_attribute = attribute_section
    return attribute_section

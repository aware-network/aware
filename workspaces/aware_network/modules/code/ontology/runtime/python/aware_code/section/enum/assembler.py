"""Assembler helpers for CodeSectionEnum objects (free-function driven)."""

from __future__ import annotations

# Kernel Graph Ontology
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.enum.code_section_enum import CodeSectionEnum

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.section.enum.segments import CodeSectionEnumSegment

# Aware Storage
from aware_storage.blob_store import BlobStore


def assemble_enum(
    *,
    code_section: CodeSection,
    segments: dict[str, ContentPartTextSegment | list[ContentPartTextSegment]],
    code_sections: dict[str, CodeSection | list[CodeSection]] | None = None,
    blob_store: BlobStore | None = None,
) -> CodeSectionEnum:
    """Assemble a `CodeSectionEnum` from explicit section inputs (no metadata contract)."""
    if CodeSectionEnumSegment.NAME.value not in segments:
        raise ValueError(f"Enum assembler requires a '{CodeSectionEnumSegment.NAME.value}' segment")

    name_segment = segments[CodeSectionEnumSegment.NAME.value]
    if not isinstance(name_segment, ContentPartTextSegment):
        raise ValueError(f"Name segment must be a ContentPartTextSegment, got {type(name_segment)}")

    name = get_segment_text(content_part_text_segment=name_segment, blob_store=blob_store)
    enum_section = CodeSectionEnum(
        code_section=code_section,
        name_segment=name_segment,
        name_segment_id=name_segment.id,
        name=name,
    )
    code_section.code_section_enum = enum_section

    if not code_sections or CodeSectionType.enum_value.value not in code_sections:
        raise ValueError(
            "Enum assembler requires nested enum value CodeSections under "
            + f"'{CodeSectionType.enum_value.value}' after introducing CodeSectionType.enum_value"
        )

    nested = code_sections[CodeSectionType.enum_value.value]
    enum_value_sections = nested if isinstance(nested, list) else [nested]
    enum_value_sections = sorted(enum_value_sections, key=lambda s: s.content_part_text_segment.byte_start or 0)

    for position, enum_value_section in enumerate(enum_value_sections):
        if enum_value_section.code_section_enum_value is None:
            raise ValueError(f"Enum value section {enum_value_section.qualname} has no associated enum value")
        enum_value_section.code_section_enum_value.code_section_enum_id = enum_section.id
        enum_value_section.code_section_enum_value.position = position
        enum_section.code_section_enum_values.append(enum_value_section.code_section_enum_value)

    return enum_section

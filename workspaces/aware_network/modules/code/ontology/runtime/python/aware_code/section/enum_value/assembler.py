"""Assembler helpers for CodeSectionEnumValue objects (free-function driven)."""

from __future__ import annotations

from uuid import UUID

from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.enum.code_section_enum_value import CodeSectionEnumValue

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.section.enum_value.segments import CodeSectionEnumValueSegment

# Aware Storage
from aware_storage.blob_store import BlobStore

_ZERO_UUID = UUID("00000000-0000-0000-0000-000000000000")


def assemble_enum_value(
    *,
    code_section: CodeSection,
    segments: dict[str, ContentPartTextSegment | list[ContentPartTextSegment]],
    blob_store: BlobStore | None = None,
) -> CodeSectionEnumValue:
    """Assemble a `CodeSectionEnumValue` from explicit section inputs."""
    if CodeSectionEnumValueSegment.VALUE.value not in segments:
        raise ValueError(f"Enum value assembler requires a '{CodeSectionEnumValueSegment.VALUE.value}' segment")

    value_segment = segments[CodeSectionEnumValueSegment.VALUE.value]
    if not isinstance(value_segment, ContentPartTextSegment):
        raise ValueError(f"Value segment must be a ContentPartTextSegment, got {type(value_segment)}")

    value = get_segment_text(content_part_text_segment=value_segment, blob_store=blob_store).strip()
    enum_value = CodeSectionEnumValue(
        code_section=code_section,
        code_section_enum_id=_ZERO_UUID,
        value_segment=value_segment,
        value=value,
    )
    code_section.code_section_enum_value = enum_value
    return enum_value

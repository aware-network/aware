"""Assembler helpers for CodeSectionFunction objects (free-function driven)."""

# Content
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.function.code_section_function import (
    CodeSectionFunction,
)

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.section.function.segments import CodeSectionFunctionSegment

# Aware Storage
from aware_storage.blob_store import BlobStore


def assemble_function(
    *,
    code_section: CodeSection,
    segments: dict[str, ContentPartTextSegment | list[ContentPartTextSegment]],
    is_public: bool,
    description: str | None = None,
    blob_store: BlobStore | None = None,
) -> CodeSectionFunction:
    """Assemble a `CodeSectionFunction` with explicit semantics (no metadata dict contract)."""
    if CodeSectionFunctionSegment.NAME.value not in segments:
        raise ValueError(f"Function assembler requires a '{CodeSectionFunctionSegment.NAME.value}' segment")

    # Determine if function is async
    is_async = CodeSectionFunctionSegment.IS_ASYNC.value in segments

    name_segment = segments[CodeSectionFunctionSegment.NAME.value]
    if not isinstance(name_segment, ContentPartTextSegment):
        raise ValueError(f"Name segment must be a ContentPartTextSegment, got {type(name_segment)}")
    signature_segment = segments[CodeSectionFunctionSegment.SIGNATURE.value]
    if not isinstance(signature_segment, ContentPartTextSegment):
        raise ValueError(f"Signature segment must be a ContentPartTextSegment, got {type(signature_segment)}")
    return_type_segment = segments.get(CodeSectionFunctionSegment.RETURN_TYPE.value)
    body_segment = segments.get(CodeSectionFunctionSegment.BODY.value)

    name = get_segment_text(content_part_text_segment=name_segment, blob_store=blob_store)

    function_section = CodeSectionFunction(
        code_section=code_section,
        name=name,
        description=description,
        is_public=is_public,
        is_async=is_async,
        name_segment=name_segment,
        name_segment_id=name_segment.id,
        signature_segment=signature_segment,
        signature_segment_id=signature_segment.id,
        return_type_segment=(return_type_segment if isinstance(return_type_segment, ContentPartTextSegment) else None),
        return_type_segment_id=(
            return_type_segment.id if isinstance(return_type_segment, ContentPartTextSegment) else None
        ),
        body_segment=(body_segment if isinstance(body_segment, ContentPartTextSegment) else None),
        body_segment_id=(body_segment.id if isinstance(body_segment, ContentPartTextSegment) else None),
    )

    code_section.code_section_function = function_section
    return function_section

"""Assembler helpers for CodeSectionDecorator objects (free-function driven)."""

# Kernel Graph Ontology
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.decorator.code_section_decorator import (
    CodeSectionDecorator,
)

from aware_code.section.decorator.segments import CodeSectionDecoratorSegment


def assemble_decorator(
    *,
    code_section: CodeSection,
    segments: dict[str, ContentPartTextSegment | list[ContentPartTextSegment]],
) -> CodeSectionDecorator:
    """Assemble a `CodeSectionDecorator` from explicit section inputs (no metadata contract)."""
    if CodeSectionDecoratorSegment.NAME.value not in segments:
        raise ValueError(f"Decorator assembler requires a '{CodeSectionDecoratorSegment.NAME.value}' segment")

    name_segment = segments[CodeSectionDecoratorSegment.NAME.value]
    if not isinstance(name_segment, ContentPartTextSegment):
        raise ValueError(f"Name segment must be a ContentPartTextSegment, got {type(name_segment)}")

    decorator_section = CodeSectionDecorator(
        code_section=code_section,
        name_segment=name_segment,
    )
    code_section.code_section_decorator = decorator_section
    return decorator_section

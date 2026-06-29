"""Assembler helpers for CodeSectionClass objects (free-function driven)."""

# Kernel Graph Ontology
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_code_ontology.class_.code_section_class import CodeSectionClass
from aware_code_ontology.class_.code_section_class_attribute import (
    CodeSectionClassAttribute,
)
from aware_code_ontology.class_.code_section_class_function import (
    CodeSectionClassFunction,
)
from aware_code_ontology.comment.code_section_comment import CodeSectionComment
from aware_code_ontology.decorator.code_section_decorator import CodeSectionDecorator
from aware_code_ontology.function.code_section_function import CodeSectionFunction

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.section.class_.segments import CodeSectionClassSegment

# Aware Storage
from aware_storage.blob_store import BlobStore


def add_class_attribute(
    *,
    class_section: CodeSectionClass,
    attribute_section: CodeSectionAttribute,
) -> CodeSectionClassAttribute:
    code_section_class_attribute = CodeSectionClassAttribute(
        code_section_attribute_id=attribute_section.id,
        code_section_class_id=class_section.id,
        code_section_attribute=attribute_section,
    )
    class_section.code_section_class_attributes.append(code_section_class_attribute)
    return code_section_class_attribute


def add_class_comment(
    *,
    class_section: CodeSectionClass,
    comment_section: CodeSectionComment,
) -> CodeSectionComment:
    class_section.code_section_comments.append(comment_section)
    return comment_section


def add_class_function(
    *,
    class_section: CodeSectionClass,
    function_section: CodeSectionFunction,
) -> CodeSectionClassFunction:
    position = len(class_section.code_section_class_functions)
    code_section_class_function = CodeSectionClassFunction(
        code_section_class_id=class_section.id,
        code_section_function_id=function_section.id,
        code_section_function=function_section,
        position=position,
    )
    class_section.code_section_class_functions.append(code_section_class_function)
    return code_section_class_function


def add_class_decorator(
    *,
    class_section: CodeSectionClass,
    decorator_section: CodeSectionDecorator,
) -> CodeSectionDecorator:
    class_section.code_section_decorators.append(decorator_section)
    return decorator_section


def assemble_class(
    *,
    code_section: CodeSection,
    segments: dict[str, ContentPartTextSegment | list[ContentPartTextSegment]],
    code_sections: dict[str, CodeSection | list[CodeSection]] | None = None,
    blob_store: BlobStore | None = None,
) -> CodeSectionClass:
    """Assemble a `CodeSectionClass` from explicit section inputs (no metadata contract)."""
    if CodeSectionClassSegment.NAME.value not in segments:
        raise ValueError(f"Class assembler requires a '{CodeSectionClassSegment.NAME.value}' segment")

    name_segment = segments[CodeSectionClassSegment.NAME.value]
    if not isinstance(name_segment, ContentPartTextSegment):
        raise ValueError(f"Name segment must be a ContentPartTextSegment, got {type(name_segment)}")

    name = get_segment_text(content_part_text_segment=name_segment, blob_store=blob_store)
    class_section = CodeSectionClass(
        code_section=code_section,
        name=name,
        name_segment=name_segment,
        name_segment_id=name_segment.id,
    )

    code_section.code_section_class = class_section

    # Nested function sections (methods)
    if code_sections and CodeSectionType.function.value in code_sections:
        function_sections = code_sections[CodeSectionType.function.value]

        def _get_byte_start(section: CodeSection) -> int:
            segment = section.content_part_text_segment
            if segment and segment.byte_start is not None:
                return segment.byte_start
            return 0

        if isinstance(function_sections, list):
            sorted_functions = sorted(
                function_sections,
                key=lambda s: (_get_byte_start(s), s.qualname),
            )
            for func_section in sorted_functions:
                if func_section.code_section_function:
                    _ = add_class_function(
                        class_section=class_section,
                        function_section=func_section.code_section_function,
                    )
        else:
            if function_sections.code_section_function:
                _ = add_class_function(
                    class_section=class_section,
                    function_section=function_sections.code_section_function,
                )

    # Nested attribute sections
    if code_sections and CodeSectionType.attribute.value in code_sections:
        attribute_sections = code_sections[CodeSectionType.attribute.value]
        if isinstance(attribute_sections, list):
            for attr_section in attribute_sections:
                if attr_section.code_section_attribute:
                    _ = add_class_attribute(
                        class_section=class_section,
                        attribute_section=attr_section.code_section_attribute,
                    )
        else:
            if attribute_sections.code_section_attribute:
                _ = add_class_attribute(
                    class_section=class_section,
                    attribute_section=attribute_sections.code_section_attribute,
                )

    # Nested comment sections
    if code_sections and CodeSectionType.comment.value in code_sections:
        comment_sections = code_sections[CodeSectionType.comment.value]
        if isinstance(comment_sections, list):
            for comment_section in comment_sections:
                if comment_section.code_section_comment:
                    _ = add_class_comment(
                        class_section=class_section,
                        comment_section=comment_section.code_section_comment,
                    )
        else:
            if comment_sections.code_section_comment:
                _ = add_class_comment(
                    class_section=class_section,
                    comment_section=comment_sections.code_section_comment,
                )

    return class_section

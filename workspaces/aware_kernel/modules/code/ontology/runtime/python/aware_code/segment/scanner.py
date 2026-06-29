"""Centralized segment scanning utilities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import cast
from uuid import UUID

from aware_utils.logging import logger

from aware_content.builder import get_segment_bytes
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_code_ontology.class_.code_section_class import CodeSectionClass
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.comment.code_section_comment import CodeSectionComment
from aware_code_ontology.decorator.code_section_decorator import CodeSectionDecorator
from aware_code_ontology.enum.code_section_enum import CodeSectionEnum
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_code_ontology.import_.code_section_import import CodeSectionImport
from aware_code_ontology.mirror.code_section_mirror import CodeSectionMirror

from aware_code.section.annotation.handlers import get_segment as get_annotation_segment
from aware_code.section.annotation.segments import CodeSectionAnnotationSegment
from aware_code.section.attribute.handlers import get_segment as get_attribute_segment
from aware_code.section.attribute.segments import CodeSectionAttributeSegment
from aware_code.section.class_.handlers import get_segment as get_class_segment
from aware_code.section.class_.segments import CodeSectionClassSegment
from aware_code.section.comment.handlers import get_segment as get_comment_segment
from aware_code.section.comment.segments import CodeSectionCommentSegment
from aware_code.section.decorator.handlers import get_segment as get_decorator_segment
from aware_code.section.decorator.segments import CodeSectionDecoratorSegment
from aware_code.section.enum.handlers import get_segment as get_enum_segment
from aware_code.section.enum.segments import CodeSectionEnumSegment
from aware_code.section.function.handlers import get_segment as get_function_segment
from aware_code.section.function.segments import CodeSectionFunctionSegment
from aware_code.section.import_.handlers import get_segment as get_import_segment
from aware_code.section.import_.segments import CodeSectionImportSegment
from aware_code.section.mirror.handlers import get_segment as get_mirror_segment
from aware_code.section.mirror.segments import CodeSectionMirrorSegment


@dataclass(frozen=True)
class _SectionSegmentBinding:
    section_attr: str
    segment_values: tuple[Enum, ...]
    parse_segment: Callable[[str], Enum]
    segment_getter: Callable[[object, Enum], ContentPartTextSegment | None]


def _get_class_segment_for_obj(section_obj: object, segment_type: Enum) -> ContentPartTextSegment | None:
    if not isinstance(section_obj, CodeSectionClass):
        return None
    if not isinstance(segment_type, CodeSectionClassSegment):
        return None
    return get_class_segment(section_obj, segment_type)


def _get_annotation_segment_for_obj(section_obj: object, segment_type: Enum) -> ContentPartTextSegment | None:
    if not isinstance(section_obj, CodeSectionAnnotation):
        return None
    if not isinstance(segment_type, CodeSectionAnnotationSegment):
        return None
    return get_annotation_segment(section_obj, segment_type)


def _get_function_segment_for_obj(section_obj: object, segment_type: Enum) -> ContentPartTextSegment | None:
    if not isinstance(section_obj, CodeSectionFunction):
        return None
    if not isinstance(segment_type, CodeSectionFunctionSegment):
        return None
    return get_function_segment(section_obj, segment_type)


def _get_attribute_segment_for_obj(section_obj: object, segment_type: Enum) -> ContentPartTextSegment | None:
    if not isinstance(section_obj, CodeSectionAttribute):
        return None
    if not isinstance(segment_type, CodeSectionAttributeSegment):
        return None
    return get_attribute_segment(section_obj, segment_type)


def _get_enum_segment_for_obj(section_obj: object, segment_type: Enum) -> ContentPartTextSegment | None:
    if not isinstance(section_obj, CodeSectionEnum):
        return None
    if not isinstance(segment_type, CodeSectionEnumSegment):
        return None
    return get_enum_segment(section_obj, segment_type)


def _get_import_segment_for_obj(section_obj: object, segment_type: Enum) -> ContentPartTextSegment | None:
    if not isinstance(section_obj, CodeSectionImport):
        return None
    if not isinstance(segment_type, CodeSectionImportSegment):
        return None
    return get_import_segment(section_obj, segment_type)


def _get_comment_segment_for_obj(section_obj: object, segment_type: Enum) -> ContentPartTextSegment | None:
    if not isinstance(section_obj, CodeSectionComment):
        return None
    if not isinstance(segment_type, CodeSectionCommentSegment):
        return None
    return get_comment_segment(section_obj, segment_type)


def _get_decorator_segment_for_obj(section_obj: object, segment_type: Enum) -> ContentPartTextSegment | None:
    if not isinstance(section_obj, CodeSectionDecorator):
        return None
    if not isinstance(segment_type, CodeSectionDecoratorSegment):
        return None
    return get_decorator_segment(section_obj, segment_type)


def _get_mirror_segment_for_obj(section_obj: object, segment_type: Enum) -> ContentPartTextSegment | None:
    if not isinstance(section_obj, CodeSectionMirror):
        return None
    if not isinstance(segment_type, CodeSectionMirrorSegment):
        return None
    return get_mirror_segment(section_obj, segment_type)


CODE_SECTION_SEGMENT_MAPPING: dict[CodeSectionType, _SectionSegmentBinding] = {
    CodeSectionType.annotation: _SectionSegmentBinding(
        section_attr="code_section_annotation",
        segment_values=tuple(CodeSectionAnnotationSegment),
        parse_segment=lambda name: CodeSectionAnnotationSegment(name),
        segment_getter=_get_annotation_segment_for_obj,
    ),
    CodeSectionType.class_: _SectionSegmentBinding(
        section_attr="code_section_class",
        segment_values=tuple(CodeSectionClassSegment),
        parse_segment=lambda name: CodeSectionClassSegment(name),
        segment_getter=_get_class_segment_for_obj,
    ),
    CodeSectionType.function: _SectionSegmentBinding(
        section_attr="code_section_function",
        segment_values=tuple(CodeSectionFunctionSegment),
        parse_segment=lambda name: CodeSectionFunctionSegment(name),
        segment_getter=_get_function_segment_for_obj,
    ),
    CodeSectionType.attribute: _SectionSegmentBinding(
        section_attr="code_section_attribute",
        segment_values=tuple(CodeSectionAttributeSegment),
        parse_segment=lambda name: CodeSectionAttributeSegment(name),
        segment_getter=_get_attribute_segment_for_obj,
    ),
    CodeSectionType.enum: _SectionSegmentBinding(
        section_attr="code_section_enum",
        segment_values=tuple(CodeSectionEnumSegment),
        parse_segment=lambda name: CodeSectionEnumSegment(name),
        segment_getter=_get_enum_segment_for_obj,
    ),
    CodeSectionType.import_: _SectionSegmentBinding(
        section_attr="code_section_import",
        segment_values=tuple(CodeSectionImportSegment),
        parse_segment=lambda name: CodeSectionImportSegment(name),
        segment_getter=_get_import_segment_for_obj,
    ),
    CodeSectionType.comment: _SectionSegmentBinding(
        section_attr="code_section_comment",
        segment_values=tuple(CodeSectionCommentSegment),
        parse_segment=lambda name: CodeSectionCommentSegment(name),
        segment_getter=_get_comment_segment_for_obj,
    ),
    CodeSectionType.decorator: _SectionSegmentBinding(
        section_attr="code_section_decorator",
        segment_values=tuple(CodeSectionDecoratorSegment),
        parse_segment=lambda name: CodeSectionDecoratorSegment(name),
        segment_getter=_get_decorator_segment_for_obj,
    ),
    CodeSectionType.mirror: _SectionSegmentBinding(
        section_attr="code_section_mirror",
        segment_values=tuple(CodeSectionMirrorSegment),
        parse_segment=lambda name: CodeSectionMirrorSegment(name),
        segment_getter=_get_mirror_segment_for_obj,
    ),
}


class CodeSegmentScanner:
    """Unified segment scanner that works across supported section types."""

    @staticmethod
    def scan_section_segments(section: CodeSection) -> dict[str, str]:
        """Scan segments in any supported section type and compute SHA-1 hashes."""
        mapping = CODE_SECTION_SEGMENT_MAPPING.get(section.type)
        if mapping is None:
            logger.warning("No segment mapping found for section type: %s", section.type)
            return {}

        section_obj_raw = getattr(section, mapping.section_attr, None)
        if section_obj_raw is None:
            logger.warning("No %s found in section %s", mapping.section_attr, section.qualname)
            return {}
        section_obj = cast(object, section_obj_raw)

        return CodeSegmentScanner._scan_segments_for_object(section_obj, mapping)

    @staticmethod
    def _scan_segments_for_object(section_obj: object, mapping: _SectionSegmentBinding) -> dict[str, str]:
        segments: dict[str, str] = {}
        for segment_type in mapping.segment_values:
            segment = mapping.segment_getter(section_obj, segment_type)
            if segment is None:
                continue
            segment_bytes = get_segment_bytes(segment)
            if not segment_bytes:
                continue
            segment_name = cast(str, segment_type.value)
            segments[segment_name] = CodeSegmentScanner._compute_segment_hash(segment_bytes)
        return segments

    @staticmethod
    def _compute_segment_hash(segment_bytes: bytes) -> str:
        return hashlib.sha1(segment_bytes).hexdigest()

    @staticmethod
    def get_segment_from_section(section: CodeSection, segment_name: str) -> ContentPartTextSegment | None:
        """Get a segment by name from a supported section type."""
        mapping = CODE_SECTION_SEGMENT_MAPPING.get(section.type)
        if mapping is None:
            logger.warning("No segment mapping found for section type: %s", section.type)
            return None

        section_obj_raw = getattr(section, mapping.section_attr, None)
        if section_obj_raw is None:
            logger.warning("No %s found in section %s", mapping.section_attr, section.qualname)
            return None
        section_obj = cast(object, section_obj_raw)

        try:
            segment_type = mapping.parse_segment(segment_name)
        except ValueError:
            return None
        return mapping.segment_getter(section_obj, segment_type)

    @staticmethod
    def get_all_segments_for_section(section: CodeSection) -> dict[str, ContentPartTextSegment]:
        """Get all available segments for a section."""
        mapping = CODE_SECTION_SEGMENT_MAPPING.get(section.type)
        if mapping is None:
            logger.warning("No segment mapping found for section type: %s", section.type)
            return {}

        section_obj_raw = getattr(section, mapping.section_attr, None)
        if section_obj_raw is None:
            logger.warning("No %s found in section %s", mapping.section_attr, section.qualname)
            return {}
        section_obj = cast(object, section_obj_raw)

        segments: dict[str, ContentPartTextSegment] = {}
        for segment_type in mapping.segment_values:
            segment = mapping.segment_getter(section_obj, segment_type)
            if segment is not None:
                segment_name = cast(str, segment_type.value)
                segments[segment_name] = segment
        return segments

    @staticmethod
    def compute_section_segment_hashes(section: CodeSection) -> dict[str, str]:
        """Compute SHA-256 hashes for all discovered segments in one section."""
        hashes: dict[str, str] = {}
        for segment_name, segment in CodeSegmentScanner.get_all_segments_for_section(section).items():
            segment_bytes = get_segment_bytes(segment)
            hashes[segment_name] = hashlib.sha256(segment_bytes).hexdigest()
        return hashes

    @staticmethod
    def compute_all_segment_hashes(sections: list[CodeSection]) -> dict[UUID, dict[str, str]]:
        """Compute segment hashes for all provided sections."""
        segment_hashes: dict[UUID, dict[str, str]] = {}
        for section in sections:
            section_hashes = CodeSegmentScanner.compute_section_segment_hashes(section)
            if section_hashes:
                segment_hashes[section.id] = section_hashes
        return segment_hashes

    @staticmethod
    def scan_all_sections(sections: list[CodeSection]) -> dict[UUID, dict[str, str]]:
        """Scan all sections and compute SHA-1 hashes per segment."""
        segment_hashes: dict[UUID, dict[str, str]] = {}
        for section in sections:
            section_hashes = CodeSegmentScanner.scan_section_segments(section)
            if section_hashes:
                segment_hashes[section.id] = section_hashes
        return segment_hashes

    @staticmethod
    def get_supported_section_types() -> list[CodeSectionType]:
        """Get all section types that currently support segment scanning."""
        return list(CODE_SECTION_SEGMENT_MAPPING.keys())

    @staticmethod
    def get_segment_types_for_section_type(section_type: CodeSectionType) -> list[str]:
        """Get all segment type names for a given section type."""
        mapping = CODE_SECTION_SEGMENT_MAPPING.get(section_type)
        if mapping is None:
            return []
        return [cast(str, segment.value) for segment in mapping.segment_values]

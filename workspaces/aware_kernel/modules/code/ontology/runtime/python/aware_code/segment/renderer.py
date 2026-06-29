"""Code segment renderer for applying behavioral changes using surgical editing."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, final
from uuid import UUID

from aware_utils.logging import logger

from aware_content.builder import get_segment_text
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection

from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer_surgical import CodeSectionWriterSurgical
from aware_code.segment.scanner import CodeSegmentScanner


class _ChangeDiffLike(Protocol):
    property: str
    new_value: object


class _PrimitiveChangeLike(Protocol):
    change_diffs: Sequence[_ChangeDiffLike]


class ContentPartTextSegmentChangeLike(Protocol):
    segment_name: str
    change: _PrimitiveChangeLike | None


class CodeSectionChangeLike(Protocol):
    code_section_id: UUID
    content_part_text_segment_changes: Sequence[ContentPartTextSegmentChangeLike]


class CodeChangeLike(Protocol):
    code_section_changes: Sequence[CodeSectionChangeLike]


@final
class CodeSegmentRenderer:
    """Apply code segment changes using surgical editing."""

    def __init__(self, section_index: CodeSectionBuilderIndex, builder: object | None = None):
        """Initialize the renderer.

        `builder` is retained for call-site compatibility but not required by the
        surgical writer path.
        """
        self.section_index = section_index
        self._builder = builder

    def apply_changes(self, code: Code, code_change: CodeChangeLike) -> Code:
        """Apply all section changes in a code-change payload."""
        logger.info(
            "Applying %s section changes using surgical editing",
            len(code_change.code_section_changes),
        )

        writer = CodeSectionWriterSurgical(code=code, index=self.section_index, indent_size=4)
        for section_change in code_change.code_section_changes:
            try:
                self.apply_section_change(writer, section_change)
            except Exception as exc:
                logger.error(
                    "Failed to apply section change %s: %s",
                    section_change.code_section_id,
                    exc,
                )

        return code

    def apply_section_change(
        self,
        writer: CodeSectionWriterSurgical,
        section_change: CodeSectionChangeLike,
    ) -> None:
        """Apply all segment changes within a section."""
        section = self.section_index.get_by_id(section_change.code_section_id)
        if section is None:
            logger.warning("Could not find section %s", section_change.code_section_id)
            return

        logger.info("Applying changes to section %s", section.qualname)

        for segment_change in section_change.content_part_text_segment_changes:
            try:
                self.apply_segment_change(writer, section, segment_change)
            except Exception as exc:
                logger.error(
                    "Failed to apply segment change %s in section %s: %s",
                    segment_change.segment_name,
                    section.qualname,
                    exc,
                )

    def apply_segment_change(
        self,
        writer: CodeSectionWriterSurgical,
        section: CodeSection,
        segment_change: ContentPartTextSegmentChangeLike,
    ) -> None:
        """Apply a single segment change to a known section."""
        new_text = self._extract_new_text_from_change(segment_change)
        if new_text is None:
            logger.warning(
                "Could not extract new text from segment change %s",
                segment_change.segment_name,
            )
            return

        segment = CodeSegmentScanner.get_segment_from_section(section, segment_change.segment_name)
        if segment is None:
            logger.warning(
                "Could not find segment %s in section %s",
                segment_change.segment_name,
                section.qualname,
            )
            return

        old_text = get_segment_text(content_part_text_segment=segment)
        logger.info(
            "Replacing segment %s.%s",
            section.qualname,
            segment_change.segment_name,
        )
        logger.info(
            "  Old text: %r%s",
            old_text[:100],
            "..." if len(old_text) > 100 else "",
        )
        logger.info(
            "  New text: %r%s",
            new_text[:100],
            "..." if len(new_text) > 100 else "",
        )

        writer.replace_segment_text(segment, new_text)

        logger.info(
            "Successfully replaced segment %s.%s",
            section.qualname,
            segment_change.segment_name,
        )

    def _extract_new_text_from_change(self, change: ContentPartTextSegmentChangeLike) -> str | None:
        """Extract replacement text from a segment change payload."""
        primitive_change = change.change
        if primitive_change is None:
            return None

        for diff in primitive_change.change_diffs:
            if diff.property != "text":
                continue
            value = diff.new_value
            if isinstance(value, str):
                return value
            if value is None:
                return ""
            return str(value)

        return None

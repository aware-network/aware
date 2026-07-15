from __future__ import annotations

from aware_code_ontology.annotation.code_section_annotation import (
    CodeSectionAnnotation,
)
from aware_content.builder import get_segment_text
from aware_content_ontology.part.content_part_text_segment import (
    ContentPartTextSegment,
)

from aware_code.section.annotation.segments import CodeSectionAnnotationSegment


def get_segment(
    annotation: CodeSectionAnnotation,
    kind: CodeSectionAnnotationSegment,
) -> ContentPartTextSegment | None:
    if kind is CodeSectionAnnotationSegment.RAW:
        return annotation.code_section.content_part_text_segment
    if kind is CodeSectionAnnotationSegment.PATH:
        return _text_segment_for_token(
            annotation=annotation,
            token=annotation.path,
            search_start=0,
        )
    path_segment = _text_segment_for_token(
        annotation=annotation,
        token=annotation.path,
        search_start=0,
    )
    path_end = (
        path_segment.byte_end
        if path_segment is not None and path_segment.byte_end is not None
        else 0
    )
    if kind is CodeSectionAnnotationSegment.VERB:
        return _text_segment_for_token(
            annotation=annotation,
            token=annotation.verb,
            search_start=path_end,
        )
    if kind is CodeSectionAnnotationSegment.ARGS:
        return _args_segment(annotation=annotation, search_start=path_end)
    return None


def _args_segment(
    *,
    annotation: CodeSectionAnnotation,
    search_start: int,
) -> ContentPartTextSegment | None:
    args = [arg for arg in annotation.args if arg]
    if not args:
        return None
    raw_segment = annotation.code_section.content_part_text_segment
    raw_text = get_segment_text(raw_segment)
    relative_search_start = max(0, search_start - (raw_segment.byte_start or 0))
    first = args[0]
    last = args[-1]
    start_index = raw_text.find(
        first,
        _char_index_for_byte(raw_text, relative_search_start),
    )
    if start_index < 0:
        return None
    end_index = raw_text.find(last, start_index)
    if end_index < 0:
        return None
    end_index += len(last)
    return _child_segment_for_char_range(
        parent=raw_segment,
        raw_text=raw_text,
        start_index=start_index,
        end_index=end_index,
    )


def _text_segment_for_token(
    *,
    annotation: CodeSectionAnnotation,
    token: str,
    search_start: int,
) -> ContentPartTextSegment | None:
    if not token:
        return None
    raw_segment = annotation.code_section.content_part_text_segment
    raw_text = get_segment_text(raw_segment)
    relative_search_start = max(0, search_start - (raw_segment.byte_start or 0))
    start_index = raw_text.find(
        token,
        _char_index_for_byte(raw_text, relative_search_start),
    )
    if start_index < 0:
        return None
    return _child_segment_for_char_range(
        parent=raw_segment,
        raw_text=raw_text,
        start_index=start_index,
        end_index=start_index + len(token),
    )


def _child_segment_for_char_range(
    *,
    parent: ContentPartTextSegment,
    raw_text: str,
    start_index: int,
    end_index: int,
) -> ContentPartTextSegment:
    byte_start = (parent.byte_start or 0) + len(raw_text[:start_index].encode("utf-8"))
    byte_end = (parent.byte_start or 0) + len(raw_text[:end_index].encode("utf-8"))
    return ContentPartTextSegment(
        content_part_text=parent.content_part_text,
        byte_start=byte_start,
        byte_end=byte_end,
        parent_id=parent.id,
    )


def _char_index_for_byte(text: str, byte_offset: int) -> int:
    if byte_offset <= 0:
        return 0
    encoded = text.encode("utf-8")
    if byte_offset >= len(encoded):
        return len(text)
    return len(encoded[:byte_offset].decode("utf-8", errors="ignore"))

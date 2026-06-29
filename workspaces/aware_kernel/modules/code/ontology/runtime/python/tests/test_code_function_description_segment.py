from __future__ import annotations

from uuid import uuid4

from aware_code.segment.scanner import CodeSegmentScanner
from aware_code.section.function.segments import CodeSectionFunctionSegment
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.comment.code_section_comment import CodeSectionComment
from aware_code_ontology.comment.code_section_comment_content import (
    CodeSectionCommentContent,
)
from aware_code_ontology.comment.code_section_comment_enums import (
    CodeSectionCommentType,
)
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_segment import (
    ContentPartTextSegment,
)


def test_code_segment_scanner_resolves_function_description_comment() -> None:
    content = ContentPartText(inline_text='def demo():\n    """Hello."""\n')
    section_segment = ContentPartTextSegment(
        content_part_text=content,
        byte_start=0,
        byte_end=len(content.inline_text or ""),
    )
    name_segment = ContentPartTextSegment(
        content_part_text=content,
        byte_start=4,
        byte_end=8,
        parent_id=section_segment.id,
    )
    signature_segment = ContentPartTextSegment(
        content_part_text=content,
        byte_start=8,
        byte_end=10,
        parent_id=section_segment.id,
    )
    body_segment = ContentPartTextSegment(
        content_part_text=content,
        byte_start=17,
        byte_end=29,
        parent_id=section_segment.id,
    )
    description_segment = ContentPartTextSegment(
        content_part_text=content,
        byte_start=17,
        byte_end=29,
        parent_id=section_segment.id,
    )
    code_section = CodeSection(
        code_id=uuid4(),
        content_part_text_segment=section_segment,
        identity_hash="function:demo",
        qualname="demo",
        section_key="demo",
        type=CodeSectionType.function,
    )
    comment = CodeSectionComment(
        code_section=code_section,
        type=CodeSectionCommentType.doc,
        code_section_comment_contents=[
            CodeSectionCommentContent(
                code_section_comment_id=uuid4(),
                position=0,
                content_part_text_segment=description_segment,
            )
        ],
    )
    function = CodeSectionFunction(
        code_section=code_section,
        name_segment=name_segment,
        signature_segment=signature_segment,
        body_segment=body_segment,
        name="demo",
        description="Hello.",
        is_async=False,
        is_public=True,
        code_section_comments=[comment],
    )
    code_section.code_section_function = function

    segment = CodeSegmentScanner.get_segment_from_section(
        code_section,
        CodeSectionFunctionSegment.DESCRIPTION_COMMENT.value,
    )
    segments = CodeSegmentScanner.get_all_segments_for_section(code_section)

    assert segment is description_segment
    assert segments[CodeSectionFunctionSegment.DESCRIPTION_COMMENT.value] is (
        description_segment
    )
    assert segments[CodeSectionFunctionSegment.BODY.value] is body_segment

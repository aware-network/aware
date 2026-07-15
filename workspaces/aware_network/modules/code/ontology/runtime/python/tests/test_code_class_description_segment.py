from __future__ import annotations

from uuid import uuid4

from aware_code.segment.scanner import CodeSegmentScanner
from aware_code.section.class_.segments import CodeSectionClassSegment
from aware_code_ontology.class_.code_section_class import CodeSectionClass
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.comment.code_section_comment import CodeSectionComment
from aware_code_ontology.comment.code_section_comment_content import (
    CodeSectionCommentContent,
)
from aware_code_ontology.comment.code_section_comment_enums import (
    CodeSectionCommentType,
)
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_segment import (
    ContentPartTextSegment,
)


def test_code_segment_scanner_resolves_class_description_comment() -> None:
    text = "/// Old class contract.\nclass TvChannel {\n}\n"
    content = ContentPartText(inline_text=text)
    comment_segment = ContentPartTextSegment(
        content_part_text=content,
        byte_start=0,
        byte_end=len("/// Old class contract."),
    )
    comment_content_segment = ContentPartTextSegment(
        content_part_text=content,
        byte_start=len("/// "),
        byte_end=len("/// Old class contract."),
        parent_id=comment_segment.id,
    )
    class_segment = ContentPartTextSegment(
        content_part_text=content,
        byte_start=len("/// Old class contract.\n"),
        byte_end=len(text),
    )
    keyword_segment = ContentPartTextSegment(
        content_part_text=content,
        byte_start=len("/// Old class contract.\n"),
        byte_end=len("/// Old class contract.\nclass"),
        parent_id=class_segment.id,
    )
    name_segment = ContentPartTextSegment(
        content_part_text=content,
        byte_start=len("/// Old class contract.\nclass "),
        byte_end=len("/// Old class contract.\nclass TvChannel"),
        parent_id=class_segment.id,
    )
    comment_code_section = CodeSection(
        code_id=uuid4(),
        content_part_text_segment=comment_segment,
        identity_hash="comment:TvChannel.description",
        qualname="TvChannel.description",
        section_key="TvChannel.description",
        type=CodeSectionType.comment,
    )
    class_code_section = CodeSection(
        code_id=uuid4(),
        content_part_text_segment=class_segment,
        identity_hash="class:TvChannel",
        qualname="TvChannel",
        section_key="TvChannel",
        type=CodeSectionType.class_,
    )
    comment = CodeSectionComment(
        code_section=comment_code_section,
        type=CodeSectionCommentType.doc,
        code_section_comment_contents=[
            CodeSectionCommentContent(
                code_section_comment_id=uuid4(),
                position=0,
                content_part_text_segment=comment_content_segment,
            )
        ],
    )
    class_ = CodeSectionClass(
        code_section=class_code_section,
        keyword_segment=keyword_segment,
        name_segment=name_segment,
        name="TvChannel",
        description="Old class contract.",
        code_section_comments=[comment],
    )
    class_code_section.code_section_class = class_

    segment = CodeSegmentScanner.get_segment_from_section(
        class_code_section,
        CodeSectionClassSegment.DESCRIPTION_COMMENT.value,
    )
    segments = CodeSegmentScanner.get_all_segments_for_section(class_code_section)

    assert segment is comment_segment
    assert segments[CodeSectionClassSegment.DESCRIPTION_COMMENT.value] is (
        comment_segment
    )
    assert segments[CodeSectionClassSegment.NAME.value] is name_segment

from __future__ import annotations

from aware_code.builder import build_code_from_content
from aware_code.section.annotation.segments import CodeSectionAnnotationSegment
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.segment.scanner import CodeSegmentScanner
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_content.builder import get_segment_text


def test_code_segment_scanner_resolves_aware_annotation_load_policy_args() -> None:
    setup_code_plugins()
    source_text = "ann home.RemoteControl::selected_channel load forward eager\n"
    code = build_code_from_content(
        sections_index=CodeSectionBuilderIndex(),
        content=source_text,
        code_key="inline://home/tv_channel.aware",
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    section = next(
        item for item in code.code_sections if item.type is CodeSectionType.annotation
    )

    segments = CodeSegmentScanner.get_all_segments_for_section(section)

    assert section.qualname == (
        "ann:ann home.RemoteControl::selected_channel load forward eager"
    )
    assert (
        get_segment_text(
            segments[CodeSectionAnnotationSegment.PATH.value],
        )
        == "home.RemoteControl::selected_channel"
    )
    assert (
        get_segment_text(
            segments[CodeSectionAnnotationSegment.VERB.value],
        )
        == "load"
    )
    assert (
        get_segment_text(
            segments[CodeSectionAnnotationSegment.ARGS.value],
        )
        == "forward eager"
    )
    assert (
        get_segment_text(
            segments[CodeSectionAnnotationSegment.RAW.value],
        )
        == "ann home.RemoteControl::selected_channel load forward eager"
    )

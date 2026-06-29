from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator

import pytest

from aware_code.builder import build_code_from_content
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.parse import (
    build_code_content_plan,
    collect_top_level_section_identity_descriptors,
    make_section_key,
    parse_content_tree,
)
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodeContentPlan,
    CodeSectionPlan,
)
from aware_code_ontology.code.code_section_enums import CodeSectionType


@contextmanager
def _isolated_registry() -> Iterator[None]:
    CodeLanguagePluginRegistry.clear()
    try:
        yield
    finally:
        CodeLanguagePluginRegistry.clear()
        setup_code_plugins()


def _top_level_builder_descriptors(
    *, content: str
) -> list[tuple[CodeSectionType, str, str, str, int, int]]:
    built = build_code_from_content(
        sections_index=CodeSectionBuilderIndex(),
        content=content,
        code_key="inline://builder-oracle",
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    descriptors: list[tuple[CodeSectionType, str, str, str, int, int]] = []
    for section in built.code_sections:
        segment = section.content_part_text_segment
        if segment.parent_id is not None:
            continue
        byte_start = segment.byte_start
        byte_end = segment.byte_end
        if byte_start is None or byte_end is None:
            continue
        descriptors.append(
            (
                section.type,
                section.section_key,
                section.qualname,
                section.identity_hash,
                byte_start,
                byte_end,
            )
        )
    descriptors.sort(key=lambda item: (item[4], item[5], item[0].value))
    return descriptors


def test_parse_content_tree_fails_closed_when_plugin_missing() -> None:
    with _isolated_registry():
        with pytest.raises(KeyError, match="No language plugin registered"):
            parse_content_tree(content="class A {}", language=CodeLanguage.aware)


def test_collect_top_level_section_identity_descriptors_basic_smoke() -> None:
    setup_code_plugins()

    descriptors = collect_top_level_section_identity_descriptors(
        content="class A {}",
        language=CodeLanguage.aware,
    )

    assert descriptors
    assert descriptors[0].section_type == CodeSectionType.class_
    assert descriptors[0].qualname == "A"
    assert descriptors[0].section_key == "A"


def test_collect_top_level_section_identity_descriptors_matches_builder_oracle() -> (
    None
):
    setup_code_plugins()
    content = """
class A {
    name String
}

class B {
    age Int
}
""".strip()

    parser_descriptors = [
        (
            descriptor.section_type,
            descriptor.section_key,
            descriptor.qualname,
            descriptor.identity_hash,
            descriptor.byte_start,
            descriptor.byte_end,
        )
        for descriptor in collect_top_level_section_identity_descriptors(
            content=content,
            language=CodeLanguage.aware,
        )
    ]
    builder_descriptors = _top_level_builder_descriptors(content=content)

    assert parser_descriptors == builder_descriptors


def test_build_code_content_plan_fails_closed_when_plugin_missing() -> None:
    with _isolated_registry():
        with pytest.raises(KeyError, match="No language plugin registered"):
            build_code_content_plan(content="class A {}", language=CodeLanguage.aware)


def test_build_code_content_plan_basic_smoke() -> None:
    setup_code_plugins()

    plan = build_code_content_plan(
        content="class A {}",
        language=CodeLanguage.aware,
    )

    assert isinstance(plan, CodeContentPlan)
    assert plan.language.value == CodeLanguage.aware.value
    assert plan.content_text == "class A {}"
    assert plan.section_plans
    assert isinstance(plan.section_plans[0], CodeSectionPlan)
    assert plan.section_plans[0].qualname == "A"
    assert plan.section_plans[0].section_key == "A"


def test_build_code_content_plan_matches_parser_descriptor_oracle() -> None:
    setup_code_plugins()
    content = """
class A {
    name String
}

class B {
    age Int
}
""".strip()

    plan = build_code_content_plan(content=content, language=CodeLanguage.aware)
    parser_descriptors = collect_top_level_section_identity_descriptors(
        content=content,
        language=CodeLanguage.aware,
    )

    plan_tuples = [
        (
            descriptor.section_type.value,
            descriptor.section_key,
            descriptor.qualname,
            descriptor.identity_hash,
            descriptor.byte_start,
            descriptor.byte_end,
            descriptor.reference,
        )
        for descriptor in plan.section_plans
    ]
    parser_tuples = [
        (
            descriptor.section_type.value,
            descriptor.section_key,
            descriptor.qualname,
            descriptor.identity_hash,
            descriptor.byte_start,
            descriptor.byte_end,
            descriptor.reference,
        )
        for descriptor in parser_descriptors
    ]

    assert plan_tuples == parser_tuples


def test_build_code_content_plan_emits_aware_import_payload_plan() -> None:
    setup_code_plugins()
    content = """
import module.submodule;
import package.utils as helpers;
import core.* as CoreUtils;
""".strip()

    plan = build_code_content_plan(content=content, language=CodeLanguage.aware)
    import_sections = [
        section
        for section in plan.section_plans
        if section.section_type.value == CodeSectionType.import_.value
    ]
    assert len(import_sections) == 3

    first_import = import_sections[0]
    assert first_import.import_plan is not None
    assert first_import.import_plan.module_text == "module.submodule"
    assert first_import.import_plan.is_from_import is False
    assert first_import.import_plan.is_star_import is False
    assert first_import.import_plan.module_segment_plan.slot_key == "module"
    assert len(first_import.import_plan.name_plans) == 1
    assert first_import.import_plan.name_plans[0].name_text == "module.submodule"
    assert first_import.import_plan.name_plans[0].alias_text is None
    assert first_import.import_plan.name_plans[0].name_segment_plan.slot_key == "name"

    second_import = import_sections[1]
    assert second_import.import_plan is not None
    assert second_import.import_plan.module_text == "package.utils"
    assert len(second_import.import_plan.name_plans) == 1
    assert second_import.import_plan.name_plans[0].name_text == "package.utils"
    assert second_import.import_plan.name_plans[0].alias_text == "helpers"
    assert second_import.import_plan.name_plans[0].alias_segment_plan is not None
    assert (
        second_import.import_plan.name_plans[0].alias_segment_plan.slot_key == "alias"
    )

    third_import = import_sections[2]
    assert third_import.import_plan is not None
    assert third_import.import_plan.module_text == "core"
    assert third_import.import_plan.is_star_import is True
    assert len(third_import.import_plan.name_plans) == 1
    assert third_import.import_plan.name_plans[0].name_text == "*"
    assert third_import.import_plan.name_plans[0].alias_text == "CoreUtils"


def test_build_code_content_plan_suffixes_duplicate_section_keys() -> None:
    setup_code_plugins()
    content = """
import module.submodule;
import module.submodule;
""".strip()

    plan = build_code_content_plan(content=content, language=CodeLanguage.aware)
    import_sections = [
        section
        for section in plan.section_plans
        if section.section_type is CodeSectionType.import_
    ]

    assert [section.section_key for section in import_sections] == [
        "import.module.submodule",
        "import.module.submodule#2",
    ]
    assert [section.qualname for section in import_sections] == [
        "import.module.submodule",
        "import.module.submodule",
    ]
    assert import_sections[0].identity_hash == import_sections[1].identity_hash
    assert import_sections[0].byte_start != import_sections[1].byte_start


def test_make_section_key_fails_closed_without_semantic_anchor() -> None:
    with pytest.raises(ValueError, match="canonical descriptive key"):
        make_section_key(
            section_type=CodeSectionType.comment,
            qualname="",
            reference=None,
        )

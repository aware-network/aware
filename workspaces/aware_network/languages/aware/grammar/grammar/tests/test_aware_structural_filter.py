from __future__ import annotations

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN


def test_aware_structural_filter_keeps_structural_test_domain_nouns() -> None:
    content = "class CodeTest {\n    name String\n}\n"

    assert (
        AWARE_CODE_PLUGIN.is_structural(
            "workspaces/aware_kernel/modules/code/ontology/structure/aware/code/code_test.aware",
            content,
        )
        is True
    )


def test_aware_structural_filter_keeps_tests_directory_non_structural() -> None:
    content = "class FixtureOnly {\n    name String\n}\n"

    assert (
        AWARE_CODE_PLUGIN.is_structural(
            "modules/demo/structure/ontology/tests/test_fixture.aware",
            content,
        )
        is False
    )

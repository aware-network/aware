from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Iterator
from uuid import uuid4

import pytest
from tree_sitter import Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_code.builder import build_code_from_content, collect_nodes
from aware_code.handlers.impl.code import code as code_handler
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.ontology.materialization import (
    apply_code_content_plan,
    build_code_content_plan_from_text,
    create_code_in_package_from_text,
    upsert_code_in_package_from_text,
)
from aware_code.node.adapter import CodeNodeAdapter
from aware_code.node.node import CodeNode
from aware_code.semantic_package.registry import SemanticPackageRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType


@contextmanager
def _isolated_registry() -> Iterator[None]:
    CodeLanguagePluginRegistry.clear()
    SemanticPackageRegistry.clear()
    try:
        yield
    finally:
        SemanticPackageRegistry.clear()
        CodeLanguagePluginRegistry.clear()
        setup_code_plugins()


def _sample_tree_sitter_node():
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(b"class A {}")
    root = tree.root_node
    first = root.children[0] if root.children else root
    return first


def test_setup_code_plugins_registers_languages_idempotently() -> None:
    with _isolated_registry():
        setup_code_plugins()
        expected = {
            CodeLanguage.aware,
            CodeLanguage.dart,
            CodeLanguage.python,
            CodeLanguage.sql,
        }

        first = set(CodeLanguagePluginRegistry.get_supported_languages())
        assert expected <= first

        setup_code_plugins()
        second = set(CodeLanguagePluginRegistry.get_supported_languages())
        assert second == first


def test_registry_get_fail_closed_for_missing_language() -> None:
    with _isolated_registry():
        with pytest.raises(KeyError, match="No language plugin registered"):
            CodeLanguagePluginRegistry.get(CodeLanguage.aware)


def test_builder_index_reference_collision_rules() -> None:
    index = CodeSectionBuilderIndex()

    first = SimpleNamespace(id=uuid4())
    second = SimpleNamespace(id=uuid4())

    index.add_reference(CodeSectionType.class_, "User", first)
    with pytest.raises(ValueError, match="Reference collision"):
        index.add_reference(CodeSectionType.class_, "User", second)


def test_builder_index_add_section_node_is_idempotent_for_same_range() -> None:
    index = CodeSectionBuilderIndex()
    section_id = uuid4()
    raw_node = _sample_tree_sitter_node()
    node_first = CodeNode(node=raw_node, byte_start=4, byte_end=10)
    node_same = CodeNode(node=raw_node, byte_start=4, byte_end=10)
    node_different = CodeNode(node=raw_node, byte_start=5, byte_end=11)

    index.add_section_node(section_id, node_first)
    index.add_section_node(section_id, node_same)
    assert index.get_section_node(section_id) is node_first

    with pytest.raises(ValueError, match="different byte range"):
        index.add_section_node(section_id, node_different)


class _FakeAdapter(CodeNodeAdapter[int]):
    @property
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.class_

    def match_nodes(self, root: int, source: bytes):  # noqa: ARG002
        _ = root
        _ = source
        return [
            CodeNode(node=1, byte_start=12, byte_end=13),
            CodeNode(node=2, byte_start=2, byte_end=3),
            CodeNode(node=3, byte_start=8, byte_end=9),
        ]

    def qualname(
        self, node: CodeNode[int], parent: str | None = None
    ) -> str:  # noqa: ARG002
        _ = parent
        return f"n{node.node}"

    def body_bytes(self, node: CodeNode[int], source: bytes) -> bytes:  # noqa: ARG002
        _ = node
        _ = source
        return b""


def test_collect_nodes_returns_deterministic_byte_order() -> None:
    adapter = _FakeAdapter()
    fake_tree = SimpleNamespace(
        root=SimpleNamespace(node=0),
        source_bytes=b"irrelevant",
    )

    nodes = collect_nodes(adapter=adapter, code_tree=fake_tree)
    assert [node.byte_start for node in nodes] == [2, 8, 12]


def test_build_code_from_content_fails_closed_when_plugin_missing() -> None:
    with _isolated_registry():
        with pytest.raises(KeyError, match="No language plugin registered"):
            build_code_from_content(
                sections_index=CodeSectionBuilderIndex(),
                content="class A {}",
                code_key="inline://missing-plugin",
                language=CodeLanguage.aware,
                symbol_table=CodeSymbolTable(),
            )


def test_build_code_from_content_basic_path_smoke() -> None:
    setup_code_plugins()
    built = build_code_from_content(
        sections_index=CodeSectionBuilderIndex(),
        content="class A {}",
        code_key="inline://basic-smoke",
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    assert built.language == CodeLanguage.aware
    assert built.content_part_text is not None


def test_build_code_from_content_allows_documented_relationship_field_without_attribute_section() -> (
    None
):
    setup_code_plugins()
    content = """
class ObjectConfigGraph {
    // Relationships
    /// Stable identity for this config graph family.
    object_config_graph_identity ObjectConfigGraphIdentity?
    object_config_graph_nodes ObjectConfigGraphNode[]

    // Attributes
    name String unique
}
"""

    built = build_code_from_content(
        sections_index=CodeSectionBuilderIndex(),
        content=content,
        code_key="inline://documented-relationship-field",
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )

    assert built.language == CodeLanguage.aware
    assert any(
        section.type is CodeSectionType.comment for section in built.code_sections
    )


def test_build_code_content_plan_from_text_sets_up_plugins() -> None:
    with _isolated_registry():
        plan = build_code_content_plan_from_text(
            content_text="class A {}",
            language=CodeLanguage.aware,
        )

    assert plan.language.value == CodeLanguage.aware.value
    assert plan.section_plans
    assert plan.section_plans[0].section_key == "A"


@pytest.mark.asyncio
async def test_apply_code_content_plan_invokes_canonical_code_surface() -> None:
    plan = build_code_content_plan_from_text(
        content_text="class A {}",
        language=CodeLanguage.aware,
    )
    captured: dict[str, object] = {}

    class _FakeCode:
        async def apply_content_plan(self, *, plan):  # noqa: ANN001
            captured["plan"] = plan

    await apply_code_content_plan(
        code=_FakeCode(),  # type: ignore[arg-type]
        plan=plan,
    )

    assert captured == {
        "plan": plan,
    }


@pytest.mark.asyncio
async def test_replace_content_handler_delegates_to_ontology_materialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_code = object()
    captured: dict[str, object] = {}

    async def _fake_replace_code_content_from_text(
        *, code, content_text: str, language
    ):  # noqa: ANN001
        captured["code"] = code
        captured["content_text"] = content_text
        captured["language"] = language

    monkeypatch.setattr(
        code_handler,
        "replace_code_content_from_text",
        _fake_replace_code_content_from_text,
    )

    await code_handler.replace_content(
        fake_code,  # type: ignore[arg-type]
        content_text="class A {}",
        language=CodeLanguage.aware,
    )

    assert captured == {
        "code": fake_code,
        "content_text": "class A {}",
        "language": CodeLanguage.aware,
    }


@pytest.mark.asyncio
async def test_create_code_in_package_from_text_invokes_canonical_package_surface() -> (
    None
):
    captured: dict[str, object] = {}

    class _FakeCodePackage:
        language = CodeLanguage.aware

        async def create_code(self, *, relative_path: str, plan):  # noqa: ANN001
            captured["relative_path"] = relative_path
            captured["plan"] = plan
            return "created"

    result = await create_code_in_package_from_text(
        code_package=_FakeCodePackage(),  # type: ignore[arg-type]
        relative_path="src/main.aware",
        content_text="class A {}",
        language=None,
    )

    assert result == "created"
    assert captured["relative_path"] == "src/main.aware"
    assert captured["plan"].language == CodeLanguage.aware
    assert captured["plan"].content_text == "class A {}"


@pytest.mark.asyncio
async def test_upsert_code_in_package_from_text_invokes_canonical_package_surface() -> (
    None
):
    captured: dict[str, object] = {}

    class _FakeCodePackage:
        language = CodeLanguage.aware

        async def upsert_code(self, *, relative_path: str, plan):  # noqa: ANN001
            captured["relative_path"] = relative_path
            captured["plan"] = plan
            return "upserted"

    result = await upsert_code_in_package_from_text(
        code_package=_FakeCodePackage(),  # type: ignore[arg-type]
        relative_path="src/main.aware",
        content_text="class B {}",
        language=None,
    )

    assert result == "upserted"
    assert captured["relative_path"] == "src/main.aware"
    assert captured["plan"].language == CodeLanguage.aware
    assert captured["plan"].content_text == "class B {}"

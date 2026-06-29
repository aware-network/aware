from __future__ import annotations

from pathlib import Path
from uuid import UUID

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_grammar.meta_language_plugin import AWARE_META_PLUGIN
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry


def _build_graph(*, file_path: str) -> tuple[ObjectConfigGraph, dict[UUID, NamespacePath]]:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(AWARE_META_PLUGIN)

    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_file(
        sections_index=sections_index,
        file_path=file_path,
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )

    namespace_by_code_id: dict[UUID, NamespacePath] = {
        code.id: NamespacePath(package="test_pkg", namespace="alpha.beta")
    }

    result = build_object_config_graph_from_code(
        name="json_defaults",
        description="test json defaults are structured",
        fqn_prefix="test_pkg",
        file_codes=[(file_path, code)],
        namespace_by_code_id=namespace_by_code_id,
    )
    return result.graph, namespace_by_code_id


def _class_by_name(graph: ObjectConfigGraph, name: str):
    for node in graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_:
            continue
        cls = node.class_config
        if cls is not None and cls.name == name:
            return cls
    raise AssertionError(f"Class not found: {name}")


def test_json_defaults_parse_as_structured_values(tmp_path: Path) -> None:
    path = tmp_path / "domains" / "alpha" / "beta" / "doc.aware"
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(
        ("class Foo {\n" "    args JsonArray = []\n" "    kwargs JsonObject = {}\n" "}\n"),
        encoding="utf-8",
    )

    graph, _namespace_by_code_id = _build_graph(file_path=str(path))
    foo = _class_by_name(graph, "Foo")

    attrs = {attr.name: attr for link in foo.class_config_attribute_configs for attr in [link.attribute_config]}
    assert attrs["args"].default_value == "[]"
    assert attrs["kwargs"].default_value == "{}"


def test_code_sections_capture_json_default_text(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    path = tmp_path / "domains" / "alpha" / "beta" / "doc.aware"
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(
        ("class Foo {\n" "    args JsonArray = []\n" "    kwargs JsonObject = {}\n" "}\n"),
        encoding="utf-8",
    )

    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_file(
        sections_index=sections_index,
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )

    default_by_name: dict[str, str | None] = {}
    for sec in code.code_sections:
        if sec.type != CodeSectionType.attribute:
            continue
        attr = sec.code_section_attribute
        if attr is None:
            continue
        default_by_name[attr.name] = attr.default_value_text

    assert default_by_name["args"] == "[]"
    assert default_by_name["kwargs"] == "{}"

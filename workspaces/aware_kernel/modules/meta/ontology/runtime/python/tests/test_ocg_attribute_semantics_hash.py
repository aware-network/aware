from __future__ import annotations

from pathlib import Path
from uuid import UUID

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code


def _build_code(tmp_path: Path, name: str, content: str):
    path = tmp_path / name
    path.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


CODE_BASE = """
class Example {
    foo String
}
""".strip()


CODE_UNIQUE = """
class Example {
    foo String unique
}
""".strip()


def test_ocg_hash_changes_when_attribute_uniqueness_changes(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_a = _build_code(tmp_path, "a.aware", CODE_BASE)
    ns_a, domains_a = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_a.id]
    )
    res_a = build_object_config_graph_from_code(
        name="attr",
        description="attr",
        fqn_prefix="pkg",
        file_codes=[("a.aware", code_a)],
        namespace_by_code_id=ns_a,
    )

    code_b = _build_code(tmp_path, "b.aware", CODE_UNIQUE)
    ns_b, domains_b = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_b.id]
    )
    res_b = build_object_config_graph_from_code(
        name="attr",
        description="attr",
        fqn_prefix="pkg",
        file_codes=[("b.aware", code_b)],
        namespace_by_code_id=ns_b,
    )

    assert res_a.graph.hash != res_b.graph.hash

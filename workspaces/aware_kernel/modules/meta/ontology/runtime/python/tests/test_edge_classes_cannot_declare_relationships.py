# @code-under-test: ../aware_meta/class_/config/relationship/builder.py

from pathlib import Path
from uuid import UUID

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.fqn_resolver import NamespacePath


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(p),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


EDGE_WITH_REL = """
class A {
    bs B[] @AB
}

class B {}

edge AB {
    b B
}
""".strip()


def test_edge_classes_must_not_declare_relationships(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(tmp_path, "bad_edge.aware", EDGE_WITH_REL)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    with pytest.raises(
        ValueError,
        match=r"association \(edge container\) classes must not declare relationships",
    ):
        build_object_config_graph_from_code(
            name="bad",
            description="bad",
            fqn_prefix="pkg",
            file_codes=[("bad_edge.aware", code)],
            namespace_by_code_id=ns,
        )

# @code-under-test: ../aware_meta/graph/config/builder.py

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.manifest.spec import AwarePackageKind
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
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


def test_relationship_rejects_inline_value_endpoint_in_ontology_package(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "bad_inline_rel.aware",
        """
class Target {
    // Attributes
    name String
}

class Payload : inline_value {
    // Relationships
    target Target
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg",
        namespace="types",
        code_ids=[code.id],
    )

    with pytest.raises(ValueError, match=r"inline_value"):
        build_object_config_graph_from_code(
            name="pkg",
            description="pkg",
            fqn_prefix="pkg",
            file_codes=[("pkg", code)],
            namespace_by_code_id=ns,
            package_kind=AwarePackageKind.ontology,
        )


def test_api_allows_inline_value_composition_and_emits_no_relationships(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "api_inline_composition.aware",
        """
class A {
    b B
}

class B {
    id String
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg_api",
        namespace="api",
        code_ids=[code.id],
    )

    result = build_object_config_graph_from_code(
        name="pkg_api",
        description="pkg_api",
        fqn_prefix="pkg_api",
        file_codes=[("pkg_api", code)],
        namespace_by_code_id=ns,
        package_kind=AwarePackageKind.api,
    )
    assert all(
        node.class_config is None
        or node.class_config.value_mode == ClassValueMode.inline_value
        for node in result.graph.object_config_graph_nodes
    )
    assert not any(
        node.type == ObjectConfigGraphNodeType.relationship
        for node in result.graph.object_config_graph_nodes
    )

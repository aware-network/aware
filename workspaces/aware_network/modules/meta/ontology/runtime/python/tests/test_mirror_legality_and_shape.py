# @code-under-test: ../aware_meta/graph/config/builder.py
# @code-under-test: ../aware_meta/graph/config/mirror/builder.py
# @code-under-test: ../aware_meta/graph/config/mirror/apply.py

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar (canonical plugins)
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Meta Ontology

# Meta Runtime
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.manifest.spec import AwarePackageKind


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content.strip() + "\n", encoding="utf-8")
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


EXT_ONTOLOGY_INLINE = """
class Payload : inline_value {
    x String
}
""".strip()


EXT_ONTOLOGY_GRAPH_REF = """
class GraphRef {
    x String
}
""".strip()


EXT_ONTOLOGY_AMBIGUOUS = """
enum Foo {
    a
}

class Foo : inline_value {
    x String
}
""".strip()


def test_mirror_forbidden_outside_api_packages(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    ext_code = _build_code(tmp_path, "ext.aware", EXT_ONTOLOGY_INLINE)
    ext_ns, ext_domains = _ns(
        fqn_prefix="ext", namespace="demo", code_ids=[ext_code.id]
    )
    ext_graph = build_object_config_graph_from_code(
        name="ext",
        description="ext",
        fqn_prefix="ext",
        file_codes=[("ext.aware", ext_code)],
        namespace_by_code_id=ext_ns,
        package_kind=AwarePackageKind.ontology,
    ).graph

    local_code = _build_code(tmp_path, "local.aware", "mirror ext.demo.Payload")
    local_ns, local_domains = _ns(
        fqn_prefix="local",
        namespace="demo",
        code_ids=[local_code.id],
    )

    with pytest.raises(
        ValueError, match=r"Mirrors are only supported for API packages"
    ):
        build_object_config_graph_from_code(
            name="local",
            description="local",
            fqn_prefix="local",
            file_codes=[("local.aware", local_code)],
            namespace_by_code_id=local_ns,
            package_kind=AwarePackageKind.ontology,
            external_graphs=[ext_graph],
        )


def test_mirror_requires_external_graphs(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    local_code = _build_code(tmp_path, "local.aware", "mirror ext.demo.Payload")
    local_ns, local_domains = _ns(
        fqn_prefix="local_api",
        namespace="demo",
        code_ids=[local_code.id],
    )

    with pytest.raises(
        ValueError, match=r"Mirror statements require external graphs for resolution"
    ):
        build_object_config_graph_from_code(
            name="local_api",
            description="local_api",
            fqn_prefix="local_api",
            file_codes=[("local.aware", local_code)],
            namespace_by_code_id=local_ns,
            package_kind=AwarePackageKind.api,
            external_graphs=None,
        )


def test_mirror_target_not_found(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    ext_code = _build_code(tmp_path, "ext.aware", EXT_ONTOLOGY_INLINE)
    ext_ns, ext_domains = _ns(
        fqn_prefix="ext", namespace="demo", code_ids=[ext_code.id]
    )
    ext_graph = build_object_config_graph_from_code(
        name="ext",
        description="ext",
        fqn_prefix="ext",
        file_codes=[("ext.aware", ext_code)],
        namespace_by_code_id=ext_ns,
        package_kind=AwarePackageKind.ontology,
    ).graph

    local_code = _build_code(tmp_path, "local.aware", "mirror ext.demo.MissingType")
    local_ns, local_domains = _ns(
        fqn_prefix="local_api",
        namespace="demo",
        code_ids=[local_code.id],
    )

    with pytest.raises(ValueError, match=r"Mirror target not found"):
        build_object_config_graph_from_code(
            name="local_api",
            description="local_api",
            fqn_prefix="local_api",
            file_codes=[("local.aware", local_code)],
            namespace_by_code_id=local_ns,
            package_kind=AwarePackageKind.api,
            external_graphs=[ext_graph],
        )


def test_mirror_target_ambiguity_class_and_enum(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    ext_code = _build_code(tmp_path, "ext.aware", EXT_ONTOLOGY_AMBIGUOUS)
    ext_ns, ext_domains = _ns(
        fqn_prefix="ext", namespace="demo", code_ids=[ext_code.id]
    )
    ext_graph = build_object_config_graph_from_code(
        name="ext",
        description="ext",
        fqn_prefix="ext",
        file_codes=[("ext.aware", ext_code)],
        namespace_by_code_id=ext_ns,
        package_kind=AwarePackageKind.ontology,
    ).graph

    local_code = _build_code(tmp_path, "local.aware", "mirror ext.demo.Foo")
    local_ns, local_domains = _ns(
        fqn_prefix="local_api",
        namespace="demo",
        code_ids=[local_code.id],
    )

    with pytest.raises(ValueError, match=r"Mirror target is ambiguous"):
        build_object_config_graph_from_code(
            name="local_api",
            description="local_api",
            fqn_prefix="local_api",
            file_codes=[("local.aware", local_code)],
            namespace_by_code_id=local_ns,
            package_kind=AwarePackageKind.api,
            external_graphs=[ext_graph],
        )


def test_mirror_forbids_graph_ref_class_targets(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    ext_code = _build_code(tmp_path, "ext.aware", EXT_ONTOLOGY_GRAPH_REF)
    ext_ns, ext_domains = _ns(
        fqn_prefix="ext", namespace="demo", code_ids=[ext_code.id]
    )
    ext_graph = build_object_config_graph_from_code(
        name="ext",
        description="ext",
        fqn_prefix="ext",
        file_codes=[("ext.aware", ext_code)],
        namespace_by_code_id=ext_ns,
        package_kind=AwarePackageKind.ontology,
    ).graph

    local_code = _build_code(tmp_path, "local.aware", "mirror ext.demo.GraphRef")
    local_ns, local_domains = _ns(
        fqn_prefix="local_api",
        namespace="demo",
        code_ids=[local_code.id],
    )

    with pytest.raises(
        ValueError, match=r"Mirror copy forbids referencing GRAPH_REF classes"
    ):
        build_object_config_graph_from_code(
            name="local_api",
            description="local_api",
            fqn_prefix="local_api",
            file_codes=[("local.aware", local_code)],
            namespace_by_code_id=local_ns,
            package_kind=AwarePackageKind.api,
            external_graphs=[ext_graph],
        )

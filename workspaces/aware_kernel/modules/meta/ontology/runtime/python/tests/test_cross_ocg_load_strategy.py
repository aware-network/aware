# @code-under-test: ../aware_meta/graph/config/builder.py

from pathlib import Path

# Kernel graph ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipSideLoadingStrategy,
)

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar (canonical plugins)
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Aware Kernel Meta
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.fqn_resolver import NamespacePath


DEFAULT_CODE = """
class Child {
    base dep_pkg.dep_domain.dep_schema.Base
}

ann default.Child::base load forward lazy
""".strip()


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


def test_cross_ocg_relationship_load_strategy_is_applied_to_cross_map(
    tmp_path: Path,
) -> None:
    """
    When a relationship targets an external graph, the relationship is returned in
    cross_relationships_by_target_ocg. LOAD annotations must still apply deterministically.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(tmp_path, "dep.aware", "class Base { id String }\n")
    dep_ns = {
        dep_code.id: NamespacePath(package="dep_pkg", namespace="dep_domain.dep_schema")
    }
    dep_res = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="dep_pkg",
        file_codes=[("dep.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    local_code = _build_code(
        tmp_path,
        "local.aware",
        DEFAULT_CODE,
    )
    local_ns = {
        local_code.id: NamespacePath(package="main_pkg", namespace="main_domain.default")
    }

    local_res = build_object_config_graph_from_code(
        name="local",
        description="local",
        fqn_prefix="main_pkg",
        file_codes=[("local.aware", local_code)],
        namespace_by_code_id=local_ns,
        external_graphs=[dep_res.graph],
    )

    cross = local_res.cross_relationships_by_target_ocg.get(dep_res.graph.id)
    assert cross, "Expected a cross-OCG relationship"
    rel = cross[0]
    assert (
        rel.forward_loading_strategy == ClassConfigRelationshipSideLoadingStrategy.lazy
    )

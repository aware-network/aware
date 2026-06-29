from __future__ import annotations

from pathlib import Path
from uuid import UUID

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_grammar.transformers.aware_to_runtime_transformer import (
    AwareToRuntimeTransformer,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.relationship_analysis import analyze_relationships
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)


SOURCE = """
class LayoutConfig {
    section_configs LayoutConfigSectionConfig[]

    key String key
    title String
    description String?

    fn build construct (key String key, title String, description String? = null) -> LayoutConfig {
    }

    fn add_section_config (
        section_key String,
        title String,
        description String? = null,
        order Int = 0,
        flex Float = 1.0,
        is_visible Bool = true
    ) -> LayoutConfigSectionConfig {
        let created_layout_config_section_config = construct section_configs.create(
            section_key = section_key,
            title = title,
            description = description,
            order = order,
            flex = flex,
            is_visible = is_visible,
        )
    }
}

class LayoutConfigSectionConfig {
    section_config SectionConfig unique

    section_key String key
    order Int = 0
    flex Float = 1.0
    is_visible Bool = true

    fn create construct (
        section_key String key,
        title String,
        description String? = null,
        order Int = 0,
        flex Float = 1.0,
        is_visible Bool = true
    ) -> LayoutConfigSectionConfig {
        let created_section_config = construct section_config.build(
            key = section_key,
            title = title,
            description = description,
        )
    }
}

class SectionConfig {
    key String key
    title String
    description String?

    fn build construct (key String key, title String, description String? = null) -> SectionConfig {
    }
}
""".strip()


def _build_graph(tmp_path: Path) -> tuple[ObjectConfigGraph, dict[UUID, NamespacePath]]:
    file_path = tmp_path / "nested_construct_analysis.aware"
    file_path.write_text(SOURCE, encoding="utf-8")
    code = build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(file_path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    namespace_by_code_id = {
        code.id: NamespacePath(package="pkg", namespace="dom.sch"),
    }
    result = build_object_config_graph_from_code(
        name="nested_construct_analysis",
        description="nested_construct_analysis",
        fqn_prefix="pkg",
        file_codes=[(str(file_path), code)],
        namespace_by_code_id=namespace_by_code_id,
    )
    return result.graph, namespace_by_code_id


def test_relationship_analysis_accepts_runtime_graph_with_nested_path_constructors(
    tmp_path: Path,
) -> None:
    graph, namespace_by_code_id = _build_graph(tmp_path)

    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id,
        relationship_loading_config=None,
    ).transform(graph)

    analyses = analyze_relationships(runtime, namespace_by_code_id=namespace_by_code_id)
    by_signature = {
        (analysis.source_class.name, analysis.forward_reference_attr.name): analysis
        for analysis in analyses
    }

    assert ("LayoutConfig", "section_configs") in by_signature
    assert ("LayoutConfigSectionConfig", "section_config") in by_signature
    assert (
        by_signature[
            ("LayoutConfigSectionConfig", "section_config")
        ].construct_target_class
        is not None
    )
    assert (
        by_signature[
            ("LayoutConfigSectionConfig", "section_config")
        ].construct_target_class.name
        == "SectionConfig"
    )

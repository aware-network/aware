from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

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
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)


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
    file_path = tmp_path / "nested_path_constructor.aware"
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
        name="nested_path_constructor",
        description="nested_path_constructor",
        fqn_prefix="pkg",
        file_codes=[(str(file_path), code)],
        namespace_by_code_id=namespace_by_code_id,
    )
    return result.graph, namespace_by_code_id


def _class_by_name(graph: ObjectConfigGraph, name: str) -> ClassConfig:
    for node in graph.object_config_graph_nodes:
        if (
            node.type == ObjectConfigGraphNodeType.class_
            and node.class_config is not None
            and node.class_config.name == name
        ):
            return node.class_config
    raise AssertionError(f"class not found: {name}")


def _function_by_name(cls: ClassConfig, name: str):
    for link in cls.class_config_function_configs:
        if link.function_config.name == name:
            return link.function_config
    raise AssertionError(f"function not found: {cls.name}.{name}")


def test_nested_path_constructors_are_retargeted_transitively(tmp_path: Path) -> None:
    graph, namespace_by_code_id = _build_graph(tmp_path)

    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id,
        relationship_loading_config=None,
    ).transform(graph)

    layout_config = _class_by_name(runtime, "LayoutConfig")
    layout_config_section_config = _class_by_name(runtime, "LayoutConfigSectionConfig")
    section_config = _class_by_name(runtime, "SectionConfig")

    add_section_config = _function_by_name(layout_config, "add_section_config")
    create_via_layout_config = _function_by_name(
        layout_config_section_config, "create_via_layout_config"
    )
    build_via_layout_config_section_config = _function_by_name(
        section_config,
        "build_via_layout_config_section_config",
    )

    section_function_names = {
        link.function_config.name
        for link in section_config.class_config_function_configs
    }
    assert section_function_names == {"build_via_layout_config_section_config"}

    add_section_invocation = next(
        inv for inv in add_section_config.invocations if inv.kind.value == "construct"
    )
    assert (
        add_section_invocation.target_function_config_id == create_via_layout_config.id
    )

    nested_construct_invocation = next(
        inv
        for inv in create_via_layout_config.invocations
        if inv.kind.value == "construct"
    )
    assert (
        nested_construct_invocation.target_function_config_id
        == build_via_layout_config_section_config.id
    )


def test_nested_path_constructors_avoid_graph_wide_deepcopy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph, namespace_by_code_id = _build_graph(tmp_path)

    original_attribute_model_copy = AttributeConfig.model_copy
    original_graph_model_copy = ObjectConfigGraph.model_copy
    original_relationship_model_copy = ObjectConfigGraphRelationship.model_copy

    def _guard_attribute_model_copy(self, *, update=None, deep: bool = False):
        if deep:
            raise AssertionError(
                "AttributeConfig.model_copy(deep=True) must not run during runtime transform"
            )
        return original_attribute_model_copy(self, update=update, deep=deep)

    def _guard_graph_model_copy(self, *, update=None, deep: bool = False):
        if deep:
            raise AssertionError(
                "ObjectConfigGraph.model_copy(deep=True) must not run during runtime transform"
            )
        return original_graph_model_copy(self, update=update, deep=deep)

    def _guard_relationship_model_copy(self, *, update=None, deep: bool = False):
        if deep:
            raise AssertionError(
                "ObjectConfigGraphRelationship.model_copy(deep=True) must not run during runtime transform"
            )
        return original_relationship_model_copy(self, update=update, deep=deep)

    monkeypatch.setattr(AttributeConfig, "model_copy", _guard_attribute_model_copy)
    monkeypatch.setattr(ObjectConfigGraph, "model_copy", _guard_graph_model_copy)
    monkeypatch.setattr(
        ObjectConfigGraphRelationship,
        "model_copy",
        _guard_relationship_model_copy,
    )

    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id,
        relationship_loading_config=None,
    ).transform(graph)

    section_config = _class_by_name(runtime, "SectionConfig")
    section_function_names = {
        link.function_config.name
        for link in section_config.class_config_function_configs
    }
    assert section_function_names == {"build_via_layout_config_section_config"}

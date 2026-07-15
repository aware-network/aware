"""Runtime-transform context assembly for the Aware runtime transformer."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_meta.graph.config.relationship_analysis import (
    FkOverrideKey,
    FkOverrideSpec,
    ObjectConfigGraphRelationshipAnalysis,
    analyze_relationships,
    index_fk_override_annotations,
    index_relationship_name_override_annotations,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_meta_ontology.graph.config.object_config_graph_relationship import ObjectConfigGraphRelationship

from aware_grammar.transformers.runtime.function_surface_support import RuntimeFunctionSurfaceSupport
from aware_grammar.transformers.runtime.support import RuntimeTransformSupport


@dataclass(slots=True)
class RuntimeTransformContext:
    """Mutable stage context shared across runtime-transform steps."""

    support: RuntimeTransformSupport
    function_surface_support: RuntimeFunctionSurfaceSupport
    source_graph: ObjectConfigGraph
    class_configs: list[ClassConfig]
    enum_configs: list[EnumConfig]
    function_configs: list[FunctionConfig]
    relationships: list[ClassConfigRelationship]
    analyses: list[ObjectConfigGraphRelationshipAnalysis]
    fk_overrides_by_key: dict[FkOverrideKey, FkOverrideSpec]
    rel_name_overrides_by_key: dict[FkOverrideKey, str]
    local_class_ids: set[UUID]
    object_config_graph_relationships: list[ObjectConfigGraphRelationship]


def build_runtime_transform_context(
    *,
    support: RuntimeTransformSupport,
    function_surface_support: RuntimeFunctionSurfaceSupport,
    source_graph: ObjectConfigGraph,
) -> RuntimeTransformContext:
    """Collect mutable runtime-transform inputs from the canonical source graph."""

    fk_overrides_by_key = index_fk_override_annotations(source_graph)
    rel_name_overrides_by_key = index_relationship_name_override_annotations(source_graph)

    class_configs: list[ClassConfig] = []
    enum_configs: list[EnumConfig] = []
    function_configs: list[FunctionConfig] = []
    relationships: list[ClassConfigRelationship] = []
    relationships_by_id: dict[UUID, ClassConfigRelationship] = {}

    def _append_relationship(relationship: ClassConfigRelationship) -> None:
        if relationship.id in relationships_by_id:
            return
        relationships_by_id[relationship.id] = relationship
        relationships.append(relationship)

    for node in source_graph.object_config_graph_nodes:
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            class_configs.append(node.class_config)
            for relationship in node.class_config.class_config_relationships:
                _append_relationship(relationship)
        elif node.type == ObjectConfigGraphNodeType.relationship and node.class_config_relationship is not None:
            _append_relationship(node.class_config_relationship)
        elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
            enum_configs.append(node.enum_config)
        elif node.type == ObjectConfigGraphNodeType.function:
            raise ValueError(
                "Canonical Aware runtime transform does not accept standalone/global FunctionConfig nodes; "
                + f"node_id={node.id} "
                + "Functions must remain class-owned via ClassConfig.class_config_function_configs."
            )

    local_class_ids = {cls.id for cls in class_configs}
    analyses = analyze_relationships(
        source_graph,
        namespace_by_code_id=support.namespace_by_code_id,
        external_graphs_by_id=support.external_graphs_by_id,
    )

    return RuntimeTransformContext(
        support=support,
        function_surface_support=function_surface_support,
        source_graph=source_graph,
        class_configs=class_configs,
        enum_configs=enum_configs,
        function_configs=function_configs,
        relationships=relationships,
        analyses=analyses,
        fk_overrides_by_key=fk_overrides_by_key,
        rel_name_overrides_by_key=rel_name_overrides_by_key,
        local_class_ids=local_class_ids,
        object_config_graph_relationships=source_graph.object_config_graph_relationships,
    )


__all__ = ["RuntimeTransformContext", "build_runtime_transform_context"]

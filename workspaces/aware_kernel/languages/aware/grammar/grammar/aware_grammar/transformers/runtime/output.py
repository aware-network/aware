"""Runtime output stage for the Aware runtime transformer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship_class import (
    ObjectConfigGraphRelationshipClass,
)

from aware_meta.graph.config.builder import build_object_config_graph

from aware_grammar.transformers.runtime.context import RuntimeTransformContext

if TYPE_CHECKING:
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


def build_runtime_output_graph(
    *,
    ctx: RuntimeTransformContext,
) -> ObjectConfigGraph:
    """Build the derived runtime OCG from the extracted stage context."""

    namespace_bundle = ctx.support.resolve_namespace_bundle_for_derived_graph(
        source_graph=ctx.source_graph,
        derived_class_configs=ctx.class_configs,
        derived_relationships=ctx.relationships,
        derived_enum_configs=ctx.enum_configs,
        derived_function_configs=[],
        namespace_by_code_id=ctx.support.namespace_by_code_id or {},
    )
    derived = build_object_config_graph(
        language=CodeLanguage.aware,
        name=ctx.source_graph.name,
        description=ctx.source_graph.description,
        fqn_prefix=ctx.source_graph.fqn_prefix,
        class_configs=ctx.class_configs,
        class_config_relationships=ctx.relationships,
        enum_configs=ctx.enum_configs,
        function_configs=[],
        namespace_bundle=namespace_bundle,
        object_config_graph_annotations=list(
            ctx.source_graph.object_config_graph_annotations
        ),
        object_projection_graph_declarations=list(
            ctx.source_graph.object_projection_graph_declarations
        ),
        object_config_graph_mirrors=list(ctx.source_graph.object_config_graph_mirrors),
        source_graph=ctx.source_graph,
    )
    derived_schema_relationships = list(derived.object_config_graph_relationships or [])

    derived.object_config_graph_relationships = (
        _merge_object_config_graph_relationships(
            source_relationships=list(ctx.object_config_graph_relationships or []),
            derived_relationships=derived_schema_relationships,
        )
    )
    derived.object_projection_graphs = ctx.source_graph.object_projection_graphs
    derived.object_projection_graph_declarations = (
        ctx.source_graph.object_projection_graph_declarations
    )
    derived.object_config_graph_identity = ctx.source_graph.object_config_graph_identity
    return derived


def _merge_object_config_graph_relationships(
    *,
    source_relationships: list[ObjectConfigGraphRelationship],
    derived_relationships: list[ObjectConfigGraphRelationship],
) -> list[ObjectConfigGraphRelationship]:
    """Preserve source cross-graph relationships plus runtime-derived relationship edges."""

    merged_by_key: dict[
        tuple[object, object, object],
        ObjectConfigGraphRelationship,
    ] = {}
    ordered_keys: list[tuple[object, object, object]] = []

    def key_for(rel: ObjectConfigGraphRelationship) -> tuple[object, object, object]:
        return (rel.id, rel.object_config_graph_id, rel.target_object_config_graph_id)

    def append_relationship(rel: ObjectConfigGraphRelationship) -> None:
        key = key_for(rel)
        existing = merged_by_key.get(key)
        if existing is None:
            merged_by_key[key] = _clone_relationship_for_runtime_merge(rel)
            ordered_keys.append(key)
            return

        class_relationships_by_id = {
            class_rel.id: class_rel
            for class_rel in (existing.class_config_relationships or [])
            if class_rel.id is not None
        }
        for class_rel in rel.class_config_relationships or []:
            if class_rel.id is None or class_rel.id not in class_relationships_by_id:
                existing.class_config_relationships.append(
                    _clone_class_relationship_for_runtime_merge(class_rel)
                )
                if class_rel.id is not None:
                    class_relationships_by_id[class_rel.id] = (
                        existing.class_config_relationships[-1]
                    )

        relationship_classes_by_id = {
            relationship_class.id: relationship_class
            for relationship_class in (
                existing.object_config_graph_relationship_classes or []
            )
            if relationship_class.id is not None
        }
        for relationship_class in rel.object_config_graph_relationship_classes or []:
            if (
                relationship_class.id is None
                or relationship_class.id not in relationship_classes_by_id
            ):
                existing.object_config_graph_relationship_classes.append(
                    _clone_relationship_class_for_runtime_merge(relationship_class)
                )
                if relationship_class.id is not None:
                    relationship_classes_by_id[relationship_class.id] = (
                        existing.object_config_graph_relationship_classes[-1]
                    )

    for source_relationship in source_relationships:
        append_relationship(source_relationship)
    for derived_relationship in derived_relationships:
        append_relationship(derived_relationship)

    return [merged_by_key[key] for key in ordered_keys]


def _clone_relationship_for_runtime_merge(
    rel: ObjectConfigGraphRelationship,
) -> ObjectConfigGraphRelationship:
    """Clone the relationship container without traversing attached graph refs."""

    return rel.model_copy(
        deep=False,
        update={
            "class_config_relationships": [
                _clone_class_relationship_for_runtime_merge(class_rel)
                for class_rel in rel.class_config_relationships or []
            ],
            "object_config_graph_relationship_classes": [
                _clone_relationship_class_for_runtime_merge(relationship_class)
                for relationship_class in rel.object_config_graph_relationship_classes
                or []
            ],
        },
    )


def _clone_class_relationship_for_runtime_merge(
    rel: ClassConfigRelationship,
) -> ClassConfigRelationship:
    """Clone mutable relationship lists while preserving target object refs."""

    return rel.model_copy(
        deep=False,
        update={
            "class_config_relationship_attributes": list(
                rel.class_config_relationship_attributes or []
            ),
        },
    )


def _clone_relationship_class_for_runtime_merge(
    relationship_class: ObjectConfigGraphRelationshipClass,
) -> ObjectConfigGraphRelationshipClass:
    """Clone relationship-class edge metadata without deep-copying ClassConfig."""

    return relationship_class.model_copy(deep=False)


__all__ = ["build_runtime_output_graph"]

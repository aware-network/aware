"""Cross-OCG relationship linking for Meta object config graphs."""

from __future__ import annotations

from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.builder import ObjectConfigGraphBuildResult
from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_relationship_class_id,
    stable_object_config_graph_relationship_id,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship_class import (
    ObjectConfigGraphRelationshipClass,
)


def _materialize_cross_ocg_relationships(
    *,
    graphs_by_id: dict[UUID, ObjectConfigGraph],
    cross_by_pair: dict[tuple[UUID, UUID], list[ClassConfigRelationship]],
) -> dict[tuple[UUID, UUID], ObjectConfigGraphRelationship]:
    rel_map: dict[tuple[UUID, UUID], ObjectConfigGraphRelationship] = {}
    edge_seen: set[tuple[UUID, UUID, UUID]] = set()

    for (src_graph_id, tgt_graph_id), rels in (cross_by_pair or {}).items():
        if not rels:
            continue
        src_graph = graphs_by_id.get(src_graph_id)
        tgt_graph = graphs_by_id.get(tgt_graph_id)
        if src_graph is None or tgt_graph is None:
            continue

        key = (src_graph_id, tgt_graph_id)
        ocg_rel = rel_map.get(key)
        if ocg_rel is None:
            ocg_rel_id = stable_object_config_graph_relationship_id(
                object_config_graph_id=src_graph.id,
                target_object_config_graph_id=tgt_graph.id,
            )
            ocg_rel = ObjectConfigGraphRelationship(
                id=ocg_rel_id,
                object_config_graph_id=src_graph.id,
                target_object_config_graph_id=tgt_graph.id,
                target_object_config_graph=tgt_graph,
            )
            rel_map[key] = ocg_rel
            src_graph.object_config_graph_relationships.append(ocg_rel)

        for rel in rels:
            edge_key = (src_graph_id, tgt_graph_id, rel.id)
            if edge_key in edge_seen:
                continue
            edge_seen.add(edge_key)
            ocg_rel.class_config_relationships.append(rel)

    return rel_map


def _materialize_cross_ocg_augments(
    *,
    graphs_by_id: dict[UUID, ObjectConfigGraph],
    cross_classes_by_pair: dict[tuple[UUID, UUID], dict[UUID, list[ClassConfig]]],
    rel_map: dict[tuple[UUID, UUID], ObjectConfigGraphRelationship],
) -> None:
    for (src_graph_id, tgt_graph_id), class_map in (
        cross_classes_by_pair or {}
    ).items():
        if not class_map:
            continue
        src_graph = graphs_by_id.get(src_graph_id)
        tgt_graph = graphs_by_id.get(tgt_graph_id)
        if src_graph is None or tgt_graph is None:
            continue

        key = (src_graph_id, tgt_graph_id)
        ocg_rel = rel_map.get(key)
        if ocg_rel is None:
            ocg_rel_id = stable_object_config_graph_relationship_id(
                object_config_graph_id=src_graph.id,
                target_object_config_graph_id=tgt_graph.id,
            )
            ocg_rel = ObjectConfigGraphRelationship(
                id=ocg_rel_id,
                object_config_graph_id=src_graph.id,
                target_object_config_graph_id=tgt_graph.id,
                target_object_config_graph=tgt_graph,
            )
            rel_map[key] = ocg_rel
            src_graph.object_config_graph_relationships.append(ocg_rel)

        rel_obj_by_class_config_id: dict[UUID, ObjectConfigGraphRelationshipClass] = {
            r.class_config_id: r
            for r in ocg_rel.object_config_graph_relationship_classes
        }

        for class_config_id, class_configs in class_map.items():
            if not class_configs:
                continue
            rel_obj = rel_obj_by_class_config_id.get(class_config_id)
            if rel_obj is None:
                rel_obj = ObjectConfigGraphRelationshipClass(
                    id=stable_object_config_graph_relationship_class_id(
                        object_config_graph_relationship_id=ocg_rel.id,
                        class_config_id=class_config_id,
                    ),
                    object_config_graph_relationship_id=ocg_rel.id,
                    class_config_id=class_config_id,
                )
                ocg_rel.object_config_graph_relationship_classes.append(rel_obj)
                rel_obj_by_class_config_id[class_config_id] = rel_obj


def link_cross_ocg_relationships(
    build_results_by_language: dict[CodeLanguage, ObjectConfigGraphBuildResult],
    external_graphs: list[ObjectConfigGraph] | None = None,
) -> dict[tuple[UUID, UUID], ObjectConfigGraphRelationship]:
    """Materialize detached cross-OCG edges produced by single-OCG builders."""

    graphs_by_id: dict[UUID, ObjectConfigGraph] = {
        res.graph.id: res.graph for res in build_results_by_language.values()
    }
    for graph in external_graphs or []:
        graphs_by_id.setdefault(graph.id, graph)

    cross_by_pair: dict[tuple[UUID, UUID], list[ClassConfigRelationship]] = {}
    cross_classes_by_pair: dict[tuple[UUID, UUID], dict[UUID, list[ClassConfig]]] = {}

    for result in build_results_by_language.values():
        src_graph = result.graph
        for target_id, rels in result.cross_relationships_by_target_ocg.items():
            cross_by_pair.setdefault((src_graph.id, target_id), []).extend(rels or [])
        for target_id, object_map in result.cross_class_configs_by_target_ocg.items():
            if not object_map:
                continue
            key = (src_graph.id, target_id)
            dest = cross_classes_by_pair.setdefault(key, {})
            for object_id, class_list in object_map.items():
                dest.setdefault(object_id, []).extend(class_list)

    rel_map = _materialize_cross_ocg_relationships(
        graphs_by_id=graphs_by_id,
        cross_by_pair=cross_by_pair,
    )
    _materialize_cross_ocg_augments(
        graphs_by_id=graphs_by_id,
        cross_classes_by_pair=cross_classes_by_pair,
        rel_map=rel_map,
    )
    return rel_map


def describe_cross_ocg_relationships(
    *,
    all_graphs: list[ObjectConfigGraph],
    rel_map: dict[tuple[UUID, UUID], ObjectConfigGraphRelationship],
) -> list[str]:
    descriptions: list[str] = []
    class_configs_by_id: dict[UUID, ClassConfig] = {
        node.class_config.id: node.class_config
        for graph in all_graphs
        for node in graph.object_config_graph_nodes
        if node.class_config is not None
    }
    all_graphs_by_id: dict[UUID, ObjectConfigGraph] = {
        graph.id: graph for graph in all_graphs
    }

    for (src_graph_id, tgt_graph_id), rel in rel_map.items():
        src_graph = all_graphs_by_id.get(src_graph_id)
        tgt_graph = all_graphs_by_id.get(tgt_graph_id)
        if src_graph is None or tgt_graph is None:
            raise ValueError(f"Graph not found for {src_graph_id} or {tgt_graph_id}")
        descriptions.append(
            f"Cross-OCG relationship: {src_graph.name} -> {tgt_graph.name}"
        )
        for rel_obj in rel.object_config_graph_relationship_classes:
            class_config = class_configs_by_id.get(rel_obj.class_config_id)
            if class_config is None:
                descriptions.append(
                    f"     Object: <missing class_config_id={rel_obj.class_config_id}>"
                )
            else:
                descriptions.append(f"      - Class: {class_config.name}")
    return descriptions


__all__ = [
    "describe_cross_ocg_relationships",
    "link_cross_ocg_relationships",
]

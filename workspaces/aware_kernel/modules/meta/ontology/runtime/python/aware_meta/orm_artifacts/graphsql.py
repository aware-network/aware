"""Helpers for constructing ORM GraphSQL plan components from Meta graphs.

Contract (canonical-only):
- GraphSQL plans are compiled from the derived SQL OCG produced by the runtime→SQL transformer.
- ORM must not guess join semantics; it consumes explicit relationship metadata from the graph.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from aware_orm._support import logger, to_snake_case
from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm.graph.plan_cache import GraphPlan, GraphPlanCache
from aware_orm.graph.plan_compiler import GraphPlanCompiler, RelationshipDescriptor
from aware_meta.graph.config.namespace_index import build_node_namespace_by_node_id


if TYPE_CHECKING:
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology.graph.config.object_config_graph_node import (
        ObjectConfigGraphNode,
    )
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.class_.class_config_relationship import (
        ClassConfigRelationship,
    )


def _index_rendered_sql_names(
    object_config_graph: ObjectConfigGraph,
) -> tuple[dict[UUID, str], dict[UUID, str]]:
    """Index rendered SQL table/column names from SQL overlays embedded in the graph."""

    table_by_class_id: dict[UUID, str] = {}
    column_by_attr_id: dict[UUID, str] = {}

    for overlay in object_config_graph.object_config_graph_overlays:
        lang = overlay.language
        if str(lang.value).lower() != "sql":
            continue

        for cls_overlay in overlay.class_config_overlays:
            cls_id = cls_overlay.class_config_id
            rendered = cls_overlay.rendered_name
            if rendered:
                table_by_class_id[cls_id] = str(rendered)

        for attr_overlay in overlay.attribute_config_overlays:
            attr_id = attr_overlay.attribute_config_id
            rendered = attr_overlay.rendered_name
            if rendered:
                column_by_attr_id[attr_id] = str(rendered)

    return table_by_class_id, column_by_attr_id


def _resolve_table_schema_by_class_config_id(
    object_config_graph: ObjectConfigGraph,
) -> dict[UUID, str]:
    from aware_meta_ontology.graph.config.object_config_graph_enums import (
        ObjectConfigGraphNodeType,
    )

    namespace_by_node_id = build_node_namespace_by_node_id(object_config_graph)
    table_schema_by_class_id: dict[UUID, str] = {}
    for node in object_config_graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        namespace = namespace_by_node_id.get(node.id)
        if namespace is None:
            continue
        table_schema = to_snake_case(namespace.namespace.replace(".", "_"))
        table_schema_by_class_id[node.class_config.id] = table_schema or "default"
    return table_schema_by_class_id


def get_graph_config_registry(
    object_config_graph: ObjectConfigGraph,
) -> GraphConfigRegistry:
    from aware_meta_ontology.graph.config.object_config_graph_enums import (
        ObjectConfigGraphNodeType,
    )
    from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
        AttributeTypeDescriptorKind,
    )

    # Collect table descriptors keyed by class_config_id.
    table_overrides, column_overrides = _index_rendered_sql_names(object_config_graph)
    table_schema_by_class_id = _resolve_table_schema_by_class_config_id(object_config_graph)
    table_descriptors: list[TableDescriptor] = []

    for node in object_config_graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        class_config = node.class_config
        table_schema = table_schema_by_class_id.get(class_config.id) or "default"
        table_name = table_overrides.get(class_config.id) or to_snake_case(class_config.name)

        columns: list[str] = []
        seen: set[str] = set()

        def add(col: str | None) -> None:
            if not col:
                return
            if col in seen:
                return
            seen.add(col)
            columns.append(col)

        # Persisted columns derived from AttributeConfigs.
        attr_links = class_config.class_config_attribute_configs
        attr_links.sort(key=lambda acc: (int(acc.position or 10**9), str(acc.attribute_config.id)))

        # Base columns first, honoring overlay overrides.
        #
        # Why this exists:
        # - `attr_links` is sorted by `position`, which is an authoring concern and may not guarantee
        #   stable/expected physical ordering for core columns.
        # - We want at least `id` to be present and first for predictable table descriptors and
        #   downstream plan compilation.
        #
        # Keep this list minimal; adding more "base" columns is an explicit schema decision.
        # (Potential future: "branch_id" once it exists in the graph.)
        base_column_order = ("id",)
        base_rank = {name: idx for idx, name in enumerate(base_column_order)}
        base_cols: dict[str, str] = {}
        for acc in attr_links:
            attr = acc.attribute_config
            name = attr.name
            if name not in base_rank:
                continue
            base_cols[name] = column_overrides.get(attr.id) or to_snake_case(attr.name)

        for base_name in base_column_order:
            add(base_cols.get(base_name) or base_name)

        for acc in attr_links:
            attr = acc.attribute_config
            if attr.name in base_rank:
                continue
            if attr.is_virtual:
                continue
            kind = attr.type_descriptor.kind
            if kind not in {
                AttributeTypeDescriptorKind.primitive,
                AttributeTypeDescriptorKind.enum,
                AttributeTypeDescriptorKind.mapping,
            }:
                continue
            add(column_overrides.get(attr.id) or to_snake_case(attr.name))

        table_descriptors.append(
            TableDescriptor(
                class_config_id=class_config.id,
                table_schema=table_schema,
                table_name=table_name,
                attributes=tuple(columns),
            )
        )

    return GraphConfigRegistry(table_descriptors)


def build_relationship_descriptors(
    object_config_graph: ObjectConfigGraph,
    config_registry: GraphConfigRegistry,
) -> list[RelationshipDescriptor]:
    from aware_meta_ontology.class_.class_config_relationship_enums import (
        ClassConfigRelationshipAttributeRole,
        ClassConfigRelationshipDirection,
        ClassConfigRelationshipType,
    )
    from aware_meta_ontology.graph.config.object_config_graph_enums import (
        ObjectConfigGraphNodeType,
    )

    descriptors: list[RelationshipDescriptor] = []

    # Index overlay name overrides for join condition correctness.
    _table_overrides, column_overrides = _index_rendered_sql_names(object_config_graph)

    # Index class/attribute ownership for FK resolution.
    class_by_id: dict[UUID, ClassConfig] = {}
    attr_by_id: dict[UUID, AttributeConfig] = {}
    owner_by_attr_id: dict[UUID, UUID] = {}
    relationships_by_id: dict[UUID, ClassConfigRelationship] = {}

    for node in object_config_graph.object_config_graph_nodes:
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            cc = node.class_config
            class_by_id[cc.id] = cc
            for acc in cc.class_config_attribute_configs:
                attr = acc.attribute_config
                attr_by_id[attr.id] = attr
                owner_by_attr_id[attr.id] = cc.id
        elif node.type == ObjectConfigGraphNodeType.relationship and node.class_config_relationship is not None:
            rel = node.class_config_relationship
            relationships_by_id[rel.id] = rel

    # Include relationships attached directly to ClassConfig (cross-OCG link phase).
    for cc in class_by_id.values():
        for rel in cc.class_config_relationships:
            rel_id = rel.id
            if rel_id not in relationships_by_id:
                relationships_by_id[rel_id] = rel

    for rel in relationships_by_id.values():
        source_id = rel.class_config_id
        target_id = rel.target_class_config_id
        source_cc = class_by_id.get(source_id)
        target_cc = class_by_id.get(target_id)
        if not source_cc or not target_cc:
            continue

        source_table_descriptor = config_registry.get_by_class_config_id(source_id)
        target_table_descriptor = config_registry.get_by_class_config_id(target_id)
        if source_table_descriptor is None or target_table_descriptor is None:
            continue

        source_table_key = source_table_descriptor.table_key
        target_table_key = target_table_descriptor.table_key

        rel_type = rel.relationship_type
        uses_collection = rel_type in (
            ClassConfigRelationshipType.one_to_many,
            ClassConfigRelationshipType.many_to_many,
        )

        join_condition: str | None = None

        assoc = rel.class_config_relationship_association_edge
        assoc_class_id = assoc.class_config_id if assoc is not None else None

        fk_edges = [
            ra
            for ra in rel.class_config_relationship_attributes
            if ra.role == ClassConfigRelationshipAttributeRole.foreign_key
        ]

        if assoc_class_id is not None:
            join_desc = config_registry.get_by_class_config_id(assoc_class_id)
            if join_desc is None:
                logger.warning(
                    "GraphSQL: missing association table descriptor for relationship %s",
                    rel.id,
                )
                continue

            join_table_key = join_desc.table_key
            src_fk_col: str | None = None
            tgt_fk_col: str | None = None
            for ra in fk_edges:
                attr_id = ra.attribute_config_id
                if owner_by_attr_id.get(attr_id) != assoc_class_id:
                    continue
                attr = attr_by_id.get(attr_id)
                col = column_overrides.get(attr_id) or (to_snake_case(attr.name) if attr is not None else None)
                if ra.direction == ClassConfigRelationshipDirection.forward:
                    src_fk_col = col
                elif ra.direction == ClassConfigRelationshipDirection.reverse:
                    tgt_fk_col = col

            if not src_fk_col or not tgt_fk_col:
                logger.warning(
                    "GraphSQL: missing association FK columns for relationship %s",
                    getattr(rel, "id", None),
                )
                continue

            join_condition = (
                f"EXISTS (SELECT 1 FROM {join_table_key} jt "
                f"WHERE jt.{src_fk_col} = {source_table_key}.id AND jt.{tgt_fk_col} = {target_table_key}.id)"
            )
        else:
            resolved_fk: tuple[UUID, UUID] | None = None  # (fk_attr_id, owner_class_id)
            for ra in fk_edges:
                owner_id = owner_by_attr_id.get(ra.attribute_config_id)
                if owner_id not in {source_id, target_id}:
                    continue
                if owner_id == source_id:
                    resolved_fk = (ra.attribute_config_id, owner_id) if owner_id is not None else None
                    break
                if resolved_fk is None:
                    resolved_fk = (ra.attribute_config_id, owner_id) if owner_id is not None else None

            if resolved_fk is None:
                continue

            fk_attr_id, fk_owner_id = resolved_fk
            fk_attr = attr_by_id.get(fk_attr_id)
            fk_col = column_overrides.get(fk_attr_id) or (to_snake_case(fk_attr.name) if fk_attr is not None else None)
            if not fk_col:
                continue

            if fk_owner_id == source_id:
                join_condition = f"{source_table_key}.{fk_col} = {target_table_key}.id"
            else:
                join_condition = f"{source_table_key}.id = {target_table_key}.{fk_col}"

        if not join_condition:
            continue

        descriptors.append(
            RelationshipDescriptor(
                canonical_relationship_id=rel.id,
                source_table_key=source_table_key,
                target_table_key=target_table_key,
                join_condition=join_condition,
                uses_collection=bool(uses_collection),
            )
        )

    return descriptors


def compile_plan_cache_from_object_config_graph(
    object_config_graph: ObjectConfigGraph,
) -> GraphPlanCache:
    config_registry = get_graph_config_registry(object_config_graph)
    descriptors = build_relationship_descriptors(object_config_graph, config_registry)

    compiler = GraphPlanCompiler(config_registry)
    plans: list[GraphPlan] = []
    for table in config_registry.all():
        plans.append(compiler.compile_plan(table.table_key, descriptors))
    return GraphPlanCache(plans)

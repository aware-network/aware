"""Compile ORM ProjectionPlan instances from SQL-lowered Meta OCG + OPG metadata.

This mirrors the GraphSQL plan pipeline:
- GraphSQLPlan: read/hydration joins (DB → JSON graph)
- ProjectionPlan: write/materialization mapping (OIG snapshot → DB rows)

Contract (canonical-only):
- Plans must be derived from the SQL OCG (post-transform) so association tables and
  FK ownership rules are explicit and deterministic.
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from aware_orm._support import to_snake_case
from aware_orm.projection.plan import (
    ProjectionAssociationPlan,
    ProjectionColumnPlan,
    ProjectionDialect,
    ProjectionPlan,
    ProjectionPlanCache,
    ProjectionTablePlan,
)
from aware_meta.graph.config.namespace_index import build_node_namespace_by_node_id


def _index_rendered_sql_names(
    object_config_graph,
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


def _resolve_table_schema_by_class_config_id(object_config_graph) -> dict[UUID, str]:
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


def compile_projection_plan_cache_from_object_config_graph(
    object_config_graph,
    *,
    dialect: ProjectionDialect,
) -> ProjectionPlanCache:
    """Compile all ProjectionPlans for the graph's OPGs (by projection_hash)."""

    from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
    from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
        AttributeTypeDescriptorKind,
    )
    from aware_meta_ontology.class_.class_config_relationship_enums import (
        ClassConfigRelationshipAttributeRole,
        ClassConfigRelationshipDirection,
    )
    from aware_meta_ontology.graph.config.object_config_graph_enums import (
        ObjectConfigGraphNodeType,
    )

    table_overrides, column_overrides = _index_rendered_sql_names(object_config_graph)
    table_schema_by_class_id = _resolve_table_schema_by_class_config_id(object_config_graph)

    # Index classes, attributes, and relationship records for FK ownership resolution.
    class_by_id = {}
    attr_by_id = {}
    owner_by_attr_id: dict[UUID, UUID] = {}
    relationships_by_id = {}

    for node in object_config_graph.object_config_graph_nodes:
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            cc = node.class_config
            if cc.id is None:
                continue
            class_by_id[cc.id] = cc
            for acc in cc.class_config_attribute_configs:
                attr = acc.attribute_config
                if attr is None or attr.id is None:
                    continue
                attr_by_id[attr.id] = attr
                owner_by_attr_id[attr.id] = cc.id
        elif node.type == ObjectConfigGraphNodeType.relationship and node.class_config_relationship is not None:
            rel = node.class_config_relationship
            if rel.id is not None:
                relationships_by_id[rel.id] = rel

    # Include relationships attached directly to ClassConfig (cross-OCG link phase).
    for cc in class_by_id.values():
        for rel in cc.class_config_relationships:
            rel_id = rel.id
            if rel_id is not None and rel_id not in relationships_by_id:
                relationships_by_id[rel_id] = rel

    plans: list[ProjectionPlan] = []

    for opg in object_config_graph.object_projection_graphs:
        included_class_ids = {n.class_config_id for n in (opg.object_projection_graph_nodes or []) if n.class_config_id}
        if not included_class_ids:
            continue

        # StrongRef is projection-relative: only relationships represented as membership edges
        # are present as ClassInstanceRelationship entries in the OIG snapshot.
        edge_relationship_ids: set[UUID] = {
            e.class_config_relationship_id
            for e in (opg.object_projection_graph_edges or [])
            if e.class_config_relationship_id is not None
        }

        # FK columns on endpoint tables (non-association) that should be filled from relationship edges.
        fk_meta_by_attr_id: dict[UUID, tuple[UUID, str]] = {}

        # Association/join tables derived from relationship edges.
        associations: list[ProjectionAssociationPlan] = []

        for rel in relationships_by_id.values():
            src_id = rel.class_config_id
            tgt_id = rel.target_class_config_id
            if src_id is None or tgt_id is None:
                continue

            assoc_edge = rel.class_config_relationship_association_edge
            assoc_class_id = assoc_edge.class_config_id if assoc_edge is not None else None

            # Only StrongRef relationships can be used to derive FK column values from edges.
            # SoftRef/portal relationships preserve the FK UUID as a data attribute (commit-backed),
            # so their columns must be projected from AttributeValue, not from ClassInstanceRelationship.
            is_strong_ref = rel.id is not None and rel.id in edge_relationship_ids

            fk_edges = [
                ra
                for ra in rel.class_config_relationship_attributes
                if ra.role == ClassConfigRelationshipAttributeRole.foreign_key and ra.attribute_config_id is not None
            ]

            # Association table: derive source/target FK column names from role metadata on the association class.
            if assoc_class_id is not None and src_id in included_class_ids and tgt_id in included_class_ids:
                assoc_cls = class_by_id.get(assoc_class_id)
                if assoc_cls is not None:
                    assoc_schema = table_schema_by_class_id.get(assoc_class_id) or "default"
                    assoc_table = table_overrides.get(assoc_class_id) or to_snake_case(assoc_cls.name)
                    assoc_table_key = f"{assoc_schema}.{assoc_table}"

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
                    if src_fk_col and tgt_fk_col:
                        associations.append(
                            ProjectionAssociationPlan(
                                association_table_key=assoc_table_key,
                                relationship_id=rel.id,
                                source_fk_column=src_fk_col,
                                target_fk_column=tgt_fk_col,
                            )
                        )

                # Do not treat association-class FK attributes as endpoint FK columns.
                for ra in fk_edges:
                    attr_id = ra.attribute_config_id
                    if owner_by_attr_id.get(attr_id) == assoc_class_id:
                        continue

            # Endpoint FK attributes: mark so we can fill them from relationship edges if needed.
            if not is_strong_ref:
                continue
            for ra in fk_edges:
                attr_id = ra.attribute_config_id
                owner_id = owner_by_attr_id.get(attr_id)
                if owner_id is None:
                    continue
                if owner_id not in included_class_ids:
                    continue
                if assoc_class_id is not None and owner_id == assoc_class_id:
                    continue
                direction = "forward" if ra.direction == ClassConfigRelationshipDirection.forward else "reverse"
                fk_meta_by_attr_id[attr_id] = (rel.id, direction)

        table_plans: list[ProjectionTablePlan] = []

        for class_id in sorted(included_class_ids, key=lambda x: str(x)):
            cls = class_by_id.get(class_id)
            if cls is None:
                continue

            table_schema = table_schema_by_class_id.get(class_id) or "default"
            table_name = table_overrides.get(class_id) or to_snake_case(cls.name)
            table_key = f"{table_schema}.{table_name}"

            # Deterministic attribute order.
            links = sorted(
                cls.class_config_attribute_configs,
                key=lambda acc: (
                    acc.position if acc.position is not None else 10**9,
                    acc.attribute_config.name,
                ),
            )

            pk_cols: list[str] = []
            cols: list[ProjectionColumnPlan] = []

            for link in links:
                attr = link.attribute_config
                if attr is None or attr.id is None:
                    continue
                info = resolve_type_info(attr)
                if info.kind not in {
                    AttributeTypeDescriptorKind.primitive,
                    AttributeTypeDescriptorKind.enum,
                }:
                    continue

                col_name = column_overrides.get(attr.id) or to_snake_case(attr.name)
                if bool(attr.is_primary):
                    pk_cols.append(col_name)

                if bool(attr.is_primary) and attr.name == "id":
                    cols.append(
                        ProjectionColumnPlan(
                            column_name=col_name,
                            source="id",
                            sql_type_hint=None,
                            nullable=False,
                        )
                    )
                    continue

                # Lane scope columns are DB/index concerns (virtual in the SQL-lowered OCG),
                # not SSOT AttributeValues stored in the OIG snapshot.
                if attr.name == "branch_id":
                    cols.append(
                        ProjectionColumnPlan(
                            column_name=col_name,
                            source="branch_id",
                            sql_type_hint=None,
                            nullable=False,
                        )
                    )
                    continue
                if attr.name == "projection_hash":
                    cols.append(
                        ProjectionColumnPlan(
                            column_name=col_name,
                            source="projection_hash",
                            sql_type_hint=None,
                            nullable=False,
                        )
                    )
                    continue

                fk_meta = fk_meta_by_attr_id.get(attr.id)
                if fk_meta is not None:
                    rel_id, direction = fk_meta
                    cols.append(
                        ProjectionColumnPlan(
                            column_name=col_name,
                            source="fk_attribute",
                            attribute_config_id=attr.id,
                            relationship_id=rel_id,
                            direction=direction,
                            sql_type_hint=None,
                            nullable=not bool(attr.is_required),
                        )
                    )
                    continue

                cols.append(
                    ProjectionColumnPlan(
                        column_name=col_name,
                        source="attribute",
                        attribute_config_id=attr.id,
                        sql_type_hint=None,
                        nullable=not bool(attr.is_required),
                    )
                )

            if not pk_cols:
                pk_cols = ["id"]

            table_plans.append(
                ProjectionTablePlan(
                    table_key=table_key,
                    class_config_id=class_id,
                    primary_key=tuple(pk_cols),
                    columns=tuple(cols),
                )
            )

        # De-duplicate association plans deterministically.
        grouped: dict[str, dict[UUID, ProjectionAssociationPlan]] = defaultdict(dict)
        for assoc in associations:
            grouped[assoc.association_table_key][assoc.relationship_id] = assoc
        assoc_unique = []
        for table_key in sorted(grouped.keys()):
            for rel_id in sorted(grouped[table_key].keys(), key=lambda x: str(x)):
                assoc_unique.append(grouped[table_key][rel_id])

        plans.append(
            ProjectionPlan(
                projection_hash=opg.projection_hash,
                opg_name=opg.name,
                dialect=dialect,
                tables=tuple(table_plans),
                associations=tuple(assoc_unique),
            )
        )

    return ProjectionPlanCache(plans)


__all__ = ["compile_projection_plan_cache_from_object_config_graph"]

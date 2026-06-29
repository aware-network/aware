"""
Dart SQLite projection plan renderer.

Emits a pure-data plan bundle that allows the Interface runtime to project
OIG lane snapshots into SQLite module tables without per-module projector logic.
"""

from __future__ import annotations

import re
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast
from uuid import UUID
from typing_extensions import override

from aware_code.section.writer import CodeSectionWriter
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_utils.string_transform import to_camel_case, to_pascal_case
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

from dart_grammar.layout_strategy import DartGraphFixedFileLayoutStrategy
from dart_grammar.renderer import DartRenderer


class _ProjectionPlanColumn(Protocol):
    column_name: str
    source: str
    attribute_config_id: UUID | None
    relationship_id: UUID | None
    direction: str | None
    sql_type_hint: str | None
    nullable: bool


class _ProjectionPlanTable(Protocol):
    table_key: str
    class_config_id: UUID | None
    primary_key: list[str]
    columns: list[_ProjectionPlanColumn]


class _ProjectionPlanAssociation(Protocol):
    association_table_key: str
    relationship_id: UUID
    source_fk_column: str
    target_fk_column: str


class _ProjectionPlan(Protocol):
    opg_name: str
    projection_hash: str
    tables: list[_ProjectionPlanTable]
    associations: list[_ProjectionPlanAssociation]


class _ProjectionPlanCache(Protocol):
    def all(self) -> list[_ProjectionPlan]:
        ...


class _ProjectionPlanCompiler(Protocol):
    def __call__(
        self,
        object_config_graph: ObjectConfigGraph,
        *,
        dialect: str,
    ) -> _ProjectionPlanCache:
        ...


def _safe_identifier(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", name or "")
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        return "value"
    if cleaned[0].isdigit():
        cleaned = f"v_{cleaned}"
    return cleaned


def _safe_pascal(name: str) -> str:
    return _safe_identifier(to_pascal_case(name or ""))


def _dart_string(value: str) -> str:
    v = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{v}'"


def _plan_rel_path(graph: ObjectConfigGraph) -> Path:
    prefix = graph.fqn_prefix or "graph"
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", prefix)
    slug = re.sub(r"_+", "_", slug).strip("_") or "graph"
    return Path("_aware/projection") / f"{slug}_sqlite_projection_plan.dart"


class DartSqliteProjectionPlanRenderer(DartRenderer):
    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy) -> None:
        fixed = DartGraphFixedFileLayoutStrategy(parent=layout_strategy, rel_path_factory=_plan_rel_path)
        super().__init__(layout_strategy=fixed)
        self._graph: ObjectConfigGraph | None = None

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        super().bind_object_config_graph(graph)
        self._graph = graph

    @override
    def emit_file(
        self,
        meta_objects: list[object],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        _ = meta_objects
        _ = schema
        _ = class_to_class_config_map
        _ = base_class_module
        _ = base_class_name

        graph = self._graph
        if graph is None:
            return

        # IMPORTANT:
        # Renderers are emit-only; they must never run transformers.
        #
        # This renderer expects to be invoked on the **SQL-lowered** graph
        # (pipeline derives via RuntimeToSQLTransformer) so plans match canonical
        # SQL DDL semantics (join-table synthesis, FK ownership rules, etc.).
        projection_builders = import_module("aware_meta.orm_artifacts.projection_plans")
        compiler = cast(
            _ProjectionPlanCompiler,
            projection_builders.compile_projection_plan_cache_from_object_config_graph,
        )
        cache = compiler(graph, dialect="sqlite")
        plans = sorted(cache.all(), key=lambda p: (p.opg_name, p.projection_hash))
        if not plans:
            return

        prefix = graph.fqn_prefix or "graph"
        const_base = _safe_identifier(to_camel_case(prefix))
        pascal = _safe_pascal(prefix)

        const_name = f"{const_base}SqliteProjectionPlan"
        register_fn = f"register{pascal}SqliteProjectionPlan"

        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// SQLite projection plan bundle for this graph.\n\n")
        _ = writer.token("import 'package:aware_meta/graph/instance/sqlite_projection_plan.dart';\n\n")

        _ = writer.token(f"const SqliteProjectionPlanDefinition {const_name} = SqliteProjectionPlanDefinition(\n")
        _ = writer.token(f"  fqnPrefix: {_dart_string(prefix)},\n")
        # EnumOption.id -> wire value mapping for enum columns.
        enum_option_value_by_id: dict[str, str] = {}
        for node in graph.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.enum:
                continue
            enum_cfg = node.enum_config
            if enum_cfg is None:
                continue
            for opt in enum_cfg.enum_options or []:
                enum_option_value_by_id[str(opt.id)] = str(opt.value)

        if enum_option_value_by_id:
            _ = writer.token("  enumOptionValueById: const {\n")
            for k in sorted(enum_option_value_by_id.keys()):
                _ = writer.token(f"    {_dart_string(k)}: {_dart_string(enum_option_value_by_id[k])},\n")
            _ = writer.token("  },\n")
        _ = writer.token("  plans: const [\n")

        for plan in plans:
            _ = writer.token("    SqliteProjectionPlan(\n")
            _ = writer.token(f"      projectionHash: {_dart_string(plan.projection_hash)},\n")
            _ = writer.token(f"      opgName: {_dart_string(plan.opg_name)},\n")

            _ = writer.token("      tables: const [\n")
            for table in plan.tables:
                _ = writer.token("        SqliteProjectionTablePlan(\n")
                _ = writer.token(f"          tableKey: {_dart_string(table.table_key)},\n")
                if table.class_config_id is None:
                    _ = writer.token("          classConfigId: null,\n")
                else:
                    _ = writer.token(f"          classConfigId: {_dart_string(str(table.class_config_id))},\n")
                _ = writer.token("          primaryKey: const [\n")
                for pk in table.primary_key:
                    _ = writer.token(f"            {_dart_string(pk)},\n")
                _ = writer.token("          ],\n")
                _ = writer.token("          columns: const [\n")
                for col in table.columns:
                    _ = writer.token("            SqliteProjectionColumnPlan(\n")
                    _ = writer.token(f"              columnName: {_dart_string(col.column_name)},\n")
                    _ = writer.token(f"              source: {_dart_string(col.source)},\n")
                    if col.attribute_config_id is None:
                        _ = writer.token("              attributeConfigId: null,\n")
                    else:
                        _ = writer.token(
                            f"              attributeConfigId: {_dart_string(str(col.attribute_config_id))},\n"
                        )
                    if col.relationship_id is None:
                        _ = writer.token("              relationshipId: null,\n")
                    else:
                        _ = writer.token(f"              relationshipId: {_dart_string(str(col.relationship_id))},\n")
                    if col.direction is None:
                        _ = writer.token("              direction: null,\n")
                    else:
                        _ = writer.token(f"              direction: {_dart_string(col.direction)},\n")
                    if col.sql_type_hint is None:
                        _ = writer.token("              sqlTypeHint: null,\n")
                    else:
                        _ = writer.token(f"              sqlTypeHint: {_dart_string(col.sql_type_hint)},\n")
                    _ = writer.token(f"              nullable: {str(bool(col.nullable)).lower()},\n")
                    _ = writer.token("            ),\n")
                _ = writer.token("          ],\n")
                _ = writer.token("        ),\n")
            _ = writer.token("      ],\n")

            _ = writer.token("      associations: const [\n")
            for assoc in plan.associations:
                _ = writer.token("        SqliteProjectionAssociationPlan(\n")
                _ = writer.token(f"          associationTableKey: {_dart_string(assoc.association_table_key)},\n")
                _ = writer.token(f"          relationshipId: {_dart_string(str(assoc.relationship_id))},\n")
                _ = writer.token(f"          sourceFkColumn: {_dart_string(assoc.source_fk_column)},\n")
                _ = writer.token(f"          targetFkColumn: {_dart_string(assoc.target_fk_column)},\n")
                _ = writer.token("        ),\n")
            _ = writer.token("      ],\n")

            _ = writer.token("    ),\n")

        _ = writer.token("  ],\n")
        _ = writer.token(");\n\n")

        _ = writer.token(f"void {register_fn}(SqliteProjectionPlanRegistry registry) {{\n")
        _ = writer.token(f"  registry.register({const_name});\n")
        _ = writer.token("}\n")


__all__ = ["DartSqliteProjectionPlanRenderer"]

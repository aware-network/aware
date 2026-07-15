"""
Dart SQLite schema renderer.

Embeds SQLite DDL as Dart constants so clients can install schemas without
filesystem or monorepo layout dependencies.
"""

from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID
from typing_extensions import override

from aware_code.section.writer import CodeSectionWriter
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_utils.string_transform import to_camel_case, to_pascal_case
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

from dart_grammar.layout_strategy import DartGraphFixedFileLayoutStrategy
from dart_grammar.renderer import DartRenderer

from sql_grammar.layout_strategy import SQLLayoutStrategyNamespace
from sql_grammar.renderers.renderer import SqliteSQLRenderer


class _SqliteSqlRendererBridge(SqliteSQLRenderer):
    def table_name(self, cls: ClassConfig) -> str:
        return self._table_name(cls)

    def emit_table(self, cls: ClassConfig, *, class_lookup: dict[UUID, ClassConfig]) -> str:
        return self._emit_table(cls, class_lookup=class_lookup)


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


def _schema_rel_path(graph: ObjectConfigGraph) -> Path:
    prefix = graph.fqn_prefix or "graph"
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", prefix)
    slug = re.sub(r"_+", "_", slug).strip("_") or "graph"
    return Path("_aware/db") / f"{slug}_sqlite_schema.dart"


class DartSqliteSchemaRenderer(DartRenderer):
    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy) -> None:
        fixed = DartGraphFixedFileLayoutStrategy(parent=layout_strategy, rel_path_factory=_schema_rel_path)
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
        _ = schema
        _ = base_class_module
        _ = base_class_name

        graph = self._graph
        if graph is None:
            return

        # IMPORTANT:
        # Renderers are emit-only; they must never run transformers.
        #
        # This renderer expects to be invoked on the **SQL-lowered** graph
        # (pipeline derives via RuntimeToSQLTransformer), so schema bundles match
        # canonical SQL DDL semantics (join-table synthesis, FK requiredness, etc.).
        sql_graph = graph

        # Inline values are wire/payload types, not persistent ORM entities.
        # SQLite schema bundles must include only persistent graph_ref classes,
        # including any synthetic join/association tables introduced by SQL lowering.
        classes: list[ClassConfig] = []
        for node in sql_graph.object_config_graph_nodes or []:
            if node.type != ObjectConfigGraphNodeType.class_:
                continue
            cls = node.class_config
            if cls is None:
                continue
            if cls.value_mode != ClassValueMode.graph_ref:
                continue
            classes.append(cls)
        if not classes:
            return

        classes.sort(key=lambda c: c.name)

        # Build a class lookup that includes:
        # - all local SQL-lowered classes (including synthetic join tables)
        # - external classes (to resolve FK REFERENCES targets)
        class_lookup: dict[UUID, ClassConfig] = {}
        for cls in classes:
            class_lookup[cls.id] = cls
        if class_to_class_config_map:
            class_lookup.update(class_to_class_config_map)
        else:
            class_lookup.update(self._graph_classes_by_id)

        sql_layout = SQLLayoutStrategyNamespace(base_dir=Path("."))
        sql_renderer = _SqliteSqlRendererBridge(layout_strategy=sql_layout)
        # IMPORTANT:
        # This renderer emits **SQL** DDL, so it must apply the SQL overlays
        # (reserved keywords, rendered names), not the Dart overlays that may be
        # active for the current Dart materialization pass.
        sql_overlay = next(
            (
                o
                for o in (sql_graph.object_config_graph_overlays or [])
                if o.language.value.lower() == "sql"
            ),
            None,
        )
        if sql_overlay is not None:
            sql_renderer.set_language_overlay(sql_overlay)
        else:
            # Best-effort fallback (legacy): use the current renderer's overlays.
            sql_renderer.overlays_by_entity_id = self.overlays_by_entity_id
        sql_renderer.bind_object_config_graph(sql_graph)

        entries: list[tuple[str, str]] = []
        for cls in classes:
            table_name = sql_renderer.table_name(cls)
            create_sql = sql_renderer.emit_table(cls, class_lookup=class_lookup)
            entries.append((table_name, create_sql))

        prefix = graph.fqn_prefix or "graph"
        const_name = _safe_identifier(to_camel_case(prefix))
        pascal = _safe_pascal(prefix)
        register_fn = f"register{pascal}SqliteSchema"

        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// SQLite schema bundle for this graph.\n\n")
        _ = writer.token("import 'package:aware_meta/graph/instance/sqlite_schema.dart';\n\n")

        _ = writer.token(f"const SqliteSchemaDefinition {const_name}SqliteSchema = SqliteSchemaDefinition(\n")
        _ = writer.token(f"  fqnPrefix: '{prefix}',\n")
        _ = writer.token("  tables: const [\n")
        for table_name, create_sql in entries:
            _ = writer.token("    SqliteTableDefinition(\n")
            _ = writer.token(f"      tableName: '{table_name}',\n")
            _ = writer.token("      createSql: '''\n")
            _ = writer.token(create_sql.rstrip() + "\n")
            _ = writer.token("''',\n")
            _ = writer.token("    ),\n")
        _ = writer.token("  ],\n")
        _ = writer.token(");\n\n")

        _ = writer.token(f"void {register_fn}(SqliteSchemaRegistry registry) {{\n")
        _ = writer.token(f"  registry.register({const_name}SqliteSchema);\n")
        _ = writer.token("}\n")


__all__ = ["DartSqliteSchemaRenderer"]

"""
Dart OPG lane materialization renderer.

Emits a single file with lane materializers for each ObjectProjectionGraph (OPG),
plus a module-level materialization registrar.
"""

import os
import re
from pathlib import Path
from uuid import UUID
from typing_extensions import override

from aware_code.section.writer import CodeSectionWriter
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy
from aware_utils.string_transform import to_camel_case, to_pascal_case, to_snake_case

from dart_grammar.layout_strategy import DartFixedFileLayoutStrategy
from dart_grammar.renderer import DartRenderer
from dart_grammar.reserved_keywords import DART_RESERVED_IDENTIFIERS


_OUTPUT_REL_PATH = Path("_aware/materialization/materializers_opg.dart")


def _safe_import_alias(module: str) -> str:
    alias = module
    if alias.startswith("package:"):
        alias = alias[len("package:"):]
    alias = alias.replace("/", "_").replace("\\", "_").replace(".", "_").replace("-", "_")
    alias = re.sub(r"[^a-zA-Z0-9_]", "_", alias)
    alias = re.sub(r"_+", "_", alias).strip("_")
    if not alias:
        alias = "m"
    if alias[0].isdigit():
        alias = f"m_{alias}"
    return alias


def _safe_identifier(name: str) -> str:
    if not name:
        return "value"
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = "value"
    if cleaned[0].isdigit():
        cleaned = f"v_{cleaned}"
    if cleaned in DART_RESERVED_IDENTIFIERS:
        cleaned = f"{cleaned}_"
    return cleaned


def _safe_pascal_case(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", (name or "").strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        return ""
    return _safe_identifier(to_pascal_case(cleaned))


def _relative_import(from_path: Path, to_path: Path) -> str:
    rel = os.path.relpath(to_path, start=from_path.parent)
    return rel.replace(os.path.sep, "/")


def _external_model_import_root(graph: ObjectConfigGraph) -> str:
    prefix = (graph.fqn_prefix or "").strip()
    if not prefix:
        raise ValueError(f"External graph {graph.id} is missing fqn_prefix for Dart model import resolution")
    if prefix.endswith("_ontology") or prefix.endswith("_api"):
        return prefix
    return f"{prefix}_ontology"


def _external_class_relative_path(
    *,
    graph: ObjectConfigGraph,
    class_config: ClassConfig,
) -> str:
    for node in graph.object_config_graph_nodes:
        if node.class_config is None or node.class_config.id != class_config.id:
            continue
        aware_layouts = [layout for layout in node.layouts if not layout.layout_kind or layout.layout_kind == "aware"]
        if aware_layouts:
            layout = min(
                aware_layouts,
                key=lambda layout_entry: (
                    layout_entry.source_position is None,
                    layout_entry.source_position or 0,
                    layout_entry.relative_path or "",
                ),
            )
            if layout.relative_path:
                return str(Path(layout.relative_path).with_suffix(".dart")).replace("\\", "/")

    fqn_parts = class_config.class_fqn.split(".")
    if len(fqn_parts) >= 4:
        schema = fqn_parts[2]
    else:
        schema = "default"
    return str(Path(schema) / f"{to_snake_case(class_config.name)}.dart").replace("\\", "/")


class DartMaterializationOpgRenderer(DartRenderer):
    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy) -> None:
        fixed = DartFixedFileLayoutStrategy(parent=layout_strategy, rel_path=_OUTPUT_REL_PATH)
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

        local_class_ids: set[UUID] = set()
        for node in graph.object_config_graph_nodes:
            if node.class_config is not None:
                local_class_ids.add(node.class_config.id)

        external_graphs: list[ObjectConfigGraph] = list(self.external_graphs or [])
        external_graph_by_class_id: dict[UUID, ObjectConfigGraph] = {}
        for ext_graph in external_graphs:
            for node in ext_graph.object_config_graph_nodes:
                if node.class_config is None:
                    continue
                _ = external_graph_by_class_id.setdefault(node.class_config.id, ext_graph)

        opgs = sorted(
            list(graph.object_projection_graphs or []),
            key=lambda opg: opg.name,
        )

        inner_layout = self.layout_strategy.get_parent()
        if inner_layout is None:
            raise ValueError("No parent layout strategy found")

        entries: list[dict[str, str]] = []
        modules: set[str] = set()
        seen_prefixes: set[str] = set()

        for opg in opgs:
            nodes = list(opg.object_projection_graph_nodes or [])
            roots = [n for n in nodes if n.is_root]
            if len(roots) != 1:
                raise ValueError(f"Expected exactly one root node for OPG {opg.name!r}, found {len(roots)}")
            root_node = roots[0]
            root_cls = self._graph_classes_by_id.get(root_node.class_config_id)
            root_external_graph = None
            if root_node.class_config_id not in local_class_ids:
                root_external_graph = external_graph_by_class_id.get(root_node.class_config_id)
                if root_external_graph is not None:
                    for ext_node in root_external_graph.object_config_graph_nodes:
                        if ext_node.class_config is None:
                            continue
                        if ext_node.class_config.id == root_node.class_config_id:
                            root_cls = ext_node.class_config
                            break
            if root_cls is None:
                raise ValueError(f"Missing ClassConfig {root_node.class_config_id} for OPG {opg.name!r}")

            prefix = _safe_pascal_case(opg.name or "")
            if not prefix:
                raise ValueError(f"OPG name is empty for id={opg.id}")
            if prefix in seen_prefixes:
                raise ValueError(f"Duplicate OPG name after normalization: {prefix}")
            seen_prefixes.add(prefix)

            root_var = _safe_identifier(to_camel_case(root_cls.name))
            root_param = f"{root_var}ClassInstanceId"

            override = self.import_overrides.get(str(root_cls.id)) if self.import_overrides else None
            if override:
                module = override
            else:
                root_path = inner_layout.get_class_file_path(root_cls)
                if root_external_graph is None:
                    module = inner_layout.get_module_import_path(root_path)
                else:
                    rel = _external_class_relative_path(
                        graph=root_external_graph,
                        class_config=root_cls,
                    )
                    module = f"package:{_external_model_import_root(root_external_graph)}/{rel}"
            modules.add(module)

            entries.append(
                {
                    "opg_name": opg.name,
                    "prefix": prefix,
                    "root_class_name": root_cls.name,
                    "root_var": root_var,
                    "root_param": root_param,
                    "root_module": module,
                }
            )

        # External graph materializers: determine which external graphs are referenced by OPG nodes.
        needed_external_graphs_by_id: dict[UUID, ObjectConfigGraph] = {}
        for opg in opgs:
            for node in opg.object_projection_graph_nodes or []:
                class_id = node.class_config_id
                if class_id in local_class_ids:
                    continue
                ext_graph_ref = external_graph_by_class_id.get(class_id)
                if ext_graph_ref is None:
                    continue
                _ = needed_external_graphs_by_id.setdefault(ext_graph_ref.id, ext_graph_ref)

        import_root = self.layout_strategy.import_root
        if not import_root:
            raise ValueError("Dart OPG materialization requires import_root for model imports")

        aliases_by_module: dict[str, str] = {}
        used: set[str] = set()
        for module in sorted(modules):
            base = _safe_import_alias(module)
            alias = base
            i = 2
            while alias in used:
                alias = f"{base}_{i}"
                i += 1
            used.add(alias)
            aliases_by_module[module] = alias

        # Build import + alias table for external graph materializer modules.
        external_materializer_entries: list[dict[str, str]] = []
        for ext_graph in sorted(
            needed_external_graphs_by_id.values(),
            key=lambda g: ((g.fqn_prefix or ""), (g.name or ""), str(g.id)),
        ):
            if not ext_graph.fqn_prefix:
                continue
            ext_module_name = ext_graph.name
            if ext_module_name:
                ext_module_name = re.sub(r"[_-]aware$", "", ext_module_name, flags=re.IGNORECASE)
            ext_prefix = _safe_pascal_case(ext_module_name or "")
            if not ext_prefix:
                continue

            # Representation packages follow the canonical fqn_prefix (e.g. aware_content).
            module = f"package:{ext_graph.fqn_prefix}/_aware/materialization/materializers_opg.dart"

            alias_base = ext_graph.fqn_prefix
            if alias_base.startswith("aware_"):
                alias_base = alias_base[len("aware_"):]
            alias_base = alias_base.replace("-", "_")
            base_alias = _safe_identifier(f"{alias_base}_materializers")
            alias = base_alias
            i = 2
            while alias in used:
                alias = f"{base_alias}_{i}"
                i += 1
            used.add(alias)
            external_materializer_entries.append(
                {
                    "module": module,
                    "alias": alias,
                    "prefix": ext_prefix,
                }
            )

        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// OPG lane materializers and module materialization helpers.\n\n")

        _ = writer.token("import 'package:uuid/uuid_value.dart';\n")
        _ = writer.token("import 'package:aware_meta/graph/instance/commit_applier.dart';\n")
        _ = writer.token("import 'package:aware_meta/graph/instance/materialization_registry.dart';\n")
        _ = writer.token("import 'package:aware_meta/graph/instance/model_cache.dart';\n")
        _ = writer.token("import 'package:aware_meta/graph/instance/snapshot_index.dart';\n")

        for entry in external_materializer_entries:
            _ = writer.token(f"import '{entry['module']}' as {entry['alias']};\n")

        opg_path = Path(self.layout_strategy.base_dir) / _OUTPUT_REL_PATH
        manifest_path = opg_path.parent / "oig_materialization_manifest.dart"
        tables_path = opg_path.parent / "oig_materialization_tables.dart"
        manifest_import = _relative_import(opg_path, manifest_path)
        tables_import = _relative_import(opg_path, tables_path)
        _ = writer.token(f"import '{manifest_import}' as oig_manifest;\n")
        _ = writer.token(f"import '{tables_import}' as oig_tables;\n")

        for module in sorted(aliases_by_module.keys()):
            alias = aliases_by_module[module]
            _ = writer.token(f"import '{module}' as {alias};\n")

        _ = writer.token("\n")

        module_name = graph.name
        if module_name:
            module_name = re.sub(r"[_-]aware$", "", module_name, flags=re.IGNORECASE)
        module_prefix = _safe_pascal_case(module_name or "")
        if not module_prefix:
            module_prefix = "Module"

        _ = writer.token(
            f"void register{module_prefix}Materializations("
            + "ObjectInstanceGraphMaterializationRegistry registry) {\n"
        )
        if external_materializer_entries:
            _ = writer.token("  // External graph materializations (OPG nodes can span OCG dependencies).\n")
            for entry in external_materializer_entries:
                _ = writer.token(f"  {entry['alias']}.register{entry['prefix']}Materializations(registry);\n")
        _ = writer.token("  registry.registerAll(oig_manifest.oigMaterializationManifest);\n")
        _ = writer.token("  registry.registerAllForeignKeyBindings(\n")
        _ = writer.token("    oig_tables.oigForeignKeyBindingsByClassConfigId,\n")
        _ = writer.token("  );\n")
        _ = writer.token("  registry.registerAllRelationshipBindings(\n")
        _ = writer.token("    oig_tables.oigRelationshipBindingsByClassConfigId,\n")
        _ = writer.token("  );\n")
        _ = writer.token("  registry.registerAllRelationshipListPrototypes(\n")
        _ = writer.token("    oig_tables.oigRelationshipListPrototypesByKey,\n")
        _ = writer.token("  );\n")
        _ = writer.token("}\n")

        for entry in entries:
            opg_name = entry["opg_name"]
            prefix = entry["prefix"]
            root_var = entry["root_var"]
            root_param = entry["root_param"]
            root_class_name = entry["root_class_name"]
            root_module = entry["root_module"]
            alias = aliases_by_module[root_module]

            _ = writer.token("\n")
            _ = writer.token(f"const String k{prefix}OpgName = '{opg_name}';\n\n")

            _ = writer.token(f"class {prefix}LaneMaterialization {{\n")
            _ = writer.token(f"  const {prefix}LaneMaterialization({{\n")
            _ = writer.token("    required this.snapshot,\n")
            _ = writer.token("    required this.index,\n")
            _ = writer.token("    required this.cache,\n")
            _ = writer.token(f"    required this.{root_var},\n")
            _ = writer.token("  });\n\n")
            _ = writer.token("  final ObjectInstanceGraphSnapshot snapshot;\n")
            _ = writer.token("  final ObjectInstanceGraphSnapshotIndex index;\n")
            _ = writer.token("  final ObjectInstanceGraphModelCache cache;\n")
            _ = writer.token(f"  final {alias}.{root_class_name} {root_var};\n")
            _ = writer.token("}\n\n")

            _ = writer.token(f"class {prefix}LaneMaterializer {{\n")
            _ = writer.token(f"  {prefix}LaneMaterializer({{required this.registry}});\n\n")
            _ = writer.token("  final ObjectInstanceGraphMaterializationRegistry registry;\n\n")
            _ = writer.token(f"  {prefix}LaneMaterialization materialize({{\n")
            _ = writer.token("    required ObjectInstanceGraphSnapshot snapshot,\n")
            _ = writer.token(f"    UuidValue? {root_param},\n")
            _ = writer.token("  }) {\n")
            _ = writer.token("    final index = ObjectInstanceGraphSnapshotIndex(snapshot: snapshot);\n")
            _ = writer.token("    final cache = ObjectInstanceGraphModelCache(index: index, registry: registry);\n\n")
            _ = writer.token(f"    final rootId = {root_param} ?? snapshot.rootClassInstanceId;\n")
            _ = writer.token("    if (rootId == null) {\n")
            _ = writer.token(
                f"      throw StateError('{prefix} lane snapshot is missing "
                + f"rootClassInstanceId; provide {root_param} explicitly');\n"
            )
            _ = writer.token("    }\n\n")
            _ = writer.token(
                f"    final {root_var} = cache.materializeAs<{alias}.{root_class_name}>("
                + "classInstanceId: rootId);\n"
            )
            _ = writer.token(f"    return {prefix}LaneMaterialization(\n")
            _ = writer.token("      snapshot: snapshot,\n")
            _ = writer.token("      index: index,\n")
            _ = writer.token("      cache: cache,\n")
            _ = writer.token(f"      {root_var}: {root_var},\n")
            _ = writer.token("    );\n")
            _ = writer.token("  }\n")
            _ = writer.token("}\n")


__all__ = ["DartMaterializationOpgRenderer"]

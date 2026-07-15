"""
Dart OIG materialization manifest renderer.

Emits a single manifest map keyed by ClassConfigId so callers can dispatch from a
`ClassInstance` (OIG) to the correct Dart model `fromClassInstance`.

The registry machinery itself lives in the Interface API package; this renderer
only emits the per-environment UUID -> factory bindings.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

from aware_code.section.writer import CodeSectionWriter
from aware_meta_ontology.class_.class_config import ClassConfig
from typing_extensions import override
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

from dart_grammar.layout_strategy import DartFixedFileLayoutStrategy, DartOigMaterializationLayoutStrategy
from dart_grammar.renderer import DartRenderer


_OUTPUT_REL_PATH = Path("_aware/materialization/oig_materialization_manifest.dart")

_API_OIG_REGISTRY_IMPORT = "package:aware_meta/graph/instance/materialization_registry.dart"


def _safe_import_alias(module: str) -> str:
    # Convert `package:foo/a/b.dart` or `a/b.dart` into a stable identifier.
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


def _relative_import(from_path: Path, to_path: Path) -> str:
    rel = os.path.relpath(to_path, start=from_path.parent)
    return rel.replace(os.path.sep, "/")


class DartMaterializationRegistryRenderer(DartRenderer):
    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy) -> None:
        fixed = DartFixedFileLayoutStrategy(parent=layout_strategy, rel_path=_OUTPUT_REL_PATH)
        super().__init__(layout_strategy=fixed)

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
        _ = class_to_class_config_map
        _ = base_class_module
        _ = base_class_name

        classes = sorted([obj for obj in meta_objects if isinstance(obj, ClassConfig)], key=lambda c: c.name)
        if not classes:
            return

        # Skip discriminated-union variant-only classes (not emitted standalone).
        union_by_base_id: Mapping[UUID, object] = self._discriminated_unions_by_base_id
        base_id_by_variant_id: dict[UUID, UUID] = self._discriminated_union_base_id_by_variant_id

        def is_variant_only(cls_cfg: ClassConfig) -> bool:
            base_id = base_id_by_variant_id.get(cls_cfg.id)
            if base_id is None:
                return False
            return cls_cfg.id not in union_by_base_id

        classes = [c for c in classes if not is_variant_only(c)]
        if not classes:
            return

        inner_layout = self.layout_strategy.get_parent()
        if inner_layout is None:
            raise ValueError("No parent layout strategy found")

        oig_layout = DartOigMaterializationLayoutStrategy.from_parent(inner_layout)

        # Build import table: module -> alias, keep it deterministic.
        registry_path = self.layout_strategy.get_class_file_path(classes[0])

        module_by_class_id: dict[str, str] = {}
        for cls in classes:
            ext_path = oig_layout.get_class_file_path(cls)
            module = _relative_import(registry_path, ext_path)
            module_by_class_id[str(cls.id)] = module

        aliases_by_module: dict[str, str] = {}
        used: set[str] = set()
        for module in sorted(set(module_by_class_id.values())):
            base = _safe_import_alias(module)
            alias = base
            i = 2
            while alias in used:
                alias = f"{base}_{i}"
                i += 1
            used.add(alias)
            aliases_by_module[module] = alias

        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// OIG materialization manifest (ClassConfigId -> fromClassInstance factory).\n\n")

        _ = writer.token(f"import '{_API_OIG_REGISTRY_IMPORT}' show OigFactory;\n")
        _ = writer.token("import 'package:aware_meta_ontology/class_/class_instance.dart';\n")
        for module in sorted(aliases_by_module.keys()):
            alias = aliases_by_module[module]
            _ = writer.token(f"import '{module}' as {alias};\n")

        _ = writer.token("\n")
        _ = writer.token("final Map<String, OigFactory> oigMaterializationManifest = {\n")
        for cls in classes:
            class_id = str(cls.id)
            module = module_by_class_id[class_id]
            alias = aliases_by_module[module]
            ext_name = f"{cls.name}OigMaterialization"
            _ = writer.token(f"  '{class_id}': ({{required Object instance}}) => ")
            _ = writer.token(f"{alias}.{ext_name}.fromClassInstance(instance: instance as ClassInstance),\n")
        _ = writer.token("};\n")


__all__ = ["DartMaterializationRegistryRenderer"]

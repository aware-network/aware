"""
Dart API barrel renderer.

For each ClassConfig canonical module `<name>.dart`, emit a small barrel library that
exports:
- `<name>_model.dart` (Freezed/JsonSerializable model library)
- `<name>_oig.dart` (OIG -> model materialization extension)
- `<name>_functions.dart` (EnvClient-backed methods) when present

This standardizes imports for consumers: `import '<name>.dart'` yields the model and
canonical extensions without generating shared logic into ontology packages.
"""

from __future__ import annotations

from uuid import UUID

from aware_code.section.writer import CodeSectionWriter
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from typing_extensions import override

from dart_grammar.renderer import DartRenderer


class DartApiBarrelRenderer(DartRenderer):
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
        classes_all = list(classes)

        # Skip discriminated-union variant-only classes (they are emitted within their base union file).
        def is_variant_only(cls_cfg: ClassConfig) -> bool:
            base_id = self._discriminated_union_base_id_by_variant_id.get(cls_cfg.id)
            if base_id is None:
                return False
            return cls_cfg.id not in self._discriminated_unions_by_base_id.keys()

        classes = [c for c in classes if not is_variant_only(c)]
        if not classes:
            return

        # Determine the canonical basename from the barrel file path.
        barrel_path = self.layout_strategy.get_class_file_path(classes[0])
        basename = barrel_path.stem

        has_functions = any(cls.class_config_function_configs for cls in classes)
        has_enums = any(isinstance(obj, EnumConfig) for obj in meta_objects)
        expected_enums_path = barrel_path.with_name(f"{basename}_enums{barrel_path.suffix}")
        if not has_enums:
            # Some layouts assign enums to dedicated `*_enums.dart` modules that are not part of
            # the class module's meta_objects. Detect those by checking enum file paths.
            for enum_cfg in self._graph_enums_by_id.values():
                enum_path = self.layout_strategy.get_enum_file_path(enum_cfg)
                # Enum file path can either already be redirected to `*_enums.dart` OR still
                # point at the canonical module (which will be redirected by model renderers).
                if enum_path == expected_enums_path or enum_path == barrel_path:
                    has_enums = True
                    break

        _ = writer.token("// coverage:ignore-file\n")
        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// ignore_for_file: type=lint\n\n")

        # Export subordinate module barrels when referenced by this module's public API.
        #
        # Example: `environment.dart` exposes `EnvironmentServiceOperation` in request/response API models,
        # which lives in `environment_service_operation.dart`. Without re-export, consumers need an
        # extra import even though the type is part of the environment API surface.
        dependent_barrel_stems: set[str] = set()

        class_index: dict[UUID, ClassConfig] = {}
        if class_to_class_config_map is not None:
            class_index.update(class_to_class_config_map)
        class_index.update(self._graph_classes_by_id.items())
        class_index_by_str: dict[str, ClassConfig] = {str(k): v for k, v in class_index.items()}

        def _collect_class_ids(desc: AttributeTypeDescriptor) -> set[UUID]:
            ids: set[UUID] = set()
            if desc.kind == AttributeTypeDescriptorKind.class_ and desc.class_config_id is not None:
                ids.add(desc.class_config_id)
            for link in desc.child_links:
                ids.update(_collect_class_ids(link.child))
            return ids

        # Include union variant classes for dependency scanning even if they are not
        # assigned to this module by the layout strategy (Freezed unions inline them).
        scan_classes: list[ClassConfig] = list(classes_all)
        for base_cls in classes_all:
            union = self._discriminated_unions_by_base_id.get(base_cls.id)
            if union is None:
                continue
            for variant in union.variants:
                scan_classes.append(variant.class_config)

        for cls_cfg in scan_classes:
            for class_config_attribute_config in cls_cfg.class_config_attribute_configs:
                attr = class_config_attribute_config.attribute_config
                dep_ids = _collect_class_ids(attr.type_descriptor)
                # Fallback: some profiles may omit FK wiring on descriptor nodes but still
                # side-load the resolved ClassConfig relationship.
                if not dep_ids:
                    info = resolve_type_info(attr)
                    if info.kind == AttributeTypeDescriptorKind.class_ and info.class_config is not None:
                        dep_ids.add(info.class_config.id)
                for dep_id in dep_ids:
                    dep_cls = class_index.get(dep_id) or class_index_by_str.get(str(dep_id))
                    if dep_cls is None:
                        continue
                    dep_path = self.layout_strategy.get_class_file_path(dep_cls)

                    # Only re-export subordinate modules in the same folder that follow the
                    # `<basename>_...` naming convention to avoid circular export graphs.
                    if dep_path.parent != barrel_path.parent:
                        continue
                    dep_stem = dep_path.stem
                    if dep_stem == basename:
                        continue
                    if not dep_stem.startswith(f"{basename}_"):
                        continue
                    dependent_barrel_stems.add(dep_stem)

        if has_enums:
            _ = writer.token(f"export '{expected_enums_path.name}';\n")
        _ = writer.token(f"export '{basename}_model.dart';\n")
        if has_functions:
            _ = writer.token(f"export '{basename}_functions.dart';\n")
        if self.policy.export_oig_extensions:
            _ = writer.token(f"export '{basename}_oig.dart';\n")
        for dep_stem in sorted(dependent_barrel_stems):
            _ = writer.token(f"export '{dep_stem}.dart';\n")


__all__ = ["DartApiBarrelRenderer"]

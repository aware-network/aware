"""
Dart OIG materialization tables renderer.

Emits a single helper module under `_aware/materialization/` containing:
- EnumOptionId -> wire-value lookup tables (per EnumConfig)
- Foreign-key binding tables derived from ClassConfigRelationshipAttribute(role=FOREIGN_KEY)

This file is intentionally "tokens only": shared decoding logic lives in the
Interface API package, and only per-environment UUID/value tables are emitted
here.
"""

from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID

from aware_code.section.writer import CodeSectionWriter
from typing_extensions import override
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_config_overlay import AttributeConfigOverlay
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_utils.string_transform import to_camel_case
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

from dart_grammar.layout_strategy import DartFixedFileLayoutStrategy
from dart_grammar.renderer import DartRenderer


_OUTPUT_REL_PATH = Path("_aware/materialization/oig_materialization_tables.dart")


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


class DartMaterializationSupportRenderer(DartRenderer):
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

        used_enums: dict[UUID, EnumConfig] = {}
        for cls in classes:
            for edge in sorted(cls.class_config_attribute_configs, key=lambda a: a.position):
                attr = edge.attribute_config
                type_info = resolve_type_info(attr)
                if type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config is not None:
                    used_enums[type_info.enum_config.id] = type_info.enum_config

        enums = sorted(used_enums.values(), key=lambda e: e.name)

        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// OIG materialization tables (tokens only).\n\n")

        # Relationship list prototypes require referencing Dart model types.
        imports_by_module = self._collect_relationship_prototype_imports(classes)
        if imports_by_module:
            for module in sorted(imports_by_module.keys()):
                _ = writer.token(f"import '{module}' as {imports_by_module[module]};\n")
            _ = writer.token("\n")

        if enums:
            _ = writer.token("// Enum option lookup tables (EnumOption.id -> EnumOption.value)\n\n")
        for enum_cfg in enums:
            self._emit_enum_option_value_map(writer, enum_cfg)

        # Relationship-derived "FK" fields are a projection convenience in Dart models; commits are edge-truth.
        # These bindings allow the client to deterministically derive FK attribute payloads from
        # ClassInstanceRelationship edges without name heuristics.
        self._emit_foreign_key_bindings(writer, classes)
        self._emit_relationship_bindings(writer, classes)
        self._emit_relationship_list_prototypes(writer, classes, imports_by_module)

    def _emit_enum_option_value_map(self, writer: CodeSectionWriter, enum_cfg: EnumConfig) -> None:
        enum_name = enum_cfg.name
        const_name = f"_enumOptionValueById{enum_name}"
        fn_name = f"enumOptionValueFor{enum_name}"

        _ = writer.token(f"const Map<String, String> {const_name} = {{\n")
        # Stable ordering: position then value then id
        options = sorted(enum_cfg.enum_options, key=lambda o: (o.position, o.value, str(o.id)))
        for opt in options:
            opt_id = str(opt.id)
            val = opt.value.replace("'", "\\'")
            _ = writer.token(f"  '{opt_id}': '{val}',\n")
        _ = writer.token("};\n\n")

        _ = writer.token(f"String? {fn_name}(String optionId) {{\n")
        _ = writer.token(f"  return {const_name}[optionId];\n")
        _ = writer.token("}\n\n")

    def _emit_foreign_key_bindings(self, writer: CodeSectionWriter, classes: list[ClassConfig]) -> None:
        # Build AttributeConfigId -> owning ClassConfigId so reverse-direction relationship attributes
        # are attributed to the correct class (relationships are declared single-sided in canonical mode).
        owner_by_attr_id: dict[UUID, UUID] = {}
        for cls in classes:
            for edge in cls.class_config_attribute_configs:
                attr = edge.attribute_config
                owner_by_attr_id[attr.id] = cls.id

        # Some FK fields are deterministically derivable from the snapshot context (not from edges),
        # e.g. `object_instance_graph_id` is the lane's `oigId`. We encode this as a fallback policy
        # so runtime hydration stays non-heuristic.
        oig_class_ids: set[UUID] = {c.id for c in classes if (c.name or "").strip() == "ObjectInstanceGraph"}

        bindings_by_class_id: dict[UUID, set[tuple[str, str, str, str]]] = {}

        for cls in classes:
            for rel in cls.class_config_relationships:
                for rel_attr in rel.class_config_relationship_attributes:
                    if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                        continue
                    owner_class_id = owner_by_attr_id.get(rel_attr.attribute_config_id)
                    if owner_class_id is None:
                        continue
                    fallback = ""
                    if (
                        oig_class_ids
                        and rel.class_config_id in oig_class_ids
                        and rel_attr.direction == ClassConfigRelationshipDirection.reverse
                    ):
                        fallback = "snapshot_oig_id"
                    bindings_by_class_id.setdefault(owner_class_id, set()).add(
                        (
                            str(rel_attr.attribute_config_id),
                            str(rel_attr.class_config_relationship_id),
                            rel_attr.direction.value,
                            fallback,
                        )
                    )

        # Always emit this table even if empty so representation-only outputs (e.g. OPG lane materializers)
        # can import and call `registerAllForeignKeyBindings(...)` without conditional logic.
        _ = writer.token("// Foreign-key bindings (ClassConfigId -> derived FK attribute payloads)\n")
        _ = writer.token(
            "// Each entry maps an AttributeConfigId (FK field) to a ClassConfigRelationshipId and direction.\n"
        )
        _ = writer.token(
            "// Clients use these bindings to inject synthetic AttributeValue payloads from relationship edges.\n\n"
        )

        _ = writer.token("const Map<String, List<Map<String, String>>> oigForeignKeyBindingsByClassConfigId = {\n")
        for class_id in sorted(bindings_by_class_id.keys(), key=lambda u: str(u)):
            bindings = sorted(bindings_by_class_id[class_id], key=lambda t: (t[0], t[1], t[2], t[3]))
            _ = writer.token(f"  '{class_id}': const <Map<String, String>>[\n")
            for attr_id, rel_id, direction, fallback in bindings:
                _ = writer.token("    const <String, String>{\n")
                _ = writer.token(f"      'attribute_config_id': '{attr_id}',\n")
                _ = writer.token(f"      'class_config_relationship_id': '{rel_id}',\n")
                _ = writer.token(f"      'direction': '{direction}',\n")
                if fallback:
                    _ = writer.token(f"      'fallback': '{fallback}',\n")
                _ = writer.token("    },\n")
            _ = writer.token("  ],\n")
        _ = writer.token("};\n\n")

    # ---------------------------------------------------------------------
    # Relationship bindings (relationship object fields)
    # ---------------------------------------------------------------------

    def _collect_relationship_prototype_imports(self, classes: list[ClassConfig]) -> dict[str, str]:
        """
        Collect `package:` imports needed for relationship list prototype types.

        We only import types for `many` relationships (list fields). Single-object relationships
        can be hydrated without compile-time type references.
        """

        parent = self.layout_strategy.get_parent()
        if parent is None:
            return {}
        model_layout = parent.get_parent() or parent

        def _module_for_class(cls_cfg: ClassConfig) -> str | None:
            if self.import_overrides:
                override = self.import_overrides.get(str(cls_cfg.id))
                if override:
                    return override
            try:
                path = model_layout.get_class_file_path(cls_cfg)
                return model_layout.get_module_import_path(path)
            except Exception:
                return None

        attr_by_id: dict[UUID, AttributeConfig] = {}
        for cls in classes:
            for edge in cls.class_config_attribute_configs:
                attr = edge.attribute_config
                attr_by_id[attr.id] = attr

        used_modules: set[str] = set()
        for cls in classes:
            for rel in cls.class_config_relationships:
                for rel_attr in rel.class_config_relationship_attributes:
                    if rel_attr.role != ClassConfigRelationshipAttributeRole.reference:
                        continue
                    ref_attr = attr_by_id.get(rel_attr.attribute_config_id)
                    if ref_attr is None:
                        continue
                    type_info = resolve_type_info(ref_attr)
                    if type_info.kind != AttributeTypeDescriptorKind.class_ or type_info.class_config is None:
                        continue
                    if not bool(type_info.is_collection):
                        continue
                    module = _module_for_class(type_info.class_config)
                    if module:
                        used_modules.add(module)

        aliases_by_module: dict[str, str] = {}
        used_aliases: set[str] = set()
        for module in sorted(used_modules):
            base = _safe_import_alias(module)
            alias = base
            i = 2
            while alias in used_aliases:
                alias = f"{base}_{i}"
                i += 1
            used_aliases.add(alias)
            aliases_by_module[module] = alias

        return aliases_by_module

    def _emit_relationship_bindings(self, writer: CodeSectionWriter, classes: list[ClassConfig]) -> None:
        """
        Emit relationship bindings for hydrating relationship object fields from snapshot edges.

        Contract:
        - Use `ClassConfigRelationshipAttribute(role=reference)` to identify relationship object fields.
        - `field_name` must match the Dart `copyWith(...)` named parameter (camelCase + overlays).
        - `cardinality` is derived from the reference attribute's descriptor (one vs many).
        """

        owner_by_attr_id: dict[UUID, UUID] = {}
        attr_by_id: dict[UUID, AttributeConfig] = {}
        for cls in classes:
            for edge in cls.class_config_attribute_configs:
                attr = edge.attribute_config
                owner_by_attr_id[attr.id] = cls.id
                attr_by_id[attr.id] = attr

        bindings_by_class_id: dict[UUID, set[tuple[str, str, str, str]]] = {}

        for cls in classes:
            for rel in cls.class_config_relationships:
                for rel_attr in rel.class_config_relationship_attributes:
                    if rel_attr.role != ClassConfigRelationshipAttributeRole.reference:
                        continue
                    owner_class_id = owner_by_attr_id.get(rel_attr.attribute_config_id)
                    if owner_class_id is None:
                        continue
                    ref_attr = attr_by_id.get(rel_attr.attribute_config_id)
                    if ref_attr is None:
                        continue

                    type_info = resolve_type_info(ref_attr)
                    if type_info.kind != AttributeTypeDescriptorKind.class_ or type_info.class_config is None:
                        continue

                    field_name = to_camel_case(ref_attr.name)
                    overlay = self.get_overlay_by_entity_id(
                        CodeSectionAnnotationOverlayEntity.attribute,
                        ref_attr.id,
                    )
                    if overlay is not None:
                        if not isinstance(overlay, AttributeConfigOverlay):
                            raise ValueError(f"Overlay for attribute {ref_attr.id} is not an AttributeConfigOverlay")
                        if overlay.rendered_name:
                            field_name = overlay.rendered_name

                    cardinality = "many" if bool(type_info.is_collection) else "one"
                    bindings_by_class_id.setdefault(owner_class_id, set()).add(
                        (
                            field_name,
                            str(rel_attr.class_config_relationship_id),
                            rel_attr.direction.value,
                            cardinality,
                        )
                    )

        _ = writer.token("// Relationship bindings (ClassConfigId -> relationship field hydration)\n")
        _ = writer.token(
            "// Each entry maps a Dart model field name to a ClassConfigRelationshipId, "
            + "traversal direction, and cardinality.\n\n"
        )
        _ = writer.token("const Map<String, List<Map<String, String>>> oigRelationshipBindingsByClassConfigId = {\n")
        for class_id in sorted(bindings_by_class_id.keys(), key=lambda u: str(u)):
            bindings = sorted(bindings_by_class_id[class_id], key=lambda t: (t[0], t[1], t[2], t[3]))
            _ = writer.token(f"  '{class_id}': const <Map<String, String>>[\n")
            for field_name, rel_id, direction, cardinality in bindings:
                _ = writer.token("    const <String, String>{\n")
                _ = writer.token(f"      'field_name': '{field_name}',\n")
                _ = writer.token(f"      'class_config_relationship_id': '{rel_id}',\n")
                _ = writer.token(f"      'direction': '{direction}',\n")
                _ = writer.token(f"      'cardinality': '{cardinality}',\n")
                _ = writer.token("    },\n")
            _ = writer.token("  ],\n")
        _ = writer.token("};\n\n")

    def _emit_relationship_list_prototypes(
        self,
        writer: CodeSectionWriter,
        classes: list[ClassConfig],
        imports_by_module: dict[str, str],
    ) -> None:
        """
        Emit typed empty-list prototypes for `many` relationship fields.

        Rationale:
        - Freezed `copyWith` casts list fields using `as List<T>`, which requires the list to be typed.
        - Runtime hydration code is type-agnostic, so we provide typed prototypes here and use them
          to build `List<T>` values without reflection.
        """

        parent = self.layout_strategy.get_parent()
        model_layout = parent.get_parent() if parent is not None else None
        if model_layout is None and parent is not None:
            model_layout = parent

        def _module_for_class(cls_cfg: ClassConfig) -> str | None:
            if self.import_overrides:
                override = self.import_overrides.get(str(cls_cfg.id))
                if override:
                    return override
            if model_layout is None:
                return None
            try:
                path = model_layout.get_class_file_path(cls_cfg)
                return model_layout.get_module_import_path(path)
            except Exception:
                return None

        owner_by_attr_id: dict[UUID, UUID] = {}
        attr_by_id: dict[UUID, AttributeConfig] = {}
        for cls in classes:
            for edge in cls.class_config_attribute_configs:
                attr = edge.attribute_config
                owner_by_attr_id[attr.id] = cls.id
                attr_by_id[attr.id] = attr

        prototypes: dict[str, tuple[str, str]] = {}
        for cls in classes:
            for rel in cls.class_config_relationships:
                for rel_attr in rel.class_config_relationship_attributes:
                    if rel_attr.role != ClassConfigRelationshipAttributeRole.reference:
                        continue
                    owner_class_id = owner_by_attr_id.get(rel_attr.attribute_config_id)
                    if owner_class_id is None:
                        continue
                    ref_attr = attr_by_id.get(rel_attr.attribute_config_id)
                    if ref_attr is None:
                        continue
                    type_info = resolve_type_info(ref_attr)
                    if type_info.kind != AttributeTypeDescriptorKind.class_ or type_info.class_config is None:
                        continue
                    if not bool(type_info.is_collection):
                        continue
                    module = _module_for_class(type_info.class_config)
                    if not module:
                        continue
                    alias = imports_by_module.get(module)
                    if not alias:
                        continue

                    field_name = to_camel_case(ref_attr.name)
                    overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.attribute, ref_attr.id)
                    if overlay is not None:
                        if not isinstance(overlay, AttributeConfigOverlay):
                            raise ValueError(f"Overlay for attribute {ref_attr.id} is not an AttributeConfigOverlay")
                        if overlay.rendered_name:
                            field_name = overlay.rendered_name

                    key = f"{owner_class_id}:{field_name}"
                    prototypes[key] = (alias, type_info.class_config.name)

        _ = writer.token("// Relationship list prototypes (ClassConfigId:field_name -> typed empty list)\n")
        _ = writer.token(
            "// Clients use these to build `List<T>` values for Freezed copyWith without importing ontology types.\n\n"
        )
        _ = writer.token("const Map<String, Object> oigRelationshipListPrototypesByKey = {\n")
        for key in sorted(prototypes.keys()):
            alias, type_name = prototypes[key]
            _ = writer.token(f"  '{key}': const <{alias}.{type_name}>[],\n")
        _ = writer.token("};\n\n")


__all__ = ["DartMaterializationSupportRenderer"]

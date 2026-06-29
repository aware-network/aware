"""
Dart OIG materialization renderer.

Emits `*_oig.dart` extension files that provide `fromClassInstance` constructors for each
ClassConfig. The generated code is intentionally "IDs + attributes" first:
- Scalar attributes are decoded from AttributeValue trees and fed into `fromJson`.
- Relationship object fields (CLASS descriptors) are not populated by these factories.
  They are hydrated deterministically from snapshot relationship edges by the Dart runtime
  (`ObjectInstanceGraphModelCache`) using generated relationship binding tables.

Dispatch is handled separately via a registry renderer keyed by ClassConfigId.
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

from aware_code.section.writer import CodeSectionWriter
from typing_extensions import override

from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_config_overlay import AttributeConfigOverlay
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info

from dart_grammar.layout_strategy import DartOigMaterializationLayoutStrategy
from dart_grammar.renderer import DartRenderer


_KERNEL_OIG_IMPORTS = [
    "package:aware_meta_ontology/attribute/attribute.dart",
    "package:aware_meta_ontology/class_/class_instance.dart",
]

_API_OIG_SUPPORT_IMPORT = "package:aware_meta/graph/instance/materialization_support.dart"
_OIG_TABLES_REL_PATH = Path("_aware/materialization/oig_materialization_tables.dart")


def _relative_import(from_path: Path, to_path: Path) -> str:
    rel = os.path.relpath(to_path, start=from_path.parent)
    return rel.replace(os.path.sep, "/")


class DartMaterializationRenderer(DartRenderer):
    """
    Emit `*_oig.dart` extension modules that provide `fromClassInstance`.

    The implementation targets the canonical instance graph types:
    - `ClassInstance` (has `id`, `classConfigId`, `attributes`)
    - `Attribute` (has `attributeConfigId`, `valueRoot`)
    - `AttributeValue` (descriptor-driven value tree nodes)
    """

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy) -> None:
        oig_layout = DartOigMaterializationLayoutStrategy.from_parent(layout_strategy)
        super().__init__(layout_strategy=oig_layout)
        self._enum_tables_alias_by_enum_id: dict[UUID, str] = {}

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

        # Relationship-driven loading semantics:
        # - Lazy relationship reference attributes may be absent and must also be treated as runtime-optional.
        for obj in meta_objects:
            if not isinstance(obj, ClassConfigRelationship):
                continue
            self._rels_by_source_class_id.setdefault(obj.class_config_id, []).append(obj)
            for ra in obj.class_config_relationship_attributes:
                if ra.role != ClassConfigRelationshipAttributeRole.reference:
                    continue
                if ra.direction == ClassConfigRelationshipDirection.forward:
                    if obj.forward_loading_strategy == ClassConfigRelationshipSideLoadingStrategy.lazy:
                        self._lazy_attr_ids.add(ra.attribute_config_id)
                elif ra.direction == ClassConfigRelationshipDirection.reverse:
                    if obj.reverse_loading_strategy == ClassConfigRelationshipSideLoadingStrategy.lazy:
                        self._lazy_attr_ids.add(ra.attribute_config_id)

        classes = sorted([obj for obj in meta_objects if isinstance(obj, ClassConfig)], key=lambda c: c.name)
        if not classes:
            return

        # Skip discriminated-union variant-only classes (they are not emitted standalone in DartRenderer).
        def is_variant_only(cls_cfg: ClassConfig) -> bool:
            base_id = self._discriminated_union_base_id_by_variant_id.get(cls_cfg.id)
            if base_id is None:
                return False
            return cls_cfg.id not in self._discriminated_unions_by_base_id

        classes = [c for c in classes if not is_variant_only(c)]
        if not classes:
            return

        inner_layout = self.layout_strategy.get_parent()
        if inner_layout is None:
            raise ValueError("No parent layout strategy found")

        oig_path = self.layout_strategy.get_class_file_path(classes[0])
        model_module: str | None = None
        try:
            model_path = inner_layout.get_class_file_path(classes[0])
            model_module = inner_layout.get_module_import_path(model_path)
        except Exception:
            model_module = None

        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// OIG materialization extensions for Dart OCG objects.\n\n")

        if model_module is not None:
            _ = writer.token(f"import '{model_module}';\n")

        for imp in _KERNEL_OIG_IMPORTS:
            _ = writer.token(f"import '{imp}';\n")

        _ = writer.token(f"import '{_API_OIG_SUPPORT_IMPORT}' as oig;\n")

        # Enum decoding requires EnumOption.id -> wire-value lookup tables.
        #
        # IMPORTANT:
        # - Enums can be imported from dependency graphs (e.g. CodeLanguage, ChangeType).
        # - Table functions are generated in the owning representation package under `_aware/materialization/...`.
        # - We must import the correct package tables module per enum to avoid missing symbols.
        used_enum_cfgs: dict[UUID, EnumConfig] = {}
        for cls in classes:
            for acc in sorted(cls.class_config_attribute_configs, key=lambda x: x.position):
                type_info = resolve_type_info(acc.attribute_config)
                if type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config is not None:
                    used_enum_cfgs[type_info.enum_config.id] = type_info.enum_config

        if used_enum_cfgs:
            tables_path = Path(inner_layout.base_dir) / _OIG_TABLES_REL_PATH
            local_tables_module = _relative_import(oig_path, tables_path)
            _ = writer.token(f"import '{local_tables_module}' as oig_tables;\n")
            self._enum_tables_alias_by_enum_id = {enum_id: "oig_tables" for enum_id in used_enum_cfgs.keys()}

        _ = writer.token("\n")

        for cls in classes:
            self._emit_class_materializer(writer, cls)

    def _emit_class_materializer(self, writer: CodeSectionWriter, cls: ClassConfig) -> None:
        class_name = cls.name
        ext_name = f"{class_name}OigMaterialization"
        class_config_id = str(cls.id)

        _ = writer.token(f"extension {ext_name} on {class_name} {{\n")
        _ = writer.token(f"  static {class_name} fromClassInstance({{required ClassInstance instance}}) {{\n")
        _ = writer.token("    // Safety: ensure the caller dispatches by ClassConfigId.\n")
        _ = writer.token("    if (instance.classConfigId.toString() != ")
        _ = writer.token(f"'{class_config_id}'")
        _ = writer.token(") {\n")
        _ = writer.token("      throw StateError('fromClassInstance: expected classConfigId ")
        _ = writer.token(f"{class_config_id}")
        _ = writer.token(" but got ' + instance.classConfigId.toString());\n")
        _ = writer.token("    }\n\n")

        _ = writer.token("    final attrsByConfigId = <String, Attribute>{};\n")
        _ = writer.token("    for (final a in instance.attributes) {\n")
        _ = writer.token("      attrsByConfigId[a.attributeConfigId.toString()] = a;\n")
        _ = writer.token("    }\n\n")

        _ = writer.token("    final json = <String, dynamic>{};\n")
        _ = writer.token("    json['id'] = instance.id.uuid;\n")

        # Sort AttributeConfigs by position for deterministic output
        attribute_configs = sorted(cls.class_config_attribute_configs, key=lambda x: x.position)

        # Emit scalar attributes (PRIMITIVE/ENUM); relationship object fields (CLASS) are ignored for now.
        for link in attribute_configs:
            attr = link.attribute_config
            if attr.name == "id":
                continue
            type_info = resolve_type_info(attr)
            if type_info.kind == AttributeTypeDescriptorKind.class_:
                continue
            if type_info.kind not in (AttributeTypeDescriptorKind.primitive, AttributeTypeDescriptorKind.enum):
                continue

            wire_name = self._resolve_wire_name(attr)
            value_expr = f"attrsByConfigId['{attr.id}']?.valueRoot"

            decode_expr = self._render_json_decode_expression(attr_config=attr, value_expr=value_expr)
            _ = writer.token(f"    json['{wire_name}'] = {decode_expr};\n")

        _ = writer.token("\n")
        _ = writer.token(f"    return {class_name}.fromJson(json);\n")
        _ = writer.token("  }\n")
        _ = writer.token("}\n\n")

    def _resolve_wire_name(self, attr_config: AttributeConfig) -> str:
        wire_name = attr_config.name
        overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.attribute, attr_config.id)
        if overlay is not None:
            if not isinstance(overlay, AttributeConfigOverlay):
                raise ValueError(f"Overlay for attribute {attr_config.id} is not an AttributeConfigOverlay")
            if overlay.wire_name:
                wire_name = overlay.wire_name
        return wire_name

    def _render_json_decode_expression(self, *, attr_config: AttributeConfig, value_expr: str) -> str:
        """
        Render a Dart expression that produces a JSON-compatible value for `attr_config`.

        The generated `fromClassInstance` implementations call `<Model>.fromJson`, so this returns
        primitive JSON types:
        - UUID/DateTime/Bytes => String
        - enums => String (wire value)
        - JSON => Map<String, dynamic>
        - collections => List<...>
        """
        type_info = resolve_type_info(attr_config)
        is_optional = self._is_optional_on_runtime(attr_config) or bool(type_info.nullable)

        def _call(name: str) -> str:
            return f"oig.{name}({value_expr})"

        # Collections: emit List<...> JSON values.
        if type_info.collection_kind == AttributeCollectionType.list:
            element_expr = self._render_leaf_json_decode_expression(attr_config=attr_config, leaf_expr="leaf")
            fn = "decodeListOrNull" if is_optional else "decodeList"
            return f"oig.{fn}({value_expr}, (leaf) => {element_expr})"

        # Sets are not currently emitted as model fields in DartRenderer; support anyway for future.
        if type_info.collection_kind == AttributeCollectionType.set:
            element_expr = self._render_leaf_json_decode_expression(attr_config=attr_config, leaf_expr="leaf")
            fn = "decodeSetOrNull" if is_optional else "decodeSet"
            return f"oig.{fn}({value_expr}, (leaf) => {element_expr})"

        # Leaf: ENUM
        if type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config is not None:
            enum_cfg = type_info.enum_config
            enum_name = enum_cfg.name
            alias = self._enum_tables_alias_by_enum_id.get(enum_cfg.id, "oig_tables")
            mapper = f"{alias}.enumOptionValueFor{enum_name}"
            fn = "decodeEnumWireOrNull" if is_optional else "decodeEnumWire"
            return f"oig.{fn}({value_expr}, {mapper})"

        # Leaf: PRIMITIVE
        leaf_fn = self._leaf_decoder_name(attr_config, optional=is_optional)
        if leaf_fn is None:
            # Fallback: return raw primitive payload for debugging (may be null).
            return _call("primitivePayloadOrNull")
        return _call(leaf_fn)

    def _render_leaf_json_decode_expression(self, *, attr_config: AttributeConfig, leaf_expr: str) -> str:
        """
        Render a leaf decode expression where `leaf_expr` is an AttributeValue node.

        This is used inside collection decoders.
        """
        type_info = resolve_type_info(attr_config)
        if type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config is not None:
            enum_cfg = type_info.enum_config
            enum_name = enum_cfg.name
            alias = self._enum_tables_alias_by_enum_id.get(enum_cfg.id, "oig_tables")
            mapper = f"{alias}.enumOptionValueFor{enum_name}"
            return f"oig.decodeEnumWire({leaf_expr}, {mapper})"

        leaf_fn = self._leaf_decoder_name(attr_config, optional=False)
        if leaf_fn is None:
            return f"oig.primitivePayloadOrNull({leaf_expr})"
        return f"oig.{leaf_fn}({leaf_expr})"

    def _leaf_decoder_name(self, attr_config: AttributeConfig, *, optional: bool) -> str | None:
        type_info = resolve_type_info(attr_config)

        if type_info.kind != AttributeTypeDescriptorKind.primitive or type_info.primitive_config is None:
            return None

        prim = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
        bt = prim.base_type
        suffix = "OrNull" if optional else ""

        if bt == CodePrimitiveBaseType.uuid:
            return f"decodeUuidString{suffix}"
        if bt == CodePrimitiveBaseType.string:
            return f"decodeString{suffix}"
        if bt == CodePrimitiveBaseType.integer:
            return f"decodeInt{suffix}"
        if bt == CodePrimitiveBaseType.float:
            return f"decodeDouble{suffix}"
        if bt == CodePrimitiveBaseType.boolean:
            return f"decodeBool{suffix}"
        if bt == CodePrimitiveBaseType.datetime:
            return f"decodeDateTimeString{suffix}"
        if bt == CodePrimitiveBaseType.json:
            return f"decodeJsonObject{suffix}"
        if bt == CodePrimitiveBaseType.bytes:
            return f"decodeBytesBase64{suffix}"

        # Unknown primitive: fall back to raw payload.
        return "primitivePayloadOrNull"


__all__ = ["DartMaterializationRenderer"]

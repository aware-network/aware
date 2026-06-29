"""
Dart renderer for generating Dart code sections from meta models using the CodeSectionWriter.

This renderer serves as a language-specific plugin for the ObjectConfigGraphRenderer,
handling the Dart-specific aspects of code generation with freezed and JsonSerializable.
"""

from pathlib import Path, PurePosixPath
from dataclasses import dataclass
from uuid import UUID
from typing_extensions import override

# Code Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Code Runtime
from aware_code.section.class_.assembler import assemble_class
from aware_code.section.class_.segments import CodeSectionClassSegment
from aware_code.section.function.assembler import assemble_function
from aware_code.section.function.segments import CodeSectionFunctionSegment
from aware_code.section.attribute.assembler import assemble_attribute
from aware_code.section.attribute.segments import CodeSectionAttributeSegment
from aware_code.section.import_.assembler import assemble_import
from aware_code.section.import_.segments import CodeSectionImportSegment
from aware_code.section.enum.assembler import assemble_enum
from aware_code.section.enum.segments import CodeSectionEnumSegment
from aware_code.section.enum_value.assembler import assemble_enum_value
from aware_code.section.enum_value.segments import CodeSectionEnumValueSegment
from aware_code.section.writer import CodeSectionScope, CodeSectionWriter
from aware_code.section.spec import SectionSpec
from aware_code.types.json import Json

# Meta Ontology
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_option_overlay import EnumOptionOverlay
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_config_overlay import AttributeConfigOverlay
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.annotation.code_section_annotation_discriminate import (
    CodeSectionAnnotationDiscriminate,
)

# Meta Runtime
from aware_meta.attribute.config.type_descriptor_helpers import (
    AttributeTypeInfo,
    resolve_type_class_config_id,
    resolve_type_info,
)
from aware_meta.graph.config.model_bootstrap import get_node_function_config
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    ObjectConfigGraphRendererPolicy,
    build_renderer_empty_code,
)
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

# Canonical SSOT for primitive rendering
from dart_grammar.primitive_codec import DartPrimitiveCodec

# Utils
from aware_utils.string_transform import to_camel_case, to_pascal_case
from aware_utils.logging import logger

from dart_grammar.renderer_policy import DartRenderPolicy


@dataclass(frozen=True, slots=True)
class _DiscriminatedUnionVariant:
    class_config: ClassConfig
    tag_value: str


@dataclass(slots=True)
class _DiscriminatedUnion:
    base_class: ClassConfig
    discriminator: str
    variants: list[_DiscriminatedUnionVariant]


def _layout_module_import_path(
    *,
    layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
    file_path: Path,
) -> str:
    module_path = layout_strategy.get_module_import_path(file_path)
    if module_path.startswith("package:") or module_path.startswith("dart:"):
        return module_path
    if "/" in module_path:
        return module_path

    parts = file_path.parts
    for index, part in enumerate(parts):
        if part in {"lib", "bin", "test", "src"} and index + 1 < len(parts):
            return PurePosixPath(*parts[index + 1:]).as_posix()

    if not file_path.is_absolute() and file_path.parent != Path("."):
        return PurePosixPath(file_path).as_posix()
    return module_path


class DartRenderer(ObjectConfigGraphRendererLanguage):
    """
    Dart implementation of the ObjectConfigGraphRendererLanguage for rendering meta models to Dart code.

    Uses freezed annotations and JsonSerializable for proper JSON handling, following Dart best practices.
    """

    def __init__(
        self,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
    ):
        super().__init__(layout_strategy=layout_strategy)
        self.policy: DartRenderPolicy = DartRenderPolicy.orm_default()
        self._lazy_attr_ids: set[UUID] = set()
        self._rels_by_source_class_id: dict[UUID, list[ClassConfigRelationship]] = {}

        self._local_enum_ids: set[UUID] = set()
        self._local_class_ids: set[UUID] = set()
        self._bound_graph_class_ids: set[UUID] = set()

        # Graph-wide lookups (for robust import resolution even when ORM relationships
        # are not side-loaded on AttributeTypeDescriptor leaf nodes).
        self._graph_classes_by_id: dict[UUID, ClassConfig] = {}
        self._graph_enums_by_id: dict[UUID, EnumConfig] = {}
        self._class_owned_function_ids: set[UUID] = set()

        # base_class_id -> union info
        self._discriminated_unions_by_base_id: dict[UUID, _DiscriminatedUnion] = {}
        # variant_class_id -> base_class_id
        self._discriminated_union_base_id_by_variant_id: dict[UUID, UUID] = {}
        # Layout ordering (relative_path, source_position) by entity id.
        self._layout_order_by_class_id: dict[UUID, tuple[str, int]] = {}
        self._layout_order_by_enum_id: dict[UUID, tuple[str, int]] = {}
        self._layout_order_by_function_id: dict[UUID, tuple[str, int]] = {}

    @property
    @override
    def language(self) -> CodeLanguage:
        """Return the language supported by this plugin."""
        return CodeLanguage.dart

    @property
    @override
    def indent(self) -> int:
        """Return the indentation size for this language."""
        return 2

    @property
    @override
    def comment_prefix(self) -> str:
        """Return the comment prefix for Dart (//)."""
        return "//"

    @override
    def set_policy(self, policy: ObjectConfigGraphRendererPolicy | None) -> None:
        """Inject a render policy (API vs ORM)."""
        if policy is None:
            self.policy = DartRenderPolicy.orm_default()
            return
        if isinstance(policy, DartRenderPolicy):
            self.policy = policy

    @override
    def define_assemblers(self):
        # Canonical renderers should be free-function driven (no assembler classes).
        self._spec_import: SectionSpec = SectionSpec(
            section_type=CodeSectionType.import_,
            assemble=lambda code_section, segments, _nested: assemble_import(
                code_section=code_section,
                segments=segments,
            ),
        )
        self._spec_enum: SectionSpec = SectionSpec(
            section_type=CodeSectionType.enum,
            assemble=lambda code_section, segments, nested: assemble_enum(
                code_section=code_section,
                segments=segments,
                code_sections=nested,
            ),
        )
        self._spec_enum_value: SectionSpec = SectionSpec(
            section_type=CodeSectionType.enum_value,
            assemble=lambda code_section, segments, _nested: assemble_enum_value(
                code_section=code_section,
                segments=segments,
            ),
        )
        self._spec_class: SectionSpec = SectionSpec(
            section_type=CodeSectionType.class_,
            assemble=lambda code_section, segments, nested: assemble_class(
                code_section=code_section,
                segments=segments,
                code_sections=nested,
            ),
        )
        self._primitive_codec: DartPrimitiveCodec = DartPrimitiveCodec()

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        """
        Bind graph-level state required by this renderer.

        Currently:
        - Precompute discriminated union groups from `.aware` `ann ... discriminate ...`
          annotations so union rendering is deterministic and emit-only.
        """

        # Build class lookup for this graph.
        classes_by_id: dict[UUID, ClassConfig] = {}
        classes_by_name: dict[str, list[ClassConfig]] = {}
        for node in graph.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.class_:
                continue
            cls = node.class_config
            if cls is None:
                continue
            classes_by_id[cls.id] = cls
            classes_by_name.setdefault(cls.name, []).append(cls)
            self._graph_classes_by_id[cls.id] = cls
        self._bound_graph_class_ids = set(classes_by_id)

        self._class_owned_function_ids = set()
        for cls in classes_by_id.values():
            for fn_link in cls.class_config_function_configs:
                fn_id = fn_link.function_config_id
                if fn_id is None:
                    fn_id = fn_link.function_config.id
                self._class_owned_function_ids.add(fn_id)

        for node in graph.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.enum:
                continue
            enum_cfg = node.enum_config
            if enum_cfg is None:
                continue
            self._graph_enums_by_id[enum_cfg.id] = enum_cfg

        self._layout_order_by_class_id = {}
        self._layout_order_by_enum_id = {}
        self._layout_order_by_function_id = {}
        for node in graph.object_config_graph_nodes:
            layouts = node.layouts
            if not layouts:
                continue
            aware_layouts = [layout for layout in layouts if not layout.layout_kind or layout.layout_kind == "aware"]
            if not aware_layouts:
                continue
            layout = min(
                aware_layouts,
                key=lambda layout_entry: (
                    layout_entry.source_position is None,
                    layout_entry.source_position or 0,
                    layout_entry.relative_path or "",
                ),
            )
            if not layout.relative_path:
                continue
            rel_path = layout.relative_path
            source_pos = int(layout.source_position or 0)
            if node.class_config is not None:
                self._layout_order_by_class_id[node.class_config.id] = (rel_path, source_pos)
            elif node.enum_config is not None:
                self._layout_order_by_enum_id[node.enum_config.id] = (rel_path, source_pos)
            elif node.type == ObjectConfigGraphNodeType.function:
                node_function_config = get_node_function_config(node)
                if node_function_config is not None:
                    self._layout_order_by_function_id[node_function_config.id] = (
                        rel_path,
                        source_pos,
                    )

        local_class_ids = set(classes_by_id.keys())
        external_classes_by_id: dict[UUID, ClassConfig] = self.external_class_lookup
        external_classes_by_name_by_graph_id: dict[UUID, dict[str, list[ClassConfig]]] = {}
        for ext_graph in self.external_graphs:
            ext_name_map: dict[str, list[ClassConfig]] = {}
            for node in ext_graph.object_config_graph_nodes:
                if node.type != ObjectConfigGraphNodeType.class_:
                    continue
                cls = node.class_config
                if cls is None:
                    continue
                external_classes_by_id[cls.id] = cls
                ext_name_map.setdefault(cls.name, []).append(cls)
            external_classes_by_name_by_graph_id[ext_graph.id] = ext_name_map

        # Extend graph-wide class lookup with externals so imports/relationships resolve.
        for cls in external_classes_by_id.values():
            _ = self._graph_classes_by_id.setdefault(cls.id, cls)

        classes_by_name_by_graph_id: dict[UUID, dict[str, list[ClassConfig]]] = {
            graph.id: classes_by_name,
        }
        classes_by_name_by_graph_id.update(external_classes_by_name_by_graph_id)

        combined_classes_by_name: dict[str, list[ClassConfig]] = {}
        for name, matches in classes_by_name.items():
            combined_classes_by_name.setdefault(name, []).extend(matches)
        for name_map in external_classes_by_name_by_graph_id.values():
            for name, matches in name_map.items():
                combined_classes_by_name.setdefault(name, []).extend(matches)

        def _resolve_class_in_graph(name: str, *, graph_id: UUID | None) -> ClassConfig | None:
            matches: list[ClassConfig] = []
            if graph_id is not None:
                matches = classes_by_name_by_graph_id.get(graph_id, {}).get(name, []) or []
            if not matches:
                matches = combined_classes_by_name.get(name, []) or []
            if not matches:
                return None
            if len(matches) > 1:
                logger.warning(
                    f"Multiple ClassConfig entries found for {name}; using the first for discriminate mapping",
                )
            return matches[0]

        base_key_attr_by_id: dict[UUID, str] = {}

        # (variant_class_name, discriminator_attr) -> ((missing_bucket, path_key, byte_start, tag, class), tag_value)
        #
        # Note: Dart unions cannot span packages, so we only consider tag annotations from
        # the current graph. External graphs are used for base-key resolution only.
        # We preserve source appearance order by sorting on stable paths + annotation byte offsets.
        tag_entries: dict[tuple[str, str], tuple[tuple[int, str, int, str, str], str]] = {}

        def _annotation_order_key(
            disc: CodeSectionAnnotationDiscriminate, variant_cls: ClassConfig | None
        ) -> tuple[int, str, int, str, str]:
            missing_bucket = 1
            path_key = ""
            if variant_cls is not None:
                layout_path = self.layout_strategy.entity_layout_paths.get(str(variant_cls.id))
                if layout_path is not None:
                    path_key = layout_path.as_posix()
                    missing_bucket = 0
            if disc.source_position is None:
                raise ValueError(f"Discriminate annotation {disc.id} has no source position")
            return (missing_bucket, path_key, disc.source_position, disc.tag_value or "", disc.class_name or "")

        def _register_key(*, disc: CodeSectionAnnotationDiscriminate, source_graph_id: UUID | None) -> None:
            cls = _resolve_class_in_graph(disc.class_name, graph_id=source_graph_id)
            if cls is None:
                logger.warning(f"Discriminate key references unknown class {disc.class_name}")
                return
            prev_attr = base_key_attr_by_id.get(cls.id)
            if prev_attr is not None and prev_attr != disc.attribute_name:
                logger.warning(
                    f"Multiple discriminate keys detected on base {cls.name} "
                    + f"({prev_attr} vs {disc.attribute_name}); using {prev_attr}",
                )
                return
            base_key_attr_by_id[cls.id] = disc.attribute_name

        for ann in graph.object_config_graph_annotations:
            if ann.kind != ObjectConfigGraphAnnotationKind.discriminate:
                continue
            disc = ann.code_section_annotation_discriminate
            if disc is None:
                continue

            key = (disc.class_name, disc.attribute_name)
            if disc.mode == "key":
                _register_key(disc=disc, source_graph_id=graph.id)
            elif disc.mode == "tag" and disc.tag_value:
                variant_cls = _resolve_class_in_graph(disc.class_name, graph_id=graph.id)
                tag_entries[key] = (_annotation_order_key(disc, variant_cls), disc.tag_value)

        for ext_graph in self.external_graphs:
            for ann in ext_graph.object_config_graph_annotations:
                if ann.kind != ObjectConfigGraphAnnotationKind.discriminate:
                    continue
                disc = ann.code_section_annotation_discriminate
                if disc is None or disc.mode != "key":
                    continue
                _register_key(disc=disc, source_graph_id=ext_graph.id)

        ordered_tags = sorted(tag_entries.items(), key=lambda item: item[1][0])

        for (variant_name, discriminator), (_order_key, tag_value) in ordered_tags:
            variant_cls = _resolve_class_in_graph(variant_name, graph_id=graph.id)
            if variant_cls is None:
                logger.warning(
                    f"Discriminate tag references unknown class {variant_name} (tag={tag_value})",
                )
                continue

            base_cls: ClassConfig | None = None
            cursor: ClassConfig | None = variant_cls
            visited: set[UUID] = set()
            while cursor is not None:
                base_attr = base_key_attr_by_id.get(cursor.id)
                if base_attr is not None and base_attr == discriminator:
                    base_cls = cursor
                    break
                parent_id = cursor.parent_class_id
                if parent_id is None:
                    cursor = cursor.parent_class
                    continue
                if parent_id in visited:
                    logger.warning(
                        f"Discriminate ancestry cycle detected for {variant_name}; stopping traversal",
                    )
                    break
                visited.add(parent_id)
                cursor = classes_by_id.get(parent_id) or external_classes_by_id.get(parent_id) or cursor.parent_class

            if base_cls is None:
                logger.warning(
                    f"Discriminate tag {tag_value} on {variant_name}::{discriminator} "
                    + "has no ancestor discriminate key; skipping",
                )
                continue
            if base_cls.id not in local_class_ids:
                # Discriminated unions cannot span Dart packages; keep the variant local.
                continue

            union = self._discriminated_unions_by_base_id.get(base_cls.id)
            if union is None:
                union = _DiscriminatedUnion(
                    base_class=base_cls,
                    discriminator=discriminator,
                    variants=[],
                )
                self._discriminated_unions_by_base_id[base_cls.id] = union
            elif union.discriminator != discriminator:
                logger.warning(
                    f"Multiple discriminators detected on base {base_cls.name} "
                    + f"({union.discriminator} vs {discriminator}); using {union.discriminator}",
                )

            union.variants.append(_DiscriminatedUnionVariant(class_config=variant_cls, tag_value=tag_value))
            self._discriminated_union_base_id_by_variant_id[variant_cls.id] = base_cls.id

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
        """
        Emit a complete Dart file with all the given meta objects.

        Args:
            meta_objects: List of meta objects (ClassConfig, EnumConfig, etc.) to render
            writer: CodeSectionWriter to use for writing the code
            schema: Schema name for the objects in this file
            class_to_class_config_map: Mapping from class ID to ClassConfig (global lookup)
            base_class_module: Module name for the base class
            base_class_name: Name of the base class
        """
        if class_to_class_config_map is None:
            class_to_class_config_map = {}

        # Relationship-driven loading semantics (canonical)
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

        # 1. Collect objects
        enums = [obj for obj in meta_objects if isinstance(obj, EnumConfig)]
        classes = [obj for obj in meta_objects if isinstance(obj, ClassConfig)]
        functions = [
            obj
            for obj in meta_objects
            if isinstance(obj, FunctionConfig) and obj.id not in self._class_owned_function_ids
        ]

        # Discriminated union policy (API runtime):
        # - Union bases own their variants even when layout places variants in other files.
        # - Variant classes are never emitted standalone; they are emitted via the base union.
        def _is_variant_only(cls_cfg: ClassConfig) -> bool:
            base_id = self._discriminated_union_base_id_by_variant_id.get(cls_cfg.id)
            if base_id is None:
                return False
            # If a class is both a variant and a union base itself, prefer emitting it as a base.
            return cls_cfg.id not in self._discriminated_unions_by_base_id

        emitted_class_ids: set[UUID] = set()
        classes_to_scan_for_imports: list[ClassConfig] = []
        for cls_cfg in classes:
            if _is_variant_only(cls_cfg):
                continue

            union = self._discriminated_unions_by_base_id.get(cls_cfg.id)
            if union is not None:
                emitted_class_ids.add(cls_cfg.id)
                classes_to_scan_for_imports.append(cls_cfg)
                for variant in union.variants:
                    emitted_class_ids.add(variant.class_config.id)
                    classes_to_scan_for_imports.append(variant.class_config)
            else:
                emitted_class_ids.add(cls_cfg.id)
                classes_to_scan_for_imports.append(cls_cfg)

        # Categorize + preserve SSOT order of appearance within the source `.aware` module.
        # This mirrors the Python renderer behavior and keeps API output readable/stable.
        top_level: list[EnumConfig | ClassConfig | FunctionConfig] = []
        for obj in meta_objects:
            if (
                isinstance(obj, EnumConfig)
                or isinstance(obj, ClassConfig)
                or (isinstance(obj, FunctionConfig) and obj.id not in self._class_owned_function_ids)
            ):
                top_level.append(obj)

        def _source_appearance_key(
            obj: EnumConfig | ClassConfig | FunctionConfig,
        ) -> tuple[int, str, int, str, str, str]:
            """
            Stable key for "order of appearance" within the source `.aware` file(s).

            We rely on OCG layout metadata as the SSOT for order.
            """
            # (missing_binding_bucket, code_id, byte_start, kind, name, id)
            missing_bucket = 1
            code_id = ""
            byte_start = 0
            kind = obj.__class__.__name__
            name = obj.name or ""
            obj_id = str(obj.id)

            if isinstance(obj, ClassConfig):
                layout_key = self._layout_order_by_class_id.get(obj.id)
                if layout_key is not None:
                    code_id, byte_start = layout_key
                    missing_bucket = 0
                    kind = "class"
                    return (missing_bucket, code_id, byte_start, kind, name, obj_id)
            elif isinstance(obj, EnumConfig):
                layout_key = self._layout_order_by_enum_id.get(obj.id)
                if layout_key is not None:
                    code_id, byte_start = layout_key
                    missing_bucket = 0
                    kind = "enum"
                    return (missing_bucket, code_id, byte_start, kind, name, obj_id)
            else:
                layout_key = self._layout_order_by_function_id.get(obj.id)
                if layout_key is not None:
                    code_id, byte_start = layout_key
                    missing_bucket = 0
                    kind = "function"
                    return (missing_bucket, code_id, byte_start, kind, name, obj_id)

            return (missing_bucket, code_id, byte_start, kind, name, obj_id)

        top_level.sort(key=_source_appearance_key)

        # Class-owned functions are emitted by DartFunctionsRenderer in class files.
        # When a file carries only class-owned function nodes, keep this renderer no-op.
        if not top_level:
            return

        # If this file only contains discriminated-union variants (and no other emit-worthy entities),
        # generate an export stub that forwards to the union base module(s).
        #
        # Motivation:
        # - Freezed requires union variants to be declared in the same library as the union base.
        # - Our canonical layout strategy may still place the variant class in its own file for
        #   SSOT/template parity. We keep that path stable by exporting the union base.
        variant_only_classes = [c for c in classes if _is_variant_only(c)]
        has_only_variant_classes = bool(variant_only_classes) and not emitted_class_ids and not enums and not functions
        if has_only_variant_classes:
            self._emit_generated_file_header(writer)

            current_module: str | None = None
            first_variant = variant_only_classes[0]
            try:
                current_path = self.layout_strategy.get_class_file_path(first_variant)
                current_module = _layout_module_import_path(
                    layout_strategy=self.layout_strategy,
                    file_path=current_path,
                )
            except Exception:
                current_module = None

            base_modules: set[str] = set()
            for variant_cls in variant_only_classes:
                base_id = self._discriminated_union_base_id_by_variant_id.get(variant_cls.id)
                if base_id is None:
                    continue
                union_base = self._discriminated_unions_by_base_id.get(base_id)
                base_cls: ClassConfig | None
                if union_base:
                    base_cls = union_base.base_class
                else:
                    # Fall back to graph-wide lookup (should be present for local unions).
                    base_cls = self._graph_classes_by_id.get(base_id)
                if base_cls is None:
                    continue
                base_path = self.layout_strategy.get_class_file_path(base_cls)
                module = _layout_module_import_path(
                    layout_strategy=self.layout_strategy,
                    file_path=base_path,
                )
                base_modules.add(
                    _normalize_relative_import_path(
                        import_path=module,
                        current_module=current_module,
                    )
                )

            for module in sorted(base_modules):
                with writer.start_section(self._spec_import, qualname=f"export.{module}") as export_section:
                    _ = export_section.token("export ")
                    _ = export_section.token(f"'{module}'", CodeSectionImportSegment.MODULE.value)
                    _ = export_section.token(";\n")

            return

        # Track local entity IDs for this file so we can distinguish between:
        # - local enums/classes (no import override needed)
        # - external referenced enums/classes (must have an import override, otherwise fall back)
        self._local_enum_ids = {e.id for e in enums}
        self._local_class_ids = emitted_class_ids

        # Resolve the module path for this file to avoid generating self-imports.
        current_module: str | None = None
        first_class = next((obj for obj in meta_objects if isinstance(obj, ClassConfig)), None)
        if first_class is not None:
            try:
                path = self.layout_strategy.get_class_file_path(first_class)
                current_module = _layout_module_import_path(
                    layout_strategy=self.layout_strategy,
                    file_path=path,
                )
            except Exception:
                current_module = None
        if current_module is None:
            first_enum = next((obj for obj in meta_objects if isinstance(obj, EnumConfig)), None)
            if first_enum is not None:
                try:
                    path = self.layout_strategy.get_enum_file_path(first_enum)
                    current_module = _layout_module_import_path(
                        layout_strategy=self.layout_strategy,
                        file_path=path,
                    )
                except Exception:
                    current_module = None

        # 2. Emit imports at the top of the file
        imports = self._gather_imports(
            meta_objects,
            current_module=current_module,
            local_class_ids=emitted_class_ids,
            classes_to_scan=classes_to_scan_for_imports,
        )
        self._emit_imports(
            writer,
            imports,
            meta_objects,
            has_class=bool(emitted_class_ids),
            has_enum=bool(enums),
            classes_to_scan=classes_to_scan_for_imports,
        )

        # 3. Emit in source order (interleaving enums/classes/functions).
        first_item = True
        for obj in top_level:
            if isinstance(obj, EnumConfig):
                if not first_item:
                    _ = writer.token("\n")
                self._render_enum(writer, obj)
                first_item = False
                continue

            if isinstance(obj, ClassConfig):
                if _is_variant_only(obj):
                    # Variant classes are emitted as part of the base union, even if their layout file differs.
                    continue
                union = self._discriminated_unions_by_base_id.get(obj.id)
                if not first_item:
                    _ = writer.token("\n")
                if union is not None:
                    self._render_discriminated_union(writer, union, list(union.variants))
                else:
                    self._render_class(writer, obj, class_to_class_config_map)
                first_item = False
                continue

            else:
                if not first_item:
                    _ = writer.token("\n")
                self._render_function(writer, obj, schema)
                first_item = False

    def _emit_generated_file_header(self, writer: CodeSectionWriter) -> None:
        _ = writer.token("// coverage:ignore-file\n")
        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// ignore_for_file: type=lint\n")
        _ = writer.token(
            "// ignore_for_file: unused_element, deprecated_member_use, "
            + "deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, "
            + "unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, "
            + "prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, "
            + "unnecessary_question_mark\n\n"
        )

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.dart,
            renderer_key=type(self).__name__,
        )

    def _emit_imports(
        self,
        writer: CodeSectionWriter,
        imports: list[str],
        meta_objects: list[object],
        *,
        has_class: bool,
        has_enum: bool,
        classes_to_scan: list[ClassConfig],
    ) -> None:
        """
        Emit the necessary imports for Dart code.

        Args:
            writer: CodeSectionWriter to write to
            meta_objects: List of meta objects to analyze for imports
        """
        merged_imports: set[str] = set()
        if has_class:
            merged_imports.add("package:freezed_annotation/freezed_annotation.dart")
        if has_enum and not has_class:
            merged_imports.add("package:json_annotation/json_annotation.dart")

        # Descriptor/type-driven UUID detection for imports
        has_uuid = any(
            any(
                self._should_emit_attribute_for_policy(
                    obj,
                    class_config_attribute_config.attribute_config,
                    resolve_type_info(class_config_attribute_config.attribute_config),
                )
                and self._attribute_is_base_type(
                    class_config_attribute_config.attribute_config,
                    CodePrimitiveBaseType.uuid,
                )
                for class_config_attribute_config in (obj.class_config_attribute_configs)
            )
            for obj in classes_to_scan
        )

        has_uint8list = any(
            any(
                self._should_emit_attribute_for_policy(
                    obj,
                    class_config_attribute_config.attribute_config,
                    resolve_type_info(class_config_attribute_config.attribute_config),
                )
                and self._attribute_is_base_type(
                    class_config_attribute_config.attribute_config, CodePrimitiveBaseType.bytes
                )
                for class_config_attribute_config in (obj.class_config_attribute_configs)
            )
            for obj in classes_to_scan
        )
        if has_uuid:
            merged_imports.add("package:uuid/uuid.dart")
            # Converters for UuidValue, UuidValueList, Uint8List, etc.
            merged_imports.add("package:aware_model_helpers/converters.dart")

        if has_uint8list:
            # Uint8List lives in the Dart SDK typed_data library; import only when needed.
            merged_imports.add("dart:typed_data")
            # Converters for Uint8List serialization.
            merged_imports.add("package:aware_model_helpers/converters.dart")

        merged_imports.update(imports)

        # Part declaration for generated files
        _ = writer.token("// coverage:ignore-file\n")
        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// ignore_for_file: type=lint\n")
        _ = writer.token(
            "// ignore_for_file: unused_element, deprecated_member_use, "
            + "deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, "
            + "unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, "
            + "prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, "
            + "unnecessary_question_mark\n\n"
        )

        # Emit imports
        for import_path in sorted(merged_imports):
            with writer.start_section(self._spec_import, qualname=f"import.{import_path}") as import_section:
                _ = import_section.token("import ")
                _ = import_section.token(f"'{import_path}'", CodeSectionImportSegment.MODULE.value)
                _ = import_section.token(";\n")

        _ = writer.token("\n")

        # Determine current file basename from layout strategy and meta objects
        file_basename = "models"
        file_path: Path | None = None

        first_class = next((obj for obj in meta_objects if isinstance(obj, ClassConfig)), None)
        if first_class is not None:
            try:
                file_path = self.layout_strategy.get_class_file_path(first_class)
            except Exception as e:
                logger.warning(f"Error determining file path for class {first_class.name}: {e}")

        if file_path is None:
            first_enum = next((obj for obj in meta_objects if isinstance(obj, EnumConfig)), None)
            if first_enum is not None:
                try:
                    file_path = self.layout_strategy.get_enum_file_path(first_enum)
                except Exception as e:
                    logger.warning(f"Error determining file path for enum {first_enum.name}: {e}")

        if file_path is not None:
            file_basename = file_path.stem

        # Only add .freezed if it contains at least one Freezed class/union.
        if has_class:
            _ = writer.token(f"part '{file_basename}.freezed.dart';\n")

        # JsonSerializable part is required for any enums or classes in this file.
        if has_class or has_enum:
            _ = writer.token(f"part '{file_basename}.g.dart';\n\n")

    def _gather_imports(
        self,
        meta_objects: list[object],
        *,
        current_module: str | None,
        local_class_ids: set[UUID],
        classes_to_scan: list[ClassConfig],
    ) -> list[str]:
        """Collect required imports for related classes/enums, honoring overrides."""
        imports: set[str] = set()
        # Build a lookup for class configs by id (graph-wide, scoped by the bound graph).
        for cls_cfg in classes_to_scan:
            self._graph_classes_by_id[cls_cfg.id] = cls_cfg
        for entity in meta_objects:
            if isinstance(entity, ClassConfig):
                self._graph_classes_by_id[entity.id] = entity

        local_enum_ids: set[UUID] = {entity.id for entity in meta_objects if isinstance(entity, EnumConfig)}
        for entity in meta_objects:
            if isinstance(entity, EnumConfig):
                self._graph_enums_by_id[entity.id] = entity

        def _module_for_class(cls_cfg: ClassConfig) -> str | None:
            # Variant-only discriminated-union classes are emitted within their base union file.
            # Importing the variant's own module would be invalid/empty.
            base_id = self._discriminated_union_base_id_by_variant_id.get(cls_cfg.id)
            if base_id is not None and cls_cfg.id not in self._discriminated_unions_by_base_id:
                base_cls = self._graph_classes_by_id.get(base_id)
                if base_cls is not None:
                    cls_cfg = base_cls

            if self.import_overrides:
                override = self.import_overrides.get(str(cls_cfg.id))
                if override:
                    return override
            path = self.layout_strategy.get_class_file_path(cls_cfg)
            return _layout_module_import_path(
                layout_strategy=self.layout_strategy,
                file_path=path,
            )

        def _module_for_enum(enum_cfg: EnumConfig) -> str | None:
            if self.import_overrides:
                override = self.import_overrides.get(str(enum_cfg.id))
                if override:
                    return override
            # Local (same-package) enums: we can safely import them even if they are emitted in a
            # different file, as long as the layout strategy knows the entity placement.
            if enum_cfg.id not in local_enum_ids and not self._layout_has_entity_path(enum_cfg.id):
                return None
            path = self.layout_strategy.get_enum_file_path(enum_cfg)
            return _layout_module_import_path(
                layout_strategy=self.layout_strategy,
                file_path=path,
            )

        # Determine modules for the entities that live in this file so we can
        # avoid generating self-imports (e.g., local enums/classes importing their own module).
        current_modules: set[str] = set()
        if current_module:
            current_modules.add(current_module)
        else:
            for entity in meta_objects:
                if isinstance(entity, ClassConfig):
                    mod = _module_for_class(entity)
                    if mod:
                        current_modules.add(mod)
                elif isinstance(entity, EnumConfig):
                    mod = _module_for_enum(entity)
                    if mod:
                        current_modules.add(mod)

        def _collect_descriptor_entity_ids(desc: AttributeTypeDescriptor) -> tuple[set[UUID], set[UUID]]:
            """
            Collect referenced ClassConfig/EnumConfig ids from a descriptor tree.

            Motivation:
            - AttributeTypeDescriptor.class_config relationships are excluded and may not be loaded.
            - The *_id foreign keys are always present and are the canonical linkage.
            """
            class_ids: set[UUID] = set()
            enum_ids: set[UUID] = set()

            if desc.kind == AttributeTypeDescriptorKind.class_ and desc.class_config_id is not None:
                class_ids.add(desc.class_config_id)
            elif desc.kind == AttributeTypeDescriptorKind.enum and desc.enum_config_id is not None:
                enum_ids.add(desc.enum_config_id)

            for link in desc.child_links:
                child_class_ids, child_enum_ids = _collect_descriptor_entity_ids(link.child)
                class_ids.update(child_class_ids)
                enum_ids.update(child_enum_ids)

            return class_ids, enum_ids

        for obj in classes_to_scan:
            # Parent class import
            parent = obj.parent_class
            if parent is None and obj.parent_class_id:
                parent = self._graph_classes_by_id.get(obj.parent_class_id)
            if parent:
                # Skip parent import when it is emitted in the same file, but still scan
                # attribute descriptors below (child classes can reference external types).
                if parent.id not in local_class_ids:
                    mod = _module_for_class(parent)
                    if mod and mod not in current_modules:
                        imports.add(mod)
            # Attribute-based imports
            for class_config_attribute_config in obj.class_config_attribute_configs:
                attribute_config = class_config_attribute_config.attribute_config
                type_info = resolve_type_info(attribute_config)
                if not self._should_emit_attribute_for_policy(obj, attribute_config, type_info):
                    continue
                class_ids, enum_ids = _collect_descriptor_entity_ids(attribute_config.type_descriptor)

                for class_id in class_ids:
                    if class_id in local_class_ids:
                        continue
                    resolved_cls = self._graph_classes_by_id.get(class_id)
                    if resolved_cls is not None:
                        mod = _module_for_class(resolved_cls)
                        if mod and mod not in current_modules:
                            imports.add(mod)
                        continue

                    # External class reference: prefer SSOT import override if present.
                    if self.import_overrides:
                        override = self.import_overrides.get(str(class_id))
                        if override and override not in current_modules:
                            imports.add(override)

                for enum_id in enum_ids:
                    # External enum reference: prefer SSOT import override if present.
                    if self.import_overrides:
                        override = self.import_overrides.get(str(enum_id))
                        if override and override not in current_modules:
                            imports.add(override)
                            continue

                    enum_cfg = self._graph_enums_by_id.get(enum_id)
                    if enum_cfg is None:
                        continue
                    mod = _module_for_enum(enum_cfg)
                    if mod and mod not in current_modules:
                        imports.add(mod)
        normalized_imports = {
            _normalize_relative_import_path(import_path=import_path, current_module=current_module)
            for import_path in imports
        }
        return list(normalized_imports)

    def _render_enum(self, writer: CodeSectionWriter, enum_config: EnumConfig) -> None:
        """
        Render an enum using Dart JsonEnum annotation.

        Args:
            writer: The CodeSectionWriter to write to
            enum_config: The enum config to render
        """
        # Add description as doc comment if available (one `///` per line).
        if enum_config.description:
            for raw_line in enum_config.description.splitlines():
                line = raw_line.rstrip()
                _ = writer.token(f"/// {line}\n" if line else "///\n")

        # Start enum definition
        with writer.start_section(self._spec_enum, qualname=enum_config.name) as enum_scope:
            # JsonEnum annotation
            _ = enum_scope.token("@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)\n")

            # Enum declaration
            _ = enum_scope.token("enum ")
            _ = enum_scope.token(enum_config.name, CodeSectionEnumSegment.NAME.value)
            _ = enum_scope.token(" {\n")

            # Use indentation for enum body
            with enum_scope.indent():
                # Canonical ordering: stable by position, then value.
                sorted_options = sorted(enum_config.enum_options, key=lambda opt: (opt.position, opt.value))

                # Add each enum value (camelCase or overlay-provided)
                for i, option in enumerate(sorted_options):
                    rendered_name: str | None = None
                    wire_name: str | None = None
                    overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.enum_option, option.id)
                    if overlay:
                        if not isinstance(overlay, EnumOptionOverlay):
                            raise ValueError(f"Overlay for enum option {option.id} is not an EnumOptionOverlay")
                        rendered_name = overlay.rendered_name
                        wire_name = overlay.wire_name

                    canonical_case_name = to_camel_case(option.value)
                    case_name = rendered_name or canonical_case_name
                    # If the rendered name differs from the canonical name, preserve canonical wire value.
                    if wire_name is None and case_name != canonical_case_name:
                        wire_name = option.value

                    option_desc = option.description

                    with enum_scope.start_section(
                        self._spec_enum_value,
                        qualname=f"{enum_config.name}.{case_name}",
                        reference=f"{enum_config.name}.{case_name}",
                        metadata=Json({"position": option.position}),
                    ) as enum_value_scope:
                        # Emit doc comment for this enum value (if available).
                        if option_desc:
                            for raw_line in option_desc.splitlines():
                                line = raw_line.rstrip()
                                _ = enum_value_scope.token(f"/// {line}\n" if line else "///\n")

                        # If wire_name is present and differs from the default wire name implied by `@JsonEnum`,
                        # emit @JsonValue before the case.
                        if (wire_name and wire_name != option.value) or (case_name != canonical_case_name):
                            _ = enum_value_scope.token(f"@JsonValue('{wire_name or option.value}')\n")

                        # Manual indent token to keep VALUE segment clean (no leading spaces).
                        _ = enum_value_scope.token(" " * (enum_value_scope.indent_level * writer.indent_size))
                        _ = enum_value_scope.token(case_name, CodeSectionEnumValueSegment.VALUE.value)

                        # Use commas between values; no trailing semicolon unless members follow (not emitted here).
                        if i < len(sorted_options) - 1:
                            _ = enum_value_scope.token(",")
                        _ = enum_value_scope.token("\n")

            _ = enum_scope.token("}\n\n")

            # Extension for JSON conversion
            _ = enum_scope.token(f"extension {enum_config.name}Extension on {enum_config.name} {{\n")
            with enum_scope.indent():
                _ = enum_scope.token(
                    f"static String toJson({enum_config.name} type) => _${enum_config.name}EnumMap[type]!;\n\n"
                )
                _ = enum_scope.token(f"static {enum_config.name} fromJson(String json) =>\n")
                with enum_scope.indent():
                    _ = enum_scope.token(
                        f"_${enum_config.name}EnumMap.map((key, value) => MapEntry(value, key))[json]!;\n"
                    )
                _ = enum_scope.token("\n")
                # Nullable helpers are required because we emit @JsonKey(fromJson: XExtension.fromJsonNullable, ...)
                # for optional enum attributes.
                _ = enum_scope.token(
                    f"static String? toJsonNullable({enum_config.name}? type) => "
                    + "type == null ? null : toJson(type);\n\n"
                )
                _ = enum_scope.token(
                    f"static {enum_config.name}? fromJsonNullable(String? json) => "
                    + "json == null ? null : fromJson(json);\n"
                )
            _ = enum_scope.token("}\n\n")

            # List/Set helpers for collection enum attributes (used by @JsonKey(fromJson/toJson) emit).
            _ = enum_scope.token(f"extension List{enum_config.name}Extension on List<{enum_config.name}> {{\n")
            with enum_scope.indent():
                _ = enum_scope.token(
                    f"static List<String> toJson(List<{enum_config.name}> values) => "
                    + f"values.map({enum_config.name}Extension.toJson).toList();\n\n"
                )
                _ = enum_scope.token(
                    f"static List<{enum_config.name}> fromJson(List<dynamic> json) => "
                    + f"json.map((e) => {enum_config.name}Extension.fromJson(e as String)).toList();\n\n"
                )
                _ = enum_scope.token(
                    f"static List<String>? toJsonNullable(List<{enum_config.name}>? values) => "
                    + "values == null ? null : toJson(values);\n\n"
                )
                _ = enum_scope.token(
                    f"static List<{enum_config.name}>? fromJsonNullable(List<dynamic>? json) => "
                    + "json == null ? null : fromJson(json);\n"
                )
            _ = enum_scope.token("}\n\n")

            _ = enum_scope.token(f"extension Set{enum_config.name}Extension on Set<{enum_config.name}> {{\n")
            with enum_scope.indent():
                _ = enum_scope.token(
                    f"static List<String> toJson(Set<{enum_config.name}> values) => "
                    + f"values.map({enum_config.name}Extension.toJson).toList();\n\n"
                )
                _ = enum_scope.token(
                    f"static Set<{enum_config.name}> fromJson(List<dynamic> json) => "
                    + f"json.map((e) => {enum_config.name}Extension.fromJson(e as String)).toSet();\n\n"
                )
                _ = enum_scope.token(
                    f"static List<String>? toJsonNullable(Set<{enum_config.name}>? values) => "
                    + "values == null ? null : toJson(values);\n\n"
                )
                _ = enum_scope.token(
                    f"static Set<{enum_config.name}>? fromJsonNullable(List<dynamic>? json) => "
                    + "json == null ? null : fromJson(json);\n"
                )
            _ = enum_scope.token("}")

    def _resolve_parent_class_config(
        self,
        class_config: ClassConfig,
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
    ) -> ClassConfig | None:
        """Resolve a ClassConfig parent even when ORM side-loading is filtered."""

        parent = class_config.parent_class
        if parent is not None:
            return parent

        parent_id = class_config.parent_class_id
        if parent_id is None:
            return None

        if class_to_class_config_map is not None:
            resolved = class_to_class_config_map.get(parent_id)
            if resolved is not None:
                return resolved

        resolved = self._graph_classes_by_id.get(parent_id)
        if resolved is not None:
            return resolved

        return None

    def _ordered_attribute_configs(
        self,
        class_config: ClassConfig,
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        *,
        _seen_classes: set[UUID] | None = None,
    ) -> list[AttributeConfig]:
        """Return AttributeConfig in canonical SSOT order across augment/inheritance chains."""

        if _seen_classes is None:
            _seen_classes = set()
        if class_config.id in _seen_classes:
            return []
        _seen_classes.add(class_config.id)

        parent = self._resolve_parent_class_config(
            class_config,
            class_to_class_config_map=class_to_class_config_map,
        )
        parent_attrs = (
            self._ordered_attribute_configs(
                parent,
                class_to_class_config_map=class_to_class_config_map,
                _seen_classes=_seen_classes,
            )
            if parent is not None
            else []
        )

        # Canonical override semantics:
        # - If a child re-declares an attribute with the same name, treat it as an override
        #   (replace the inherited attribute) rather than emitting duplicates.
        # - IDs are still used to guard against repeated links to the same AttributeConfig.
        ordered: list[AttributeConfig] = list(parent_attrs)
        index_by_name: dict[str, int] = {a.name: i for i, a in enumerate(ordered)}
        seen_attr_ids: set[UUID] = {a.id for a in ordered}

        ordered_links = sorted(
            class_config.class_config_attribute_configs,
            key=lambda link: (link.position, (link.attribute_config.name if link.attribute_config else "")),
        )
        for link in ordered_links:
            attr = link.attribute_config
            if attr.id in seen_attr_ids:
                continue
            # Override-by-name (replaces the inherited attribute, preserving parent ordering).
            if attr.name in index_by_name:
                idx = index_by_name[attr.name]
                prior = ordered[idx]
                seen_attr_ids.discard(prior.id)
                ordered[idx] = attr
            else:
                index_by_name[attr.name] = len(ordered)
                ordered.append(attr)
            seen_attr_ids.add(attr.id)

        return ordered

    def _render_class(
        self,
        writer: CodeSectionWriter,
        class_config: ClassConfig,
        class_to_class_config_map: dict[UUID, ClassConfig],
    ) -> None:
        """
        Render a class using freezed annotation.

        Args:
            writer: The CodeSectionWriter to write to
            class_config: The class config to render
            schema: Schema name for the objects in this file
            class_to_class_config_map: Global lookup for ClassConfig by id (optional)
        """
        # Add description as comment if available
        if class_config.description:
            for line in class_config.description.split("\n"):
                _ = writer.token(f"/// {line}\n")

        # Start class definition using assembler
        with writer.start_section(self._spec_class, qualname=class_config.name) as cls:
            # Freezed annotation
            _ = cls.token("@freezed\n")

            # Class declaration
            _ = cls.token("abstract class ")
            _ = cls.token(class_config.name, CodeSectionClassSegment.NAME.value)
            _ = cls.token(f" with _${class_config.name} {{\n")

            # Use indentation for class body
            with cls.indent():
                # JsonSerializable annotation for factory constructor
                _ = cls.token("@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)\n")
                _ = cls.token(f"factory {class_config.name}.def({{\n")

                # Canonical field ordering: preserve SSOT order of appearance.
                attrs_in_order: list[tuple[AttributeConfig, bool]] = []
                for attr in self._ordered_attribute_configs(
                    class_config,
                    class_to_class_config_map=class_to_class_config_map,
                ):
                    type_info = resolve_type_info(attr)
                    if not self._should_emit_attribute_for_policy(class_config, attr, type_info):
                        continue
                    is_relationship = (
                        type_info.kind == AttributeTypeDescriptorKind.class_ and type_info.class_config is not None
                    )
                    attrs_in_order.append((attr, is_relationship))

                # Canonical: edge-backed sugar is expressed via ClassConfigRelationship, not ObjectConfig.
                # For now we render all relationship attributes; canonical renderers will later add
                # explicit edge-backed policy based on relationship associations.
                edge_backed_rel_attrs: list[AttributeConfig] = []

                # Render primitive attributes in factory constructor
                with cls.indent():
                    for attr, is_relationship in attrs_in_order:
                        if is_relationship:
                            if attr in edge_backed_rel_attrs:
                                continue
                            self._render_relationship_parameter(cls, attr, is_factory=False)
                        else:
                            self._render_factory_parameter(cls, attr)

                _ = cls.token(f"}}) = _{class_config.name};\n\n")

                # Regular factory constructor
                _ = cls.token(f"factory {class_config.name}({{\n")
                with cls.indent():
                    for attr, is_relationship in attrs_in_order:
                        if is_relationship:
                            if attr in edge_backed_rel_attrs:
                                continue
                            self._render_relationship_parameter(cls, attr, is_factory=True)
                        else:
                            self._render_constructor_parameter(cls, attr)

                _ = cls.token("}) {\n")
                with cls.indent():
                    _ = cls.token(f"return _{class_config.name}(\n")
                    with cls.indent():
                        for attr, is_relationship in attrs_in_order:
                            if is_relationship and attr in edge_backed_rel_attrs:
                                continue

                            field_name = to_camel_case(attr.name)
                            overlay = self.get_overlay_by_entity_id(
                                CodeSectionAnnotationOverlayEntity.attribute, attr.id
                            )
                            if overlay:
                                if not isinstance(overlay, AttributeConfigOverlay):
                                    raise ValueError(
                                        f"Overlay for attribute {attr.id} is not an AttributeConfigOverlay"
                                    )
                                if overlay.rendered_name:
                                    field_name = overlay.rendered_name

                            _ = cls.token(f"{field_name}: {field_name}")
                            if not is_relationship and attr.name == "id":
                                _ = cls.token(" ?? UuidValue.fromString(Uuid().v4())")
                            _ = cls.token(",\n")

                    _ = cls.token(");\n")
                _ = cls.token("}\n\n")

                # JSON factory constructor
                _ = cls.token(f"factory {class_config.name}.fromJson(Map<String, dynamic> json) => ")
                _ = cls.token(f"_${class_config.name}FromJson(json);\n")

            _ = cls.token("}")

    def _render_discriminated_union(
        self,
        writer: CodeSectionWriter,
        union: _DiscriminatedUnion,
        variants: list[_DiscriminatedUnionVariant],
    ) -> None:
        """
        Render a Freezed discriminated union based on `.aware` discriminate annotations.

        This is the canonical Dart representation for API unions:
        - `union.discriminator` becomes the Freezed `unionKey`
        - Each tagged variant becomes a union constructor with `@FreezedUnionValue(tag)`
        """

        base = union.base_class
        discriminator = union.discriminator

        # Add description as comment if available
        if base.description:
            for line in base.description.split("\n"):
                _ = writer.token(f"/// {line}\n")

        with writer.start_section(self._spec_class, qualname=base.name) as cls:
            _ = cls.token(f"@Freezed(unionKey: '{discriminator}')\n")
            _ = cls.token("abstract class ")
            _ = cls.token(base.name, CodeSectionClassSegment.NAME.value)
            _ = cls.token(f" with _${base.name} {{\n")

            with cls.indent():
                for variant in variants:
                    tag_value = variant.tag_value
                    variant_class = variant.class_config

                    ctor_name = to_camel_case(tag_value)

                    _ = cls.token(f"@FreezedUnionValue('{tag_value}')\n")
                    _ = cls.token("@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)\n")
                    _ = cls.token(f"factory {base.name}.{ctor_name}({{\n")

                    # Canonical field ordering: preserve SSOT order of appearance.
                    attrs_in_order: list[tuple[AttributeConfig, bool]] = []
                    for attr in self._ordered_attribute_configs(variant_class):
                        if attr.name == discriminator:
                            continue
                        type_info = resolve_type_info(attr)
                        if not self._should_emit_attribute_for_policy(variant_class, attr, type_info):
                            continue
                        is_relationship = (
                            type_info.kind == AttributeTypeDescriptorKind.class_ and type_info.class_config is not None
                        )
                        attrs_in_order.append((attr, is_relationship))

                    with cls.indent():
                        for attr, is_relationship in attrs_in_order:
                            if is_relationship:
                                self._render_relationship_parameter(cls, attr, is_factory=False)
                            else:
                                self._render_union_parameter(cls, attr)

                    _ = cls.token(f"}}) = {variant_class.name};\n\n")

                _ = cls.token(
                    f"factory {base.name}.fromJson(Map<String, dynamic> json) => _${base.name}FromJson(json);\n"
                )

            _ = cls.token("}")

    def _render_union_parameter(self, scope: CodeSectionScope, attr_config: AttributeConfig) -> None:
        """
        Render a constructor parameter for union variants.

        This intentionally avoids CodeSection sub-scopes (attribute qualnames would collide
        across multiple union constructors), while still honoring overlays and type adapters.
        """

        dart_type = self._get_type_from_attribute_config(attr_config)
        type_info = resolve_type_info(attr_config)
        list_default = self._should_default_empty_list(attr_config)

        rendered_name = to_camel_case(attr_config.name)
        wire_name: str | None = None
        overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.attribute, attr_config.id)
        if overlay is not None:
            if not isinstance(overlay, AttributeConfigOverlay):
                raise ValueError(f"Overlay for attribute {attr_config.id} is not an AttributeConfigOverlay")
            if overlay.rendered_name:
                rendered_name = overlay.rendered_name
            if overlay.wire_name:
                wire_name = overlay.wire_name

        if dart_type == "UuidValue":
            _ = scope.token("@UuidValueConverter() ")
        elif dart_type == "List<UuidValue>":
            _ = scope.token("@UuidValueListConverter() ")
        elif dart_type == "Uint8List":
            _ = scope.token("@Uint8ListConverter() ")
        elif self._is_enum_type(attr_config):
            name_prefix = f"name: '{wire_name}', " if wire_name else ""
            enum_name = type_info.enum_config.name if type_info.enum_config is not None else None
            enum_ext = (
                f"List{enum_name}Extension"
                if enum_name and type_info.collection_kind == AttributeCollectionType.list
                else (
                    f"Set{enum_name}Extension"
                    if enum_name and type_info.collection_kind == AttributeCollectionType.set
                    else f"{enum_name}Extension" if enum_name else f"{dart_type}Extension"
                )
            )
            _ = scope.token(f"@JsonKey({name_prefix}fromJson: {enum_ext}.")
            _ = scope.token("fromJsonNullable" if self._is_optional_on_runtime(attr_config) else "fromJson")
            _ = scope.token(f", toJson: {enum_ext}.")
            _ = scope.token("toJsonNullable" if self._is_optional_on_runtime(attr_config) else "toJson")
            _ = scope.token(") ")
        elif wire_name:
            _ = scope.token(f"@JsonKey(name: '{wire_name}') ")

        if list_default:
            _ = scope.token("@Default(const []) ")

        if not self._is_optional_on_runtime(attr_config) and not list_default:
            _ = scope.token("required ")

        _ = scope.token(dart_type)
        if self._is_optional_on_runtime(attr_config) and not dart_type.endswith("?") and not list_default:
            _ = scope.token("?")
        _ = scope.token(f" {rendered_name},\n")

    def _render_factory_parameter(self, scope: CodeSectionScope, attr_config: AttributeConfig) -> None:
        """
        Render a parameter in the factory constructor.

        Args:
            scope: The CodeSectionScope to write to
            attr_config: The attribute config to render
        """
        # Create qualified name for the attribute
        qualname = f"{scope.qualname}.{attr_config.name}"

        with scope.start_section(
            SectionSpec(
                section_type=CodeSectionType.attribute,
                assemble=lambda code_section, segments, _nested: assemble_attribute(
                    code_section=code_section,
                    segments=segments,
                    is_required=attr_config.is_required,
                    is_public=attr_config.is_public,
                    is_unique=attr_config.is_unique,
                    is_primary=attr_config.is_primary,
                ),
            ),
            qualname=qualname,
        ) as attr:
            # Add type-specific annotations
            dart_type = self._get_type_from_attribute_config(attr_config)
            type_info = resolve_type_info(attr_config)
            list_default = self._should_default_empty_list(attr_config)

            # Apply overlay if present (reserved keywords, explicit overlays, etc.)
            rendered_name = to_camel_case(attr_config.name)
            wire_name: str | None = None
            overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.attribute, attr_config.id)
            if overlay is not None:
                if not isinstance(overlay, AttributeConfigOverlay):
                    raise ValueError(f"Overlay for attribute {attr_config.id} is not an AttributeConfigOverlay")
                if overlay.rendered_name:
                    rendered_name = overlay.rendered_name
                if overlay.wire_name:
                    wire_name = overlay.wire_name

            if dart_type == "UuidValue":
                _ = attr.token("@UuidValueConverter() ")
            elif dart_type == "List<UuidValue>":
                _ = attr.token("@UuidValueListConverter() ")
            elif dart_type == "Uint8List":
                _ = attr.token("@Uint8ListConverter() ")
            elif self._is_enum_type(attr_config):
                # Single JsonKey annotation: include `name:` when we renamed the identifier.
                name_prefix = f"name: '{wire_name}', " if wire_name else ""
                enum_name = type_info.enum_config.name if type_info.enum_config is not None else None
                enum_ext = (
                    f"List{enum_name}Extension"
                    if enum_name and type_info.collection_kind == AttributeCollectionType.list
                    else (
                        f"Set{enum_name}Extension"
                        if enum_name and type_info.collection_kind == AttributeCollectionType.set
                        else f"{enum_name}Extension" if enum_name else f"{dart_type}Extension"
                    )
                )
                _ = attr.token(f"@JsonKey({name_prefix}fromJson: {enum_ext}.")
                if self._is_optional_on_runtime(attr_config):
                    _ = attr.token("fromJsonNullable")
                else:
                    _ = attr.token("fromJson")
                _ = attr.token(f", toJson: {enum_ext}.")
                if self._is_optional_on_runtime(attr_config):
                    _ = attr.token("toJsonNullable")
                else:
                    _ = attr.token("toJson")
                _ = attr.token(") ")
            elif wire_name:
                # Preserve the canonical wire name when the rendered identifier differs.
                _ = attr.token(f"@JsonKey(name: '{wire_name}') ")

            if list_default:
                _ = attr.token("@Default(const []) ")

            # Required keyword for non-optional fields
            if not self._is_optional_on_runtime(attr_config) and not list_default:
                _ = attr.token("required ")

            # Type and name (camelCase field name in Dart)
            _ = attr.token(dart_type, CodeSectionAttributeSegment.TYPE.value)
            if self._is_optional_on_runtime(attr_config) and not dart_type.endswith("?") and not list_default:
                _ = attr.token("?")
            _ = attr.token(" ")
            _ = attr.token(rendered_name, CodeSectionAttributeSegment.NAME.value)
            _ = attr.token(",\n")

    def _render_constructor_parameter(self, scope: CodeSectionScope, attr_config: AttributeConfig) -> None:
        """
        Render a parameter in the regular constructor.

        Args:
            scope: The CodeSectionScope to write to
            attr_config: The attribute config to render
        """
        dart_type = self._get_type_from_attribute_config(attr_config)
        param_name = to_camel_case(attr_config.name)
        overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.attribute, attr_config.id)
        if overlay is not None:
            if not isinstance(overlay, AttributeConfigOverlay):
                raise ValueError(f"Overlay for attribute {attr_config.id} is not an AttributeConfigOverlay")
            if overlay.rendered_name:
                param_name = overlay.rendered_name

        if self._should_default_empty_list(attr_config):
            _ = scope.token(f"{dart_type} {param_name} = const [],\n")
            return

        if not self._is_optional_on_constructor(attr_config):
            _ = scope.token("required ")

        _ = scope.token(dart_type)
        if self._is_optional_on_constructor(attr_config) and not dart_type.endswith("?"):
            _ = scope.token("?")
        _ = scope.token(f" {param_name},\n")

    def _render_relationship_parameter(
        self, scope: CodeSectionScope, attr_config: AttributeConfig, is_factory: bool = False
    ) -> None:
        """
        Render a relationship parameter.

        Args:
            scope: The CodeSectionScope to write to
            attr_config: The attribute config to render
            is_factory: Whether the parameter is being rendered in the factory constructor
        """
        type_info = resolve_type_info(attr_config)
        if type_info.kind != AttributeTypeDescriptorKind.class_ or type_info.class_config is None:
            return

        class_name = to_pascal_case(type_info.class_config.name)
        attribute_name = to_camel_case(attr_config.name)

        # Apply overlay if present
        prefix = ""
        overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.attribute, attr_config.id)
        if overlay:
            if not isinstance(overlay, AttributeConfigOverlay):
                raise ValueError(f"Overlay for attribute {attr_config.id} is not an AttributeConfigOverlay")
            if overlay.rendered_name:
                attribute_name = overlay.rendered_name
            if overlay.wire_name:
                prefix = f"@JsonKey(name: '{overlay.wire_name}') "

        # Render the parameter
        is_list = self._relationship_is_list_from_descriptor(attr_config)
        if is_list:
            if is_factory:
                _ = scope.token(f"{prefix}List<{class_name}> {attribute_name} = const [],\n")
            else:
                _ = scope.token(f"{prefix}@Default(const []) List<{class_name}> {attribute_name},\n")
        else:
            is_optional = (
                self._is_optional_on_constructor(attr_config)
                if is_factory
                else self._is_optional_on_runtime(attr_config)
            )
            if not is_optional:
                _ = scope.token(f"{prefix}required {class_name} {attribute_name},\n")
            else:
                _ = scope.token(f"{prefix}{class_name}? {attribute_name},\n")

    def _should_emit_attribute_for_policy(
        self,
        class_config: ClassConfig,
        attr_config: AttributeConfig,
        type_info: AttributeTypeInfo,
    ) -> bool:
        target_cls = type_info.class_config
        if type_info.kind == AttributeTypeDescriptorKind.class_ and target_cls is not None:
            target_is_inline = target_cls.value_mode == ClassValueMode.inline_value
            if (
                class_config.value_mode != ClassValueMode.inline_value
                and not target_is_inline
            ):
                if not self.policy.emit_relationship_fields:
                    return False
                target_class_id = resolve_type_class_config_id(attr_config)
                if (
                    not self.policy.emit_external_relationship_fields
                    and target_class_id not in self._bound_graph_class_ids
                ):
                    return False
                if (
                    self.policy.external_relationship_import_root_suffix
                    and target_class_id not in self._bound_graph_class_ids
                    and not self._external_relationship_import_override_matches_policy(
                        target_class_id=target_class_id,
                    )
                ):
                    return False
        primitive_config = type_info.primitive_config
        if (
            not attr_config.is_public
            and type_info.kind == AttributeTypeDescriptorKind.primitive
            and primitive_config is not None
            and CodePrimitiveType.model_validate(primitive_config.primitive_type).base_type
            == CodePrimitiveBaseType.uuid
            and not self.policy.emit_foreign_key_fields
        ):
            return False
        return True

    def _external_relationship_import_override_matches_policy(self, *, target_class_id: UUID | None) -> bool:
        if target_class_id is None:
            return False
        suffix = self.policy.external_relationship_import_root_suffix
        if not suffix:
            return True
        override = (self.import_overrides or {}).get(str(target_class_id))
        if not override:
            return False
        if override.startswith("package:"):
            package_root = override.removeprefix("package:").split("/", 1)[0]
        else:
            package_root = override.split("/", 1)[0]
        return package_root.endswith(suffix)

    def _render_function(self, writer: CodeSectionWriter, function_config: FunctionConfig, schema: str) -> None:
        """
        Render a standalone function.

        Args:
            writer: The CodeSectionWriter to write to
            function_config: The function config to render
            schema: Schema name for the objects in this file
        """
        _ = schema

        # Start function section using assembler
        with writer.start_section(
            SectionSpec(
                section_type=CodeSectionType.function,
                assemble=lambda code_section, segments, _nested: assemble_function(
                    code_section=code_section,
                    segments=segments,
                    is_public=True,
                    description=function_config.description if function_config.description else None,
                ),
            ),
            qualname=function_config.name,
        ) as func:
            # Add description as comment if available
            if function_config.description:
                _ = func.token(f"/// {function_config.description}\n")

            # Function signature
            _ = func.token("void ")  # Default return type - can be enhanced
            _ = func.token(function_config.name, CodeSectionFunctionSegment.NAME.value)
            _ = func.token("()", CodeSectionFunctionSegment.SIGNATURE.value)
            _ = func.token(" {\n")

            # Function body
            with func.indent():
                _ = func.token("// TODO: Implement function\n")

            _ = func.token("}")

    def _get_type_from_attribute_config(self, attr_config: AttributeConfig) -> str:
        """
        Get the Dart type for an attribute.

        Args:
            attr_config: The attribute config

        Returns:
            Dart type string
        """
        type_info = resolve_type_info(attr_config)

        base_type = "dynamic"
        if type_info.kind == AttributeTypeDescriptorKind.primitive and type_info.primitive_config:
            prim = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
            base_type = self._primitive_codec.render(prim) or "dynamic"
        elif type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config:
            enum_id = type_info.enum_config.id
            # Use enum type when:
            # - it is emitted in this file (no import needed), OR
            # - it is importable cross-file within this package (layout has the entity), OR
            # - it is importable cross-package via import_overrides (SSOT: node-paths manifest).
            if enum_id in self._local_enum_ids:
                base_type = type_info.enum_config.name
            elif self.import_overrides and self.import_overrides.get(str(enum_id)):
                base_type = type_info.enum_config.name
            else:
                if self._layout_has_entity_path(enum_id):
                    base_type = type_info.enum_config.name
                else:
                    # Otherwise fall back to String so codegen can proceed without an unresolved symbol.
                    base_type = "String"
        elif type_info.kind == AttributeTypeDescriptorKind.class_ and type_info.class_config:
            base_type = to_pascal_case(type_info.class_config.name)

        # Descriptor-first: collection kind is SSOT (e.g. `String[]` in `.aware` must become `List<String>` in Dart).
        if type_info.collection_kind == AttributeCollectionType.list:
            return f"List<{base_type}>"
        if type_info.collection_kind == AttributeCollectionType.set:
            return f"Set<{base_type}>"

        return base_type

    def _get_type_from_primitive_type(self, dart_primitive_type: CodePrimitiveType) -> str:
        # Back-compat helper kept temporarily; SSOT is the primitive codec.
        return self._primitive_codec.render(dart_primitive_type) or "dynamic"

    # Descriptor-driven helpers -------------------------------------------------

    def _relationship_is_list_from_descriptor(self, attr_config: AttributeConfig) -> bool:
        """
        Determine whether a relationship attribute is a collection using its descriptor tree.

        We intentionally avoid AttributeConfig.is_list() here because that depends on
        AttributeConfigObjectConfigRelationshipSide wiring, which is optional for many
        meta/kernel relationships. The descriptor is the canonical source of truth.
        """
        try:
            type_info = resolve_type_info(attr_config)
            return bool(type_info.is_collection)
        except Exception as e:
            logger.debug(f"Descriptor collection inference failed for {attr_config.name}: {e}")
            return False

    def _is_enum_type(self, attr_config: AttributeConfig) -> bool:
        """Check if the attribute is an enum type."""
        type_info = resolve_type_info(attr_config)
        if type_info.kind != AttributeTypeDescriptorKind.enum or type_info.enum_config is None:
            return False
        enum_id = type_info.enum_config.id
        if enum_id in self._local_enum_ids:
            return True
        if self.import_overrides and self.import_overrides.get(str(enum_id)):
            return True
        return self._layout_has_entity_path(enum_id)

    def _layout_has_entity_path(self, entity_id: UUID) -> bool:
        """Return whether the active layout stack can place an entity."""

        entity_key = str(entity_id)
        layout: ObjectConfigGraphRenderLayoutStrategy | None = self.layout_strategy
        while layout is not None:
            if entity_key in getattr(layout, "entity_template_paths", {}):
                return True
            if entity_key in getattr(layout, "entity_layout_paths", {}):
                return True
            layout = layout.get_parent()
        return False

    def _is_optional_on_runtime(self, attr_config: AttributeConfig) -> bool:
        """Check if the attribute is optional at runtime."""
        if attr_config.id in self._lazy_attr_ids:
            return True
        return not attr_config.is_required

    def _is_optional_on_constructor(self, attr_config: AttributeConfig) -> bool:
        """Check if the attribute is optional in the constructor."""
        # ID is optional in constructor as it has a default
        return attr_config.name in ["id"] or not attr_config.is_required

    def _should_default_empty_list(self, attr_config: AttributeConfig) -> bool:
        """Return True when the attribute is a list collection that should default to empty."""
        type_info = resolve_type_info(attr_config)
        return type_info.collection_kind == AttributeCollectionType.list

    def _attribute_is_base_type(self, attr_config: AttributeConfig, base_type: CodePrimitiveBaseType) -> bool:
        """
        Determine whether the given attribute uses a primitive type of the given base type.

        This mirrors the primitive-type resolution used in _get_type_from_primitive_type so that
        imports for the given base type are driven by the same type information, including
        unions and nested container types.
        """
        type_info = resolve_type_info(attr_config)
        if type_info.kind != AttributeTypeDescriptorKind.primitive or type_info.primitive_config is None:
            return False
        code_primitive_type = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
        return self._primitive_type_uses_base_type(code_primitive_type, base_type)

    def _primitive_type_uses_base_type(
        self,
        dart_primitive_type: CodePrimitiveType,
        base_type: CodePrimitiveBaseType,
    ) -> bool:
        """
        Recursively determine whether a CodePrimitiveType (including unions/containers)
        references the given base_type anywhere in its structure.
        """
        bt = dart_primitive_type.base_type

        # Direct match
        if bt == base_type:
            return True

        # Union types – check all union members (e.g. Bytes? => UNION[BYTES, NULL])
        if bt == CodePrimitiveBaseType.union and dart_primitive_type.union_types:
            return any(self._primitive_type_uses_base_type(t, base_type) for t in dart_primitive_type.union_types)

        # Arrays – check the item type
        if bt == CodePrimitiveBaseType.array and dart_primitive_type.item_type:
            return self._primitive_type_uses_base_type(dart_primitive_type.item_type, base_type)

        # Dicts – check key/value types (conservative)
        if bt == CodePrimitiveBaseType.dict:
            key = dart_primitive_type.key_type
            value = dart_primitive_type.value_type
            return any(self._primitive_type_uses_base_type(t, base_type) for t in (key, value) if t is not None)

        return False


def _normalize_relative_import_path(*, import_path: str, current_module: str | None) -> str:
    if current_module is None or import_path.startswith("package:") or import_path.startswith("dart:"):
        return import_path
    current_path = PurePosixPath(current_module)
    target_path = PurePosixPath(import_path)
    if not current_path.parts or not target_path.parts:
        return import_path
    current_parent = current_path.parent
    current_parts = current_parent.parts
    target_parts = target_path.parts
    shared_prefix_len = 0
    for current_part, target_part in zip(current_parts, target_parts):
        if current_part != target_part:
            break
        shared_prefix_len += 1

    upward = [".."] * (len(current_parts) - shared_prefix_len)
    downward = list(target_parts[shared_prefix_len:])
    relative_parts = upward + downward
    if not relative_parts:
        return target_path.name
    return "/".join(relative_parts)

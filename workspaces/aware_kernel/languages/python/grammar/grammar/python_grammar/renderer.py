"""
Python one-shot renderer for generating structure + IO models from meta models.

This renderer uses CodeSectionWriter for deterministic layout (imports, spacing)
but emits *generated, non-editable* artifacts:
- Structure-only ORMModel classes (no methods/behavior).
- Pydantic IO classes (Input/Output per function).
- A registry mapping function name → canonical metadata + IO classes.
"""

# Standard
import json
import re
import textwrap
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import cast
from uuid import UUID
from typing_extensions import override

# Code Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Content Ontology
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Content Runtime
# Code Runtime
from aware_code.section.class_.assembler import assemble_class
from aware_code.section.function.assembler import assemble_function
from aware_code.section.function.segments import CodeSectionFunctionSegment
from aware_code.section.attribute.assembler import assemble_attribute
from aware_code.section.attribute.segments import CodeSectionAttributeSegment
from aware_code.section.import_.assembler import assemble_import
from aware_code.section.import_.segments import CodeSectionImportSegment
from aware_code.section.comment.assembler import assemble_comment
from aware_code.section.comment.segments import CodeSectionCommentSegment
from aware_code.section.enum.assembler import assemble_enum
from aware_code.section.enum_value.assembler import assemble_enum_value
from aware_code.section.writer import CodeSectionScope, CodeSectionWriter
from aware_code.section.spec import SectionSpec
from aware_types import JsonObject

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.annotation.code_section_annotation_oneof_enums import (
    CodeSectionAnnotationOneOfMode,
)
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_option_overlay import EnumOptionOverlay
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_config_overlay import (
    AttributeConfigOverlay,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Aware Kernel Meta
from aware_meta.graph.config.namespace.builder import (
    build_namespace_bundle_from_ocg_topology,
)
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    ObjectConfigGraphRendererPolicy,
    build_renderer_empty_code,
)
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.attribute.config.type_descriptor_helpers import (
    AttributeTypeInfo,
    resolve_type_class_config_id,
    resolve_type_info,
)
from aware_meta.class_.config.relationship.handlers import get_association_class_ids

# Python Grammar
from python_grammar.primitive_codec import PythonPrimitiveCodec
from python_grammar.renderer_token_emit import (
    emit_attribute_line,
    emit_class_header,
    emit_enum_header,
    emit_enum_value_line,
    emit_function_header,
)

# Utils
from aware_utils.string_transform import to_pascal_case, to_snake_case
from aware_utils.logging import logger

from python_grammar.renderer_policy import (
    PythonRenderPolicy,
)
from python_grammar.import_grouping import (
    PythonImportGroupingPolicy,
    group_python_imports,
    semantic_import_roots_from_renderer_inputs,
)

_PRIMITIVE_CODEC = PythonPrimitiveCodec()
_DOCSTRING_WRAP_WIDTH = 100


def _wrap_docstring_lines(description: str) -> list[str]:
    lines: list[str] = []
    for raw_line in description.strip("\n").splitlines():
        if not raw_line.strip():
            lines.append("")
            continue
        lines.extend(
            textwrap.wrap(
                raw_line,
                width=_DOCSTRING_WRAP_WIDTH,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [""]
        )
    return lines


@dataclass(frozen=True)
class FunctionRegistryEntry:
    function_config: FunctionConfig
    input_class_name: str
    output_class_name: str
    is_constructor: bool = False


@dataclass(frozen=True)
class ClassRegistryEntry:
    class_config: ClassConfig
    function_registry_entries: list[FunctionRegistryEntry]


@dataclass(frozen=True)
class AttributeRenderFlags:
    """
    SSOT for attribute-level rendering decisions that affect both:
    - emitted code (annotation/default/exclude)
    - required imports (e.g., whether `Field` is needed)
    """

    is_optional: bool
    is_collection: bool
    should_exclude: bool
    needs_field: bool


@dataclass
class ImportPlan:
    """
    Typed import collector to avoid brittle `dict[str, set[str]]` usage throughout the renderer.

    We keep the internal storage as a dict-of-sets for natural de-duplication, but the
    *API surface* is explicit and type-safe.
    """

    by_module: dict[str, set[str]] = field(default_factory=dict)

    def add(self, module: str, symbol: str) -> None:
        self.by_module.setdefault(module, set()).add(symbol)

    def merge(self, other: "ImportPlan") -> None:
        for module, symbols in other.by_module.items():
            target = self.by_module.setdefault(module, set())
            target.update(symbols)

    def as_mapping(self) -> dict[str, set[str]]:
        # Expose a mapping only at integration boundaries.
        return self.by_module


@dataclass(frozen=True)
class ImportNeeds:
    """
    Typed flags describing which support imports are needed for a rendered file.

    This replaces ad-hoc dict lookups like flags.get("field", False).
    """

    field: bool = False
    any_: bool = False
    uuid: bool = False
    datetime: bool = False
    serialize_as_any: bool = False
    field_validator: bool = False


class PythonRenderer(ObjectConfigGraphRendererLanguage):
    """
    Python implementation of the LanguagePlugin for rendering meta models to Python code.

    Uses the CodeSectionWriter and various assemblers to generate properly structured
    Python code from meta models.

    Section order for class bodies:
      1. Relationships
      2. Attributes
      3. Foreign Keys
      4. Edges
      5. Function facades
    Within each section, the canonical attribute ordering (ClassConfigAttributeConfig.position) is preserved.
    """

    _spec_class: SectionSpec
    _spec_enum: SectionSpec
    _spec_enum_value: SectionSpec
    _spec_comment: SectionSpec
    _spec_import: SectionSpec

    def __init__(
        self,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
        *,
        policy: PythonRenderPolicy | None = None,
    ):
        super().__init__(layout_strategy)
        self.policy: PythonRenderPolicy = policy or PythonRenderPolicy.orm_default()
        self._warnings: list[str] = []
        self._context_stack: list[str] = []
        # Per-file cache of relationship imports that should be treated as lazy
        # (resolved via ObjectConfigRelationshipSideLoadingStrategy).
        self._lazy_imports_for_file: dict[str, set[str]] = {}
        self._current_relationships_by_class_id: dict[UUID, list[ClassConfigRelationship]] = {}
        # Per-file FK attribute ids (derived from canonical relationship role metadata)
        self._fk_attr_ids: set[UUID] = set()
        # Per-file relationship REFERENCE attr ids that are edge-backed via association.
        # These should be imported via TYPE_CHECKING and rendered as @property views.
        self._edge_backed_ref_attr_ids: set[UUID] = set()
        # Discriminated unions (DTO/wire) - SSOT via compiled OCG annotations.
        # (class_config_id, attribute_name) -> tag_value
        self._discriminate_tag_by_class_and_attr: dict[tuple[UUID, str], str] = {}
        # (class_config_id, attribute_name) -> source_position (for deterministic tag ordering)
        self._discriminate_tag_position_by_class_and_attr: dict[tuple[UUID, str], int] = {}
        # Discriminator keys (base declarations): (class_config_id, attribute_name)
        self._discriminate_key_by_class_and_attr: set[tuple[UUID, str]] = set()
        # Explicit oneof (XOR) constraints: class_config_id -> [ [attr_name, ...], ... ]
        self._oneof_groups_by_class_config_id: dict[UUID, list[list[str]]] = {}
        # Current class context during attribute rendering.
        self._current_class_config_id: UUID | None = None
        # Layout ordering (relative_path, source_position) by entity id.
        self._layout_order_by_class_id: dict[UUID, tuple[str, int]] = {}
        self._layout_order_by_enum_id: dict[UUID, tuple[str, int]] = {}
        # Current module being emitted (import path), set during emit_file.
        self._current_module: str | None = None
        # Class ids that belong to the bound source graph, excluding external dependency graphs.
        self._bound_graph_class_ids: set[UUID] = set()
        self._type_info_by_attribute_config_id: dict[UUID, AttributeTypeInfo] = {}

    @override
    def set_policy(self, policy: ObjectConfigGraphRendererPolicy | None) -> None:
        """Inject a render policy (DTO vs ORM)."""
        if policy is None:
            self.policy = PythonRenderPolicy.orm_default()
            return
        if isinstance(policy, PythonRenderPolicy):
            self.policy = policy

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        """
        Bind graph-level state required for honest DTO emission.

        SSOT:
        - discriminator semantics are defined by compiled OCG annotations
          (ObjectConfigGraph.object_config_graph_annotations with DISCRIMINATE views).
        """

        # Reset per-graph state.
        self._discriminate_tag_by_class_and_attr = {}
        self._discriminate_tag_position_by_class_and_attr = {}
        self._discriminate_key_by_class_and_attr = set()
        self._oneof_groups_by_class_config_id = {}
        self._layout_order_by_class_id = {}
        self._layout_order_by_enum_id = {}
        self._type_info_by_attribute_config_id = {}
        self._bound_graph_class_ids = {
            node.class_config.id for node in graph.object_config_graph_nodes if node.class_config is not None
        }

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
                self._layout_order_by_class_id[node.class_config.id] = (
                    rel_path,
                    source_pos,
                )
            elif node.enum_config is not None:
                self._layout_order_by_enum_id[node.enum_config.id] = (
                    rel_path,
                    source_pos,
                )

        discrim_views = [
            a.code_section_annotation_discriminate
            for a in graph.object_config_graph_annotations
            if a.kind == ObjectConfigGraphAnnotationKind.discriminate
            and a.code_section_annotation_discriminate is not None
        ]
        oneof_views = [
            a.code_section_annotation_oneof
            for a in graph.object_config_graph_annotations
            if a.kind == ObjectConfigGraphAnnotationKind.oneof and a.code_section_annotation_oneof is not None
        ]
        if not discrim_views and not oneof_views:
            return

        # Resolve class targets deterministically via the graph topology namespace bundle.
        bundle = build_namespace_bundle_from_ocg_topology(ocg=graph)

        # Index classes by (package, namespace, class_name) for resolution.
        class_by_key: dict[tuple[str, str, str], ClassConfig] = {}
        for node in graph.object_config_graph_nodes:
            if node.class_config is None:
                continue
            ns = bundle.namespace_by_class_config_id.get(node.class_config.id)
            if ns is None:
                continue
            key = (ns.package, ns.namespace, node.class_config.name)
            # First wins; any ambiguity should have been caught during build-time validation.
            _ = class_by_key.setdefault(key, node.class_config)

        for v in discrim_views:
            mode = (v.mode or "").strip().lower()
            class_lookup_key = (
                v.fqn_prefix,
                v.namespace,
                v.class_name,
            )
            cls = class_by_key.get(class_lookup_key)
            if cls is None:
                continue
            if mode == "key":
                self._discriminate_key_by_class_and_attr.add((cls.id, v.attribute_name))
                continue
            if mode == "tag":
                tag_value = (v.tag_value or "").strip()
                if not tag_value:
                    continue
                class_attr_key = (cls.id, v.attribute_name)
                self._discriminate_tag_by_class_and_attr[class_attr_key] = tag_value
                if v.source_position is not None:
                    self._discriminate_tag_position_by_class_and_attr[class_attr_key] = int(v.source_position)
                continue

        for v in oneof_views:
            if v.mode != CodeSectionAnnotationOneOfMode.validation:
                continue
            key = (v.fqn_prefix, v.namespace, v.class_name)
            cls = class_by_key.get(key)
            if cls is None:
                continue
            attrs = [a for a in (v.attribute_names or []) if (a or "").strip()]
            if len(attrs) < 2:
                continue
            self._oneof_groups_by_class_config_id.setdefault(cls.id, []).append(attrs)

    @property
    @override
    def language(self) -> CodeLanguage:
        """Return the language supported by this plugin."""
        return CodeLanguage.python

    @property
    @override
    def indent(self) -> int:
        """Return the indentation size for this language."""
        return 4

    @property
    @override
    def comment_prefix(self) -> str:
        """Return the comment prefix for Python (#)."""
        return "#"

    @override
    def define_assemblers(self):
        # Canonical renderers should be free-function driven (no assembler classes).
        self._spec_class = SectionSpec(
            section_type=CodeSectionType.class_,
            assemble=lambda code_section, segments, nested: assemble_class(
                code_section=code_section,
                segments=segments,
                code_sections=nested,
            ),
        )
        self._spec_enum = SectionSpec(
            section_type=CodeSectionType.enum,
            assemble=lambda code_section, segments, nested: assemble_enum(
                code_section=code_section,
                segments=segments,
                code_sections=nested,
            ),
        )
        self._spec_enum_value = SectionSpec(
            section_type=CodeSectionType.enum_value,
            assemble=lambda code_section, segments, _nested: assemble_enum_value(
                code_section=code_section,
                segments=segments,
            ),
        )
        self._spec_comment = SectionSpec(
            section_type=CodeSectionType.comment,
            assemble=lambda code_section, segments, _nested: assemble_comment(
                code_section=code_section,
                segments=segments,
            ),
        )
        self._spec_import = SectionSpec(
            section_type=CodeSectionType.import_,
            assemble=lambda code_section, segments, _nested: assemble_import(
                code_section=code_section,
                segments=segments,
            ),
        )

    @override
    def clear_warnings(self) -> None:
        self._warnings.clear()

    @override
    def get_warnings(self) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for msg in self._warnings:
            if msg in seen:
                continue
            seen.add(msg)
            ordered.append(msg)
        return ordered

    @contextmanager
    def _attribute_context(self, context: str):
        self._context_stack.append(context)
        try:
            yield
        finally:
            _ = self._context_stack.pop()

    def _resolve_attribute_type_info(
        self,
        attribute_config: AttributeConfig,
        *,
        context: str,
    ) -> AttributeTypeInfo:
        cached = self._type_info_by_attribute_config_id.get(attribute_config.id)
        if cached is not None:
            return cached
        with self._attribute_context(context):
            type_info = resolve_type_info(attribute_config)
        self._type_info_by_attribute_config_id[attribute_config.id] = type_info
        return type_info

    def _is_nullable(self, attribute_config: AttributeConfig, type_info: AttributeTypeInfo) -> bool:
        if type_info.nullable:
            return True
        if attribute_config.default_value is not None:
            try:
                # default_value is stored as a string; treat JSON null as nullable.
                if json.loads(attribute_config.default_value) is None:
                    return True
            except Exception:
                # Non-JSON defaults do not imply nullability.
                pass
        return not attribute_config.is_required

    def _attribute_render_flags(
        self, attribute_config: AttributeConfig, type_info: AttributeTypeInfo
    ) -> AttributeRenderFlags:
        """
        Compute rendering flags from canonical semantics (honest SSOT).

        IMPORTANT:
        - "Optional" is derived from the canonical `AttributeConfig.is_required` (and descriptor nullability).
        - `exclude_serialization` is a canonical flag (set by transformers) and is mapped to
          Pydantic `Field(..., exclude=True)` by the renderer. The renderer must NOT re-derive
          exclude/optional semantics from relationship loading strategy.
        """
        is_optional = self._is_nullable(attribute_config, type_info)
        is_collection = type_info.is_collection
        should_exclude = attribute_config.exclude_serialization and self.policy.honor_exclude_serialization

        # SSOT: any time we materialize defaults via Pydantic (default/default_factory/exclude),
        # `Field` must be imported.
        #
        # Current renderer behavior:
        # - collections use Field(default_factory=...)
        # - explicit defaults use Field(default=...)
        # - implicit optional defaults use Field(default=None) (parity w/ checked-in ontology)
        needs_field = bool(
            attribute_config.default_value is not None
            or attribute_config.description
            or is_collection
            or is_optional
            or should_exclude
        )

        # Overlays: when an attribute is renamed or has a wire_name override, we must emit
        # `Field(alias=...)` so serialization stays stable while the Python identifier changes.
        overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.attribute, attribute_config.id)
        if overlay is not None and isinstance(overlay, AttributeConfigOverlay):
            if overlay.wire_name or (overlay.rendered_name and overlay.rendered_name != attribute_config.name):
                needs_field = True

        return AttributeRenderFlags(
            is_optional=is_optional,
            is_collection=is_collection,
            should_exclude=should_exclude,
            needs_field=needs_field,
        )

    def _with_field_description(self, default_expr: str | None, *, description: str) -> str:
        """Inject `description=...` into a Field(...) expression, or create Field(description=...) when missing."""
        desc = description.strip()
        if not desc:
            return default_expr or "Field()"

        desc_part = f"description={json.dumps(desc)}"
        if default_expr is None:
            return f"Field({desc_part})"
        expr = default_expr.strip()
        if expr.startswith("Field(") and expr.endswith(")"):
            inner = expr[len("Field(") : -1].strip()
            if "description=" in inner:
                return expr
            if not inner:
                return f"Field({desc_part})"
            return f"Field({inner}, {desc_part})"
        # Defensive fallback: wrap the expression as a default.
        return f"Field(default={expr}, {desc_part})"

    def _public_description(self, description: str | None) -> str | None:
        if not description or "api.public_package_plan" not in self.profile_inputs:
            return description
        return _scrub_public_api_client_text(description)

    def _attribute_overlay_names(self, attribute_config: AttributeConfig) -> tuple[str, str | None]:
        """
        Return (rendered_name, wire_name) for an AttributeConfig, honoring overlays.

        - rendered_name is used as the Python identifier.
        - wire_name (when present) is emitted via Field(alias=...) so JSON stays stable.
        """
        rendered_name = attribute_config.name
        wire_name: str | None = None
        overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.attribute, attribute_config.id)
        if overlay is not None and isinstance(overlay, AttributeConfigOverlay):
            if overlay.rendered_name:
                rendered_name = overlay.rendered_name
            if overlay.wire_name:
                wire_name = overlay.wire_name
        return rendered_name, wire_name

    def _with_field_alias(self, default_expr: str | None, *, alias: str) -> str:
        """Inject `alias=...` into a Field(...) expression, or create Field(alias=...) when missing."""
        alias_part = f"alias={json.dumps(alias)}"
        if default_expr is None:
            return f"Field({alias_part})"
        expr = default_expr.strip()
        if expr.startswith("Field(") and expr.endswith(")"):
            inner = expr[len("Field(") : -1].strip()
            if "alias=" in inner:
                return expr
            if not inner:
                return f"Field({alias_part})"
            return f"Field({inner}, {alias_part})"
        # Defensive fallback: wrap the expression as a default.
        return f"Field(default={expr}, {alias_part})"

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.python,
            renderer_key=type(self).__name__,
        )

    def _collect_file_imports(
        self,
        meta_objects: list[object],
        base_class_module: str,
        base_class_name: str,
        *,
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
    ) -> ImportPlan:
        """
        Collect all imports needed for the given meta objects.

        Args:
            meta_objects: List of meta objects to analyze

        Returns:
            ImportPlan for the file
        """
        imports = ImportPlan()
        current_module: str | None = None
        if self.layout_strategy:
            current_class = next((obj for obj in meta_objects if isinstance(obj, ClassConfig)), None)
            if current_class:
                current_file = self.layout_strategy.get_class_file_path(current_class)
                current_module = self.layout_strategy.get_module_import_path(current_file)

        def add(module: str, symbol: str) -> None:
            imports.add(module, symbol)

        has_unparented_graph_ref_class = False
        has_inline_value_class = False
        has_function_constructor = False
        has_function_instance = False
        needs_base_model = False
        needs_field = False
        needs_any = False
        needs_enum = False
        needs_uuid = False
        needs_datetime = False
        needs_serialize_as_any = False
        needs_field_validator = False
        needs_class_var = False
        needs_lru_cache = False
        needs_model_validator = False
        needs_literal = False
        functions: list[FunctionConfig] = []
        class_to_class_config_map = class_to_class_config_map or {}
        tagged_class_ids = {cls_id for cls_id, _attr in self._discriminate_tag_by_class_and_attr}
        policy = self.policy
        should_emit_functions = (
            policy.emit_function_facades or policy.emit_function_io_models or policy.emit_function_registry
        )

        for obj in meta_objects:
            if isinstance(obj, EnumConfig):
                needs_enum = True
                continue
            if isinstance(obj, ClassConfig):
                if obj.value_mode == ClassValueMode.inline_value:
                    if obj.parent_class is None and obj.parent_class_id is None:
                        has_inline_value_class = True
                elif obj.parent_class is None:
                    has_unparented_graph_ref_class = True
                if self.policy.emit_discriminated_union_parsers and any(
                    base_id == obj.id for base_id, _attr in self._discriminate_key_by_class_and_attr
                ):
                    needs_class_var = True
                    needs_lru_cache = True
                if self.policy.emit_discriminator_literal_types and obj.id in tagged_class_ids:
                    needs_literal = True
                if obj.id in self._oneof_groups_by_class_config_id:
                    needs_model_validator = True
                # Extend functions list with function configs using canonical ordering.
                if should_emit_functions:
                    for fc_link in sorted(
                        obj.class_config_function_configs,
                        key=lambda link: (
                            link.position,
                            link.function_config.name,
                        ),
                    ):
                        if fc_link.is_constructor:
                            has_function_constructor = True
                        else:
                            has_function_instance = True
                        functions.append(fc_link.function_config)

                class_imports, needs = self._gather_imports(
                    obj,
                    current_module,
                    class_to_class_config_map=class_to_class_config_map,
                )
                imports.merge(class_imports)
                needs_field = needs_field or needs.field
                needs_any = needs_any or needs.any_
                needs_uuid = needs_uuid or needs.uuid
                needs_datetime = needs_datetime or needs.datetime
                needs_serialize_as_any = needs_serialize_as_any or needs.serialize_as_any
                needs_field_validator = needs_field_validator or needs.field_validator
            if isinstance(obj, ClassConfigRelationship) and (
                policy.emit_relationship_fields or policy.emit_edge_backed_properties
            ):
                if obj.reified_from_relationship_id is not None:
                    continue
                if obj.class_config_relationship_association_edge is None:
                    continue
                target_cls = class_to_class_config_map.get(obj.target_class_config_id)
                if target_cls is None:
                    continue
                module_name = None
                if self.import_overrides:
                    override = self.import_overrides.get(str(target_cls.id), None)
                    if override:
                        module_name = override
                if module_name is None and self.layout_strategy:
                    related_path = self.layout_strategy.get_class_file_path(target_cls)
                    module_name = self.layout_strategy.get_module_import_path(related_path)
                if module_name and module_name != current_module:
                    self._lazy_imports_for_file.setdefault(module_name, set()).add(target_cls.name)

        # If the file renders any function facade IO models (Input/Output), it must import BaseModel
        # even when a function has zero parameters.
        if functions and policy.emit_function_io_models:
            needs_base_model = True

        for func in functions:
            # Heuristic: IO models may wrap optionals/any based on descriptors
            for fcac in func.function_config_attribute_configs:
                needs_base_model = True
                attr = fcac.attribute_config
                if attr.is_virtual:
                    continue
                try:
                    type_info = self._resolve_attribute_type_info(
                        attr,
                        context=f"{func.name}.{attr.name}",
                    )
                except Exception as exc:
                    logger.error(f"Failed to resolve descriptor for function attr {func.name}.{attr.name}: {exc}")
                    needs_any = True
                    continue

                if type_info.kind == AttributeTypeDescriptorKind.class_ and not type_info.class_config:
                    needs_any = True
                if type_info.kind == AttributeTypeDescriptorKind.primitive and type_info.primitive_config:
                    base = type_info.primitive_config.primitive_type.base_type
                    if base == CodePrimitiveBaseType.uuid:
                        needs_uuid = True
                    if base == CodePrimitiveBaseType.datetime:
                        needs_datetime = True
                    if base == CodePrimitiveBaseType.any:
                        needs_any = True

        if has_unparented_graph_ref_class:
            # Graph-ref classes inherit from the configured runtime base class (ORMModel by default).
            add(base_class_module, base_class_name)

        if has_inline_value_class:
            needs_base_model = True

        if needs_base_model:
            add("pydantic", "BaseModel")
        if needs_field:
            add("pydantic", "Field")
        if needs_serialize_as_any:
            add("pydantic", "SerializeAsAny")
        if needs_field_validator:
            add("pydantic", "field_validator")
        if needs_model_validator:
            add("pydantic", "model_validator")
        if needs_enum:
            add("enum", "Enum")
        if needs_any:
            add("typing", "Any")
        if needs_class_var:
            add("typing", "ClassVar")
        if needs_literal:
            add("typing", "Literal")
        if needs_lru_cache:
            add("functools", "lru_cache")
        if needs_uuid:
            add("uuid", "UUID")
        if needs_datetime:
            add("datetime", "datetime")
        # Lazy relationship imports require TYPE_CHECKING
        if self._lazy_imports_for_file:
            add("typing", "TYPE_CHECKING")
        if policy.emit_function_facades:
            if has_function_constructor:
                add("aware_orm.runtime.invocation", "invoke_constructor")
            if has_function_instance:
                add("aware_orm.runtime.invocation", "invoke_instance")

        return imports

    def _discriminator_key_attr_name(self, *, base_class_id: UUID) -> str | None:
        # Deterministic: `_discriminate_key_by_class_and_attr` is a set.
        attr_names = sorted([a for cls_id, a in self._discriminate_key_by_class_and_attr if cls_id == base_class_id])
        return attr_names[0] if attr_names else None

    def _discriminator_tagged_descendants(
        self,
        *,
        base_class_id: UUID,
        discriminator_attr_name: str,
        class_to_class_config_map: dict[UUID, ClassConfig],
    ) -> list[tuple[str, ClassConfig]]:
        """
        Return [(tag_value, class_config)] for descendants of `base_class_id` that declare a DISCRIMINATE tag.

        SSOT:
        - structural inheritance via ClassConfig.parent_class_id
        - discriminator tags via compiled OCG annotations (self._discriminate_tag_by_class_and_attr)
        """

        ordered: list[tuple[tuple[int, int | None, str], str, ClassConfig]] = []

        for cc in class_to_class_config_map.values():
            cursor: ClassConfig | None = cc
            is_descendant = False
            while cursor is not None and cursor.parent_class_id is not None:
                if cursor.parent_class_id == base_class_id:
                    is_descendant = True
                    break
                cursor = class_to_class_config_map.get(cursor.parent_class_id)

            if not is_descendant:
                continue

            tag_value = self._discriminate_tag_by_class_and_attr.get((cc.id, discriminator_attr_name))
            if not tag_value:
                continue
            pos = self._discriminate_tag_position_by_class_and_attr.get((cc.id, discriminator_attr_name))
            if pos is None:
                sort_key = (1, 0, tag_value)
            else:
                sort_key = (0, pos, tag_value)
            ordered.append((sort_key, tag_value, cc))

        ordered.sort(key=lambda item: item[0])
        return [(tag_value, cc) for _sort_key, tag_value, cc in ordered]

    def _render_discriminated_union_validators(
        self,
        *,
        cls_scope: CodeSectionScope,
        attrs: list[tuple[tuple[int, int | None], AttributeConfig]],
    ) -> bool:
        """
        Emit `@field_validator(..., mode="before")` methods for fields that reference a discriminator base class.

        This keeps DTO wire envelopes honest:
        - preserves full payloads when subclasses are assigned to base-typed fields (SerializeAsAny)
        - parses raw dict payloads into the correct subclass based on discriminator tags
        """

        if not attrs:
            return False

        wrote_any = False

        for _, attr_config in attrs:
            rendered_name, _wire_name = self._attribute_overlay_names(attr_config)
            try:
                type_info = self._resolve_attribute_type_info(
                    attr_config,
                    context=f"{cls_scope.qualname}.{rendered_name}",
                )
            except Exception:
                continue

            flags = self._attribute_render_flags(attr_config, type_info)
            if flags.is_collection:
                continue

            if type_info.kind != AttributeTypeDescriptorKind.class_ or type_info.class_config is None:
                continue

            base_cfg = type_info.class_config
            discriminator_attr = self._discriminator_key_attr_name(base_class_id=base_cfg.id)
            if discriminator_attr is None:
                continue

            if not wrote_any:
                _ = cls_scope.token("\n")
            wrote_any = True

            validator_name = f"_parse_{rendered_name}"
            _ = cls_scope.token(f'@field_validator("{rendered_name}", mode="before")\n')
            _ = cls_scope.token("@classmethod\n")
            _ = cls_scope.token(f"def {validator_name}(cls, v):\n")
            with cls_scope.indent():
                _ = cls_scope.token("if v is None:\n")
                with cls_scope.indent():
                    _ = cls_scope.token("return None\n")
                _ = cls_scope.token(f"return {base_cfg.name}.parse(v)\n")

            _ = cls_scope.token("\n")

        return wrote_any

    def _should_emit_attribute_for_policy(
        self,
        class_config: ClassConfig,
        attr_config: AttributeConfig,
        type_info: AttributeTypeInfo,
    ) -> bool:
        policy = self.policy
        if type_info.kind == AttributeTypeDescriptorKind.class_:
            target_cls = type_info.class_config
            target_is_inline = target_cls is not None and target_cls.value_mode == ClassValueMode.inline_value
            if class_config.value_mode != ClassValueMode.inline_value and not target_is_inline:
                if not (policy.emit_relationship_fields or policy.emit_edge_backed_properties):
                    return False
                target_class_id = resolve_type_class_config_id(attr_config)
                if not policy.emit_external_relationship_fields and target_class_id not in self._bound_graph_class_ids:
                    return False
                if (
                    policy.external_relationship_import_root_suffix
                    and target_class_id not in self._bound_graph_class_ids
                    and not self._external_relationship_import_override_matches_policy(
                        target_class_id=target_class_id,
                    )
                ):
                    return False
        elif (
            not attr_config.is_public
            and type_info.kind == AttributeTypeDescriptorKind.primitive
            and type_info.primitive_config is not None
            and CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type).base_type
            == CodePrimitiveBaseType.uuid
            and not policy.emit_foreign_key_fields
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
        package_root = override.split(".", 1)[0]
        return package_root.endswith(suffix)

    def _render_class(
        self,
        writer: CodeSectionWriter,
        class_config: ClassConfig,
        base_class_name: str,
        function_specs: list[tuple[FunctionConfig, str, str, bool, str, bool]],
        class_to_class_config_map: dict[UUID, ClassConfig],
    ) -> None:
        """
        Render a class to the writer.

        Args:
            writer: The CodeSectionWriter to write to
            class_config: The class config to render
            class_to_class_config_map: Mapping of class IDs to their ClassConfig (global lookup)
        """
        # Start the class definition (explicit spec)
        is_inline_value = class_config.value_mode == ClassValueMode.inline_value
        with writer.start_section(self._spec_class, qualname=class_config.name) as cls:
            parent_name = class_config.parent_class.name if class_config.parent_class else base_class_name
            emit_class_header(
                cls,
                name=class_config.name,
                base_name=parent_name,
                description=self._public_description(class_config.description),
            )

            # Use the indent helper for class body
            with cls.indent():
                # Track current class for annotation-driven discriminator rendering.
                self._current_class_config_id = class_config.id
                # Discriminator routing: base union classes own the tag->type table and parse helpers.
                discriminator_attr = None
                if self.policy.emit_discriminated_union_parsers and any(
                    cls_id == class_config.id for cls_id, _attr in self._discriminate_key_by_class_and_attr
                ):
                    discriminator_attr = self._discriminator_key_attr_name(base_class_id=class_config.id)

                rels = self._current_relationships_by_class_id.get(class_config.id, [])
                assoc_class_ids_for_class = get_association_class_ids(rels)

                attr_links: list[tuple[tuple[int, int | None], ClassConfigAttributeConfig]] = []
                for acc in class_config.class_config_attribute_configs:
                    if acc.attribute_config.is_virtual:
                        continue
                    attr_order_key = (0, acc.position)
                    attr_links.append((attr_order_key, acc))
                attr_links.sort(key=lambda item: item[0])

                primitive_attrs: list[tuple[tuple[int, int | None], AttributeConfig]] = []
                rel_attrs: list[tuple[tuple[int, int | None], AttributeConfig]] = []
                edge_attrs: list[tuple[tuple[int, int | None], AttributeConfig]] = []
                fk_attrs: list[tuple[tuple[int, int | None], AttributeConfig]] = []

                for attr_sort_key, acc in attr_links:
                    attr_config = acc.attribute_config
                    try:
                        type_info = self._resolve_attribute_type_info(
                            attr_config,
                            context=f"{class_config.name}.{attr_config.name}",
                        )
                    except Exception as exc:
                        logger.error(f"Failed to resolve descriptor for {class_config.name}.{attr_config.name}: {exc}")
                        primitive_attrs.append((attr_sort_key, attr_config))
                        continue

                    if type_info.kind == AttributeTypeDescriptorKind.class_:
                        # Inline-value classes are value objects.
                        # CLASS-typed attributes are nested payloads, not relationships.
                        if is_inline_value or (
                            type_info.class_config is not None
                            and type_info.class_config.value_mode == ClassValueMode.inline_value
                        ):
                            primitive_attrs.append((attr_sort_key, attr_config))
                        else:
                            if not self._should_emit_attribute_for_policy(
                                class_config,
                                attr_config,
                                type_info,
                            ):
                                continue
                            # Association edge helper attributes should always render under "# Edges"
                            # even if the association class is not explicitly marked is_edge.
                            if (
                                type_info.class_config is not None
                                and type_info.class_config.id in assoc_class_ids_for_class
                            ):
                                edge_attrs.append((attr_sort_key, attr_config))
                            else:
                                rel_attrs.append((attr_sort_key, attr_config))
                    else:
                        # Canonical FK attrs are typically private UUID primitives (transformer output).
                        if (
                            not attr_config.is_public
                            and type_info.kind == AttributeTypeDescriptorKind.primitive
                            and type_info.primitive_config is not None
                            and CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type).base_type
                            == CodePrimitiveBaseType.uuid
                        ):
                            fk_attrs.append((attr_sort_key, attr_config))
                        else:
                            primitive_attrs.append((attr_sort_key, attr_config))

                # Store dict of edge attributes by target class ID for quick lookup
                edge_attrs_by_target_class_id: dict[UUID, AttributeConfig] = {}
                for _, ea in edge_attrs:
                    edge_type_info = self._resolve_attribute_type_info(
                        ea,
                        context=f"{class_config.name}.{ea.name}",
                    )
                    edge_target_class = edge_type_info.class_config
                    if edge_target_class:
                        edge_attrs_by_target_class_id[edge_target_class.id] = ea

                # Edge-backed sugar properties are derived from ClassConfigRelationship +
                # relationship attributes in canonical mode (no ObjectConfig access).
                edge_backed_pairs: list[tuple[AttributeConfig, AttributeConfig]] = []
                if rels:
                    # Index attributes by id for quick resolution.
                    attr_by_id: dict[UUID, AttributeConfig] = {
                        acc.attribute_config.id: acc.attribute_config
                        for acc in class_config.class_config_attribute_configs
                    }
                    for rel in rels:
                        assoc = rel.class_config_relationship_association_edge
                        if assoc is None:
                            continue
                        assoc_class = class_to_class_config_map.get(assoc.class_config_id)
                        if assoc_class is None:
                            continue

                        # Canonical expects one REFERENCE+FORWARD attribute.
                        ref_attr_id: UUID | None = None
                        for ra in rel.class_config_relationship_attributes:
                            if (
                                ra.role == ClassConfigRelationshipAttributeRole.reference
                                and ra.direction == ClassConfigRelationshipDirection.forward
                            ):
                                ref_attr_id = ra.attribute_config_id
                                break
                        if ref_attr_id is None:
                            continue

                        rel_attr = attr_by_id.get(ref_attr_id)
                        # Prefer the dedicated edge helper attribute that points to the association class.
                        edge_attr = edge_attrs_by_target_class_id.get(assoc_class.id)
                        if rel_attr is None or edge_attr is None:
                            continue

                        edge_backed_pairs.append((rel_attr, edge_attr))

                # Deterministic ordering: render edge-backed properties in the same order as the
                # source relationship attributes declared on the class (ClassConfigAttributeConfig.position).
                #
                # This avoids non-deterministic no-op diffs when relationship iteration order varies.
                attr_sort_key_by_id: dict[UUID, tuple[int, int | None]] = {}
                for acc in class_config.class_config_attribute_configs:
                    attr_order_key = (0, acc.position)
                    _ = attr_sort_key_by_id.setdefault(acc.attribute_config.id, attr_order_key)
                edge_backed_pairs.sort(
                    key=lambda pair: (
                        attr_sort_key_by_id.get(pair[0].id, (9, 10**9)),
                        pair[0].name,
                        pair[1].name,
                    )
                )
                edge_backed_rel_attrs: list[AttributeConfig] = [rel for rel, _ in edge_backed_pairs]
                policy = self.policy
                has_rel_fields = policy.emit_relationship_fields and any(
                    attr_config not in edge_backed_rel_attrs for _, attr_config in rel_attrs
                )

                # Sort primitive attributes into discriminator key, tag, and other groups.
                discriminator_key_attrs: list[tuple[tuple[int, int | None], AttributeConfig]] = []
                discriminator_tag_attrs: list[tuple[tuple[int, int | None], AttributeConfig]] = []
                other_attrs: list[tuple[tuple[int, int | None], AttributeConfig]] = []
                if primitive_attrs:
                    for attr_sort_key, attr_config in primitive_attrs:
                        if (
                            class_config.id,
                            attr_config.name,
                        ) in self._discriminate_key_by_class_and_attr:
                            discriminator_key_attrs.append((attr_sort_key, attr_config))
                        elif (
                            class_config.id,
                            attr_config.name,
                        ) in self._discriminate_tag_by_class_and_attr:
                            discriminator_tag_attrs.append((attr_sort_key, attr_config))
                        else:
                            other_attrs.append((attr_sort_key, attr_config))

                    # Render discriminator key attributes
                    if discriminator_key_attrs:
                        _ = cls.token("# Discriminator Key\n")
                        for _, attr_config in discriminator_key_attrs:
                            self._render_attribute(cls, attr_config)
                        if discriminator_tag_attrs or has_rel_fields or other_attrs:
                            _ = cls.token("\n")

                    # Render discriminator tag attributes
                    if discriminator_tag_attrs:
                        _ = cls.token("# Discriminator Tag\n")
                        for _, attr_config in discriminator_tag_attrs:
                            self._render_attribute(cls, attr_config)
                        if has_rel_fields or other_attrs:
                            _ = cls.token("\n")

                # Render Relationships
                if has_rel_fields:
                    _ = cls.token("# Relationships\n")
                    for _, attr_config in rel_attrs:
                        if attr_config in edge_backed_rel_attrs:
                            continue
                        self._render_attribute(cls, attr_config)
                    _ = cls.token("\n")

                # DTO/wire discriminated unions: relationship fields that are typed as a discriminator base class
                # (e.g. EnvironmentOperationRequest) must preserve and parse subclass payloads.
                # Render other primitive attributes
                if other_attrs:
                    _ = cls.token("# Attributes\n")
                    for _, attr_config in other_attrs:
                        self._render_attribute(cls, attr_config)

                # DTO/wire discriminated unions: fields that are typed as a discriminator base class
                # (e.g. EnvironmentOperationRequest) must preserve and parse subclass payloads.
                #
                # IMPORTANT:
                # Inline-value classes treat CLASS-typed fields as nested payloads, not relationships,
                # so these fields appear under "# Attributes" (not "# Relationships").
                if self.policy.emit_discriminated_union_parsers:
                    rendered_attrs: list[tuple[tuple[int, int | None], AttributeConfig]] = []
                    if has_rel_fields:
                        rendered_attrs.extend(
                            [
                                (sort_key, attr_config)
                                for sort_key, attr_config in rel_attrs
                                if attr_config not in edge_backed_rel_attrs
                            ]
                        )
                    rendered_attrs.extend(other_attrs)
                    _ = self._render_discriminated_union_validators(
                        cls_scope=cls,
                        attrs=rendered_attrs,
                    )

                # Explicit oneof (XOR) constraints via compiled OCG annotations.
                if (
                    self.policy.emit_discriminated_union_parsers
                    and class_config.id in self._oneof_groups_by_class_config_id
                ):
                    rendered_name_by_canonical: dict[str, str] = {}
                    for _sort_key, acc in attr_links:
                        attr_config = acc.attribute_config
                        if attr_config.is_virtual:
                            continue
                        rendered_name, _wire_name = self._attribute_overlay_names(attr_config)
                        rendered_name_by_canonical[attr_config.name] = rendered_name

                    for idx, group in enumerate(self._oneof_groups_by_class_config_id.get(class_config.id, [])):
                        rendered_group = [rendered_name_by_canonical.get(name, name) for name in group]
                        tuple_expr = ", ".join([f"self.{name}" for name in rendered_group])
                        message = f"Exactly one of {', '.join(rendered_group)} must be set"

                        _ = cls.token('@model_validator(mode="after")\n')
                        _ = cls.token(f"def _validate_oneof_{idx}(self):\n")
                        with cls.indent():
                            _ = cls.token(f"if sum(v is not None for v in ({tuple_expr},)) != 1:\n")
                            with cls.indent():
                                _ = cls.token(f"raise ValueError({json.dumps(message)})\n")
                            _ = cls.token("return self\n")
                        _ = cls.token("\n")

                wrote_sections = bool(
                    discriminator_key_attrs or discriminator_tag_attrs or other_attrs or has_rel_fields
                )

                # Discriminator routing (SSOT): base union classes own the tag -> type table,
                # so wrapper validators stay identical and consumers can introspect route keyspaces.
                if self.policy.emit_discriminated_union_parsers and discriminator_attr is not None:
                    tagged_descendants = self._discriminator_tagged_descendants(
                        base_class_id=class_config.id,
                        discriminator_attr_name=discriminator_attr,
                        class_to_class_config_map=class_to_class_config_map,
                    )
                    unknown_class_name = f"Unknown{class_config.name}"

                    _ = cls.token("\n")
                    _ = cls.token(f"_DISCRIMINATOR_KEY: ClassVar[str] = {json.dumps(discriminator_attr)}\n")
                    _ = cls.token("_TAG_TO_TYPE: ClassVar[dict[str, str]] = {\n")
                    with cls.indent():
                        for tag_value, desc_cfg in tagged_descendants:
                            desc_module: str | None = None
                            try:
                                desc_path = self.layout_strategy.get_class_file_path(desc_cfg)
                                desc_module = self.layout_strategy.get_module_import_path(desc_path)
                            except Exception:
                                desc_module = None
                            if desc_module is None:
                                continue
                            fqn = f"{desc_module}.{desc_cfg.name}"
                            _ = cls.token(f"{json.dumps(tag_value)}: {json.dumps(fqn)},\n")
                    _ = cls.token("}\n\n")

                    _ = cls.token("@staticmethod\n")
                    _ = cls.token("@lru_cache(maxsize=None)\n")
                    _ = cls.token("def _resolve_fqn(fqn: str):\n")
                    with cls.indent():
                        _ = cls.token("from importlib import import_module\n\n")
                        _ = cls.token("module_name, class_name = fqn.rsplit('.', 1)\n")
                        _ = cls.token("return getattr(import_module(module_name), class_name)\n\n")

                    _ = cls.token("@classmethod\n")
                    _ = cls.token("def parse(cls, v, *, strict: bool = False):\n")
                    with cls.indent():
                        _ = cls.token("if isinstance(v, cls):\n")
                        with cls.indent():
                            _ = cls.token("return v\n")
                        _ = cls.token("if isinstance(v, dict):\n")
                        with cls.indent():
                            _ = cls.token("tag = v.get(cls._DISCRIMINATOR_KEY)\n")
                            _ = cls.token("fqn = cls._TAG_TO_TYPE.get(tag)\n")
                            _ = cls.token("if fqn:\n")
                            with cls.indent():
                                _ = cls.token("model_cls = cls._resolve_fqn(fqn)\n")
                                _ = cls.token("return model_cls.model_validate(v)\n")
                            _ = cls.token("if strict:\n")
                            with cls.indent():
                                _ = cls.token('raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")\n')
                            _ = cls.token(f"return {unknown_class_name}.model_validate(v)\n")
                        _ = cls.token("return cls.model_validate(v)\n")

                if fk_attrs and policy.emit_foreign_key_fields:
                    if wrote_sections:
                        _ = cls.token("\n")
                    _ = cls.token("# Foreign Keys\n")
                    for _, attr_config in fk_attrs:
                        self._render_attribute(cls, attr_config)
                    wrote_sections = True

                if edge_attrs and policy.emit_edge_fields:
                    if wrote_sections:
                        _ = cls.token("\n")
                    _ = cls.token("# Edges\n")
                    for _, attr_config in edge_attrs:
                        self._render_attribute(cls, attr_config)
                    wrote_sections = True

                # Render edge-backed relationship properties (sugar views over edges)
                if edge_backed_pairs and policy.emit_edge_backed_properties:
                    if wrote_sections:
                        _ = cls.token("\n")
                    for rel_attr, edge_attr in edge_backed_pairs:
                        self._render_edge_backed_property(
                            cls_scope=cls,
                            class_config=class_config,
                            rel_attr=rel_attr,
                            edge_attr=edge_attr,
                        )
                    wrote_sections = True

                # Render function facades
                if function_specs and policy.emit_function_facades:
                    if wrote_sections:
                        _ = cls.token("\n")
                    for (
                        fn_cfg,
                        _input_cls,
                        output_cls,
                        is_constructor,
                        _handler_key,
                        is_public,
                    ) in function_specs:
                        self._render_function_method(
                            cls,
                            fn_cfg,
                            output_cls,
                            is_constructor,
                            is_public,
                        )
                    wrote_sections = True

                # If nothing was rendered, add a pass statement
                if not wrote_sections:
                    _ = cls.token("pass\n")

                # Clear class context after finishing this class body.
                self._current_class_config_id = None

        # Forward-compat: discriminator base classes get an explicit Unknown* variant so
        # unknown tags don't silently downgrade typing (while still preserving payload).
        if self.policy.emit_discriminated_union_parsers and any(
            base_id == class_config.id for base_id, _attr in self._discriminate_key_by_class_and_attr
        ):
            discriminator_attr = self._discriminator_key_attr_name(base_class_id=class_config.id)
            if discriminator_attr is not None:
                unknown_class_name = f"Unknown{class_config.name}"
                with writer.start_section(self._spec_class, qualname=unknown_class_name) as cls:
                    emit_class_header(
                        cls,
                        name=unknown_class_name,
                        base_name=class_config.name,
                        description=(
                            f"Forward-compatible fallback when `{discriminator_attr}` is not a known discriminator tag."
                        ),
                    )
                    with cls.indent():
                        _ = cls.token('model_config = {"extra": "allow"}\n')

    def _render_edge_backed_property(
        self,
        cls_scope: CodeSectionScope,
        class_config: ClassConfig,
        rel_attr: AttributeConfig,
        edge_attr: AttributeConfig,
    ) -> None:
        """
        Render an @property that exposes a relationship backed by an edge attribute.

        The edge attribute remains the canonical data field; the property provides
        a sugar view that traverses the edge to the related objects.
        """
        # Resolve type info for the relationship attribute
        try:
            type_info = self._resolve_attribute_type_info(
                rel_attr,
                context=f"{class_config.name}.{rel_attr.name}",
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(
                f"Failed to resolve descriptor for edge-backed property {class_config.name}.{rel_attr.name}: {exc}"
            )
            return

        if type_info.kind != AttributeTypeDescriptorKind.class_ or not type_info.class_config:
            return

        target_class = type_info.class_config
        is_collection = type_info.is_collection
        is_optional = self._is_nullable(rel_attr, type_info)

        # Compute return type annotation
        base_type = target_class.name
        if is_collection:
            base_type = f"list[{base_type}]"
        if is_optional and not is_collection:
            base_type = f"{base_type} | None"

        # Resolve the edge class and find the attribute that points to the target class
        try:
            edge_type_info = self._resolve_attribute_type_info(
                edge_attr,
                context=f"{class_config.name}.{edge_attr.name}",
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Failed to resolve descriptor for edge attribute {class_config.name}.{edge_attr.name}: {exc}")
            return

        edge_class = edge_type_info.class_config
        if not edge_class:
            return

        target_attr_name: str | None = None
        for link in edge_class.class_config_attribute_configs:
            edge_side_attr = link.attribute_config
            if edge_side_attr.is_virtual:
                continue
            try:
                edge_side_info = self._resolve_attribute_type_info(
                    edge_side_attr,
                    context=f"{edge_class.name}.{edge_side_attr.name}",
                )
            except Exception:
                continue
            if edge_side_info.kind == AttributeTypeDescriptorKind.class_ and edge_side_info.class_config:
                if edge_side_info.class_config.id == target_class.id:
                    # Honor overlays on the association (edge) class endpoint attribute.
                    # Without this, a Python-only rename like `schema -> schema_` would make
                    # the generated sugar property access `edge.schema` (which resolves to
                    # BaseModel.schema) instead of the real field.
                    target_attr_name, _wire = self._attribute_overlay_names(edge_side_attr)
                    break

        if not target_attr_name:
            logger.warning(
                f"Could not find edge target attribute on {edge_class.name} pointing to {target_class.name} "
                + f"for property {class_config.name}.{rel_attr.name}"
            )
            return

        # Emit the @property method (explicit spec: no metadata)
        with cls_scope.start_section(
            SectionSpec(
                section_type=CodeSectionType.function,
                assemble=lambda code_section, segments, _nested: assemble_function(
                    code_section=code_section,
                    segments=segments,
                    is_public=True,
                    description=None,
                ),
            ),
            qualname=f"{class_config.name}.{rel_attr.name}",
        ) as fn_scope:
            emit_function_header(
                fn_scope,
                decorators=["@property"],
                name=rel_attr.name,
                signature="(self)",
                return_type=base_type,
                is_async=False,
            )

            with fn_scope.indent():
                if is_collection:
                    _ = fn_scope.token(
                        "return [edge."
                        + target_attr_name
                        + " for edge in self."
                        + edge_attr.name
                        + " if edge."
                        + target_attr_name
                        + " is not None]\n"
                    )
                else:
                    _ = fn_scope.token(
                        "return self."
                        + edge_attr.name
                        + "."
                        + target_attr_name
                        + " if self."
                        + edge_attr.name
                        + " is not None and self."
                        + edge_attr.name
                        + "."
                        + target_attr_name
                        + " is not None else None\n"
                    )
                _ = fn_scope.token("\n")

    def _render_function_method(
        self,
        cls_scope: CodeSectionScope,
        function_config: FunctionConfig,
        output_class: str,
        is_constructor: bool,
        is_public: bool = True,
    ) -> None:
        method_name = function_config.name
        description = self._public_description(function_config.description) or ""
        input_edges = [
            edge
            for edge in (function_config.function_config_attribute_configs or [])
            if edge.type == FunctionAttributeType.input
        ]
        output_edges = [
            edge
            for edge in (function_config.function_config_attribute_configs or [])
            if edge.type == FunctionAttributeType.output
        ]

        input_edges.sort(key=lambda e: int(e.position))
        output_edges.sort(key=lambda e: int(e.position))

        params: list[str] = []
        payload_items: list[str] = []
        params_have_default: list[bool] = []
        for edge in input_edges:
            attr = edge.attribute_config
            assert attr is not None
            rendered_name, _wire_name = self._attribute_overlay_names(attr)
            type_info = self._resolve_attribute_type_info(
                attr,
                context=f"{cls_scope.qualname}.{method_name}({rendered_name})",
            )

            base_type = "Any"
            if type_info.kind == AttributeTypeDescriptorKind.primitive and type_info.primitive_config:
                prim = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
                base_type = _PRIMITIVE_CODEC.render(prim) or "Any"
            elif type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config:
                base_type = type_info.enum_config.name
            elif type_info.kind == AttributeTypeDescriptorKind.class_ and type_info.class_config:
                base_type = type_info.class_config.name
                if self.policy.emit_discriminated_union_parsers and any(
                    base_id == type_info.class_config.id for base_id, _attr in self._discriminate_key_by_class_and_attr
                ):
                    base_type = f"SerializeAsAny[{base_type}]"

            type_annotation = base_type
            if type_info.is_collection:
                type_annotation = f"list[{type_annotation}]"
            if self._is_nullable(attr, type_info) and not type_info.is_collection:
                type_annotation = f"{type_annotation} | None"

            default_expr: str | None = None
            if attr.default_value is not None:
                try:
                    default_value = cast(object, json.loads(attr.default_value))
                except (json.JSONDecodeError, ValueError) as exc:
                    raise ValueError(
                        f"Failed to parse default value for {cls_scope.qualname}.{method_name}({attr.name}): "
                        + f"{attr.default_value!r}"
                    ) from exc

                if type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config:
                    if type_info.is_collection and isinstance(default_value, list):
                        rendered_items: list[str] = []
                        for item in cast(list[object], default_value):
                            rendered_items.append(
                                (
                                    "None"
                                    if item is None or item in {"NULL", "None"}
                                    else f"{type_info.enum_config.name}.{item}"
                                )
                            )
                        default_expr = "[" + ", ".join(rendered_items) + "]"
                    elif default_value is None or default_value in {"NULL", "None"}:
                        default_expr = "None"
                    else:
                        default_expr = f"{type_info.enum_config.name}.{default_value}"
                else:
                    default_expr = _PRIMITIVE_CODEC.to_literal_string(default_value)
            elif not getattr(attr, "is_required", True):
                default_expr = "None"

            param = f"{rendered_name}: {type_annotation}"
            if default_expr is not None:
                param += f" = {default_expr}"
            params.append(param)
            params_have_default.append(default_expr is not None)

            # SSOT: invocation payload keys use canonical AttributeConfig names, not overlays.
            payload_items.append(f"{json.dumps(attr.name)}: {rendered_name}")

        # Python syntax requires non-default params before default params.
        # Preserve SSOT ordering unless it would produce invalid code.
        saw_default = False
        has_non_default_after_default = False
        for has_default in params_have_default:
            if has_default:
                saw_default = True
            elif saw_default:
                has_non_default_after_default = True
                break
        if has_non_default_after_default:
            zipped = list(zip(params, payload_items, params_have_default, strict=True))
            required = [p for p in zipped if not p[2]]
            optional = [p for p in zipped if p[2]]
            params = [p for p, _payload, _has_default in required + optional]
            payload_items = [_payload for _p, _payload, _has_default in required + optional]

        return_type = output_class
        single_output_attr: AttributeConfig | None = None
        if not output_edges:
            return_type = "None"
        elif len(output_edges) == 1:
            single_output_attr = output_edges[0].attribute_config
            assert single_output_attr is not None
            out_type_info = self._resolve_attribute_type_info(
                single_output_attr,
                context=f"{cls_scope.qualname}.{method_name}(return)",
            )

            base_type = "Any"
            if out_type_info.kind == AttributeTypeDescriptorKind.primitive and out_type_info.primitive_config:
                prim = CodePrimitiveType.model_validate(out_type_info.primitive_config.primitive_type)
                base_type = _PRIMITIVE_CODEC.render(prim) or "Any"
            elif out_type_info.kind == AttributeTypeDescriptorKind.enum and out_type_info.enum_config:
                base_type = out_type_info.enum_config.name
            elif out_type_info.kind == AttributeTypeDescriptorKind.class_ and out_type_info.class_config:
                base_type = out_type_info.class_config.name
                if self.policy.emit_discriminated_union_parsers and any(
                    base_id == out_type_info.class_config.id
                    for base_id, _attr in self._discriminate_key_by_class_and_attr
                ):
                    base_type = f"SerializeAsAny[{base_type}]"

            return_type = base_type
            if out_type_info.is_collection:
                return_type = f"list[{return_type}]"
            if self._is_nullable(single_output_attr, out_type_info) and not out_type_info.is_collection:
                return_type = f"{return_type} | None"

        with cls_scope.start_section(
            SectionSpec(
                section_type=CodeSectionType.function,
                assemble=lambda code_section, segments, _nested: assemble_function(
                    code_section=code_section,
                    segments=segments,
                    is_public=is_public,
                    description=description or None,
                ),
            ),
            qualname=f"{cls_scope.qualname}.{method_name}",
        ) as fn_scope:
            self_or_cls = "self"
            decorators: list[str] = []
            if is_constructor:
                decorators.append("@classmethod")
                self_or_cls = "cls"
            signature_args = ", ".join([self_or_cls, *params]) if params else self_or_cls
            signature = f"({signature_args})"
            emit_function_header(
                fn_scope,
                decorators=decorators,
                name=method_name,
                signature=signature,
                return_type=return_type,
                is_async=True,
            )

            body_segments: list[ContentPartTextSegment] = []
            with fn_scope.indent():
                if description:
                    doc_lines = _wrap_docstring_lines(description)
                    # Match class docstring formatting: multiline descriptions render as
                    # a proper triple-quoted docstring (not an escaped "\n" string literal).
                    if len(doc_lines) > 1:
                        body_segments.append(fn_scope.token('"""\n'))
                        for line in doc_lines:
                            body_segments.append(fn_scope.token(f"{line}\n" if line else "\n"))
                        body_segments.append(fn_scope.token('"""\n'))
                    else:
                        body_segments.append(fn_scope.token(f'"""{doc_lines[0]}"""\n'))
                    body_segments.append(fn_scope.token("\n"))

                payload_literal = "{" + (", ".join(payload_items) if payload_items else "") + "}"
                body_segments.append(fn_scope.token(f"payload = {payload_literal}\n"))

                if not output_edges:
                    if is_constructor:
                        body_segments.append(
                            fn_scope.token(
                                "await invoke_constructor("
                                + f"orm_class=cls, function_name={json.dumps(function_config.name)}, "
                                + "payload=payload)\n"
                            )
                        )
                    else:
                        body_segments.append(
                            fn_scope.token(
                                "await invoke_instance("
                                + f"orm_model=self, function_name={json.dumps(function_config.name)}, "
                                + "payload=payload)\n"
                            )
                        )
                    body_segments.append(fn_scope.token("return None\n"))
                else:
                    if is_constructor:
                        body_segments.append(
                            fn_scope.token(
                                "result = await invoke_constructor("
                                + f"orm_class=cls, function_name={json.dumps(function_config.name)}, "
                                + "payload=payload)\n"
                            )
                        )
                    else:
                        body_segments.append(
                            fn_scope.token(
                                "result = await invoke_instance("
                                + f"orm_model=self, function_name={json.dumps(function_config.name)}, "
                                + "payload=payload)\n"
                            )
                        )

                    # Multi-output functions keep the explicit Output model for field names.
                    if len(output_edges) > 1:
                        body_segments.append(fn_scope.token(f"if isinstance(result, {output_class}):\n"))
                        with fn_scope.indent():
                            body_segments.append(fn_scope.token("return result\n"))
                        body_segments.append(fn_scope.token(f"return {output_class}.model_validate(result)\n"))
                    else:
                        assert single_output_attr is not None
                        out_name = json.dumps(single_output_attr.name)
                        body_segments.append(
                            fn_scope.token(
                                f"value = result.get({out_name}) if isinstance(result, dict) "
                                + f"and {out_name} in result else result\n"
                            )
                        )

                        out_type_info = self._resolve_attribute_type_info(
                            single_output_attr,
                            context=f"{cls_scope.qualname}.{method_name}(return)",
                        )

                        if self._is_nullable(single_output_attr, out_type_info) and not out_type_info.is_collection:
                            body_segments.append(fn_scope.token("if value is None:\n"))
                            with fn_scope.indent():
                                body_segments.append(fn_scope.token("return None\n"))

                        if out_type_info.kind == AttributeTypeDescriptorKind.class_ and out_type_info.class_config:
                            cls_name = out_type_info.class_config.name
                            is_inline_value_output = (
                                out_type_info.class_config.value_mode == ClassValueMode.inline_value
                            )
                            module_name: str | None = None
                            if self.import_overrides:
                                override = self.import_overrides.get(str(out_type_info.class_config.id), None)
                                if override:
                                    module_name = override
                            if module_name is None:
                                related_path = self.layout_strategy.get_class_file_path(out_type_info.class_config)
                                module_name = self.layout_strategy.get_module_import_path(related_path)

                            # IMPORTANT (canonical):
                            # Do not import cross-module ORM models at module import time;
                            # that creates cycles. Function facades may still reference output
                            # types at runtime (isinstance/model_validate).
                            # The honest solution is a *local import* inside the method
                            # body for cross-module output types.
                            if module_name and module_name != self._current_module:
                                body_segments.append(fn_scope.token(f"from {module_name} import {cls_name}\n"))
                            body_segments.append(fn_scope.token(f"if isinstance(value, {cls_name}):\n"))
                            with fn_scope.indent():
                                body_segments.append(fn_scope.token("return value\n"))
                            if is_inline_value_output:
                                body_segments.append(fn_scope.token(f"return {cls_name}.model_validate(value)\n"))
                            else:
                                body_segments.append(
                                    fn_scope.token(f"return {cls_name}.validate_invocation_value(value)\n")
                                )
                        elif out_type_info.kind == AttributeTypeDescriptorKind.enum and out_type_info.enum_config:
                            enum_name = out_type_info.enum_config.name
                            body_segments.append(fn_scope.token(f"if isinstance(value, {enum_name}):\n"))
                            with fn_scope.indent():
                                body_segments.append(fn_scope.token("return value\n"))
                            body_segments.append(fn_scope.token(f"return {enum_name}(value)\n"))
                        else:
                            body_segments.append(fn_scope.token("return value\n"))

            _ = fn_scope.compose(body_segments, CodeSectionFunctionSegment.BODY.value)
            _ = fn_scope.token("\n")

    def _render_function_io(
        self,
        writer: CodeSectionWriter,
        object_name: str,
        function_config: FunctionConfig,
        input_class_name: str | None = None,
        output_class_name: str | None = None,
    ) -> tuple[str, str]:
        """Emit Input/Output Pydantic classes for a function and return their names."""

        input_attrs = [
            edge.attribute_config
            for edge in function_config.function_config_attribute_configs
            if edge.type == FunctionAttributeType.input
        ]
        output_attrs = [
            edge.attribute_config
            for edge in function_config.function_config_attribute_configs
            if edge.type == FunctionAttributeType.output
        ]

        if input_class_name is None or output_class_name is None:
            input_class_name, output_class_name = self._get_function_io_class_names(object_name, function_config.name)

        with writer.start_section(self._spec_class, qualname=input_class_name) as cls:
            emit_class_header(cls, name=input_class_name, base_name="BaseModel", description=None)
            with cls.indent():
                if not input_attrs:
                    _ = cls.token("pass\n")
                else:
                    for attr_config in input_attrs:
                        self._render_attribute(cls, attr_config)

        _ = writer.token("\n")

        with writer.start_section(self._spec_class, qualname=output_class_name) as cls:
            emit_class_header(cls, name=output_class_name, base_name="BaseModel", description=None)
            with cls.indent():
                if not output_attrs:
                    _ = cls.token("pass\n")
                else:
                    for attr_config in output_attrs:
                        self._render_attribute(cls, attr_config)

        _ = writer.token("\n")
        return input_class_name, output_class_name

    def _render_registry(
        self,
        writer: CodeSectionWriter,
        registry_entries: list[ClassRegistryEntry],
    ) -> None:
        _ = writer.token("FUNCTIONS = {\n")
        for class_registry_entry in registry_entries:
            class_indent = "    "
            if writer.indent_level > 0:
                class_indent = class_indent * writer.indent_level
            class_name = class_registry_entry.class_config.name
            if not class_registry_entry.function_registry_entries:
                # Match existing generated style: compact empty mapping per class.
                _ = writer.token(f'{class_indent}"{class_name}": {{}},\n')
                continue

            _ = writer.token(f'{class_indent}"{class_name}": {{\n')
            for function_registry_entry in class_registry_entry.function_registry_entries:
                fn_indent = class_indent + "    "
                fn_name = function_registry_entry.function_config.name
                in_name = function_registry_entry.input_class_name
                out_name = function_registry_entry.output_class_name
                fn_cfg = function_registry_entry.function_config
                is_constructor = function_registry_entry.is_constructor
                _ = writer.token(f'{fn_indent}"{fn_name}": {{\n')
                canonical_data: dict[str, object] = {
                    # !! NOTE: AVOID CANONICAL ID UNTIL COMMIT IS STABLE to ensure stability during rebuilds.
                    # "id": str(fn_cfg.id) if fn_cfg.id else None,
                    "name": fn_cfg.name,
                    "description": self._public_description(fn_cfg.description),
                    "is_constructor": bool(is_constructor),
                }
                # Keep canonical blob as repr() for deterministic one-line output.
                _ = writer.token(f"{fn_indent}    'canonical': {canonical_data!r},\n")
                _ = writer.token(f'{fn_indent}    "input": {in_name},\n')
                _ = writer.token(f'{fn_indent}    "output": {out_name},\n')
                _ = writer.token(f"{fn_indent}}},\n")
            _ = writer.token(f"{class_indent}}},\n")
        _ = writer.token("}\n\n")
        _ = writer.token("__all__ = [\n")
        all_indent = "    "
        if writer.indent_level > 0:
            all_indent = all_indent * writer.indent_level
        for class_registry_entry in registry_entries:
            _ = writer.token(f'{all_indent}"{class_registry_entry.class_config.name}",\n')
            for function_registry_entry in class_registry_entry.function_registry_entries:
                _ = writer.token(f'{all_indent}"{function_registry_entry.input_class_name}",\n')
                _ = writer.token(f'{all_indent}"{function_registry_entry.output_class_name}",\n')
        _ = writer.token(f'{all_indent}"FUNCTIONS",\n')
        _ = writer.token("]\n")

    def _get_function_io_class_names(self, object_name: str, function_name: str) -> tuple[str, str]:
        pascal_obj = to_pascal_case(object_name)
        pascal_fn = to_pascal_case(function_name)
        return f"{pascal_obj}{pascal_fn}Input", f"{pascal_obj}{pascal_fn}Output"

    def _render_attribute(self, cls_scope: CodeSectionScope, attribute_config: AttributeConfig):
        """
        Render an attribute within a class.

        Args:
            cls_scope: The section scope for the class
            attribute_config: The attribute config to render
        """
        rendered_name, wire_name = self._attribute_overlay_names(attribute_config)
        type_info = self._resolve_attribute_type_info(
            attribute_config,
            context=f"{cls_scope.qualname}.{rendered_name}",
        )

        flags = self._attribute_render_flags(attribute_config, type_info)
        is_optional = flags.is_optional
        is_collection = flags.is_collection
        should_exclude = flags.should_exclude

        # Add attribute (explicit spec; do not pass semantics via CodeSection.metadata)
        with cls_scope.start_section(
            SectionSpec(
                section_type=CodeSectionType.attribute,
                assemble=lambda code_section, segments, _nested: assemble_attribute(
                    code_section=code_section,
                    segments=segments,
                    is_required=attribute_config.is_required,
                    is_public=attribute_config.is_public,
                    is_unique=attribute_config.is_unique,
                    is_primary=attribute_config.is_primary,
                    is_many_to_many=False,
                    edge_spec_name=None,
                ),
            ),
            qualname=f"{cls_scope.qualname}.{rendered_name}",
        ) as attr:
            base_type = "Any"
            if type_info.kind == AttributeTypeDescriptorKind.primitive and type_info.primitive_config:
                prim = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
                base_type = _PRIMITIVE_CODEC.render(prim) or "Any"
            elif type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config:
                base_type = type_info.enum_config.name
            elif type_info.kind == AttributeTypeDescriptorKind.class_ and type_info.class_config:
                base_type = type_info.class_config.name
                if self.policy.emit_discriminated_union_parsers and any(
                    base_id == type_info.class_config.id for base_id, _attr in self._discriminate_key_by_class_and_attr
                ):
                    base_type = f"SerializeAsAny[{base_type}]"
            else:
                if attribute_config.is_public:
                    logger.warning(
                        f"No related class found for public attribute {attribute_config.name} on: {cls_scope.qualname}"
                    )
                else:
                    logger.debug(
                        f"No related class found for private attribute {attribute_config.name} on: {cls_scope.qualname}"
                    )

            default_value_override = None

            type_annotation = base_type
            if is_collection:
                type_annotation = f"list[{type_annotation}]"
            if is_optional and not is_collection:
                type_annotation = f"{type_annotation} | None"

            discriminator_tag_value: str | None = None
            is_discriminator_tag = False
            discriminator_features_enabled = (
                self.policy.emit_discriminator_literals
                or self.policy.emit_discriminator_literal_types
                or self.policy.emit_discriminated_union_parsers
            )
            if (
                discriminator_features_enabled
                and self._current_class_config_id is not None
                and type_info.kind == AttributeTypeDescriptorKind.primitive
                and type_info.primitive_config is not None
            ):
                discriminator_tag_value = self._discriminate_tag_by_class_and_attr.get(
                    (self._current_class_config_id, attribute_config.name)
                )
                if discriminator_tag_value is not None:
                    prim = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
                    if prim.base_type == CodePrimitiveBaseType.string:
                        is_discriminator_tag = True
                        default_value_override = discriminator_tag_value
                        if not is_collection and self.policy.emit_discriminator_literal_types:
                            literal_type = f"Literal[{json.dumps(discriminator_tag_value)}]"
                            if is_optional:
                                type_annotation = f"{literal_type} | None"
                            else:
                                type_annotation = literal_type

            # Get default value
            default_value: object | None = None
            if attribute_config.default_value is not None:
                try:
                    default_value = cast(object, json.loads(attribute_config.default_value))
                except (json.JSONDecodeError, ValueError) as e:
                    # Log the problematic value for debugging
                    logger.error(
                        "Failed to parse default value for %s: %r. Error: %s",
                        attribute_config.name,
                        attribute_config.default_value,
                        e,
                    )
                    # Use the raw default_value as fallback
                    default_value = cast(object, attribute_config.default_value)
                    # Try to parse it as a JSON string first, if that fails, use it as-is
                    try:
                        # If it's already a JSON string, parse it
                        default_value_str = cast(str, default_value)
                        if default_value_str.startswith('"') and default_value_str.endswith('"'):
                            default_value = cast(object, json.loads(default_value_str))
                    except (json.JSONDecodeError, ValueError):
                        # If all parsing fails, use the raw value
                        pass

                    # Fail fast: canonical renderer requires deterministic defaults.
                    raise ValueError(
                        f"Failed to parse default value for {attribute_config.name}: {default_value!r}"
                    ) from e

            # Override default value when discriminator tags are SSOT (prevents drift between annotation + default).
            if default_value_override is not None:
                if default_value is not None and default_value != default_value_override:
                    raise ValueError(
                        f"Discriminator tag default mismatch for {cls_scope.qualname}.{attribute_config.name}: "
                        + f"default={default_value!r} tag={default_value_override!r}"
                    )
                default_value = default_value_override

            default_expr: str | None = None
            if attribute_config.default_value is not None or default_value is not None:
                default_expr = self._field_default_expr(
                    default_value=default_value,
                    type_info=type_info,
                    should_exclude=should_exclude,
                )
            else:
                # Handle implicit defaults for collection / optional fields
                if is_collection:
                    default_section = "default_factory=list"
                    if should_exclude:
                        default_section += ", exclude=True"
                    default_expr = f"Field({default_section})"
                elif is_optional:
                    default_expr = "Field(default=None, exclude=True)" if should_exclude else "Field(default=None)"

            # If this attribute has a wire_name override (or was renamed), emit Field(alias=...)
            # to preserve stable JSON keys while using a safe Python identifier.
            if wire_name and wire_name != rendered_name:
                default_expr = self._with_field_alias(default_expr, alias=wire_name)

            # Prefer SSOT descriptions via Pydantic Field(description=...).
            if attribute_config.description:
                default_expr = self._with_field_description(
                    default_expr,
                    description=self._public_description(attribute_config.description) or attribute_config.description,
                )

            # DTO discriminators: keep human-friendly raw literals for constant tag defaults when safe.
            if (
                is_discriminator_tag
                and self.policy.emit_discriminator_literals
                and discriminator_tag_value is not None
                and not should_exclude
                and not wire_name
                and not attribute_config.description
            ):
                default_expr = json.dumps(discriminator_tag_value)

            emit_attribute_line(
                attr,
                name=rendered_name,
                type_annotation=type_annotation,
                default_expr=default_expr,
            )

    def _render_field_default(
        self,
        attr: CodeSectionScope,
        default_value: object,
        type_info: AttributeTypeInfo,
        should_exclude: bool = False,
    ) -> None:
        """
        Render a Pydantic Field() with proper default/default_factory using the type system.

        Args:
            attr: The attribute section scope
            default_value: The parsed default value
            type_info: Resolved type descriptor info
            should_exclude: Whether to exclude the default value from serialization
        """
        # Check if it's already a complete Field() call
        if isinstance(default_value, str) and default_value.startswith(("Field(", "field(")):
            _ = attr.token(default_value, CodeSectionAttributeSegment.DEFAULT_VALUE.value)
            return

        # Use the type system to determine how to handle the default
        if type_info.kind == AttributeTypeDescriptorKind.primitive and type_info.primitive_config:
            prim = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
            default_section = self._get_primitive_field_default(default_value, prim)
        elif type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config:
            # Enum defaults are always literals
            enum_config = type_info.enum_config
            # !! TODO: Improve "default_value" is None instead of assuming "NULL".
            if default_value == "NULL":
                formatted_value = "None"
            else:
                formatted_value = f"{enum_config.name}.{default_value}"
            default_section = f"default={formatted_value}"
        elif type_info.kind == AttributeTypeDescriptorKind.class_:
            # Class relationships - typically None or use factory for lists
            if type_info.is_collection:
                default_section = "default_factory=list"
            else:
                default_section = "default=None"
        else:
            # Fallback for unknown types
            formatted_value = _PRIMITIVE_CODEC.to_literal_string(default_value)
            default_section = f"default={formatted_value}"

        if should_exclude:
            default_section += ", exclude=True"

        _ = attr.token(f"Field({default_section})", CodeSectionAttributeSegment.DEFAULT_VALUE.value)

    def _field_default_expr(
        self,
        *,
        default_value: object,
        type_info: AttributeTypeInfo,
        should_exclude: bool,
    ) -> str:
        """Return a Pydantic Field(...) expression string for a default value."""
        # Check if it's already a complete Field() call
        if isinstance(default_value, str) and default_value.startswith(("Field(", "field(")):
            return default_value

        # Collection fields (`T[]`) should never use a literal list default, even when `.aware`
        # explicitly provides `[]`. Prefer `default_factory` (and a lambda for non-empty lists)
        # so defaults are fresh per instance and consistent with implicit collection defaults.
        if type_info.is_collection:
            if default_value is None:
                default_section = "default_factory=list"
            elif isinstance(default_value, list):
                if default_value:
                    literal = _PRIMITIVE_CODEC.to_literal_string(cast(object, default_value))
                    default_section = f"default_factory=lambda: {literal}"
                else:
                    default_section = "default_factory=list"
            else:
                formatted_value = _PRIMITIVE_CODEC.to_literal_string(default_value)
                default_section = f"default={formatted_value}"

            if should_exclude:
                default_section += ", exclude=True"

            return f"Field({default_section})"

        # Use the type system to determine how to handle the default
        if type_info.kind == AttributeTypeDescriptorKind.primitive and type_info.primitive_config:
            prim = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
            default_section = self._get_primitive_field_default(default_value, prim)
        elif type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config:
            enum_config = type_info.enum_config
            # Enum defaults may come through as None (implicit null) or "NULL".
            # In both cases, emit `None` rather than invalid `<Enum>.None`.
            if default_value is None or default_value in {"NULL", "None"}:
                formatted_value = "None"
            else:
                formatted_value = f"{enum_config.name}.{default_value}"
            default_section = f"default={formatted_value}"
        elif type_info.kind == AttributeTypeDescriptorKind.class_:
            if type_info.is_collection:
                default_section = "default_factory=list"
            else:
                default_section = "default=None"
        else:
            formatted_value = _PRIMITIVE_CODEC.to_literal_string(default_value)
            default_section = f"default={formatted_value}"

        if should_exclude:
            default_section += ", exclude=True"

        return f"Field({default_section})"

    def _get_primitive_field_default(self, default_value: object, prim: CodePrimitiveType) -> str:
        """
        Render Field() default for primitive types using the type system.

        Args:
            attr: The attribute section scope
            default_value: The parsed default value
            primitive_type: The PythonPrimitiveType instance
        """
        base_type = prim.base_type
        # Handle different base types that require factories
        if base_type == CodePrimitiveBaseType.datetime:
            # DateTime fields typically use factory functions
            if isinstance(default_value, str) and default_value.strip().lower() == "now()":
                # Canonical `.aware` uses `now()` as a dynamic DateTime default. Emit a factory rather
                # than a string literal.
                return "default_factory=datetime.utcnow"
            if isinstance(default_value, str) and "datetime.now" in default_value:
                if "UTC_TZ" in default_value:
                    return "default_factory=lambda: datetime.now(UTC_TZ)"
                else:
                    return "default_factory=lambda: datetime.now()"
            else:
                # Other datetime defaults
                formatted_value = _PRIMITIVE_CODEC.to_literal_string(default_value)
                return f"default={formatted_value}"
        elif base_type == CodePrimitiveBaseType.uuid:
            # UUID fields typically use factory functions
            if isinstance(default_value, str) and ("gen_random_uuid" in default_value or "UUID" in default_value):
                return "default_factory=lambda: UUID(gen_random_uuid())"
            else:
                # Literal UUID value
                formatted_value = _PRIMITIVE_CODEC.to_literal_string(default_value)
                return f"default={formatted_value}"
        elif base_type == CodePrimitiveBaseType.array:
            # Array/list types use factory
            return "default_factory=list"
        elif base_type == CodePrimitiveBaseType.dict:
            # Dict types use factory
            return "default_factory=dict"
        elif base_type == CodePrimitiveBaseType.json:
            # SSOT: JSON defaults should be honest Python JSON values, with explicit shape.
            #
            # `.aware` defaults for JSON primitives are typically written as string literals containing
            # JSON documents (e.g. `"{}"`, `"[]"`). The OCG stores that outer string, so we must
            # parse the inner JSON to get the actual object/array value.
            json_kind = None
            if prim.constraints:
                kind_val = prim.constraints.get("json_kind")
                if isinstance(kind_val, str):
                    json_kind = kind_val.lower()

            parsed = default_value
            if isinstance(parsed, str):
                try:
                    parsed = cast(object, json.loads(parsed))
                except Exception:
                    parsed = default_value
            if parsed is None:
                return "default=None"

            if json_kind == "object":
                if not isinstance(parsed, dict):
                    raise ValueError(f"Invalid default for JsonObject: expected object, got {type(parsed).__name__}")
                if parsed:
                    literal = _PRIMITIVE_CODEC.to_literal_string(cast(object, parsed))
                    return f"default_factory=lambda: JsonObject({literal})"
                return "default_factory=JsonObject"

            if json_kind == "array":
                if not isinstance(parsed, list):
                    raise ValueError(f"Invalid default for JsonArray: expected array, got {type(parsed).__name__}")
                if parsed:
                    literal = _PRIMITIVE_CODEC.to_literal_string(cast(object, parsed))
                    return f"default_factory=lambda: JsonArray({literal})"
                return "default_factory=JsonArray"

            if json_kind == "value":
                # JsonValue is a typing alias; emit plain Python literals + factories for containers.
                if isinstance(parsed, dict):
                    if parsed:
                        literal = _PRIMITIVE_CODEC.to_literal_string(cast(object, parsed))
                        return f"default_factory=lambda: {literal}"
                    return "default_factory=dict"
                if isinstance(parsed, list):
                    if parsed:
                        literal = _PRIMITIVE_CODEC.to_literal_string(cast(object, parsed))
                        return f"default_factory=lambda: {literal}"
                    return "default_factory=list"
                literal = _PRIMITIVE_CODEC.to_literal_string(parsed)
                return f"default={literal}"

            raise ValueError(f"Invalid json_kind constraint: {json_kind!r}")
        elif base_type == CodePrimitiveBaseType.null:
            # Null/None values
            return "default=None"
        else:
            # For other primitive types (str, int, bool, float, etc.), use literal defaults
            formatted_value = _PRIMITIVE_CODEC.to_literal_string(default_value)
            return f"default={formatted_value}"

    def _render_enum(self, writer: CodeSectionWriter, enum_config: EnumConfig):
        """
        Render a single enum.

        Args:
            writer: The CodeSectionWriter
            enum_config: The enum config to render
        """
        # Start enum class (explicit spec)
        with writer.start_section(self._spec_enum, qualname=enum_config.name) as cls:
            emit_enum_header(
                cls,
                name=enum_config.name,
                description=self._public_description(enum_config.description),
            )

            with cls.indent():
                # Add each enum value in canonical position order
                options = sorted(
                    enum_config.enum_options or [],
                    key=lambda opt: (opt.position, (opt.label or opt.value)),
                )
                for option in options:
                    label = option.label or option.value
                    value = option.value
                    option_desc = self._public_description(option.description)

                    # Apply enum option overlay (for reserved words / wire compatibility)
                    overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.enum_option, option.id)
                    if overlay is not None and isinstance(overlay, EnumOptionOverlay):
                        if overlay.rendered_name:
                            label = overlay.rendered_name
                        if overlay.wire_name:
                            value = overlay.wire_name

                    # Format the value based on type
                    formatted_val = f'"{value}"'.lower()

                    with cls.start_section(
                        self._spec_enum_value,
                        qualname=f"{enum_config.name}.{label}",
                        reference=f"{enum_config.name}.{label}",
                        metadata=JsonObject({"position": option.position}),
                    ) as enum_value_scope:
                        emit_enum_value_line(
                            enum_value_scope,
                            name=label,
                            value_literal=formatted_val,
                            description=option_desc,
                        )

    def _gather_imports(
        self,
        class_config: ClassConfig,
        current_module: str | None,
        *,
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
    ) -> tuple[ImportPlan, ImportNeeds]:
        """
        Gather required imports for a class.

        Args:
            class_config: The class config

        Returns:
            (ImportPlan, ImportNeeds)
        """
        imports = ImportPlan()
        class_to_class_config_map = class_to_class_config_map or {}

        has_uuid = False
        json_types: set[str] = set()
        has_datetime = False
        has_any = False
        needs_field = False
        needs_serialize_as_any = False
        needs_field_validator = False
        has_vector = False

        policy = self.policy
        should_emit_functions = (
            policy.emit_function_facades or policy.emit_function_io_models or policy.emit_function_registry
        )

        # Collect attribute configs for both class and functions.
        attribute_configs: list[AttributeConfig] = []
        for acc in class_config.class_config_attribute_configs:
            attr_config = acc.attribute_config
            if attr_config.is_virtual:
                continue
            attribute_configs.append(attr_config)
        if should_emit_functions:
            for fc_link in class_config.class_config_function_configs:
                fn_cfg = fc_link.function_config
                for edge in fn_cfg.function_config_attribute_configs:
                    attr_config = edge.attribute_config
                    if attr_config.is_virtual:
                        continue
                    attribute_configs.append(attr_config)

        # Process attribute configs.
        for attr_config in attribute_configs:
            try:
                type_info = self._resolve_attribute_type_info(
                    attr_config,
                    context=f"{class_config.name}.{attr_config.name}",
                )
            except Exception as exc:
                logger.error(f"Failed to resolve descriptor for {class_config.name}.{attr_config.name}: {exc}")
                has_any = True
                continue

            flags = self._attribute_render_flags(attr_config, type_info)
            if not self._should_emit_attribute_for_policy(class_config, attr_config, type_info):
                continue
            needs_field = needs_field or flags.needs_field

            if type_info.kind == AttributeTypeDescriptorKind.primitive:
                primitive_config = type_info.primitive_config
                if primitive_config:
                    prim = CodePrimitiveType.model_validate(primitive_config.primitive_type)
                    base = prim.base_type
                    if base == CodePrimitiveBaseType.uuid:
                        has_uuid = True
                    if base == CodePrimitiveBaseType.json:
                        json_types.add(_PRIMITIVE_CODEC.render(prim) or "Json")
                    if base == CodePrimitiveBaseType.datetime:
                        has_datetime = True
                    if base == CodePrimitiveBaseType.any:
                        has_any = True
                    if base == CodePrimitiveBaseType.vector:
                        has_vector = True

            elif type_info.kind == AttributeTypeDescriptorKind.enum:
                enum_config = type_info.enum_config
                if enum_config:
                    module_name = None
                    if self.import_overrides:
                        override = self.import_overrides.get(str(enum_config.id), None)
                        if override:
                            module_name = override
                    if module_name is None:
                        enum_path = self.layout_strategy.get_enum_file_path(enum_config)
                        module_name = self.layout_strategy.get_module_import_path(enum_path)
                    # Avoid self-imports: importing from the module we are currently emitting
                    # produces invalid circular imports like:
                    #   from pkg.mod import MyEnum
                    #   class MyEnum(Enum): ...
                    if module_name != current_module:
                        imports.add(module_name, enum_config.name)

            elif type_info.kind == AttributeTypeDescriptorKind.class_:
                cls_cfg = type_info.class_config
                discriminator_attr = None
                is_discriminated_union_base = False
                if (
                    self.policy.emit_discriminated_union_parsers
                    and cls_cfg is not None
                    and any(base_id == cls_cfg.id for base_id, _attr in self._discriminate_key_by_class_and_attr)
                ):
                    discriminator_attr = self._discriminator_key_attr_name(base_class_id=cls_cfg.id)
                    is_discriminated_union_base = discriminator_attr is not None

                # Import strategy (Python-only, separate from loading strategy):
                #
                # Cross-module model type imports must NOT be executed at runtime; they easily
                # create Python module cycles. Since we emit `from __future__ import annotations`,
                # annotations are postponed, and we rely on:
                # - `bootstrap_orm_package(...).model_rebuild(_types_namespace=...)`
                # to resolve forward refs after modules are imported.
                #
                # Therefore: model type references are imported under TYPE_CHECKING only.

                if cls_cfg and self.layout_strategy:
                    module_name = None
                    if self.import_overrides:
                        override = self.import_overrides.get(str(cls_cfg.id), None)
                        if override:
                            module_name = override
                    if module_name is None:
                        related_path = self.layout_strategy.get_class_file_path(cls_cfg)
                        module_name = self.layout_strategy.get_module_import_path(related_path)
                    if module_name != current_module:
                        if is_discriminated_union_base:
                            # Discriminated-union parsers reference base type at runtime
                            # (isinstance/model_validate).
                            # Variants are imported lazily inside generated validators to avoid module cycles.
                            imports.add(module_name, cls_cfg.name)
                        elif (
                            self.policy.runtime_import_external_model_fields
                            and cls_cfg.id not in self._bound_graph_class_ids
                        ):
                            imports.add(module_name, cls_cfg.name)
                        else:
                            # Defer to TYPE_CHECKING import block emitted at module level.
                            self._lazy_imports_for_file.setdefault(module_name, set()).add(cls_cfg.name)
                elif cls_cfg:
                    related_file = to_snake_case(cls_cfg.name)
                    module_name = f".{related_file}"
                    if is_discriminated_union_base:
                        imports.add(module_name, cls_cfg.name)
                    else:
                        self._lazy_imports_for_file.setdefault(module_name, set()).add(cls_cfg.name)
                else:
                    has_any = True
                    if attr_config.is_public:
                        logger.warning(
                            f"No related class found for public attribute {class_config.name}.{attr_config.name}"
                        )
                    else:
                        logger.debug(
                            f"No related class found for private attribute {class_config.name}.{attr_config.name}"
                        )

            else:
                has_any = True

            # DTO/wire discriminated unions: when a field is typed as a discriminator base class
            # (e.g. EnvironmentOperationRequest), values will often be provided as subclasses.
            # We rely on SerializeAsAny[...] + field validators to preserve and parse full payloads.
            if (
                self.policy.emit_discriminated_union_parsers
                and type_info.kind == AttributeTypeDescriptorKind.class_
                and type_info.class_config is not None
            ):
                target_id = type_info.class_config.id
                if any(base_id == target_id for base_id, _attr in self._discriminate_key_by_class_and_attr):
                    needs_serialize_as_any = True
                    needs_field_validator = True

        # Parent class import (structural inheritance)
        parent_class = class_config.parent_class
        if parent_class and self.layout_strategy:
            parent_module = None
            if self.import_overrides:
                override = self.import_overrides.get(str(parent_class.id), None)
                if override:
                    parent_module = override
            if parent_module is None:
                parent_path = self.layout_strategy.get_class_file_path(parent_class)
                parent_module = self.layout_strategy.get_module_import_path(parent_path)
            if parent_module != current_module:
                imports.add(parent_module, parent_class.name)

        # Custom Aware types
        for json_type in sorted(json_types):
            imports.add("aware_types", json_type)
        if has_vector:
            imports.add("aware_types", "Vector")

        # Standard Python types
        if has_uuid:
            imports.add("uuid", "UUID")
        if has_datetime:
            imports.add("datetime", "datetime")
        if has_any:
            imports.add("typing", "Any")

        return imports, ImportNeeds(
            field=needs_field,
            any_=has_any,
            uuid=has_uuid,
            datetime=has_datetime,
            serialize_as_any=needs_serialize_as_any,
            field_validator=needs_field_validator,
        )

    def _sanitize_identifier(self, name: str) -> str:
        return re.sub(r"\W|^(?=\d)", "_", name)

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
        class_to_class_config_map = class_to_class_config_map or {}
        policy = self.policy
        if base_class_module is None:
            base_class_module = policy.base_class_module
        if base_class_name is None:
            base_class_name = policy.base_class_name

        current_module: str | None = None
        current_class = next((obj for obj in meta_objects if isinstance(obj, ClassConfig)), None)
        if current_class is not None:
            current_file = self.layout_strategy.get_class_file_path(current_class)
            current_module = self.layout_strategy.get_module_import_path(current_file)

        self._current_module = current_module
        try:
            # Reset per-file lazy import cache
            self._lazy_imports_for_file = {}
            self._current_relationships_by_class_id = {}
            self._fk_attr_ids = set()
            self._edge_backed_ref_attr_ids = set()

            # Relationship-driven role metadata (canonical)
            for obj in meta_objects:
                if not isinstance(obj, ClassConfigRelationship):
                    continue
                self._current_relationships_by_class_id.setdefault(obj.class_config_id, []).append(obj)
                # Track edge-backed view attributes (association present) so imports/rendering can
                # treat them as @property views instead of stored fields.
                if obj.class_config_relationship_association_edge is not None:
                    for ra in obj.class_config_relationship_attributes:
                        if (
                            ra.role == ClassConfigRelationshipAttributeRole.reference
                            and ra.direction == ClassConfigRelationshipDirection.forward
                        ):
                            self._edge_backed_ref_attr_ids.add(ra.attribute_config_id)
                for ra in obj.class_config_relationship_attributes:
                    if ra.role == ClassConfigRelationshipAttributeRole.foreign_key:
                        self._fk_attr_ids.add(ra.attribute_config_id)

            # Collect and group imports
            imports = self._collect_file_imports(
                meta_objects,
                base_class_module,
                base_class_name,
                class_to_class_config_map=class_to_class_config_map,
            )
            package_groups = group_python_imports(
                imports.as_mapping(),
                policy=PythonImportGroupingPolicy(
                    semantic_import_roots=semantic_import_roots_from_renderer_inputs(
                        import_root=self.layout_strategy.import_root,
                        import_overrides=self.import_overrides,
                        external_graph_fqn_prefixes=(graph.fqn_prefix for graph in self.external_graphs),
                    ),
                    support_import_roots=policy.support_import_roots,
                ),
            )

            # Always lead with future annotations to enable forward references
            _ = writer.token("from __future__ import annotations\n\n")

            for package_name, package_imports in package_groups.items():
                if package_name:
                    with writer.start_section(
                        self._spec_comment, qualname=f"comment.{package_name}"
                    ) as comment_section:
                        _ = comment_section.token("# ")
                        # Match existing generated style: spaces (not underscores) in group headers.
                        _ = comment_section.token(
                            package_name.replace("_", " "),
                            CodeSectionCommentSegment.CONTENT.value,
                        )
                        _ = comment_section.token("\n")

                def _module_sort_key(m: str) -> tuple[int, str]:
                    # Match existing generated style: enums imports first within a group.
                    return (0, m) if m.endswith("_enums") else (1, m)

                for module in sorted(package_imports.keys(), key=_module_sort_key):
                    items = sorted(package_imports[module])
                    use_multiline = len(items) > 1
                    if not items:
                        items_str = ""
                    elif use_multiline:
                        # Match existing generated style: parenthesized multi-line imports.
                        items_str = "(\n" + "".join([f"    {it},\n" for it in items]) + ")"
                    else:
                        items_str = items[0]

                    with writer.start_section(self._spec_import, qualname=f"import.{module}") as import_section:
                        _ = import_section.token("from ")
                        _ = import_section.token(module, CodeSectionImportSegment.MODULE.value)
                        _ = import_section.token(" import ")
                        _ = import_section.token(items_str, CodeSectionImportSegment.NAMES.value)
                        _ = import_section.token("\n")

                _ = writer.token("\n")

            # Emit lazy relationship imports (if any) using TYPE_CHECKING / ForwardRef
            lazy_imports = self._lazy_imports_for_file or {}
            if lazy_imports:
                _ = writer.token("if TYPE_CHECKING:\n")
                for module in sorted(lazy_imports.keys()):
                    for name in sorted(lazy_imports[module]):
                        with writer.start_section(
                            self._spec_import,
                            qualname=f"import_lazy_typecheck.{module}.{name}",
                        ) as import_section:
                            _ = import_section.token("    from ")
                            _ = import_section.token(module, CodeSectionImportSegment.MODULE.value)
                            _ = import_section.token(" import ")
                            _ = import_section.token(name, CodeSectionImportSegment.NAMES.value)
                            _ = import_section.token("\n")
                _ = writer.token("\n")

            # Categorize + preserve SSOT order of appearance (interleaving enums/classes)
            top_level: list[EnumConfig | ClassConfig] = []
            for obj in meta_objects:
                if isinstance(obj, EnumConfig) or isinstance(obj, ClassConfig):
                    top_level.append(obj)

            def _source_appearance_key(
                obj: EnumConfig | ClassConfig,
            ) -> tuple[int, str, int, str, str]:
                """
                Stable key for "order of appearance" within the source `.aware` file(s).

                We rely on OCG layout metadata as the SSOT for order.
                """
                # (missing_binding_bucket, code_id, byte_start, kind, name)
                missing_bucket = 1
                code_id = ""
                byte_start = 0
                kind = obj.__class__.__name__
                name = obj.name

                if isinstance(obj, ClassConfig):
                    layout_key = self._layout_order_by_class_id.get(obj.id)
                    if layout_key is not None:
                        code_id, byte_start = layout_key
                        missing_bucket = 0
                        kind = "class"
                        return (missing_bucket, code_id, byte_start, kind, name)
                else:
                    layout_key = self._layout_order_by_enum_id.get(obj.id)
                    if layout_key is not None:
                        code_id, byte_start = layout_key
                        missing_bucket = 0
                        kind = "enum"
                        return (missing_bucket, code_id, byte_start, kind, name)

                return (missing_bucket, code_id, byte_start, kind, name)

            if self.policy.respect_source_order:
                top_level.sort(key=_source_appearance_key)
            else:
                # Legacy deterministic ordering: keep stable grouping by kind then name.
                enums: list[EnumConfig] = [o for o in top_level if isinstance(o, EnumConfig)]
                classes: list[ClassConfig] = [o for o in top_level if isinstance(o, ClassConfig)]
                enums.sort(key=lambda e: (e.name, str(e.id)))
                classes.sort(key=lambda c: (c.name, str(c.id)))
                top_level = [*enums, *classes]

            registry_entries: list[ClassRegistryEntry] = []
            for obj in top_level:
                if isinstance(obj, EnumConfig):
                    self._render_enum(writer, obj)
                    _ = writer.token("\n\n")
                    continue

                class_config = obj
                is_inline_value = class_config.value_mode == ClassValueMode.inline_value
                method_specs: list[tuple[FunctionConfig, str, str, bool, str, bool]] = []
                if not is_inline_value and (
                    policy.emit_function_facades or policy.emit_function_io_models or policy.emit_function_registry
                ):
                    fn_links: list[ClassConfigFunctionConfig] = sorted(
                        class_config.class_config_function_configs,
                        key=lambda link: (
                            link.position,
                            link.function_config.name,
                        ),
                    )
                    # Derive object_type from the canonical class name using snake_case.
                    object_type_literal = to_snake_case(class_config.name)
                    for link in fn_links:
                        fn_cfg = link.function_config
                        is_constructor = link.is_constructor
                        is_public = link.is_public
                        input_cls, output_cls = self._get_function_io_class_names(class_config.name, fn_cfg.name)
                        method_specs.append(
                            (
                                fn_cfg,
                                input_cls,
                                output_cls,
                                is_constructor,
                                object_type_literal,
                                is_public,
                            )
                        )

                self._render_class(
                    writer,
                    class_config,
                    ("BaseModel" if is_inline_value else base_class_name),
                    method_specs,
                    class_to_class_config_map,
                )
                _ = writer.token("\n\n")

                function_registry_entries: list[FunctionRegistryEntry] = []
                if not is_inline_value and (policy.emit_function_io_models or policy.emit_function_registry):
                    for (
                        fn_cfg,
                        input_cls,
                        output_cls,
                        is_constructor,
                        _,
                        _is_public,
                    ) in method_specs:
                        if policy.emit_function_io_models:
                            input_cls, output_cls = self._render_function_io(
                                writer, class_config.name, fn_cfg, input_cls, output_cls
                            )
                            _ = writer.token("\n")
                        if policy.emit_function_registry:
                            function_registry_entries.append(
                                FunctionRegistryEntry(
                                    fn_cfg,
                                    input_cls,
                                    output_cls,
                                    is_constructor=is_constructor,
                                )
                            )

                if not is_inline_value and policy.emit_function_registry:
                    registry_entries.append(ClassRegistryEntry(class_config, function_registry_entries))

            if policy.emit_function_registry and registry_entries:
                self._render_registry(writer, registry_entries)
        finally:
            self._current_module = None


def _scrub_public_api_client_text(value: str) -> str:
    return (
        value.replace("Product A/Product B", "API/service")
        .replace("Generated Product A", "Generated API client")
        .replace("generated Product A", "generated API client")
        .replace("Product A consumers", "API client consumers")
        .replace("Product A", "generated API client")
        .replace("Generated Product B", "Generated service protocol")
        .replace("generated Product B", "generated service protocol")
        .replace("Product B", "service protocol")
        .replace("product A", "generated API client")
        .replace("product B", "service protocol")
    )

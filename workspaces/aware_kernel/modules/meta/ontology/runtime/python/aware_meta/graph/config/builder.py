"""Builder for ObjectConfigGraph instances."""

from __future__ import annotations

# @doc-ref: ../../../docs/ocg/build.md
# @test-ref: ../../../tests/test_ocg_annotations_hash.py
# @test-ref: ../../../tests/test_ocg_annotations_compilation.py
# @test-ref: ../../../tests/test_cross_ocg_inheritance_augment.py

import re
from uuid import UUID
from dataclasses import dataclass, field
import os

# Code Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation
from aware_code_ontology.binding.code_section_binding import CodeSectionBinding
from aware_code_ontology.enum.code_section_enum import CodeSectionEnum
from aware_code_ontology.class_.code_section_class import CodeSectionClass
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_code_ontology.mirror.code_section_mirror import CodeSectionMirror
from aware_code_ontology.projection.code_section_projection import CodeSectionProjection

# Code Runtime
from aware_code.language.registry import CodeLanguagePluginRegistry

# Content Ontology
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_mirror import (
    ObjectConfigGraphMirror,
)
from aware_meta_ontology.graph.config.object_config_graph_binding import (
    ObjectConfigGraphBinding,
)
from aware_meta_ontology.graph.config.object_config_graph_binding_class import (
    ObjectConfigGraphBindingClass,
)
from aware_meta_ontology.graph.config.object_config_graph_binding_formula import (
    ObjectConfigGraphBindingFormula,
)
from aware_meta_ontology.graph.config.object_config_graph_binding_formula_segment_reference import (
    ObjectConfigGraphBindingFormulaSegmentReference,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node_layout import (
    ObjectConfigGraphNodeLayout,
)
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
    ObjectProjectionGraphDeclaration,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_invocation import (
    FunctionConfigInvocation,
)
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_binding_formula_id,
    stable_object_config_graph_binding_formula_segment_reference_id,
)

# Meta Runtime
from aware_meta.fqn_resolver import NamespacePath, FqnRegistry, FqnResolver
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.graph.config.annotation.compiler import (
    compile_object_config_graph_annotations,
)
from aware_meta.graph.package.materialization import (
    compile_object_config_graph_package_projections,
    materialize_object_config_graph_package_identity_plane,
)
from aware_meta.graph.config.annotation.handlers import (
    apply_fk_override_annotations_to_relationships,
    apply_load_annotations_to_relationships,
    validate_discriminate_annotations,
    validate_index_annotations,
)
from aware_meta.graph.config.namespace_index import build_namespace_index
from aware_meta.graph.config.handlers import (
    build_object_config_graph_overlays_from_annotations,
)
from aware_meta.graph.config.hash import compute_object_config_graph_hash
from aware_meta.graph.config.mirror.builder import build_object_config_graph_mirrors
from aware_meta.graph.config.mirror.apply import (
    apply_object_config_graph_mirrors_to_build_inputs,
)
from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle
from aware_meta.graph.config.namespace.builder import (
    build_namespace_bundle_from_code_provenance,
)
from aware_meta.graph.config.overlay.handlers import (
    hydrate_object_config_graph_overlays,
)
from aware_meta.manifest.spec import AwarePackageKind
from aware_meta.graph.config.model_bootstrap import (
    build_object_config_graph_node,
    get_class_config_fqn,
    get_node_function_config,
    get_object_config_graph_node_key,
    set_class_config_identity_fields,
    set_enum_config_identity_fields,
)
from aware_meta.graph.config.stable_ids import (
    stable_class_config_id,
    stable_enum_config_id,
    stable_enum_option_id,
    stable_object_config_graph_binding_class_id,
    stable_object_config_graph_binding_id,
    stable_object_config_graph_id,
    stable_object_config_graph_node_id,
    stable_ocg_node_layout_id,
)
from aware_content_ontology.stable_ids import (
    stable_content_part_text_id,
    stable_content_part_text_segment_id,
)
from aware_meta.class_.config.builder import (
    build_class_config_from_code,
    build_class_config_members,
)
from aware_meta.class_.config.relationship.builder import (
    build_class_config_relationships,
)
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta.function.impl.builder import (
    apply_function_impl_kind,
    build_function_impl_from_body,
    build_function_invocation_plan_from_body,
    build_function_invocation_plan_from_impl,
)
from aware_meta.enum.config.builder import build_enum_config_from_code


@dataclass
class ObjectConfigGraphBuildResult:
    """Graph build result bundling the graph and cross-OCG relationships by target OCG."""

    graph: ObjectConfigGraph
    cross_relationships_by_target_ocg: dict[UUID, list[ClassConfigRelationship]]
    cross_class_configs_by_target_ocg: dict[UUID, dict[UUID, list[ClassConfig]]] = (
        field(default_factory=dict)
    )
    package_materialization_receipt: object | None = None


def _env_flag(name: str, *, default: bool) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


_ENABLE_FUNCTION_IMPL_SHADOW = _env_flag(
    "AWARE_META_ENABLE_FUNCTION_IMPL_SHADOW",
    default=False,
)
_ENABLE_FUNCTION_IMPL_INVOCATION_SOURCE = _env_flag(
    "AWARE_META_ENABLE_FUNCTION_IMPL_INVOCATION_SOURCE",
    default=False,
)


def _build_import_aliases_by_code_id(
    file_codes: list[tuple[str, Code]]
) -> dict[UUID, dict[str, str]]:
    """
    Build per-code import alias bindings from canonical `CodeSectionImport` objects.

    Canonical intent:
    - Code layer stores import *text* + byte provenance (no resolution).
    - Meta layer owns identifier resolution and may use explicit import aliases to expand identifiers.
    - Resolution precedence stays deterministic: local scope first, then import-expanded.

    Canonical Aware policy:
    - Imports only affect resolution when an explicit alias is provided (`import X as a`).
    - Imports without an alias are treated as semantic no-ops for identifier expansion.
    """
    binds_head_without_alias_by_language: dict[CodeLanguage, bool] = {}
    aliases_by_code_id: dict[UUID, dict[str, str]] = {}
    for _, code in file_codes:
        alias_map: dict[str, str] = {}
        binds_head_without_alias = True
        language = code.language
        if language:
            if language not in binds_head_without_alias_by_language:
                if MetaLanguagePluginRegistry.has_language(language):
                    binds_head_without_alias_by_language[language] = (
                        MetaLanguagePluginRegistry.get(
                            language
                        ).imports_bind_unaliased_module_head
                    )
                else:
                    # Fallback for call sites that did not register meta plugins.
                    binds_head_without_alias_by_language[language] = True
            binds_head_without_alias = binds_head_without_alias_by_language[language]

        for section in code.code_sections:
            if section.type != CodeSectionType.import_:
                continue
            imp = section.code_section_import
            if imp is None:
                continue

            module = (imp.module_text or "").strip()
            if not module:
                continue

            # `from module import name [as alias]` style imports.
            if imp.is_from_import:
                for name in imp.code_section_import_names:
                    imported = (name.name_text or "").strip()
                    if not imported:
                        continue

                    alias = (name.alias_text or "").strip() or None

                    # Star imports do not create deterministic symbol bindings here.
                    # (If/when we support them for resolution, they should surface explicitly as bindings.)
                    if imported == "*" or imp.is_star_import:
                        if alias:
                            alias_map[alias] = module
                        continue

                    bind_name = alias or imported
                    alias_map[bind_name] = f"{module}.{imported}"
                continue

            # `import module.* [as alias]` style imports.
            if imp.is_star_import:
                for name in imp.code_section_import_names:
                    alias = (name.alias_text or "").strip() or None
                    if alias:
                        # Canonical: alias points at the module prefix (no trailing `.*`).
                        alias_map[alias] = module
                continue

            # Regular `import module [as alias]` style imports.
            for name in imp.code_section_import_names:
                imported = (name.name_text or "").strip()
                if not imported:
                    continue
                alias = (name.alias_text or "").strip() or None
                if alias:
                    alias_map[alias] = imported
                else:
                    if not binds_head_without_alias:
                        continue
                    # Compatibility: first segment becomes the binding (e.g. `module.sub` binds `module`).
                    head = imported.split(".", 1)[0].strip()
                    if head:
                        alias_map[head] = imported

        if alias_map:
            aliases_by_code_id[code.id] = alias_map

    return aliases_by_code_id


def _layout_for_code_section(
    code_section: CodeSectionEnum | CodeSectionClass | CodeSectionFunction | None,
    rel_path_by_code_id: dict[UUID, str],
    graph_id: UUID,
    *,
    node_type: str,
    node_key: str,
) -> ObjectConfigGraphNodeLayout | None:
    if code_section is None:
        return None
    code_id = code_section.code_section.code_id
    rel_path = rel_path_by_code_id.get(code_id)
    if not rel_path:
        return None
    segment = code_section.code_section.content_part_text_segment
    source_position = (
        int(segment.byte_start) if segment.byte_start is not None else None
    )

    object_config_graph_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=graph_id,
        type=node_type,
        node_key=node_key,
    )
    return ObjectConfigGraphNodeLayout(
        id=stable_ocg_node_layout_id(
            object_config_graph_node_id=object_config_graph_node_id,
            layout_kind="aware",
        ),
        object_config_graph_node_id=object_config_graph_node_id,
        layout_kind="aware",
        relative_path=rel_path,
        source_position=source_position,
    )


def _hydrate_relationship_links_for_invocation_resolution(
    *,
    class_configs: list[ClassConfig],
    class_relationships: list[ClassConfigRelationship],
    cross_relationships_by_target_ocg: dict[UUID, list[ClassConfigRelationship]],
    external_graphs: list[ObjectConfigGraph] | None,
) -> None:
    """Attach relationship references needed by invocation-plan resolution.

    Invocation lowering resolves receiver paths through class relationship topology.
    Relationship synthesis is executed after class member configs are built, so we
    hydrate forward links here and then run invocation lowering in a second pass.
    """

    classes_by_id: dict[UUID, ClassConfig] = {cls.id: cls for cls in class_configs}
    for ext in external_graphs or []:
        for node in ext.object_config_graph_nodes:
            if (
                node.type == ObjectConfigGraphNodeType.class_
                and node.class_config is not None
            ):
                if node.class_config.id not in classes_by_id:
                    classes_by_id[node.class_config.id] = node.class_config

    attributes_by_id: dict[UUID, AttributeConfig] = {}
    for cls in class_configs:
        for cls_attr in cls.class_config_attribute_configs:
            attr = cls_attr.attribute_config
            attributes_by_id[attr.id] = attr
        cls.class_config_relationships.clear()

    all_relationships: list[ClassConfigRelationship] = list(class_relationships)
    for rels in cross_relationships_by_target_ocg.values():
        all_relationships.extend(rels)

    for rel in all_relationships:
        source_class = classes_by_id.get(rel.class_config_id)
        if source_class is None:
            continue
        if rel.target_class_config is None:
            rel.target_class_config = classes_by_id.get(rel.target_class_config_id)
        assoc_edge = rel.class_config_relationship_association_edge
        if assoc_edge is not None and assoc_edge.class_config is None:
            assoc_edge.class_config = classes_by_id.get(assoc_edge.class_config_id)
        for rel_attr in rel.class_config_relationship_attributes:
            if rel_attr.attribute_config is None:
                rel_attr.attribute_config = attributes_by_id.get(
                    rel_attr.attribute_config_id
                )
        source_class.class_config_relationships.append(rel)


def _rebuild_class_function_invocations(
    *,
    class_configs: list[ClassConfig],
    fail_on_unresolved: bool,
) -> None:
    """Lower canonical invocation plans after relationship topology is available.

    Compatibility rail:
    - Body-derived invocation plans remain canonical by default.
    - FunctionImpl shadow build and FunctionImpl-derived invocation plans are opt-in
      through env gates and must preserve canonical behavior.
    """

    for cls in class_configs:
        for cls_fn in cls.class_config_function_configs:
            function_config = cls_fn.function_config
            verb = str(function_config.verb or "").strip().casefold()
            is_constructor = bool(cls_fn.is_constructor) or verb == "construct"
            function_impl_required = (not fail_on_unresolved) or is_constructor
            body_invocations = build_function_invocation_plan_from_body(
                function_config=function_config,
                owner_class_config=cls,
                fail_on_unresolved=fail_on_unresolved,
            )
            function_config.invocations.clear()
            function_config.invocations.extend(body_invocations)

            function_impl = None
            if (
                function_impl_required
                or _ENABLE_FUNCTION_IMPL_SHADOW
                or _ENABLE_FUNCTION_IMPL_INVOCATION_SOURCE
            ):
                function_impl = build_function_impl_from_body(
                    function_config=function_config,
                    owner_class_config=cls,
                    fail_on_unresolved=(
                        fail_on_unresolved
                        and (
                            function_impl_required
                            or _ENABLE_FUNCTION_IMPL_SHADOW
                            or _ENABLE_FUNCTION_IMPL_INVOCATION_SOURCE
                        )
                    ),
                    is_constructor=is_constructor,
                )
                if function_impl is not None:
                    function_config.function_impl = function_impl

            if function_config.function_impl is not None:
                apply_function_impl_kind(
                    function_config=function_config,
                    function_impl=function_config.function_impl,
                    is_constructor=is_constructor,
                )

            if not _ENABLE_FUNCTION_IMPL_INVOCATION_SOURCE:
                continue
            if function_impl is None:
                continue

            capture_name_by_sequence = {
                inv.position: inv.capture_name for inv in body_invocations
            }
            impl_invocations = build_function_invocation_plan_from_impl(
                function_config=function_config,
                function_impl=function_impl,
                capture_name_by_sequence=capture_name_by_sequence,
            )
            if _invocation_plans_compatible(lhs=body_invocations, rhs=impl_invocations):
                function_config.invocations.clear()
                function_config.invocations.extend(impl_invocations)


def _invocation_plans_compatible(
    *, lhs: list[FunctionConfigInvocation], rhs: list[FunctionConfigInvocation]
) -> bool:
    if len(lhs) != len(rhs):
        return False
    lhs_sorted = sorted(lhs, key=lambda inv: (inv.position, str(inv.id)))
    rhs_sorted = sorted(rhs, key=lambda inv: (inv.position, str(inv.id)))
    for a, b in zip(lhs_sorted, rhs_sorted):
        if a.position != b.position:
            return False
        if a.kind != b.kind:
            return False
        if a.target_function_config_id != b.target_function_config_id:
            return False
        if a.class_config_relationship_id != b.class_config_relationship_id:
            return False
        if a.capture_name != b.capture_name:
            return False
        if a.root_kind != b.root_kind:
            return False
    return True


def _split_binding_target_ref(target_ref: str) -> tuple[str, str]:
    raw = (target_ref or "").strip()
    if "." not in raw:
        raise ValueError(
            f"Binding map target must resolve to Class.attr, got {target_ref!r}"
        )
    class_ref, attr_name = raw.rsplit(".", 1)
    class_ref = class_ref.strip()
    attr_name = attr_name.strip()
    if not class_ref or not attr_name:
        raise ValueError(
            f"Binding map target must resolve to Class.attr, got {target_ref!r}"
        )
    return class_ref, attr_name


def _resolve_binding_target_attribute(
    *,
    target_class: ClassConfig,
    target_attribute_name: str,
) -> ClassConfigAttributeConfig:
    for class_attr in target_class.class_config_attribute_configs:
        attr = class_attr.attribute_config
        if attr is not None and (attr.name or "").strip() == target_attribute_name:
            return class_attr
    class_fqn = (
        getattr(target_class, "class_fqn", None) or target_class.name or ""
    ).strip()
    raise ValueError(
        f"Binding map target attribute {target_attribute_name!r} not found on class {class_fqn!r}"
    )


_BINDING_TEMPLATE_PLACEHOLDER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _resolve_binding_source_attribute(
    *,
    source_class: ClassConfig,
    source_attribute_name: str,
) -> ClassConfigAttributeConfig:
    for class_attr in source_class.class_config_attribute_configs:
        attr = class_attr.attribute_config
        if attr is not None and (attr.name or "").strip() == source_attribute_name:
            return class_attr
    class_fqn = (
        getattr(source_class, "class_fqn", None) or source_class.name or ""
    ).strip()
    raise ValueError(
        f"Binding template placeholder {source_attribute_name!r} not found on source class {class_fqn!r}"
    )


def _iter_binding_template_placeholders(
    template_text: str,
) -> list[tuple[str, int, int]]:
    placeholders: list[tuple[str, int, int]] = []
    cursor = 0
    while cursor < len(template_text):
        ch = template_text[cursor]
        if ch == "}":
            raise ValueError(
                f"Binding template has stray closing brace at char offset {cursor}"
            )
        if ch != "{":
            cursor += 1
            continue
        end = template_text.find("}", cursor + 1)
        if end == -1:
            raise ValueError(
                f"Binding template has unclosed placeholder at char offset {cursor}"
            )
        placeholder_name = template_text[cursor + 1 : end].strip()
        if not _BINDING_TEMPLATE_PLACEHOLDER_RE.fullmatch(placeholder_name):
            raise ValueError(
                f"Binding template placeholder {placeholder_name!r} is invalid; "
                "expected identifier syntax like {door_label}"
            )
        placeholders.append((placeholder_name, cursor, end + 1))
        cursor = end + 1
    return placeholders


def _utf8_byte_offset(text: str, char_offset: int) -> int:
    return len(text[:char_offset].encode("utf-8"))


def _build_binding_formula(
    *,
    binding_class: ObjectConfigGraphBindingClass,
    source_class: ClassConfig,
    target_attribute: ClassConfigAttributeConfig,
    template_text: str,
) -> ObjectConfigGraphBindingFormula:
    attr = target_attribute.attribute_config
    if attr is None:
        raise ValueError(
            "Binding template target attribute relationship is missing AttributeConfig"
        )
    type_info = resolve_type_info(attr)
    if type_info.is_collection:
        raise ValueError(
            f"Binding template target attribute {attr.name!r} must be a scalar String, got collection type"
        )
    if type_info.primitive_config is None:
        raise ValueError(
            f"Binding template target attribute {attr.name!r} must be a primitive String, got {type_info.kind.value!r}"
        )
    primitive_type = CodePrimitiveType.model_validate(
        type_info.primitive_config.primitive_type
    )
    if primitive_type.base_type != CodePrimitiveBaseType.string:
        raise ValueError(
            f"Binding template target attribute {attr.name!r} must be a String-compatible primitive, got {primitive_type.base_type.value!r}"
        )

    formula_key = "default"
    formula_id = stable_object_config_graph_binding_formula_id(
        object_config_graph_binding_class_id=binding_class.id,
        key=formula_key,
    )
    content_key = f"{formula_id}:template"
    content_part_text = ContentPartText(
        id=stable_content_part_text_id(
            content_part_id=formula_id,
            key=content_key,
        ),
        content_part_id=formula_id,
        key=content_key,
        inline_text=template_text,
    )
    formula = ObjectConfigGraphBindingFormula(
        id=formula_id,
        object_config_graph_binding_class_id=binding_class.id,
        key=formula_key,
        content_part_text=content_part_text,
        content_part_text_id=content_part_text.id,
    )
    content_part_text.segments = []

    for idx, (placeholder_name, char_start, char_end) in enumerate(
        _iter_binding_template_placeholders(template_text)
    ):
        segment_key = f"{formula_id}:placeholder:{idx}:{placeholder_name}"
        segment = ContentPartTextSegment(
            id=stable_content_part_text_segment_id(
                content_part_text_id=content_part_text.id,
                key=segment_key,
            ),
            key=segment_key,
            content_part_text=content_part_text,
            content_part_text_id=content_part_text.id,
            byte_start=_utf8_byte_offset(template_text, char_start),
            byte_end=_utf8_byte_offset(template_text, char_end),
        )
        source_attr = _resolve_binding_source_attribute(
            source_class=source_class,
            source_attribute_name=placeholder_name,
        )
        formula.object_config_graph_binding_formula_segment_references.append(
            ObjectConfigGraphBindingFormulaSegmentReference(
                id=stable_object_config_graph_binding_formula_segment_reference_id(
                    object_config_graph_binding_formula_id=formula.id,
                    content_part_text_segment_id=segment.id,
                    source_class_config_attribute_config_id=source_attr.id,
                ),
                object_config_graph_binding_formula_id=formula.id,
                content_part_text_segment=segment,
                content_part_text_segment_id=segment.id,
                source_class_config_attribute_config=source_attr,
                source_class_config_attribute_config_id=source_attr.id,
            )
        )
        content_part_text.segments.append(segment)

    return formula


def _resolve_binding_target_class(
    *,
    target_graph: ObjectConfigGraph,
    target_class_ref: str,
) -> ClassConfig:
    raw = (target_class_ref or "").strip()
    parts = [part for part in raw.split(".") if part]
    if len(parts) < 2:
        raise ValueError(
            "Binding map target class must include a namespace or full FQN, "
            + f"got {target_class_ref!r}"
        )

    candidates: list[ClassConfig] = []
    for node in target_graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        class_fqn = get_class_config_fqn(node.class_config) or (
            getattr(node.class_config, "class_fqn", None) or ""
        )
        target_prefix = (target_graph.fqn_prefix or "").strip()
        fq_parts = [part for part in class_fqn.split(".") if part]
        if len(fq_parts) < 2 or fq_parts[0] != target_prefix:
            continue
        namespace = ".".join(fq_parts[1:-1])
        name = fq_parts[-1]
        if parts[0] == target_prefix:
            matched = class_fqn == raw
        else:
            matched = namespace == ".".join(parts[:-1]) and name == parts[-1]
        if matched:
            candidates.append(node.class_config)

    if not candidates:
        raise ValueError(
            f"Binding map target class {target_class_ref!r} not found in target graph {target_graph.fqn_prefix!r}"
        )
    unique_ids = {candidate.id for candidate in candidates}
    if len(unique_ids) > 1:
        raise ValueError(
            f"Binding map target class {target_class_ref!r} is ambiguous in target graph {target_graph.fqn_prefix!r}"
        )
    return candidates[0]


def _compile_object_config_graph_bindings(
    *,
    binding_sections: list[CodeSectionBinding],
    fqn_resolver: FqnResolver,
    object_config_graph_id: UUID,
    ocg_fqn_prefix: str,
    external_graphs: list[ObjectConfigGraph] | None,
) -> list[ObjectConfigGraphBinding]:
    external_graphs_by_prefix: dict[str, ObjectConfigGraph] = {}
    for ext in external_graphs or []:
        prefix = (ext.fqn_prefix or "").strip()
        if prefix:
            external_graphs_by_prefix[prefix] = ext

    bindings_by_target_graph_id: dict[UUID, ObjectConfigGraphBinding] = {}
    binding_class_keys_by_binding_id: dict[
        UUID, dict[tuple[UUID, UUID, UUID], ObjectConfigGraphBindingClass]
    ] = {}

    for binding_section in sorted(
        binding_sections,
        key=lambda item: (
            item.source_graph_ref or "",
            item.target_graph_ref or "",
            str(item.code_section.code_id),
        ),
    ):
        source_graph_ref = (binding_section.source_graph_ref or "").strip()
        if source_graph_ref != ocg_fqn_prefix:
            raise ValueError(
                f"Binding source graph must match current OCG fqn_prefix {ocg_fqn_prefix!r}, got {source_graph_ref!r}"
            )

        target_graph_ref = (binding_section.target_graph_ref or "").strip()
        target_graph = external_graphs_by_prefix.get(target_graph_ref)
        if target_graph is None:
            raise ValueError(
                f"Binding target graph {target_graph_ref!r} not found in external graphs for source {ocg_fqn_prefix!r}"
            )

        binding = bindings_by_target_graph_id.get(target_graph.id)
        if binding is None:
            binding = ObjectConfigGraphBinding(
                id=stable_object_config_graph_binding_id(
                    object_config_graph_id=object_config_graph_id,
                    target_object_config_graph_id=target_graph.id,
                ),
                object_config_graph_id=object_config_graph_id,
                target_object_config_graph=target_graph,
                target_object_config_graph_id=target_graph.id,
            )
            bindings_by_target_graph_id[target_graph.id] = binding
            binding_class_keys_by_binding_id[binding.id] = {}

        scope = fqn_resolver.scope_for_code_id(binding_section.code_section.code_id)
        binding_classes_by_key = binding_class_keys_by_binding_id[binding.id]
        for binding_map in binding_section.code_section_binding_maps or []:
            source_class = scope.resolve_class((binding_map.source_ref or "").strip())
            target_class_ref, target_attribute_name = _split_binding_target_ref(
                binding_map.target_ref or ""
            )
            target_class = _resolve_binding_target_class(
                target_graph=target_graph,
                target_class_ref=target_class_ref,
            )
            target_attribute = _resolve_binding_target_attribute(
                target_class=target_class,
                target_attribute_name=target_attribute_name,
            )
            binding_class_key = (
                source_class.id,
                target_class.id,
                target_attribute.id,
            )
            existing = binding_classes_by_key.get(binding_class_key)
            if existing is not None:
                if (existing.name or "").strip() != (binding_map.name or "").strip():
                    raise ValueError(
                        f"Binding map anchor collision for target graph {target_graph_ref!r}: "
                        f"{existing.name!r} and {binding_map.name!r} map the same Class -> Class.attr anchor"
                    )
                continue

            compiled = ObjectConfigGraphBindingClass(
                id=stable_object_config_graph_binding_class_id(
                    object_config_graph_binding_id=binding.id,
                    source_class_id=source_class.id,
                    target_class_id=target_class.id,
                    target_attribute_id=target_attribute.id,
                ),
                object_config_graph_binding_id=binding.id,
                name=(binding_map.name or "").strip(),
                description=(binding_map.description or "").strip() or None,
                source_class=source_class,
                source_class_id=source_class.id,
                target_class=target_class,
                target_class_id=target_class.id,
                target_attribute=target_attribute,
                target_attribute_id=target_attribute.id,
                source_attr_id=None,
            )
            if binding_map.template_text is not None:
                formula = _build_binding_formula(
                    binding_class=compiled,
                    source_class=source_class,
                    target_attribute=target_attribute,
                    template_text=binding_map.template_text,
                )
                compiled.binding_formula = formula
            binding.object_config_graph_binding_classes.append(compiled)
            binding_classes_by_key[binding_class_key] = compiled

    return [
        bindings_by_target_graph_id[key]
        for key in sorted(bindings_by_target_graph_id, key=str)
    ]


def build_object_config_graph(
    language: CodeLanguage,
    name: str,
    fqn_prefix: str,
    class_configs: list[ClassConfig],
    class_config_relationships: list[ClassConfigRelationship] | None,
    enum_configs: list[EnumConfig],
    function_configs: list[FunctionConfig],
    namespace_bundle: ObjectConfigGraphNamespaceBundle,
    description: str | None = None,
    object_config_graph_annotations: list[ObjectConfigGraphAnnotation] | None = None,
    object_projection_graph_declarations: (
        list[ObjectProjectionGraphDeclaration] | None
    ) = None,
    object_config_graph_bindings: list[ObjectConfigGraphBinding] | None = None,
    object_config_graph_mirrors: list[ObjectConfigGraphMirror] | None = None,
    object_config_graph_id: UUID | None = None,
    source_graph: ObjectConfigGraph | None = None,
    node_layouts_by_node_key: (
        dict[tuple[str, str], list[ObjectConfigGraphNodeLayout]] | None
    ) = None,
) -> ObjectConfigGraph:
    """
    Build an ObjectConfigGraph from its components.

    Args:
        object_config_graph_id: Optional ID of the ObjectConfigGraph (if None, a new UUID will be generated)
        language: Language of the graph
        name: Name for the graph
        package_name: Package name for the graph
        class_configs: List of ClassConfigs
        enum_configs: List of EnumConfigs
        function_configs: List of FunctionConfigs (global functions)
        description: Optional description

    Returns:
        A fully populated ObjectConfigGraph
    """
    layout_map: dict[tuple[str, str], list[ObjectConfigGraphNodeLayout]] = {}

    def _clone_layouts(
        layouts: list[ObjectConfigGraphNodeLayout] | None,
    ) -> list[ObjectConfigGraphNodeLayout]:
        return [layout.model_copy(deep=True) for layout in (layouts or [])]

    if source_graph is not None:
        for node in source_graph.object_config_graph_nodes:
            layouts = _clone_layouts(node.layouts)
            if not layouts:
                continue
            node_type = str(getattr(node.type, "value", node.type))
            node_key = get_object_config_graph_node_key(node)
            if (
                not node_key
                and node.type == ObjectConfigGraphNodeType.class_
                and node.class_config is not None
            ):
                node_key = (
                    get_class_config_fqn(node.class_config)
                    or (node.class_config.name or "").strip()
                )
            if (
                not node_key
                and node.type == ObjectConfigGraphNodeType.enum
                and node.enum_config is not None
            ):
                node_key = (node.enum_config.enum_fqn or "").strip()
            if not node_key and node.type == ObjectConfigGraphNodeType.function:
                node_function_config = get_node_function_config(node)
                if node_function_config is not None:
                    node_key = (node_function_config.name or "").strip()
            if (
                not node_key
                and node.type == ObjectConfigGraphNodeType.relationship
                and node.class_config_relationship is not None
            ):
                node_key = str(node.class_config_relationship.id)
            if node_type and node_key:
                layout_map[(node_type, node_key)] = layouts

    if node_layouts_by_node_key:
        for key, layouts in node_layouts_by_node_key.items():
            layout_map[key] = _clone_layouts(layouts)

    class_fqn_by_id: dict[UUID, str] = {}
    for class_config in class_configs:
        class_fqn = get_class_config_fqn(class_config) or ""
        if not class_fqn:
            ns = namespace_bundle.namespace_for_class(class_config.id)
            if ns is not None:
                class_fqn = ns.fqn(class_config.name)
        if class_fqn:
            class_fqn_by_id[class_config.id] = class_fqn

    def _function_node_key(function_config: FunctionConfig) -> str:
        ns = namespace_bundle.namespace_for_function(function_config.id)
        owner_fqn = ns.prefix() if ns is not None else ""
        return f"{owner_fqn}:{function_config.kind.value}:{function_config.name}".strip(
            ":"
        )

    def _relationship_node_key(relationship: ClassConfigRelationship) -> str:
        source_fqn = class_fqn_by_id.get(
            relationship.class_config_id, str(relationship.class_config_id)
        )
        target_fqn = class_fqn_by_id.get(
            relationship.target_class_config_id,
            str(relationship.target_class_config_id),
        )
        reference_name = ""
        for rel_attr in relationship.class_config_relationship_attributes:
            if (
                rel_attr.direction == ClassConfigRelationshipDirection.forward
                and rel_attr.role == ClassConfigRelationshipAttributeRole.reference
                and rel_attr.attribute_config is not None
            ):
                reference_name = rel_attr.attribute_config.name
                break
        if not reference_name:
            reference_name = str(relationship.id)
        return f"{source_fqn}:{reference_name}:{relationship.relationship_type.value}:{target_fqn}"

    # Build and return the graph using the parent builder method
    graph_hash = compute_object_config_graph_hash(
        language=language,
        fqn_prefix=fqn_prefix,
        namespace_bundle=namespace_bundle,
        class_configs=class_configs,
        class_config_relationships=class_config_relationships,
        enum_configs=enum_configs,
        function_configs=function_configs,
        object_config_graph_annotations=object_config_graph_annotations,
        object_projection_graph_declarations=object_projection_graph_declarations,
        object_config_graph_bindings=object_config_graph_bindings,
        object_config_graph_mirrors=object_config_graph_mirrors,
    )
    layout_hash = compute_object_config_graph_hash(
        language=language,
        fqn_prefix=fqn_prefix,
        namespace_bundle=namespace_bundle,
        class_configs=class_configs,
        class_config_relationships=class_config_relationships,
        enum_configs=enum_configs,
        function_configs=function_configs,
        object_config_graph_annotations=object_config_graph_annotations,
        object_projection_graph_declarations=object_projection_graph_declarations,
        object_config_graph_bindings=object_config_graph_bindings,
        object_config_graph_mirrors=object_config_graph_mirrors,
        node_layouts_by_node_key=layout_map,
        include_layout=True,
    )

    # Create basic graph structure with metadata
    #
    # Stable ID contract:
    # If callers don't supply an explicit graph id, derive it deterministically from (fqn_prefix, language).
    # This is REQUIRED because many transformers call `build_object_config_graph()` directly.
    derived_graph_id = object_config_graph_id or stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=language.value,
    )
    ocg = ObjectConfigGraph(
        id=derived_graph_id,
        language=language,
        name=name,
        description=description,
        hash=graph_hash,
        layout_hash=layout_hash,
        fqn_prefix=fqn_prefix,
    )

    # Add class configs (base + augments) as first-class nodes
    for cls in class_configs:
        class_node_key = class_fqn_by_id.get(cls.id, (cls.name or "").strip())
        ocg.object_config_graph_nodes.append(
            build_object_config_graph_node(
                object_config_graph_node_id=stable_object_config_graph_node_id(
                    object_config_graph_id=ocg.id,
                    type="class",
                    node_key=class_node_key,
                ),
                object_config_graph_id=ocg.id,
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_node_key,
                class_config=cls,
                layouts=_clone_layouts(layout_map.get(("class", class_node_key))),
            )
        )

    # Add relationship nodes (SSOT: ClassConfigRelationship)
    for rel in class_config_relationships or []:
        relationship_node_key = _relationship_node_key(rel)
        ocg.object_config_graph_nodes.append(
            build_object_config_graph_node(
                object_config_graph_node_id=stable_object_config_graph_node_id(
                    object_config_graph_id=ocg.id,
                    type="relationship",
                    node_key=relationship_node_key,
                ),
                object_config_graph_id=ocg.id,
                type=ObjectConfigGraphNodeType.relationship,
                node_key=relationship_node_key,
                class_config_relationship=rel,
                layouts=_clone_layouts(
                    layout_map.get(("relationship", relationship_node_key))
                ),
            )
        )

    # Add enum configs if provided
    for enum_config in enum_configs:
        enum_node_key = (enum_config.enum_fqn or "").strip()
        ocg.object_config_graph_nodes.append(
            build_object_config_graph_node(
                object_config_graph_node_id=stable_object_config_graph_node_id(
                    object_config_graph_id=ocg.id,
                    type="enum",
                    node_key=enum_node_key,
                ),
                object_config_graph_id=ocg.id,
                type=ObjectConfigGraphNodeType.enum,
                node_key=enum_node_key,
                enum_config=enum_config,
                layouts=_clone_layouts(layout_map.get(("enum", enum_node_key))),
            )
        )

    if function_configs:
        raise ValueError(
            "Standalone/global FunctionConfig entries are no longer allowed in canonical ObjectConfigGraph."
        )

    # Attach annotations (SSOT: CodeSectionAnnotation compiled views) to the graph.
    # IMPORTANT: callers may pass annotations from a different OCG instance (e.g., when
    # transformers rebuild graphs). Rebind object_config_graph_id so downstream overlay/
    # projection builders can operate on the derived graph deterministically.
    if object_config_graph_annotations:
        for ann in object_config_graph_annotations:
            ann.object_config_graph_id = ocg.id
        ocg.object_config_graph_annotations.extend(object_config_graph_annotations)
    if object_projection_graph_declarations:
        for decl in object_projection_graph_declarations:
            decl.object_config_graph_id = ocg.id
            for bind in decl.object_projection_graph_bindings or []:
                bind.object_projection_graph_declaration_id = decl.id
        ocg.object_projection_graph_declarations.extend(
            object_projection_graph_declarations
        )
    if object_config_graph_bindings:
        for binding in object_config_graph_bindings:
            binding.object_config_graph_id = ocg.id
            for binding_class in binding.object_config_graph_binding_classes or []:
                binding_class.object_config_graph_binding_id = binding.id
        ocg.object_config_graph_bindings.extend(object_config_graph_bindings)
    if object_config_graph_mirrors:
        ocg.object_config_graph_mirrors.extend(object_config_graph_mirrors)
    return ocg


def build_import_aliases_by_code_id(
    file_codes: list[tuple[str, Code]]
) -> dict[UUID, dict[str, str]]:
    """Public wrapper for canonical import alias extraction.

    This is consumed by both the OCG builder and language-service tooling so import
    semantics stay consistent across build-time and editor-time.
    """
    return _build_import_aliases_by_code_id(file_codes)


def build_object_config_graph_from_code(
    name: str,
    description: str,
    fqn_prefix: str,
    file_codes: list[tuple[str, Code]],
    namespace_by_code_id: dict[UUID, NamespacePath],
    package_kind: AwarePackageKind = AwarePackageKind.ontology,
    external_graphs: list[ObjectConfigGraph] | None = None,
) -> ObjectConfigGraphBuildResult:
    """
    Convert a bundle of code objects into an ObjectConfigGraph.

    Args:
        name: Name to give the graph
        description: Description of the graph
        fqn_prefix: Root namespace of the graph (NamespacePath.package)
        file_codes: List of file codes
        namespace_by_code_id: Namespace by code ID
        package_kind: Package kind (ontology, api or db) (default: ontology)
        external_graphs: List of external graphs

    Returns:
        A complete ObjectConfigGraph containing all extracted configurations
    """
    if not file_codes:
        raise ValueError("file_codes must be non-empty")

    # Canonical: single-language graph per build call
    languages = {code.language for _, code in file_codes if code.language is not None}
    if len(languages) != 1:
        raise ValueError(f"Expected one language per OCG build, got: {languages}")
    language = _normalize_code_language(next(iter(languages)))
    # Stable ID contract: graph identity is derived from (fqn_prefix, language).
    # Many downstream artifacts (mirrors/layouts) need this before full graph materialization.
    object_config_graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=language.value,
    )

    imports_by_code_id = build_import_aliases_by_code_id(file_codes)
    rel_path_by_code_id: dict[UUID, str] = {
        code.id: rel_path for rel_path, code in file_codes
    }

    # Extract sections from code sections
    enum_sections: list[CodeSectionEnum] = []
    class_sections: list[CodeSectionClass] = []
    function_sections: list[CodeSectionFunction] = []
    annotation_sections: list[CodeSectionAnnotation] = []
    mirror_sections: list[CodeSectionMirror] = []
    projection_sections: list[CodeSectionProjection] = []
    binding_sections: list[CodeSectionBinding] = []
    for _, code in file_codes:
        # Extract code sections by type
        for code_section in code.code_sections:
            if code_section.type == CodeSectionType.enum:
                if code_section.code_section_enum is not None:
                    enum_sections.append(code_section.code_section_enum)
            elif code_section.type == CodeSectionType.class_:
                if code_section.code_section_class is not None:
                    class_sections.append(code_section.code_section_class)
            elif code_section.type == CodeSectionType.function:
                if code_section.code_section_function is not None:
                    function_sections.append(code_section.code_section_function)
            elif code_section.type == CodeSectionType.annotation:
                if code_section.code_section_annotation is not None:
                    annotation_sections.append(code_section.code_section_annotation)
            elif code_section.type == CodeSectionType.mirror:
                if code_section.code_section_mirror is not None:
                    mirror_sections.append(code_section.code_section_mirror)
            elif code_section.type == CodeSectionType.projection:
                if code_section.code_section_projection is not None:
                    projection_sections.append(code_section.code_section_projection)
            elif code_section.type == CodeSectionType.binding:
                if code_section.code_section_binding is not None:
                    binding_sections.append(code_section.code_section_binding)

    def _namespace_for_code_id(code_id: UUID) -> NamespacePath:
        ns = namespace_by_code_id.get(code_id)
        if ns is None:
            raise ValueError(f"Missing NamespacePath for code_id={code_id}")
        return ns

    resolved_graph_id = object_config_graph_id or stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=language.value,
    )

    # Build enum configs under deterministic node scope.
    enum_configs: list[EnumConfig] = []
    for enum_section in enum_sections:
        ns = _namespace_for_code_id(enum_section.code_section.code_id)
        enum_config = build_enum_config_from_code(
            code_section_enum=enum_section, namespace=ns
        )
        enum_node_key = enum_config.enum_fqn
        enum_node_id = stable_object_config_graph_node_id(
            object_config_graph_id=resolved_graph_id,
            type="enum",
            node_key=enum_node_key,
        )
        set_enum_config_identity_fields(
            enum_config=enum_config,
            object_config_graph_node_id=enum_node_id,
        )
        enum_config.id = stable_enum_config_id(
            object_config_graph_node_id=enum_node_id,
            enum_fqn=enum_config.enum_fqn,
        )
        for enum_option in enum_config.enum_options:
            enum_option.enum_config_id = enum_config.id
            enum_option.id = stable_enum_option_id(
                enum_config_id=enum_config.id,
                value=enum_option.value,
            )
        enum_configs.append(enum_config)

    # ---------------------------------------------------------------------
    # Build base ClassConfigs first.
    # Canonical rule: any class with at least one CodeSectionClassBase is a child class config.
    # This keeps Meta language-agnostic: Aware `augment` and Python `class Foo(Bar)` both surface as bases.
    # ---------------------------------------------------------------------
    base_class_sections: list[CodeSectionClass] = []
    child_class_sections: list[CodeSectionClass] = []
    for cs in class_sections:
        (
            child_class_sections if cs.code_section_class_bases else base_class_sections
        ).append(cs)

    # Deterministic ordering
    base_class_sections.sort(key=lambda cs: (str(cs.code_section.code_id), cs.name))
    child_class_sections.sort(key=lambda cs: (str(cs.code_section.code_id), cs.name))

    def _value_mode_for_class(cs: CodeSectionClass) -> ClassValueMode:
        # API packages are inline-value worlds (payload trees, not graph instances).
        if package_kind == AwarePackageKind.api:
            return ClassValueMode.inline_value
        # Ontology/DB: allow explicit inline-value classes in `.aware`; otherwise graph refs.
        if cs.is_inline_value:
            return ClassValueMode.inline_value
        return ClassValueMode.graph_ref

    class_configs: list[ClassConfig] = []
    # Stable ID contract for ClassConfig: derive from deterministic class node scope + canonical FQN.
    for cs in base_class_sections:
        ns = _namespace_for_code_id(cs.code_section.code_id)
        class_fqn = ns.fqn(cs.name)
        class_node_id = stable_object_config_graph_node_id(
            object_config_graph_id=resolved_graph_id,
            type="class",
            node_key=class_fqn,
        )
        cc = build_class_config_from_code(
            code_section_class=cs,
            parent_class_id=None,
            value_mode=_value_mode_for_class(cs),
            class_fqn=class_fqn,
            object_config_graph_node_id=class_node_id,
        )
        set_class_config_identity_fields(
            class_config=cc,
            object_config_graph_node_id=class_node_id,
            class_fqn=class_fqn,
        )
        cc.id = stable_class_config_id(
            object_config_graph_node_id=class_node_id,
            class_fqn=class_fqn,
        )
        class_configs.append(cc)

    # ---------------------------------------------------------------------
    # FQN Resolution Barrier (package.namespace.{ClassName|EnumName})
    # ---------------------------------------------------------------------
    fqn_resolver = build_fqn_resolver(
        namespace_by_code_id=namespace_by_code_id,
        enum_configs=enum_configs,
        class_configs=class_configs,
        imports_by_code_id=imports_by_code_id,
        external_graphs=external_graphs,
    )

    # Local-only map; external parents are emitted as cross-OCG augments (link phase materializes them).
    class_config_id_to_class_config: dict[UUID, ClassConfig] = {
        c.id: c for c in class_configs
    }

    # External parent lookup: class_config_id -> (target_graph_id, target_class_config_id)
    external_parent_by_class_config_id: dict[UUID, tuple[UUID, UUID]] = {}
    for ext in external_graphs or []:
        # Canonical: external graphs are class-first. We map any external class_config_id
        # to its identity anchor (the root/base class_config_id within that external graph).
        ext_classes_by_id: dict[UUID, ClassConfig] = {}
        for node in ext.object_config_graph_nodes:
            if (
                node.type != ObjectConfigGraphNodeType.class_
                or node.class_config is None
            ):
                continue
            ext_classes_by_id[node.class_config.id] = node.class_config

        def _root_class_id(class_config_id: UUID) -> UUID:
            cur = ext_classes_by_id.get(class_config_id)
            if cur is None:
                return class_config_id
            seen: set[UUID] = set()
            while cur.parent_class_id is not None and cur.parent_class_id not in seen:
                seen.add(cur.id)
                nxt = ext_classes_by_id.get(cur.parent_class_id)
                if nxt is None:
                    return cur.parent_class_id
                cur = nxt
            return cur.id

        for cid in ext_classes_by_id.keys():
            root_id = _root_class_id(cid)
            prev = external_parent_by_class_config_id.get(cid)
            if prev is not None and prev[0] != ext.id:
                raise ValueError(
                    f"Duplicate class_config_id across external graphs: {cid}"
                )
            external_parent_by_class_config_id[cid] = (ext.id, root_id)

    # ---------------------------------------------------------------------
    # Build child class configs (single inheritance) with proper ordering.
    #
    # IMPORTANT: We must support chains like:
    #   class B augment A { ... }
    #   class C augment B { ... }
    #
    # The previous implementation only resolved child bases against the initial
    # resolver (base_class_sections + externals), which made `C augment B`
    # fail when `B` is also a child/augment class (not yet registered).
    #
    # Canonical approach:
    # - Iteratively resolve + build child classes whose base_ref resolves against
    #   the CURRENT symbol universe (base classes + already-built children + externals).
    # - Allow unresolved non-augment bases (e.g. framework bases like BaseModel) by treating as root.
    # - Require unresolved augment bases to resolve (error).
    # ---------------------------------------------------------------------
    cross_class_configs_by_target_ocg: dict[UUID, dict[UUID, list[ClassConfig]]] = {}
    cross_child_class_configs: list[ClassConfig] = []

    pending_children: list[CodeSectionClass] = list(child_class_sections)
    built_any = True
    while pending_children and built_any:
        built_any = False

        # Rebuild resolver with any newly built child class configs included so subsequent
        # child base edges can resolve within the same schema deterministically.
        fqn_resolver = build_fqn_resolver(
            namespace_by_code_id=namespace_by_code_id,
            enum_configs=enum_configs,
            class_configs=class_configs,
            imports_by_code_id=imports_by_code_id,
            external_graphs=external_graphs,
        )

        remaining: list[CodeSectionClass] = []
        for child_section in pending_children:
            # M0: deterministic single inheritance.
            if len(child_section.code_section_class_bases) > 1:
                raise ValueError(
                    f"Multiple base edges found for child class {child_section.name}. Not supported yet."
                )
            base_edge = child_section.code_section_class_bases[0]
            base_ref = base_edge.base_ref
            scope = fqn_resolver.scope_for_code_id(child_section.code_section.code_id)
            parent_resolved = scope.try_resolve_class_with_fqn(base_ref)
            if parent_resolved is None:
                # Canonical: allow unresolved bases (e.g., Python framework bases like `BaseModel`) by treating
                # the class as a root. Only bases that resolve within the current/external symbol universe
                # participate in meta inheritance.
                #
                # Exception: `augment` bases are semantic and must resolve.
                if base_edge.is_augment:
                    # Defer if it might be another pending child; otherwise raise at the end.
                    remaining.append(child_section)
                    continue
                ns = _namespace_for_code_id(child_section.code_section.code_id)
                child_class_fqn = ns.fqn(child_section.name)
                child_class_node_id = stable_object_config_graph_node_id(
                    object_config_graph_id=resolved_graph_id,
                    type="class",
                    node_key=child_class_fqn,
                )
                child_class_config = build_class_config_from_code(
                    code_section_class=child_section,
                    parent_class_id=None,
                    value_mode=_value_mode_for_class(child_section),
                    class_fqn=child_class_fqn,
                    object_config_graph_node_id=child_class_node_id,
                )
                set_class_config_identity_fields(
                    class_config=child_class_config,
                    object_config_graph_node_id=child_class_node_id,
                    class_fqn=child_class_fqn,
                )
                child_class_config.id = stable_class_config_id(
                    object_config_graph_node_id=child_class_node_id,
                    class_fqn=child_class_fqn,
                )
                class_configs.append(child_class_config)
                class_config_id_to_class_config[child_class_config.id] = (
                    child_class_config
                )
                built_any = True
                continue

            _parent_fqn, parent_class_config = parent_resolved
            ns = _namespace_for_code_id(child_section.code_section.code_id)
            child_class_fqn = ns.fqn(child_section.name)
            child_class_node_id = stable_object_config_graph_node_id(
                object_config_graph_id=resolved_graph_id,
                type="class",
                node_key=child_class_fqn,
            )
            child_class_config = build_class_config_from_code(
                code_section_class=child_section,
                parent_class_id=parent_class_config.id,
                value_mode=_value_mode_for_class(child_section),
                class_fqn=child_class_fqn,
                object_config_graph_node_id=child_class_node_id,
            )
            set_class_config_identity_fields(
                class_config=child_class_config,
                object_config_graph_node_id=child_class_node_id,
                class_fqn=child_class_fqn,
            )
            child_class_config.id = stable_class_config_id(
                object_config_graph_node_id=child_class_node_id,
                class_fqn=child_class_fqn,
            )
            parent_local = class_config_id_to_class_config.get(parent_class_config.id)
            if parent_local is not None:
                class_configs.append(child_class_config)
                class_config_id_to_class_config[child_class_config.id] = (
                    child_class_config
                )
            else:
                ext_parent = external_parent_by_class_config_id.get(
                    parent_class_config.id
                )
                if ext_parent is None:
                    raise KeyError(parent_class_config.id)
                target_graph_id, target_class_config_id = ext_parent
                cross_class_configs_by_target_ocg.setdefault(
                    target_graph_id, {}
                ).setdefault(target_class_config_id, []).append(child_class_config)
                # Even when the parent is external, the augmenting class is STILL a local class in this graph.
                class_configs.append(child_class_config)
                class_config_id_to_class_config[child_class_config.id] = (
                    child_class_config
                )
                cross_child_class_configs.append(child_class_config)

            built_any = True

        pending_children = remaining

    if pending_children:
        # At this point, any remaining children MUST be `augment` with unresolved bases.
        # Resolve once more to emit a high-signal error for the first missing base.
        fqn_resolver = build_fqn_resolver(
            namespace_by_code_id=namespace_by_code_id,
            enum_configs=enum_configs,
            class_configs=class_configs,
            imports_by_code_id=imports_by_code_id,
            external_graphs=external_graphs,
        )
        first = pending_children[0]
        base_edge = first.code_section_class_bases[0]
        scope = fqn_resolver.scope_for_code_id(first.code_section.code_id)
        _ = scope.resolve_class(base_edge.base_ref)
        # Should be unreachable (resolve_class raises), but keep a guard.
        raise ValueError(
            f"Unresolved augment base {base_edge.base_ref!r} for child class {first.name} in scope={scope.namespace.prefix()}"
        )

    # Final resolver including all classes (base + children) for subsequent phases
    fqn_resolver = build_fqn_resolver(
        namespace_by_code_id=namespace_by_code_id,
        enum_configs=enum_configs,
        class_configs=class_configs,
        imports_by_code_id=imports_by_code_id,
        external_graphs=external_graphs,
    )

    # ---------------------------------------------------------------------
    # Mirrors (API-only): apply before member typing so local API code can reference mirrored symbols.
    # ---------------------------------------------------------------------
    node_layouts_by_node_key: dict[
        tuple[str, str], list[ObjectConfigGraphNodeLayout]
    ] = {}
    for cls in class_configs:
        class_node_key = get_class_config_fqn(cls)
        if not class_node_key and cls.code_section_class is not None:
            class_node_key = _namespace_for_code_id(
                cls.code_section_class.code_section.code_id
            ).fqn(cls.name)
        if not class_node_key:
            continue
        layout = _layout_for_code_section(
            cls.code_section_class,
            rel_path_by_code_id,
            resolved_graph_id,
            node_type="class",
            node_key=class_node_key,
        )
        if layout is not None:
            node_layouts_by_node_key[("class", class_node_key)] = [layout]
    for enum_cfg in enum_configs:
        layout = _layout_for_code_section(
            enum_cfg.code_section_enum,
            rel_path_by_code_id,
            resolved_graph_id,
            node_type="enum",
            node_key=enum_cfg.enum_fqn,
        )
        if layout is not None:
            node_layouts_by_node_key[("enum", enum_cfg.enum_fqn)] = [layout]

    namespace_bundle = build_namespace_bundle_from_code_provenance(
        namespace_by_code_id=namespace_by_code_id,
        class_configs=class_configs,
        enum_configs=enum_configs,
        function_configs=[],
    )

    compiled_mirrors: list[ObjectConfigGraphMirror] = build_object_config_graph_mirrors(
        object_config_graph_id=resolved_graph_id,
        mirror_sections=mirror_sections,
        rel_path_by_code_id=rel_path_by_code_id,
        fqn_resolver=fqn_resolver,
        namespace_by_code_id=namespace_by_code_id,
        external_graphs=external_graphs,
    )
    if compiled_mirrors:
        if package_kind != AwarePackageKind.api:
            raise ValueError(
                f"Mirrors are only supported for API packages, not {package_kind.value!r}"
            )
        namespace_bundle = apply_object_config_graph_mirrors_to_build_inputs(
            ocg_id=resolved_graph_id,
            fqn_prefix=fqn_prefix,
            class_configs=class_configs,
            enum_configs=enum_configs,
            function_configs=[],
            namespace_bundle=namespace_bundle,
            object_config_graph_mirrors=compiled_mirrors,
            external_graphs_by_id={g.id: g for g in (external_graphs or [])},
            node_layouts_by_node_key=node_layouts_by_node_key,
        )
        # Rebuild resolver including the local mirror copies (mirror types have no code provenance).
        fqn_resolver = build_fqn_resolver(
            namespace_by_code_id=namespace_by_code_id,
            enum_configs=enum_configs,
            class_configs=class_configs,
            namespace_bundle=namespace_bundle,
            imports_by_code_id=imports_by_code_id,
            external_graphs=external_graphs,
        )

    # ---------------------------------------------------------------------
    # Link attribute + function configs to all class configs (SSOT only)
    # ---------------------------------------------------------------------
    plugin = CodeLanguagePluginRegistry.get(language)
    primitive_codec = plugin.primitive_codec
    type_descriptor_adapter = plugin.type_descriptor_adapter

    for cls_cfg in class_configs:
        if cls_cfg.code_section_class is None:
            continue
        build_class_config_members(
            cls_cfg, fqn_resolver, primitive_codec, type_descriptor_adapter
        )
    for cls_cfg in cross_child_class_configs:
        if cls_cfg.code_section_class is None:
            continue
        build_class_config_members(
            cls_cfg, fqn_resolver, primitive_codec, type_descriptor_adapter
        )

    # ---------------------------------------------------------------------
    # Build global (standalone) function configs (exclude methods via class edges)
    # ---------------------------------------------------------------------
    method_function_ids: set[UUID] = set()
    for cs in class_sections:
        for code_section_class_function in cs.code_section_class_functions:
            method_function_ids.add(
                code_section_class_function.code_section_function.id
            )

    global_function_configs: list[FunctionConfig] = []
    for function_section in function_sections:
        if function_section.id in method_function_ids:
            continue
        ns = _namespace_for_code_id(function_section.code_section.code_id)
        raise ValueError(
            "Standalone/global functions are not modeled in canonical ObjectConfigGraph. "
            f"Attach function `{function_section.name}` under a class scope "
            f"(namespace={ns.prefix()})."
        )

    # ---------------------------------------------------------------------
    # Inline-value invariants: value objects are never ORM graph entities.
    # ---------------------------------------------------------------------
    invalid_inline: list[str] = []
    for cls_cfg in class_configs:
        if cls_cfg.value_mode != ClassValueMode.inline_value:
            continue
        if cls_cfg.is_edge:
            invalid_inline.append(
                f"class_config_id={cls_cfg.id} name={cls_cfg.name} is_edge={cls_cfg.is_edge}"
            )
    if invalid_inline:
        raise ValueError(
            f"inline_value classes must not be edge/branchable (value objects are not graph instances). Invalid classes: {invalid_inline}"
        )

    # Inline-value classes must not reference graph_ref classes via AttributeTypeDescriptorKind.class_.
    # Canonical invariant: inline_value is a pure value world (no graph refs).
    classes_by_id_for_inline: dict[UUID, ClassConfig] = {c.id: c for c in class_configs}
    for ext in external_graphs or []:
        for n in ext.object_config_graph_nodes:
            if (
                n.type == ObjectConfigGraphNodeType.class_
                and n.class_config is not None
            ):
                if n.class_config.id not in classes_by_id_for_inline:
                    classes_by_id_for_inline[n.class_config.id] = n.class_config

    def _iter_type_descriptors(
        td: AttributeTypeDescriptor,
    ) -> list[AttributeTypeDescriptor]:
        out: list[AttributeTypeDescriptor] = []
        stack = [td]
        seen: set[UUID] = set()
        while stack:
            cur = stack.pop()
            if cur.id in seen:
                continue
            seen.add(cur.id)
            out.append(cur)
            for link in cur.child_links:
                stack.append(link.child)
        return out

    invalid_inline_refs: list[str] = []
    for cls_cfg in class_configs:
        if cls_cfg.value_mode != ClassValueMode.inline_value:
            continue
        for edge in cls_cfg.class_config_attribute_configs:
            attr = edge.attribute_config
            for td in _iter_type_descriptors(attr.type_descriptor):
                if (
                    td.kind != AttributeTypeDescriptorKind.class_
                    or td.class_config_id is None
                ):
                    continue
                target_cls = classes_by_id_for_inline.get(td.class_config_id)
                if target_cls is None:
                    invalid_inline_refs.append(
                        f"inline_value_missing_class_ref class_config_id={cls_cfg.id} class_name={cls_cfg.name} attr={attr.name} ref_class_config_id={td.class_config_id}"
                    )
                    continue
                if target_cls.value_mode == ClassValueMode.graph_ref:
                    invalid_inline_refs.append(
                        f"inline_value_graph_ref_ref class_config_id={cls_cfg.id} class_name={cls_cfg.name} attr={attr.name} ref_class_config_id={target_cls.id} ref_class_name={target_cls.name}"
                    )
    if invalid_inline_refs:
        raise ValueError(
            f"inline_value classes must not reference graph_ref classes (no graph refs inside value objects). Violations: {invalid_inline_refs}"
        )

    # Update namespace bundle with global function namespaces (classes/enums may include mirrors).
    provenance_bundle = build_namespace_bundle_from_code_provenance(
        namespace_by_code_id=namespace_by_code_id,
        class_configs=class_configs,
        enum_configs=enum_configs,
        function_configs=global_function_configs,
    )
    namespace_bundle = ObjectConfigGraphNamespaceBundle(
        namespace_by_class_config_id=dict(
            namespace_bundle.namespace_by_class_config_id
        ),
        namespace_by_enum_config_id=dict(namespace_bundle.namespace_by_enum_config_id),
        namespace_by_function_config_id=dict(
            provenance_bundle.namespace_by_function_config_id
        ),
    )

    # Build relationships between objects (SSOT: class relationships; single-sided)
    class_rels, cross_map = build_class_config_relationships(
        class_configs=class_configs,
        fqn_resolver=fqn_resolver,
        external_graphs=external_graphs,
    )
    # Enforce: inline_value classes are value types only and must not participate in relationships.
    # Relationships are only valid between graph_ref classes (local or cross-OCG).
    classes_by_id: dict[UUID, ClassConfig] = {c.id: c for c in class_configs}
    for ext in external_graphs or []:
        for n in ext.object_config_graph_nodes:
            if (
                n.type == ObjectConfigGraphNodeType.class_
                and n.class_config is not None
            ):
                if n.class_config.id not in classes_by_id:
                    classes_by_id[n.class_config.id] = n.class_config

    invalid_rels: list[str] = []

    def _value_mode(class_config_id: UUID) -> ClassValueMode | None:
        cls = classes_by_id.get(class_config_id)
        return cls.value_mode if cls is not None else None

    def _check_relationship(rel: ClassConfigRelationship) -> None:
        for endpoint_name, endpoint_id in (
            ("source", rel.class_config_id),
            ("target", rel.target_class_config_id),
        ):
            mode = _value_mode(endpoint_id)
            if mode is None:
                invalid_rels.append(
                    f"relationship_id={rel.id} endpoint={endpoint_name} class_config_id={endpoint_id} missing_value_mode"
                )
                continue
            if mode != ClassValueMode.graph_ref:
                invalid_rels.append(
                    f"relationship_id={rel.id} endpoint={endpoint_name} class_config_id={endpoint_id} value_mode={mode}"
                )

    for rel in class_rels or []:
        _check_relationship(rel)
    for rels in cross_map.values():
        for rel in rels or []:
            _check_relationship(rel)

    if invalid_rels:
        raise ValueError(
            f"Relationships must not touch inline_value classes; only graph_ref endpoints are allowed. Invalid endpoints: {invalid_rels}"
        )

    # ---------------------------------------------------------------------
    # Compile annotations BEFORE hashing, so annotation semantics are part of the OCG hash.
    # (Default generic compiler; optional per-language override)
    # ---------------------------------------------------------------------
    compiled_annotations = []
    if annotation_sections:
        compiler = compile_object_config_graph_annotations
        try:
            meta_plugin = MetaLanguagePluginRegistry.get(language)
        except Exception:
            meta_plugin = None
        if meta_plugin is not None and meta_plugin.annotation_compiler is not None:
            compiler = meta_plugin.annotation_compiler
        compiled_annotations = compiler(
            annotation_sections,
            fqn_resolver,
            object_config_graph_id=object_config_graph_id,
        )

    # ---------------------------------------------------------------------
    # Compile first-class `projection { ... }` declarations into compiler-owned OCG SSOT.
    # Projections are semantic (hashable) and must not be lowered into `ObjectConfigGraphAnnotation`.
    # ---------------------------------------------------------------------
    projection_declarations = []
    projection_declarations_by_name = {}
    if projection_sections:
        projection_compilation = compile_object_config_graph_package_projections(
            code_section_projections=projection_sections,
            fqn_resolver=fqn_resolver,
            object_config_graph_id=object_config_graph_id,
            ocg_fqn_prefix=fqn_prefix,
        )
        projection_declarations = list(projection_compilation.declarations)
        projection_declarations_by_name = projection_compilation.declarations_by_name

    compiled_bindings: list[ObjectConfigGraphBinding] = []
    if binding_sections:
        compiled_bindings = _compile_object_config_graph_bindings(
            binding_sections=binding_sections,
            fqn_resolver=fqn_resolver,
            object_config_graph_id=object_config_graph_id,
            ocg_fqn_prefix=fqn_prefix,
            external_graphs=external_graphs,
        )

    # ---------------------------------------------------------------------
    # Apply LOAD annotation semantics to relationships BEFORE hashing.
    # This makes relationship loading strategies SSOT at the OCG level.
    # ---------------------------------------------------------------------
    if compiled_annotations:
        validate_discriminate_annotations(
            compiled_annotations=compiled_annotations,
            class_configs=class_configs,
            namespace_by_class_config_id=namespace_bundle.namespace_by_class_config_id,
            external_graphs=external_graphs,
        )
        validate_index_annotations(
            compiled_annotations=compiled_annotations,
            class_configs=class_configs,
            namespace_by_class_config_id=namespace_bundle.namespace_by_class_config_id,
        )
        apply_fk_override_annotations_to_relationships(
            compiled_annotations=compiled_annotations,
            class_relationships=class_rels,
            cross_relationships_by_target_ocg=cross_map,
            class_configs=class_configs,
            namespace_by_class_config_id=namespace_bundle.namespace_by_class_config_id,
        )
        apply_load_annotations_to_relationships(
            compiled_annotations=compiled_annotations,
            class_relationships=class_rels,
            cross_relationships_by_target_ocg=cross_map,
            class_configs=class_configs,
            namespace_by_class_config_id=namespace_bundle.namespace_by_class_config_id,
        )

    # Rebuild function invocation plans after relationship topology is available.
    _hydrate_relationship_links_for_invocation_resolution(
        class_configs=class_configs,
        class_relationships=class_rels,
        cross_relationships_by_target_ocg=cross_map,
        external_graphs=external_graphs,
    )
    _rebuild_class_function_invocations(
        class_configs=class_configs,
        fail_on_unresolved=(language != CodeLanguage.aware),
    )

    # Build the graph
    graph = build_object_config_graph(
        language=language,
        name=name,
        description=description,
        fqn_prefix=fqn_prefix,
        class_configs=class_configs,
        class_config_relationships=class_rels,
        enum_configs=enum_configs,
        function_configs=global_function_configs,
        namespace_bundle=namespace_bundle,
        object_config_graph_annotations=compiled_annotations,
        object_config_graph_bindings=compiled_bindings,
        object_projection_graph_declarations=projection_declarations,
        object_config_graph_mirrors=compiled_mirrors,
        object_config_graph_id=object_config_graph_id,
        node_layouts_by_node_key=node_layouts_by_node_key,
    )

    # ---------------------------------------------------------------------
    # Derived artifacts (do not affect OCG hash)
    # - overlays: derived from annotations, linked to OCG for runtime consumption
    # - concrete projection graphs are runtime-derived only and must not be
    #   materialized against the pre-reification canonical graph
    # ---------------------------------------------------------------------
    overlays = build_object_config_graph_overlays_from_annotations(
        graph,
        namespace_bundle=namespace_bundle,
    )
    graph.object_config_graph_overlays.extend(overlays)
    hydrate_object_config_graph_overlays(ocg=graph, overlays=overlays)

    # ---------------------------------------------------------------------
    # Package-owned identity-plane materialization (v1 projection views syntax).
    #
    # Environment-artifacts also ensures OCGI/OPGI exist before runtime boots, but
    # only the package composer sees both OCG core output and projection declaration
    # metadata. Seeding here ensures observables are present in the persisted OCG payload.
    # ---------------------------------------------------------------------
    package_materialization_receipt = (
        materialize_object_config_graph_package_identity_plane(
            graph=graph,
            projection_declarations_by_name=projection_declarations_by_name,
        )
    )

    return ObjectConfigGraphBuildResult(
        graph=graph,
        cross_relationships_by_target_ocg=cross_map,
        cross_class_configs_by_target_ocg=cross_class_configs_by_target_ocg,
        package_materialization_receipt=package_materialization_receipt,
    )


def _normalize_code_language(language: object) -> CodeLanguage:
    if isinstance(language, CodeLanguage):
        return language
    value = getattr(language, "value", language)
    try:
        return CodeLanguage(str(value))
    except Exception as exc:
        raise ValueError(f"Unsupported code language: {language!r}") from exc


def build_fqn_resolver(
    namespace_by_code_id: dict[UUID, NamespacePath],
    class_configs: list[ClassConfig],
    enum_configs: list[EnumConfig],
    namespace_bundle: ObjectConfigGraphNamespaceBundle | None = None,
    imports_by_code_id: dict[UUID, dict[str, str]] | None = None,
    external_graphs: list[ObjectConfigGraph] | None = None,
) -> FqnResolver:
    """
    Build a FqnResolver from the given namespace by code ID, class configs, and enum configs.

    Canonical cross-OCG rule:
    - We may extend the symbol universe deterministically with EXTERNAL graphs (declared deps),
      but only as fully-qualified FQNs (no global fallback).

    Args:
        namespace_by_code_id: Namespace by code ID
        class_configs: List of ClassConfigs
        enum_configs: List of EnumConfigs
        external_graphs: List of external graphs
    Returns:
        A FqnResolver
    """

    # Build FQN resolver from FQN registry
    registry = FqnRegistry(namespace_by_code_id)
    for enum_config in enum_configs:
        code_section = enum_config.code_section_enum
        if code_section is not None:
            _ = registry.add_enum(enum_config, code_section.code_section.code_id)
            continue
        if namespace_bundle is not None:
            ns = namespace_bundle.namespace_by_enum_config_id.get(enum_config.id)
            if ns is not None:
                _ = registry.add_enum_with_namespace(enum_config, ns)
                continue
        raise ValueError(
            f"EnumConfig {enum_config.id} missing code provenance namespace (no code_section_enum and no namespace_bundle)"
        )

    for class_config in class_configs:
        code_section = class_config.code_section_class
        if code_section is not None:
            _ = registry.add_class(class_config, code_section.code_section.code_id)
            continue
        if namespace_bundle is not None:
            ns = namespace_bundle.namespace_by_class_config_id.get(class_config.id)
            if ns is not None:
                _ = registry.add_class_with_namespace(class_config, ns)
                continue
        raise ValueError(
            f"ClassConfig {class_config.id} missing code provenance namespace (no code_section_class and no namespace_bundle)"
        )

    resolver = registry.build(imports_by_code_id=imports_by_code_id)

    # Extend with external symbols (declared deps) keyed ONLY by full FQN.
    # This keeps resolution deterministic and avoids any "global name" behavior.
    if external_graphs:
        classes_by_fqn = dict(resolver.classes_by_fqn)
        enums_by_fqn = dict(resolver.enums_by_fqn)
        for g in external_graphs:
            idx = build_namespace_index(g)
            for node in g.object_config_graph_nodes:
                ns = idx.node_namespace_by_node_id.get(node.id)
                if ns is None:
                    ns = None
                if (
                    node.type == ObjectConfigGraphNodeType.class_
                    and node.class_config is not None
                ):
                    # Canonical: external graphs may arrive without full code provenance or schema
                    # membership, but compiled ClassConfig rows still persist canonical class_fqn.
                    explicit_fqn = (
                        getattr(node.class_config, "class_fqn", None) or ""
                    ).strip()
                    fqn = explicit_fqn or (
                        ns.fqn(node.class_config.name) if ns is not None else ""
                    )
                    if fqn and fqn not in classes_by_fqn:
                        classes_by_fqn[fqn] = node.class_config
                if (
                    node.type == ObjectConfigGraphNodeType.enum
                    and node.enum_config is not None
                ):
                    explicit_fqn = (
                        getattr(node.enum_config, "enum_fqn", None) or ""
                    ).strip()
                    fqn = explicit_fqn or (
                        ns.fqn(node.enum_config.name) if ns is not None else ""
                    )
                    if fqn and fqn not in enums_by_fqn:
                        enums_by_fqn[fqn] = node.enum_config

        resolver = FqnResolver(
            namespace_by_code_id=resolver.namespace_by_code_id,
            classes_by_fqn=classes_by_fqn,
            enums_by_fqn=enums_by_fqn,
            imports_by_code_id=imports_by_code_id,
        )
    return resolver

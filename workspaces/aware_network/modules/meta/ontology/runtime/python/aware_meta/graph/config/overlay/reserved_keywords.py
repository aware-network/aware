from __future__ import annotations

from collections.abc import Collection, Iterable
from uuid import UUID

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_overlay import ClassConfigOverlay
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_config_overlay import EnumConfigOverlay
from aware_meta_ontology.enum.enum_option_overlay import EnumOptionOverlay
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_config_overlay import (
    AttributeConfigOverlay,
)

# Meta Runtime
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.reserved_keyword_policy import ReservedKeywordEntityPolicy

from aware_meta.graph.config.stable_ids import (
    stable_ocg_overlay_entry_id,
    stable_ocg_overlay_id,
)
from aware_meta.graph.config.model_bootstrap import get_node_function_config


def _make_safe_identifier(*, base: str, reserved: Collection[str], used: Collection[str]) -> str:
    candidate = f"{base}_"
    if candidate not in reserved and candidate not in used:
        return candidate
    i = 1
    while True:
        candidate = f"{base}_{i}"
        if candidate not in reserved and candidate not in used:
            return candidate
        i += 1


def _get_enum_configs(ocg: ObjectConfigGraph) -> list[EnumConfig]:
    enums: list[EnumConfig] = []
    for node in ocg.object_config_graph_nodes:
        if node.enum_config is not None:
            enums.append(node.enum_config)
    return enums


def _get_class_configs(ocg: ObjectConfigGraph) -> list[ClassConfig]:
    classes: list[ClassConfig] = []
    for node in ocg.object_config_graph_nodes:
        if node.class_config is not None:
            classes.append(node.class_config)
    return classes


def _get_class_attribute_configs(
    ocg: ObjectConfigGraph,
) -> dict[UUID, list[AttributeConfig]]:
    """
    Return AttributeConfigs grouped by owning ClassConfig id.

    Only includes direct class attributes; function IO attributes are handled separately.
    """
    grouped: dict[UUID, list[AttributeConfig]] = {}
    for node in ocg.object_config_graph_nodes:
        if node.class_config is None:
            continue
        cls = node.class_config
        attrs: list[AttributeConfig] = []
        for edge in cls.class_config_attribute_configs:
            if edge.attribute_config is not None:
                attrs.append(edge.attribute_config)
        grouped[cls.id] = attrs
    return grouped


def _get_function_configs(ocg: ObjectConfigGraph) -> list[FunctionConfig]:
    """
    Return FunctionConfigs found in the graph.

    Includes:
    - standalone function nodes
    - class-bound function edges (deduped by id)
    """
    by_id: dict[UUID, FunctionConfig] = {}
    for node in ocg.object_config_graph_nodes:
        node_function_config = get_node_function_config(node)
        if node_function_config is not None:
            by_id.setdefault(node_function_config.id, node_function_config)
        if node.class_config is not None:
            for edge in node.class_config.class_config_function_configs:
                if edge.function_config is not None:
                    by_id.setdefault(edge.function_config.id, edge.function_config)
    return list(by_id.values())


def _get_function_attribute_groups(
    functions: Iterable[FunctionConfig],
) -> dict[tuple[UUID, FunctionAttributeType], list[AttributeConfig]]:
    grouped: dict[tuple[UUID, FunctionAttributeType], list[AttributeConfig]] = {}
    for fn in functions:
        for edge in fn.function_config_attribute_configs:
            if edge.attribute_config is None:
                continue
            key = (fn.id, edge.type)
            grouped.setdefault(key, []).append(edge.attribute_config)
    return grouped


def apply_reserved_keyword_overlays(
    ocg: ObjectConfigGraph,
    *,
    overlays_by_language: dict[CodeLanguage, ObjectConfigGraphOverlay],
) -> dict[CodeLanguage, ObjectConfigGraphOverlay]:
    """
    Second-pass overlay generation for reserved/invalid identifiers.

    Renderers must not rename directly. Instead, this pass:
    - inspects canonical names (per-language policy)
    - creates/merges AttributeConfigOverlay / EnumOptionOverlay entries when needed
    - preserves canonical wire names via `wire_name` when renaming
    """
    supported = MetaLanguagePluginRegistry.get_supported_languages()
    if not supported:
        return overlays_by_language

    enum_configs = _get_enum_configs(ocg)
    class_configs = _get_class_configs(ocg)
    class_attrs_by_class_id = _get_class_attribute_configs(ocg)
    function_configs = _get_function_configs(ocg)
    fn_attr_groups = _get_function_attribute_groups(function_configs)

    for language in supported:
        plugin = MetaLanguagePluginRegistry.get(language)
        policies = plugin.reserved_keyword_policies
        if not policies:
            continue

        overlay_id = stable_ocg_overlay_id(object_config_graph_id=ocg.id, language=language.value)
        overlay = overlays_by_language.get(language)
        if overlay is None:
            overlay = ObjectConfigGraphOverlay(id=overlay_id, language=language, object_config_graph_id=ocg.id)
            overlays_by_language[language] = overlay
        elif overlay.id != overlay_id:
            # Normalize legacy/random overlay IDs so compiler-owned commit rails do not drift.
            overlay.id = overlay_id
        overlay.object_config_graph_id = ocg.id

        # Normalize entry identities deterministically. This ensures that even when an
        # overlay is loaded from stale artifacts, the reserved-keyword pass yields stable
        # IDs for commit determinism.
        for co in overlay.class_config_overlays:
            co.object_config_graph_overlay_id = overlay_id
            co.id = stable_ocg_overlay_entry_id(overlay_id=overlay_id, kind="class", target_id=co.class_config_id)
        for fo in overlay.function_config_overlays:
            fo.object_config_graph_overlay_id = overlay_id
            fo.id = stable_ocg_overlay_entry_id(overlay_id=overlay_id, kind="function", target_id=fo.function_config_id)
        for ao in overlay.attribute_config_overlays:
            ao.object_config_graph_overlay_id = overlay_id
            ao.id = stable_ocg_overlay_entry_id(
                overlay_id=overlay_id,
                kind="attribute",
                target_id=ao.attribute_config_id,
            )
        for eo in overlay.enum_config_overlays:
            eo.object_config_graph_overlay_id = overlay_id
            eo.id = stable_ocg_overlay_entry_id(overlay_id=overlay_id, kind="enum", target_id=eo.enum_config_id)
        for eo in overlay.enum_option_overlays:
            eo.object_config_graph_overlay_id = overlay_id
            eo.id = stable_ocg_overlay_entry_id(overlay_id=overlay_id, kind="enum_option", target_id=eo.enum_option_id)

        # ------------------------------------------------------------------
        # CLASS
        # ------------------------------------------------------------------
        class_policy = policies.get(CodeSectionAnnotationOverlayEntity.class_)
        if class_policy is not None:
            existing_class_config_overlays: dict[UUID, ClassConfigOverlay] = {}
            for co in overlay.class_config_overlays:
                if co.class_config_id in existing_class_config_overlays:
                    raise ValueError(f"Duplicate ClassConfigOverlay for class_config_id={co.class_config_id}")
                existing_class_config_overlays[co.class_config_id] = co

            used_class_names: set[str] = set()
            for cls in sorted(class_configs, key=lambda c: c.name):
                canonical_name = class_policy.default_rendered_name(cls)
                co = existing_class_config_overlays.get(cls.id)
                explicit_name = co.rendered_name if co is not None else None
                effective_name = explicit_name or canonical_name

                if co is not None and co.rendered_name and co.rendered_name in class_policy.reserved_identifiers:
                    raise ValueError(
                        f"{language} class overlay rendered_name='{co.rendered_name}' is reserved (class={cls.name})"
                    )

                if effective_name in class_policy.reserved_identifiers:
                    if co is not None and co.rendered_name is not None:
                        raise ValueError(
                            f"{language} class overlay rendered_name='{co.rendered_name}' is reserved (class={cls.name})"
                        )
                    safe = _make_safe_identifier(
                        base=effective_name,
                        reserved=class_policy.reserved_identifiers,
                        used=used_class_names,
                    )
                    if co is None:
                        co = ClassConfigOverlay(
                            id=stable_ocg_overlay_entry_id(overlay_id=overlay_id, kind="class", target_id=cls.id),
                            object_config_graph_overlay_id=overlay_id,
                            class_config_id=cls.id,
                            rendered_name=safe,
                        )
                        overlay.class_config_overlays.append(co)
                        existing_class_config_overlays[cls.id] = co
                    else:
                        co.rendered_name = safe
                    effective_name = safe

                if effective_name in used_class_names:
                    raise ValueError(f"{language} class name collision: '{effective_name}'")
                used_class_names.add(effective_name)

        # ------------------------------------------------------------------
        # ENUM
        # ------------------------------------------------------------------
        enum_cfg_policy = policies.get(CodeSectionAnnotationOverlayEntity.enum)
        if enum_cfg_policy is not None:
            existing_enum_config_overlays: dict[UUID, EnumConfigOverlay] = {}
            for eo in overlay.enum_config_overlays:
                if eo.enum_config_id in existing_enum_config_overlays:
                    raise ValueError(f"Duplicate EnumConfigOverlay for enum_config_id={eo.enum_config_id}")
                existing_enum_config_overlays[eo.enum_config_id] = eo

            used_enum_names: set[str] = set()
            for enum_cfg in sorted(enum_configs, key=lambda e: e.name):
                canonical_name = enum_cfg_policy.default_rendered_name(enum_cfg)
                eo = existing_enum_config_overlays.get(enum_cfg.id)
                explicit_name = eo.rendered_name if eo is not None else None
                effective_name = explicit_name or canonical_name

                if eo is not None and eo.rendered_name and eo.rendered_name in enum_cfg_policy.reserved_identifiers:
                    raise ValueError(
                        f"{language} enum overlay rendered_name='{eo.rendered_name}' is reserved (enum={enum_cfg.name})"
                    )

                if effective_name in enum_cfg_policy.reserved_identifiers:
                    if eo is not None and eo.rendered_name is not None:
                        raise ValueError(
                            f"{language} enum overlay rendered_name='{eo.rendered_name}' is reserved (enum={enum_cfg.name})"
                        )
                    safe = _make_safe_identifier(
                        base=effective_name,
                        reserved=enum_cfg_policy.reserved_identifiers,
                        used=used_enum_names,
                    )
                    if eo is None:
                        eo = EnumConfigOverlay(
                            id=stable_ocg_overlay_entry_id(
                                overlay_id=overlay_id,
                                kind="enum",
                                target_id=enum_cfg.id,
                            ),
                            object_config_graph_overlay_id=overlay_id,
                            enum_config_id=enum_cfg.id,
                            rendered_name=safe,
                        )
                        overlay.enum_config_overlays.append(eo)
                        existing_enum_config_overlays[enum_cfg.id] = eo
                    else:
                        eo.rendered_name = safe
                    effective_name = safe

                if effective_name in used_enum_names:
                    raise ValueError(f"{language} enum name collision: '{effective_name}'")
                used_enum_names.add(effective_name)

        # ------------------------------------------------------------------
        # ENUM_OPTION
        # ------------------------------------------------------------------
        enum_policy = policies.get(CodeSectionAnnotationOverlayEntity.enum_option)
        if enum_policy is not None:
            existing_enum_option_overlays: dict[UUID, EnumOptionOverlay] = {}
            for eo in overlay.enum_option_overlays:
                if eo.enum_option_id in existing_enum_option_overlays:
                    raise ValueError(f"Duplicate EnumOptionOverlay for enum_option_id={eo.enum_option_id}")
                existing_enum_option_overlays[eo.enum_option_id] = eo

            for enum_cfg in sorted(enum_configs, key=lambda e: e.name):
                used_enum_option_names: set[str] = set()
                opts = sorted(enum_cfg.enum_options, key=lambda opt: (opt.position, opt.value))
                for opt in opts:
                    canonical_name = enum_policy.default_rendered_name(opt)
                    canonical_wire = (
                        enum_policy.default_wire_name(opt, canonical_name) if enum_policy.default_wire_name else None
                    )
                    eo = existing_enum_option_overlays.get(opt.id)
                    explicit_name = eo.rendered_name if eo is not None else None
                    effective_name = explicit_name or canonical_name

                    # If the name is explicitly overridden, default wire_name should preserve canonical serialization.
                    if (
                        eo is not None
                        and eo.rendered_name
                        and eo.rendered_name != canonical_name
                        and eo.wire_name is None
                        and canonical_wire is not None
                    ):
                        eo.wire_name = canonical_wire

                    # Explicit overlays must never resolve to a reserved identifier.
                    if eo is not None and eo.rendered_name and eo.rendered_name in enum_policy.reserved_identifiers:
                        raise ValueError(
                            f"{language} enum_option overlay rendered_name='{eo.rendered_name}' is reserved "
                            f"(enum={enum_cfg.name} option={opt.value})"
                        )

                    if effective_name in enum_policy.reserved_identifiers:
                        if eo is not None and eo.rendered_name is not None:
                            raise ValueError(
                                f"{language} enum_option overlay rendered_name='{eo.rendered_name}' is reserved "
                                f"(enum={enum_cfg.name} option={opt.value})"
                            )
                        safe = _make_safe_identifier(
                            base=effective_name,
                            reserved=enum_policy.reserved_identifiers,
                            used=used_enum_option_names,
                        )
                        if eo is None:
                            eo = EnumOptionOverlay(
                                id=stable_ocg_overlay_entry_id(
                                    overlay_id=overlay_id,
                                    kind="enum_option",
                                    target_id=opt.id,
                                ),
                                object_config_graph_overlay_id=overlay_id,
                                enum_option_id=opt.id,
                                rendered_name=safe,
                                wire_name=canonical_wire,
                            )
                            overlay.enum_option_overlays.append(eo)
                            existing_enum_option_overlays[opt.id] = eo
                        else:
                            eo.rendered_name = safe
                            if eo.wire_name is None and canonical_wire is not None:
                                eo.wire_name = canonical_wire
                        effective_name = safe

                    if effective_name in used_enum_option_names:
                        raise ValueError(
                            f"{language} enum_option name collision for enum={enum_cfg.name}: '{effective_name}'"
                        )
                    used_enum_option_names.add(effective_name)

        # ------------------------------------------------------------------
        # ATTRIBUTE
        # ------------------------------------------------------------------
        attr_policy = policies.get(CodeSectionAnnotationOverlayEntity.attribute)
        if attr_policy is not None:
            existing_attribute_config_overlays: dict[UUID, AttributeConfigOverlay] = {}
            for ao in overlay.attribute_config_overlays:
                if ao.attribute_config_id in existing_attribute_config_overlays:
                    raise ValueError(
                        f"Duplicate AttributeConfigOverlay for attribute_config_id={ao.attribute_config_id}"
                    )
                existing_attribute_config_overlays[ao.attribute_config_id] = ao

            # Class attributes (per class)
            for class_id, attrs in sorted(class_attrs_by_class_id.items(), key=lambda item: str(item[0])):
                _process_attr_group(
                    attrs,
                    attr_policy=attr_policy,
                    existing_attribute_config_overlays=existing_attribute_config_overlays,
                    overlay=overlay,
                    language=language,
                    scope_label=f"class_id={class_id}",
                )

            # Function IO attributes (per function + io kind)
            for (fn_id, kind), attrs in sorted(
                fn_attr_groups.items(),
                key=lambda item: (str(item[0][0]), item[0][1].value),
            ):
                _process_attr_group(
                    attrs,
                    attr_policy=attr_policy,
                    existing_attribute_config_overlays=existing_attribute_config_overlays,
                    overlay=overlay,
                    language=language,
                    scope_label=f"function_id={fn_id} io={kind.value}",
                )

    # Prune overlays that are completely empty (only created as placeholders)
    pruned: dict[CodeLanguage, ObjectConfigGraphOverlay] = {}
    for lang, ov in overlays_by_language.items():
        if (
            ov.class_config_overlays
            or ov.function_config_overlays
            or ov.attribute_config_overlays
            or ov.enum_config_overlays
            or ov.enum_option_overlays
        ):
            pruned[lang] = ov
    return pruned


def _process_attr_group(
    attrs: list[AttributeConfig],
    *,
    attr_policy: ReservedKeywordEntityPolicy,
    existing_attribute_config_overlays: dict[UUID, AttributeConfigOverlay],
    overlay: ObjectConfigGraphOverlay,
    language: CodeLanguage,
    scope_label: str,
) -> None:
    used_names: set[str] = set()
    for attr in sorted(attrs, key=lambda a: a.name):
        canonical_name = attr_policy.default_rendered_name(attr)
        canonical_wire = attr_policy.default_wire_name(attr, canonical_name) if attr_policy.default_wire_name else None
        ao = existing_attribute_config_overlays.get(attr.id)
        explicit_name = ao.rendered_name if ao is not None else None
        effective_name = explicit_name or canonical_name

        # If the name is explicitly overridden, default wire_name should preserve canonical serialization.
        if (
            ao is not None
            and ao.rendered_name
            and ao.rendered_name != canonical_name
            and ao.wire_name is None
            and canonical_wire is not None
        ):
            ao.wire_name = canonical_wire

        # Explicit overlays must never resolve to a reserved identifier.
        if ao is not None and ao.rendered_name and ao.rendered_name in attr_policy.reserved_identifiers:
            raise ValueError(
                f"{language} attribute overlay rendered_name='{ao.rendered_name}' is reserved ({scope_label})"
            )

        if effective_name in attr_policy.reserved_identifiers:
            if ao is not None and ao.rendered_name is not None:
                raise ValueError(
                    f"{language} attribute overlay rendered_name='{ao.rendered_name}' is reserved " f"({scope_label})"
                )
            safe = _make_safe_identifier(
                base=effective_name,
                reserved=attr_policy.reserved_identifiers,
                used=used_names,
            )
            if ao is None:
                ao = AttributeConfigOverlay(
                    id=stable_ocg_overlay_entry_id(overlay_id=overlay.id, kind="attribute", target_id=attr.id),
                    object_config_graph_overlay_id=overlay.id,
                    attribute_config_id=attr.id,
                    rendered_name=safe,
                    wire_name=canonical_wire,
                )
                overlay.attribute_config_overlays.append(ao)
                existing_attribute_config_overlays[attr.id] = ao
            else:
                ao.rendered_name = safe
                if ao.wire_name is None and canonical_wire is not None:
                    ao.wire_name = canonical_wire
            effective_name = safe

        if effective_name in used_names:
            raise ValueError(f"{language} attribute name collision: '{effective_name}' ({scope_label})")
        used_names.add(effective_name)

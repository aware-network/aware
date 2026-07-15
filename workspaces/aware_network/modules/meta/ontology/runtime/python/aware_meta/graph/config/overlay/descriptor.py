"""Describe an ObjectConfigGraphOverlay in natural language."""

from __future__ import annotations

import json
from typing import Any

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)


def describe_object_config_graph_overlay(overlay: ObjectConfigGraphOverlay) -> str:
    """Render a natural language description of an ObjectConfigGraphOverlay."""

    language_label = overlay.language.value
    header = f'ObjectConfigGraphOverlay language="{language_label}"'
    if overlay.object_config_graph_id is not None:
        header += f" targeting ObjectConfigGraph {str(overlay.object_config_graph_id)}"

    class_by_id = {str(cls.id): cls for cls in overlay.classes}
    attribute_by_id = {str(attr.id): attr for attr in overlay.attributes}
    enum_by_id = {str(enum.id): enum for enum in overlay.enums}
    enum_option_by_id = {str(enum_opt.id): enum_opt for enum_opt in overlay.enum_options}
    function_by_id = {str(fn.id): fn for fn in overlay.functions}

    lines: list[str] = [header, "Overrides:"]
    sections = 0

    class_overlays = sorted(
        (edge for edge in overlay.class_config_overlays if edge.class_config_id),
        key=lambda edge: (
            _resolve_class_name(class_by_id.get(str(edge.class_config_id)), str(edge.class_config_id)),
            str(edge.class_config_id),
        ),
    )
    if class_overlays:
        sections += 1
        lines.append(f"- Class overrides ({len(class_overlays)}):")
        for edge in class_overlays:
            class_id = str(edge.class_config_id)
            class_name = _resolve_class_name(class_by_id.get(class_id), class_id)
            details = _collect_overlay_fields(
                rendered_name=edge.rendered_name,
                wire_name=None,
                lang_flags=edge.lang_flags,
            )
            lines.append(f"  - {class_name} (class_config_id={class_id}){details}")

    enum_overlays = sorted(
        (edge for edge in overlay.enum_config_overlays if edge.enum_config_id),
        key=lambda edge: (
            _resolve_enum_name(enum_by_id.get(str(edge.enum_config_id)), str(edge.enum_config_id)),
            str(edge.enum_config_id),
        ),
    )
    if enum_overlays:
        sections += 1
        lines.append(f"- Enum overrides ({len(enum_overlays)}):")
        for edge in enum_overlays:
            enum_id = str(edge.enum_config_id)
            enum_name = _resolve_enum_name(enum_by_id.get(enum_id), enum_id)
            details = _collect_overlay_fields(rendered_name=edge.rendered_name)
            lines.append(f"  - {enum_name} (enum_config_id={enum_id}){details}")

    enum_option_groups: dict[str, list[Any]] = {}
    for edge in overlay.enum_option_overlays:
        if not edge.enum_option_id:
            continue
        option_id = str(edge.enum_option_id)
        option = enum_option_by_id.get(option_id)
        parent_enum_id = None
        if option is not None:
            parent_enum_id = option.enum_config_id
        parent_key = str(parent_enum_id) if parent_enum_id else "unbound"
        enum_option_groups.setdefault(parent_key, []).append(edge)

    if enum_option_groups:
        sections += 1
        lines.append("- Enum option overrides:")
        for parent_key in sorted(enum_option_groups.keys()):
            parent_enum = enum_by_id.get(parent_key)
            parent_label = _resolve_enum_name(parent_enum, parent_key)
            lines.append(f"  - Enum {parent_label} (enum_config_id={parent_key}):")
            grouped_edges = sorted(
                enum_option_groups[parent_key],
                key=lambda edge: (
                    _resolve_enum_option_name(
                        enum_option_by_id.get(str(edge.enum_option_id)),
                        str(edge.enum_option_id),
                    ),
                    str(edge.enum_option_id),
                ),
            )
            for edge in grouped_edges:
                option_id = str(edge.enum_option_id)
                option_name = _resolve_enum_option_name(enum_option_by_id.get(option_id), option_id)
                details = _collect_overlay_fields(
                    rendered_name=edge.rendered_name,
                    wire_name=edge.wire_name,
                )
                lines.append(f"    - {option_name} (enum_option_id={option_id}){details}")

    attribute_groups: dict[str, list[Any]] = {}
    for edge in overlay.attribute_config_overlays:
        if not edge.attribute_config_id:
            continue
        attr_id = str(edge.attribute_config_id)
        attribute = attribute_by_id.get(attr_id)
        class_config_id = _resolve_attribute_class_id(attribute)
        class_key = str(class_config_id) if class_config_id is not None else "unbound"
        attribute_groups.setdefault(class_key, []).append(edge)

    if attribute_groups:
        sections += 1
        lines.append("- Attribute overrides:")
        for class_key in sorted(attribute_groups.keys()):
            class_config = class_by_id.get(class_key)
            class_label = class_config.name if class_config else class_key
            lines.append(f"  - Class {class_label} (class_config_id={class_key}):")
            grouped_edges = sorted(
                attribute_groups[class_key],
                key=lambda edge: (
                    _resolve_attribute_name(
                        attribute_by_id.get(str(edge.attribute_config_id)),
                        str(edge.attribute_config_id),
                    ),
                    str(edge.attribute_config_id),
                ),
            )
            for edge in grouped_edges:
                attr_id = str(edge.attribute_config_id)
                attr_name = _resolve_attribute_name(attribute_by_id.get(attr_id), attr_id)
                details = _collect_overlay_fields(
                    rendered_name=edge.rendered_name,
                    wire_name=edge.wire_name,
                )
                lines.append(f"    - {attr_name} (attribute_config_id={attr_id}){details}")

    function_overlays = sorted(
        (edge for edge in overlay.function_config_overlays if edge.function_config_id),
        key=lambda edge: (
            _resolve_function_name(
                function_by_id.get(str(edge.function_config_id)),
                str(edge.function_config_id),
            ),
            str(edge.function_config_id),
        ),
    )
    if function_overlays:
        sections += 1
        lines.append(f"- Function overrides ({len(function_overlays)}):")
        for edge in function_overlays:
            fn_id = str(edge.function_config_id)
            fn_name = _resolve_function_name(function_by_id.get(fn_id), fn_id)
            details = _collect_overlay_fields(
                rendered_name=edge.rendered_name,
                lang_flags=edge.lang_flags,
            )
            lines.append(f"  - {fn_name} (function_config_id={fn_id}){details}")

    if sections == 0:
        lines[-1] = "Overrides: none"

    return "\n".join(lines)


def _collect_overlay_fields(
    *,
    rendered_name: str | None,
    wire_name: str | None = None,
    lang_flags: Any = None,
) -> str:
    updates: list[str] = []

    if rendered_name:
        updates.append(f'rendered_name="{rendered_name}"')
    if wire_name:
        updates.append(f'wire_name="{wire_name}"')
    if lang_flags:
        updates.append(_format_lang_flags(lang_flags))

    if not updates:
        return " (no changes)"
    formatted = ", ".join(updates)
    return f" -> {formatted}"


def _format_lang_flags(flags: Any) -> str:
    if flags is None:
        return "lang_flags=<unchanged>"
    if isinstance(flags, str):
        return f'lang_flags="{flags}"'
    try:
        serialized = json.dumps(flags, sort_keys=True)
    except (TypeError, ValueError):
        serialized = str(flags)
    return f"lang_flags={serialized}"


def _resolve_class_name(class_config: ClassConfig | None, fallback: str) -> str:
    if class_config is None:
        return fallback
    return class_config.name


def _resolve_enum_name(enum_config: EnumConfig | None, fallback: str) -> str:
    if enum_config is None:
        return fallback
    return enum_config.name


def _resolve_enum_option_name(enum_option: EnumOption | None, fallback: str) -> str:
    if enum_option is None:
        return fallback
    label = enum_option.label
    if label is None:
        return fallback
    return label


def _resolve_attribute_name(attribute_config: AttributeConfig | None, fallback: str) -> str:
    if attribute_config is None:
        return fallback
    return attribute_config.name


def _resolve_attribute_class_id(attribute_config: AttributeConfig | None) -> str | None:
    # !! TODO: Improve - traverse type descriptor tree to find the class config id
    if attribute_config is None:
        return None
    type_desc = attribute_config.type_descriptor
    if type_desc.class_config_id is None:
        return None
    return str(type_desc.class_config_id)


def _resolve_function_name(function_config: FunctionConfig | None, fallback: str) -> str:
    if function_config is None:
        return fallback
    return function_config.name

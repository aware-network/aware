from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import cast
from uuid import UUID

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance


def decode_oig_primitive_value(
    *,
    type_descriptor: AttributeTypeDescriptor,
    raw: object,
) -> object:
    primitive_cfg = type_descriptor.primitive_config
    primitive_type = primitive_cfg.primitive_type if primitive_cfg is not None else None
    base_type = primitive_type.base_type if primitive_type is not None else None

    if base_type is None:
        raise ValueError(
            "Primitive AttributeTypeDescriptor missing primitive_config/base_type: "
            f"{type_descriptor}"
        )

    if base_type == CodePrimitiveBaseType.json:
        json_kind = _json_kind(
            primitive_type.constraints if primitive_type is not None else None
        )
        if json_kind == "object" or (json_kind is None and isinstance(raw, Mapping)):
            return raw
        return _unwrap_json_envelope(raw)

    if base_type == CodePrimitiveBaseType.dict:
        return raw

    raw = _unwrap_json_envelope(raw)
    if raw is None:
        return None

    if base_type == CodePrimitiveBaseType.uuid:
        if isinstance(raw, UUID):
            return raw
        if isinstance(raw, str):
            return UUID(raw)
        raise TypeError(f"Expected UUID primitive, got {type(raw).__name__}")

    if base_type == CodePrimitiveBaseType.integer:
        if isinstance(raw, bool):
            raise TypeError("Expected integer primitive, got bool")
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str):
            return int(raw)
        raise TypeError(f"Expected integer primitive, got {type(raw).__name__}")

    if base_type == CodePrimitiveBaseType.float:
        if isinstance(raw, bool):
            raise TypeError("Expected float primitive, got bool")
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            return float(raw)
        raise TypeError(f"Expected float primitive, got {type(raw).__name__}")

    if base_type == CodePrimitiveBaseType.boolean:
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, int) and raw in (0, 1):
            return bool(raw)
        if isinstance(raw, str):
            norm = raw.strip().casefold()
            if norm in {"true", "1", "yes", "y"}:
                return True
            if norm in {"false", "0", "no", "n"}:
                return False
        raise TypeError(f"Expected boolean primitive, got {type(raw).__name__}")

    if base_type == CodePrimitiveBaseType.datetime:
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, str):
            iso = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
            return datetime.fromisoformat(iso)
        raise TypeError(f"Expected datetime primitive, got {type(raw).__name__}")

    if base_type == CodePrimitiveBaseType.null:
        return None

    return raw


def decode_oig_attribute_value(
    value: AttributeValue | None,
    *,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
) -> object:
    if value is None:
        return None

    type_descriptor = value.type_descriptor
    kind = type_descriptor.kind

    if kind == AttributeTypeDescriptorKind.primitive:
        return decode_oig_primitive_value(
            type_descriptor=type_descriptor,
            raw=value.primitive_value,
        )

    if kind == AttributeTypeDescriptorKind.enum:
        if value.enum_option is not None:
            return value.enum_option.value
        enum_option_id = value.enum_option_id
        if enum_option_id is None:
            return None
        if type_descriptor.enum_config is None:
            raise ValueError(
                f"AttributeTypeDescriptor missing enum_config: {type_descriptor.id}"
            )
        for option in tuple(type_descriptor.enum_config.enum_options):
            if option.id == enum_option_id:
                return option.value
        return enum_option_id

    if kind == AttributeTypeDescriptorKind.class_:
        class_config = _resolve_descriptor_class_config(
            type_descriptor=type_descriptor,
            class_configs_by_id=class_configs_by_id,
        )
        if class_config is None:
            raise ValueError(
                "CLASS AttributeTypeDescriptor missing class_config for "
                "value_mode resolution: "
                f"type_descriptor_id={type_descriptor.id} "
                f"class_config_id={type_descriptor.class_config_id}"
            )

        if class_config.value_mode == ClassValueMode.inline_value:
            if value.class_instance_id is not None or value.class_instance is not None:
                raise ValueError(
                    "INLINE_VALUE class payload must not set class_instance_id: "
                    f"type_descriptor_id={type_descriptor.id} "
                    f"class_config_id={type_descriptor.class_config_id}"
                )
            if value.primitive_value is not None:
                raise ValueError(
                    "INLINE_VALUE class payload must not set primitive_value: "
                    f"type_descriptor_id={type_descriptor.id} "
                    f"class_config_id={type_descriptor.class_config_id}"
                )
            if value.inline_value_instance is None:
                return None
            return _decode_inline_value_instance(
                value.inline_value_instance,
                class_configs_by_id=class_configs_by_id,
            )

        if class_config.value_mode != ClassValueMode.graph_ref:
            raise ValueError(
                "Unsupported ClassValueMode for CLASS decoding: "
                f"value_mode={class_config.value_mode} class_config_id={class_config.id}"
            )

        if value.primitive_value is not None:
            raise ValueError(
                "GRAPH_REF class payload must not set primitive_value: "
                f"type_descriptor_id={type_descriptor.id} "
                f"class_config_id={type_descriptor.class_config_id}"
            )
        if value.class_instance_id is not None:
            return value.class_instance_id
        if value.class_instance is not None:
            return value.class_instance.id
        return None

    child_links = tuple(value.child_links or ())

    if kind == AttributeTypeDescriptorKind.collection:
        elements = [
            link
            for link in child_links
            if link.role == AttributeTypeDescriptorRole.element
        ]
        collection_kind = type_descriptor.collection_kind

        if collection_kind == AttributeCollectionType.list:
            elements.sort(key=_ordered_value_link_key)
            return [
                decode_oig_attribute_value(
                    link.child,
                    class_configs_by_id=class_configs_by_id,
                )
                for link in elements
            ]

        if collection_kind == AttributeCollectionType.set:
            elements.sort(
                key=lambda link: (
                    link.identity_key or "",
                    link.position if link.position is not None else 10_000,
                    str(link.child.id),
                )
            )
            return [
                decode_oig_attribute_value(
                    link.child,
                    class_configs_by_id=class_configs_by_id,
                )
                for link in elements
            ]

        if collection_kind == AttributeCollectionType.single:
            if not elements:
                return None
            if len(elements) != 1:
                raise ValueError(
                    "Invalid SINGLE collection: expected 1 element, "
                    f"got {len(elements)}"
                )
            return decode_oig_attribute_value(
                elements[0].child,
                class_configs_by_id=class_configs_by_id,
            )

        raise ValueError(f"Unsupported collection_kind={collection_kind}")

    if kind == AttributeTypeDescriptorKind.mapping:
        grouped: dict[str, dict[AttributeTypeDescriptorRole, AttributeValue]] = {}
        for link in child_links:
            if link.role not in {
                AttributeTypeDescriptorRole.key,
                AttributeTypeDescriptorRole.value_,
            }:
                continue
            group_key = link.identity_key or (
                str(link.position)
                if link.position is not None
                else (str(link.child.id) if link.child.id else "")
            )
            grouped.setdefault(group_key, {})[link.role] = link.child

        out: dict[object, object] = {}
        for group_key in sorted(grouped.keys()):
            entry = grouped[group_key]
            if (
                AttributeTypeDescriptorRole.key not in entry
                or AttributeTypeDescriptorRole.value_ not in entry
            ):
                raise ValueError(
                    "Invalid mapping entry: missing KEY/VALUE for "
                    f"identity_key={group_key}"
                )
            out[
                decode_oig_attribute_value(
                    entry[AttributeTypeDescriptorRole.key],
                    class_configs_by_id=class_configs_by_id,
                )
            ] = decode_oig_attribute_value(
                entry[AttributeTypeDescriptorRole.value_],
                class_configs_by_id=class_configs_by_id,
            )
        return out

    if kind == AttributeTypeDescriptorKind.tuple:
        members = [
            link
            for link in child_links
            if link.role == AttributeTypeDescriptorRole.member
        ]
        members.sort(key=_ordered_value_link_key)
        return tuple(
            decode_oig_attribute_value(
                link.child,
                class_configs_by_id=class_configs_by_id,
            )
            for link in members
        )

    if kind == AttributeTypeDescriptorKind.union:
        members = [
            link
            for link in child_links
            if link.role == AttributeTypeDescriptorRole.member
        ]
        if not members:
            return None
        if len(members) != 1:
            raise ValueError(
                f"Invalid UNION value: expected 1 selected member, got {len(members)}"
            )
        return decode_oig_attribute_value(
            members[0].child,
            class_configs_by_id=class_configs_by_id,
        )

    raise ValueError(f"Unsupported AttributeTypeDescriptorKind={kind}")


def _decode_inline_value_instance(
    inline_value_instance: InlineValueInstance,
    *,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> dict[str, object]:
    values: dict[str, object] = {}
    direct_attributes = tuple(inline_value_instance.attributes or ())
    if direct_attributes:
        attributes = direct_attributes
    else:
        attributes = tuple(
            edge.attribute
            for edge in tuple(
                inline_value_instance.inline_value_instance_attributes or ()
            )
            if edge.attribute is not None
        )
    for attribute in attributes:
        attribute_config = attribute.attribute_config
        if attribute_config is None or not attribute_config.name:
            continue
        values[attribute_config.name] = decode_oig_attribute_value(
            attribute.value_root,
            class_configs_by_id=class_configs_by_id,
        )
    return values


def _resolve_descriptor_class_config(
    *,
    type_descriptor: AttributeTypeDescriptor,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> ClassConfig | None:
    if type_descriptor.class_config is not None:
        return type_descriptor.class_config
    if class_configs_by_id is None or type_descriptor.class_config_id is None:
        return None
    return class_configs_by_id.get(type_descriptor.class_config_id)


def _unwrap_json_envelope(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, dict):
        value_dict = cast(dict[object, object], value)
        if set(value_dict.keys()) == {"value"}:
            return value_dict.get("value")
        return cast(object, value_dict)
    return value


def _json_kind(constraints: object) -> str | None:
    if isinstance(constraints, Mapping):
        value = constraints.get("json_kind")
        if isinstance(value, str):
            normalized = value.strip().casefold()
            return normalized or None
    return None


def _ordered_value_link_key(link: object) -> tuple[int, str]:
    position = getattr(link, "position", None)
    child = getattr(link, "child", None)
    child_id = getattr(child, "id", "")
    return (position if isinstance(position, int) else 10_000, str(child_id))


__all__ = [
    "decode_oig_attribute_value",
    "decode_oig_primitive_value",
]

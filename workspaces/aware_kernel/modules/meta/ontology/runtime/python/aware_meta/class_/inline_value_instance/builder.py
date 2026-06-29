from __future__ import annotations

import json
from uuid import UUID

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta_ontology.class_.inline_value_instance_attribute import (
    InlineValueInstanceAttribute,
)
from aware_meta_ontology.stable_ids import (
    stable_inline_value_instance_attribute_id,
    stable_inline_value_instance_id,
)

from aware_meta.attribute.instance.builder import build_attribute
from aware_meta.attribute.instance.value.builder import (
    ClassInstanceResolver,
    EnumOptionResolver,
    UnionSelection,
)
from aware_meta.class_.inline_value_instance.resolution import (
    resolve_class_config_attribute_configs,
)

from aware_orm.models.introspection import MappingModelSource, ModelIntrospection
from aware_orm.session.autobind import disable_autobind


class InlineValueInstanceBuildError(ValueError):
    pass


def build_inline_value_instance(
    *,
    owner_key: UUID,
    class_config: ClassConfig,
    class_configs_by_id: dict[UUID, ClassConfig] | None = None,
    source: ModelIntrospection,
    enum_option_resolver: EnumOptionResolver | None = None,
    class_instance_resolver: ClassInstanceResolver | None = None,
    union_selections: dict[str, UnionSelection] | None = None,
) -> InlineValueInstance:
    """Build a canonical InlineValueInstance from a typed value payload source."""
    if not isinstance(source, ModelIntrospection):
        raise InlineValueInstanceBuildError(
            f"Invalid source type {type(source)!r}: expected a ModelIntrospection implementation."
        )
    if class_config.value_mode != ClassValueMode.inline_value:
        raise InlineValueInstanceBuildError(
            "build_inline_value_instance requires an inline_value ClassConfig: "
            f"class_config_id={class_config.id} value_mode={class_config.value_mode}"
        )

    with disable_autobind():
        inline_value_instance = InlineValueInstance(
            id=stable_inline_value_instance_id(
                class_config_id=class_config.id,
                owner_key=owner_key,
            ),
            class_config_id=class_config.id,
            class_config=class_config,
            owner_key=owner_key,
            inline_value_instance_attributes=[],
        )

    attr_links = resolve_class_config_attribute_configs(
        class_config=class_config,
        class_configs_by_id=class_configs_by_id,
    )
    for link in attr_links:
        attr_cfg = link.attribute_config
        if attr_cfg is None or attr_cfg.is_virtual:
            continue

        found, raw_value = source.try_attribute_value(attr_cfg)
        if not found:
            if attr_cfg.default_value is not None:
                raw_value = _parse_default_value(attr_cfg)
            elif attr_cfg.is_required:
                raise InlineValueInstanceBuildError(f"Missing required attribute '{attr_cfg.name}'")
            else:
                continue

        union = union_selections.get(attr_cfg.name) if union_selections else None
        attribute = build_attribute(
            owner_key=owner_key,
            attribute_config=attr_cfg,
            value=raw_value,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            union=union,
        )
        _ = link_attribute(inline_value_instance, attribute)

    return inline_value_instance


def build_inline_value_instance_from_mapping(
    *,
    owner_key: UUID,
    class_config: ClassConfig,
    values: dict[str, object],
    class_configs_by_id: dict[UUID, ClassConfig] | None = None,
    enum_option_resolver: EnumOptionResolver | None = None,
    class_instance_resolver: ClassInstanceResolver | None = None,
    union_selections: dict[str, UnionSelection] | None = None,
) -> InlineValueInstance:
    return build_inline_value_instance(
        owner_key=owner_key,
        class_config=class_config,
        class_configs_by_id=class_configs_by_id,
        source=MappingModelSource(
            id=owner_key,
            values=values,
            class_config_id=class_config.id,
        ),
        enum_option_resolver=enum_option_resolver,
        class_instance_resolver=class_instance_resolver,
        union_selections=union_selections,
    )


def link_attribute(
    inline_value_instance: InlineValueInstance,
    attribute: Attribute,
) -> InlineValueInstanceAttribute:
    inline_value_instance_id = inline_value_instance.id
    attribute_id = getattr(attribute, "id", None)
    if inline_value_instance_id is None:
        raise InlineValueInstanceBuildError("InlineValueInstance id is required to link an Attribute")
    if attribute_id is None:
        raise InlineValueInstanceBuildError("Attribute id is required to link it under an InlineValueInstance")

    edge_id = stable_inline_value_instance_attribute_id(
        inline_value_instance_id=inline_value_instance_id,
        attribute_id=attribute_id,
    )
    for existing in inline_value_instance.inline_value_instance_attributes:
        if existing.id != edge_id:
            continue
        if existing.attribute is None:
            existing.attribute = attribute
            existing.attribute_id = attribute_id
        return existing

    with disable_autobind():
        edge = InlineValueInstanceAttribute(
            id=edge_id,
            inline_value_instance_id=inline_value_instance_id,
            attribute=attribute,
            attribute_id=attribute_id,
        )
    inline_value_instance.inline_value_instance_attributes.append(edge)
    return edge


def _parse_default_value(attribute_config: AttributeConfig) -> object:
    default_value = attribute_config.default_value
    if default_value is None:
        raise InlineValueInstanceBuildError(
            f"Missing default_value for attribute '{attribute_config.name}'"
        )
    try:
        return json.loads(default_value)
    except Exception as exc:
        raise InlineValueInstanceBuildError(
            f"Invalid default_value JSON for attribute '{attribute_config.name}': {default_value}"
        ) from exc


__all__ = [
    "InlineValueInstanceBuildError",
    "build_inline_value_instance",
    "build_inline_value_instance_from_mapping",
    "link_attribute",
]

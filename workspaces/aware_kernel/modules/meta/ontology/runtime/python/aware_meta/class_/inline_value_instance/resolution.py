from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta_ontology.class_.inline_value_instance_attribute import (
    InlineValueInstanceAttribute,
)


@dataclass(frozen=True, slots=True)
class ResolvedInlineValueInstanceAttribute:
    edge: InlineValueInstanceAttribute
    attribute: Attribute
    attribute_config: AttributeConfig
    class_config_attribute_config: ClassConfigAttributeConfig


def resolve_inline_value_instance_attributes(
    *,
    inline_value_instance: InlineValueInstance,
    class_config: ClassConfig,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
) -> tuple[ResolvedInlineValueInstanceAttribute, ...]:
    if class_config.id != inline_value_instance.class_config_id:
        raise ValueError(
            "InlineValueInstance ClassConfig mismatch: "
            f"inline_value_instance.class_config_id={inline_value_instance.class_config_id} "
            f"class_config.id={class_config.id}"
        )

    links_by_attribute_config_id: dict[object, ClassConfigAttributeConfig] = {}
    for link in resolve_class_config_attribute_configs(
        class_config=class_config,
        class_configs_by_id=class_configs_by_id,
    ):
        attribute_config = link.attribute_config
        if attribute_config is None or attribute_config.id is None:
            continue
        links_by_attribute_config_id[attribute_config.id] = link

    resolved: list[ResolvedInlineValueInstanceAttribute] = []
    for edge in inline_value_instance.inline_value_instance_attributes:
        attribute = edge.attribute
        if attribute is None or attribute.attribute_config_id is None:
            raise ValueError(
                "InlineValueInstanceAttribute is missing Attribute/attribute_config_id: "
                f"edge_id={edge.id}"
            )
        link = links_by_attribute_config_id.get(attribute.attribute_config_id)
        if link is None or link.attribute_config is None:
            raise ValueError(
                "InlineValueInstance AttributeConfig must resolve via ClassConfig portal: "
                f"class_config_id={class_config.id} attribute_config_id={attribute.attribute_config_id}"
            )
        resolved.append(
            ResolvedInlineValueInstanceAttribute(
                edge=edge,
                attribute=attribute,
                attribute_config=link.attribute_config,
                class_config_attribute_config=link,
            )
        )

    resolved.sort(
        key=lambda item: (
            item.class_config_attribute_config.position,
            str(item.attribute_config.name or ""),
            str(item.attribute.id),
        )
    )
    return tuple(resolved)


def resolve_class_config_attribute_configs(
    *,
    class_config: ClassConfig,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
) -> tuple[ClassConfigAttributeConfig, ...]:
    """Resolve concrete attributes for a class, including inherited parent attributes.

    Child attributes override inherited attributes with the same wire/name key. This
    preserves discriminator tags such as a child's literal `operation` field while
    still including base envelope fields such as `request_id`.
    """

    selected_by_name: dict[str, ClassConfigAttributeConfig] = {}
    for resolved_class in _class_config_chain_root_first(
        class_config=class_config,
        class_configs_by_id=class_configs_by_id,
    ):
        for link in sorted(
            resolved_class.class_config_attribute_configs,
            key=lambda item: (
                item.position,
                _attribute_config_name(item),
                str(getattr(item.attribute_config, "id", "") or ""),
            ),
        ):
            attribute_config = link.attribute_config
            if attribute_config is None or attribute_config.id is None:
                continue
            attribute_name = _attribute_config_name(link)
            if not attribute_name:
                attribute_name = f"attribute_config_id:{attribute_config.id}"
            selected_by_name[attribute_name] = link
    return tuple(selected_by_name.values())


def _class_config_chain_root_first(
    *,
    class_config: ClassConfig,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> tuple[ClassConfig, ...]:
    chain: list[ClassConfig] = []
    current: ClassConfig | None = class_config
    seen: set[UUID] = set()
    while current is not None:
        current_id = current.id
        if current_id is not None:
            if current_id in seen:
                raise ValueError(
                    "ClassConfig parent_class chain contains a cycle: "
                    f"class_config_id={class_config.id} repeated_id={current_id}"
                )
            seen.add(current_id)
        chain.append(current)
        current = _resolve_parent_class_config(
            class_config=current,
            class_configs_by_id=class_configs_by_id,
        )
    chain.reverse()
    return tuple(chain)


def _resolve_parent_class_config(
    *,
    class_config: ClassConfig,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> ClassConfig | None:
    if class_config.parent_class is not None:
        return class_config.parent_class
    parent_class_id = class_config.parent_class_id
    if parent_class_id is None or class_configs_by_id is None:
        return None
    return class_configs_by_id.get(parent_class_id)


def _attribute_config_name(link: ClassConfigAttributeConfig) -> str:
    attribute_config = link.attribute_config
    if attribute_config is not None and attribute_config.name is not None:
        return str(attribute_config.name).strip()
    if link.name is not None:
        return str(link.name).strip()
    return ""


__all__ = [
    "ResolvedInlineValueInstanceAttribute",
    "resolve_class_config_attribute_configs",
    "resolve_inline_value_instance_attributes",
]

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping
from uuid import UUID

from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)

from aware_meta.attribute.instance.value.validator import validate_attribute_value_tree


class ClassInstanceValidationError(ValueError):
    pass


@dataclass(frozen=True)
class _AttrOrderKey:
    position: int
    name: str


def validate_class_instance(
    *,
    class_instance: ClassInstance,
    class_config: ClassConfig,
    relationship_attribute_config_ids: Iterable[UUID] | None = None,
    include_relationship_attribute_config_ids: Iterable[UUID] | None = None,
) -> None:
    """
    Validate that a ClassInstance is consistent with its ClassConfig.

    This is a pure, deterministic validator (no DB lookups, no graph traversal).
    It enforces canonical invariants required for honest OIG diffs:
    - Attributes are descriptor-driven (Attribute.value_root matches AttributeConfig.type_descriptor).
    - Relationship attributes are not represented as Attributes (they are modeled separately as relationships).
    - Required data attributes are present (either provided or defaulted).
    - Attribute ordering is deterministic (by link.position then attribute_config.name).
    """
    if class_instance.class_config_id != class_config.id:
        raise ClassInstanceValidationError(
            f"ClassInstance.class_config_id mismatch: {class_instance.class_config_id} != {class_config.id}"
        )

    relationship_attr_ids = set(relationship_attribute_config_ids or [])
    if include_relationship_attribute_config_ids is not None:
        # Allow select relationship-bound attributes (e.g. portal `<ref>_id`) to be
        # represented as data attributes when the OPG explicitly models the relationship
        # as a cross-projection portal.
        relationship_attr_ids -= set(include_relationship_attribute_config_ids)

    allowed_attribute_configs: dict[UUID, AttributeConfig] = {}
    expected_order: dict[UUID, _AttrOrderKey] = {}
    required_attribute_ids: set[UUID] = set()
    required_fk_attribute_ids = _required_fk_attribute_config_ids(class_config)

    for link in class_config.class_config_attribute_configs:
        attr_cfg = link.attribute_config
        if attr_cfg is None:
            continue
        allowed_attribute_configs[attr_cfg.id] = attr_cfg
        expected_order[attr_cfg.id] = _AttrOrderKey(position=link.position, name=attr_cfg.name)
        if attr_cfg.id in relationship_attr_ids:
            continue
        if attr_cfg.is_required or attr_cfg.id in required_fk_attribute_ids:
            required_attribute_ids.add(attr_cfg.id)

    seen_attr_ids: set[UUID] = set()
    order_keys: list[_AttrOrderKey] = []

    for attr in class_instance.attributes:
        _validate_attribute(
            class_instance=class_instance,
            attribute=attr,
            allowed_attribute_configs=allowed_attribute_configs,
            relationship_attr_ids=relationship_attr_ids,
        )

        attr_id = attr.attribute_config_id
        if attr_id in seen_attr_ids:
            raise ClassInstanceValidationError(f"Duplicate AttributeConfig on instance: {attr_id}")
        seen_attr_ids.add(attr_id)

        key = expected_order.get(attr_id)
        if key is None:
            raise ClassInstanceValidationError(f"AttributeConfig not found on ClassConfig: {attr_id}")
        order_keys.append(key)

    if order_keys != sorted(order_keys, key=lambda k: (k.position, k.name)):
        raise ClassInstanceValidationError("ClassInstance.attributes are not in deterministic order")

    missing_required = required_attribute_ids - seen_attr_ids
    if missing_required:
        missing_names = [allowed_attribute_configs[i].name for i in sorted(missing_required, key=str)]
        raise ClassInstanceValidationError(f"Missing required attributes: {missing_names}")


def _validate_attribute(
    *,
    class_instance: ClassInstance,
    attribute: Attribute,
    allowed_attribute_configs: Mapping[UUID, AttributeConfig],
    relationship_attr_ids: set[UUID],
) -> None:
    if attribute.owner_key != class_instance.source_object_id:
        raise ClassInstanceValidationError(
            f"Attribute.owner_key mismatch: {attribute.owner_key} != {class_instance.source_object_id}"
        )

    attr_cfg = allowed_attribute_configs.get(attribute.attribute_config_id)
    if attr_cfg is None:
        raise ClassInstanceValidationError(
            f"AttributeConfig not found for Attribute.attribute_config_id={attribute.attribute_config_id}"
        )

    if attribute.attribute_config_id in relationship_attr_ids:
        raise ClassInstanceValidationError(
            f"Relationship AttributeConfig must not be represented as Attribute: {attr_cfg.name}"
        )

    root = attribute.value_root
    if root is None:
        raise ClassInstanceValidationError(f"Attribute missing value_root for {attr_cfg.name}")

    if root.type_descriptor_id is not None and root.type_descriptor_id != attr_cfg.type_descriptor.id:
        raise ClassInstanceValidationError(
            f"AttributeValue.type_descriptor_id mismatch for {attr_cfg.name}: {root.type_descriptor_id} != {attr_cfg.type_descriptor.id}"
        )

    validate_attribute_value_tree(root)


def _required_fk_attribute_config_ids(class_config: ClassConfig) -> set[UUID]:
    """
    Relationship/FK requiredness for commit truth.

    Keep this independent from `AttributeConfig.is_required` so language-level
    optional FK sugar does not weaken runtime validation invariants.
    """
    owned_attr_ids = {
        link.attribute_config.id
        for link in class_config.class_config_attribute_configs
        if link.attribute_config is not None and link.attribute_config.id is not None
    }
    required_ids: set[UUID] = set()

    for rel in class_config.class_config_relationships or []:
        is_association = rel.class_config_relationship_association_edge is not None
        for rel_attr in rel.class_config_relationship_attributes or []:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            attr_id = rel_attr.attribute_config_id
            if attr_id is None or attr_id not in owned_attr_ids:
                continue

            if is_association:
                required_ids.add(attr_id)
                continue

            if bool(rel.forward_required):
                required_ids.add(attr_id)
                continue

    return required_ids


__all__ = [
    "ClassInstanceValidationError",
    "validate_class_instance",
]

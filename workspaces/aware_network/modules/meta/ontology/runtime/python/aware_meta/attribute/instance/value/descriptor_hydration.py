from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph


class AttributeValueDescriptorHydrationError(ValueError):
    pass


def hydrate_object_instance_graph_value_type_descriptors(
    *,
    graph: ObjectInstanceGraph,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
) -> None:
    """Attach canonical schema descriptors to compact persisted value trees."""

    type_descriptors_by_id: dict[UUID, AttributeTypeDescriptor] | None = None
    for class_instance in tuple(graph.class_instances or ()):
        for attribute in tuple(class_instance.attributes or ()):
            attribute_config = attribute_configs_by_id.get(
                attribute.attribute_config_id
            )
            value_root = attribute.value_root
            if attribute_config is not None:
                expected_descriptor = attribute_config.type_descriptor
            elif value_root is not None:
                if type_descriptors_by_id is None:
                    type_descriptors_by_id = _canonical_type_descriptors_by_id(
                        attribute_configs_by_id=attribute_configs_by_id
                    )
                expected_descriptor = type_descriptors_by_id.get(
                    value_root.type_descriptor_id
                )
            else:
                expected_descriptor = None
            if expected_descriptor is None:
                raise AttributeValueDescriptorHydrationError(
                    "Cannot hydrate Attribute.value_root descriptor without "
                    "AttributeConfig or canonical persisted descriptor: "
                    f"attribute_id={attribute.id} "
                    f"attribute_config_id={attribute.attribute_config_id} "
                    f"type_descriptor_id={getattr(value_root, 'type_descriptor_id', None)}"
                )
            if value_root is None:
                continue
            hydrate_attribute_value_tree_type_descriptors(
                root=value_root,
                expected_descriptor=expected_descriptor,
                validate_existing_descriptor_payload=(attribute_config is None),
            )
            attribute.value_root_id = value_root.id


def _canonical_type_descriptors_by_id(
    *,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
) -> dict[UUID, AttributeTypeDescriptor]:
    descriptors_by_id: dict[UUID, AttributeTypeDescriptor] = {}
    descriptor_payloads_by_id: dict[UUID, dict[str, object]] = {}
    for attribute_config_id, attribute_config in sorted(
        attribute_configs_by_id.items(),
        key=lambda item: str(item[0]),
    ):
        _remember_canonical_type_descriptor(
            descriptor=attribute_config.type_descriptor,
            source=f"attribute_config_id={attribute_config_id}",
            descriptors_by_id=descriptors_by_id,
            descriptor_payloads_by_id=descriptor_payloads_by_id,
        )
    return descriptors_by_id


def _remember_canonical_type_descriptor(
    *,
    descriptor: AttributeTypeDescriptor,
    source: str,
    descriptors_by_id: dict[UUID, AttributeTypeDescriptor],
    descriptor_payloads_by_id: dict[UUID, dict[str, object]],
) -> None:
    descriptor_id = descriptor.id
    if descriptor_id is None:
        raise AttributeValueDescriptorHydrationError(
            f"Canonical AttributeTypeDescriptor is missing id: {source}"
        )
    payload = _type_descriptor_contract_payload(descriptor=descriptor)
    existing_payload = descriptor_payloads_by_id.get(descriptor_id)
    if existing_payload is not None and existing_payload != payload:
        raise AttributeValueDescriptorHydrationError(
            "Conflicting canonical AttributeTypeDescriptor payloads: "
            f"type_descriptor_id={descriptor_id} source={source}"
        )
    if existing_payload is None:
        descriptors_by_id[descriptor_id] = descriptor
        descriptor_payloads_by_id[descriptor_id] = payload
    for link in tuple(descriptor.child_links or ()):
        child = link.child
        if child is None:
            continue
        _remember_canonical_type_descriptor(
            descriptor=child,
            source=f"{source} parent_type_descriptor_id={descriptor_id}",
            descriptors_by_id=descriptors_by_id,
            descriptor_payloads_by_id=descriptor_payloads_by_id,
        )


def _type_descriptor_contract_payload(
    *, descriptor: AttributeTypeDescriptor
) -> dict[str, object]:
    primitive_config = descriptor.primitive_config
    primitive_type = (
        primitive_config.primitive_type if primitive_config is not None else None
    )
    return {
        "kind": descriptor.kind.value,
        "collection_kind": descriptor.collection_kind.value,
        "primitive_config_id": (
            str(descriptor.primitive_config_id)
            if descriptor.primitive_config_id is not None
            else None
        ),
        "primitive_signature": (
            primitive_type.signature if primitive_type is not None else None
        ),
        "primitive_base_type": (
            primitive_type.base_type.value if primitive_type is not None else None
        ),
        "class_config_id": (
            str(descriptor.class_config_id)
            if descriptor.class_config_id is not None
            else None
        ),
        "enum_config_id": (
            str(descriptor.enum_config_id)
            if descriptor.enum_config_id is not None
            else None
        ),
        "child_links": tuple(
            {
                "role": link.role.value,
                "position": link.position,
                "child_id": str(link.child_id or link.child.id),
                "child": _type_descriptor_contract_payload(descriptor=link.child),
            }
            for link in sorted(
                descriptor.child_links,
                key=lambda item: (
                    item.role.value,
                    item.position,
                    str(item.child_id or item.child.id),
                ),
            )
        ),
    }


def _type_descriptor_contract_mismatch(
    *,
    actual: dict[str, object],
    expected: dict[str, object],
    path: str = "descriptor",
) -> str | None:
    for field_name in (
        "kind",
        "collection_kind",
        "primitive_config_id",
        "class_config_id",
        "enum_config_id",
    ):
        if actual[field_name] != expected[field_name]:
            return (
                f"{path}.{field_name}: actual={actual[field_name]!r} "
                f"expected={expected[field_name]!r}"
            )

    # Snapshot-state descriptors intentionally persist primitive_config_id but
    # omit the hydrated PrimitiveType object. Validate enriched details only
    # when the persisted side actually carries them.
    for field_name in ("primitive_signature", "primitive_base_type"):
        actual_value = actual[field_name]
        if actual_value is not None and actual_value != expected[field_name]:
            return (
                f"{path}.{field_name}: actual={actual_value!r} "
                f"expected={expected[field_name]!r}"
            )

    actual_links = actual["child_links"]
    expected_links = expected["child_links"]
    if not isinstance(actual_links, tuple) or not isinstance(expected_links, tuple):
        return f"{path}.child_links: invalid contract payload"
    if not actual_links:
        return None

    def _link_key(link: object) -> tuple[object, object, object] | None:
        if not isinstance(link, dict):
            return None
        return (link.get("role"), link.get("position"), link.get("child_id"))

    expected_links_by_key = {
        key: link for link in expected_links if (key := _link_key(link)) is not None
    }
    if len(expected_links_by_key) != len(expected_links):
        return f"{path}.child_links: invalid canonical link payload"
    actual_keys = tuple(_link_key(link) for link in actual_links)
    if any(key is None for key in actual_keys):
        return f"{path}.child_links: invalid persisted link payload"
    if set(actual_keys) != set(expected_links_by_key):
        return (
            f"{path}.child_links: actual_keys={actual_keys!r} "
            f"expected_keys={tuple(expected_links_by_key)!r}"
        )
    for actual_link, link_key in zip(actual_links, actual_keys, strict=True):
        if not isinstance(actual_link, dict) or link_key is None:
            return f"{path}.child_links: invalid persisted link payload"
        expected_link = expected_links_by_key[link_key]
        if not isinstance(expected_link, dict):
            return f"{path}.child_links: invalid canonical link payload"
        actual_child = actual_link.get("child")
        expected_child = expected_link.get("child")
        if not isinstance(actual_child, dict) or not isinstance(expected_child, dict):
            return f"{path}.child_links[{link_key!r}]: invalid child payload"
        mismatch = _type_descriptor_contract_mismatch(
            actual=actual_child,
            expected=expected_child,
            path=f"{path}.child_links[{link_key!r}].child",
        )
        if mismatch is not None:
            return mismatch
    return None


def hydrate_attribute_value_tree_type_descriptors(
    *,
    root: AttributeValue,
    expected_descriptor: AttributeTypeDescriptor,
    validate_existing_descriptor_payload: bool = False,
) -> None:
    actual_descriptor = root.type_descriptor
    if (
        actual_descriptor is not None
        and actual_descriptor.id is not None
        and actual_descriptor.id != expected_descriptor.id
    ):
        raise AttributeValueDescriptorHydrationError(
            "AttributeValue descriptor id mismatch during hydration: "
            f"value_id={root.id} "
            f"actual_descriptor_id={actual_descriptor.id} "
            f"expected_descriptor_id={expected_descriptor.id}"
        )
    if validate_existing_descriptor_payload and actual_descriptor is not None:
        actual_payload = _type_descriptor_contract_payload(descriptor=actual_descriptor)
        expected_payload = _type_descriptor_contract_payload(
            descriptor=expected_descriptor
        )
        mismatch = _type_descriptor_contract_mismatch(
            actual=actual_payload,
            expected=expected_payload,
        )
        if mismatch is not None:
            raise AttributeValueDescriptorHydrationError(
                "AttributeValue descriptor payload mismatch during hydration: "
                f"value_id={root.id} "
                f"type_descriptor_id={expected_descriptor.id} "
                f"mismatch={mismatch} "
                f"actual={actual_payload!r} expected={expected_payload!r}"
            )

    root.type_descriptor = expected_descriptor
    root.type_descriptor_id = expected_descriptor.id

    for link in tuple(root.child_links or ()):
        child = link.child
        if child is None:
            raise AttributeValueDescriptorHydrationError(
                "AttributeValueLink missing child during descriptor hydration: "
                f"link_id={link.id} attribute_value_id={link.attribute_value_id}"
            )
        child_descriptor = _child_descriptor_for_link(
            parent_descriptor=expected_descriptor,
            value_link=link,
        )
        hydrate_attribute_value_tree_type_descriptors(
            root=child,
            expected_descriptor=child_descriptor,
            validate_existing_descriptor_payload=(validate_existing_descriptor_payload),
        )


def _child_descriptor_for_link(
    *,
    parent_descriptor: AttributeTypeDescriptor,
    value_link: AttributeValueLink,
) -> AttributeTypeDescriptor:
    kind = parent_descriptor.kind

    if kind in (Kind.collection, Kind.mapping):
        for descriptor_link in tuple(parent_descriptor.child_links or ()):
            if descriptor_link.role == value_link.role and descriptor_link.child:
                return descriptor_link.child
        raise AttributeValueDescriptorHydrationError(
            "Descriptor missing child role during value hydration: "
            f"parent_descriptor_id={parent_descriptor.id} role={value_link.role}"
        )

    if kind in (Kind.tuple, Kind.union):
        if value_link.role != Role.member:
            raise AttributeValueDescriptorHydrationError(
                "Tuple/union value link must use MEMBER role during hydration: "
                f"parent_descriptor_id={parent_descriptor.id} role={value_link.role}"
            )
        if value_link.position is None:
            raise AttributeValueDescriptorHydrationError(
                "Tuple/union value link missing member position during hydration: "
                f"parent_descriptor_id={parent_descriptor.id} link_id={value_link.id}"
            )
        for descriptor_link in tuple(parent_descriptor.child_links or ()):
            if (
                descriptor_link.role == Role.member
                and descriptor_link.position == value_link.position
                and descriptor_link.child
            ):
                return descriptor_link.child
        raise AttributeValueDescriptorHydrationError(
            "Descriptor missing member position during value hydration: "
            f"parent_descriptor_id={parent_descriptor.id} "
            f"position={value_link.position}"
        )

    raise AttributeValueDescriptorHydrationError(
        "Leaf descriptor cannot hydrate child value link: "
        f"parent_descriptor_id={parent_descriptor.id} "
        f"kind={kind} link_id={value_link.id}"
    )


__all__ = [
    "AttributeValueDescriptorHydrationError",
    "hydrate_attribute_value_tree_type_descriptors",
    "hydrate_object_instance_graph_value_type_descriptors",
]

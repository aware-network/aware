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

    for class_instance in tuple(graph.class_instances or ()):
        for attribute in tuple(class_instance.attributes or ()):
            attribute_config = attribute_configs_by_id.get(
                attribute.attribute_config_id
            )
            if attribute_config is None:
                raise AttributeValueDescriptorHydrationError(
                    "Cannot hydrate Attribute.value_root descriptor without "
                    "AttributeConfig: "
                    f"attribute_id={attribute.id} "
                    f"attribute_config_id={attribute.attribute_config_id}"
                )
            value_root = attribute.value_root
            if value_root is None:
                continue
            hydrate_attribute_value_tree_type_descriptors(
                root=value_root,
                expected_descriptor=attribute_config.type_descriptor,
            )
            attribute.value_root_id = value_root.id


def hydrate_attribute_value_tree_type_descriptors(
    *,
    root: AttributeValue,
    expected_descriptor: AttributeTypeDescriptor,
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

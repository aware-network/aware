from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from aware_history_ontology.change.change_enums import ChangeType
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphReplayCopy:
    graph: ObjectInstanceGraph
    class_instance_copy_count: int
    attribute_copy_count: int
    value_node_copy_count: int


def copy_object_instance_graph_for_changes(
    *,
    before_oig: ObjectInstanceGraph,
    changes: Iterable[ObjectInstanceGraphChange],
) -> ObjectInstanceGraphReplayCopy:
    """Copy only mutable OIG paths addressed by a canonical change body."""
    change_tuple = tuple(changes)
    updated_attribute_ids_by_class_instance_id = (
        _updated_attribute_ids_by_class_instance_id(changes=change_tuple)
    )
    copied_class_instances_by_id: dict[UUID, ClassInstance] = {}
    replay_class_instances: list[ClassInstance] = []
    attribute_copy_count = 0
    value_node_copy_count = 0

    for class_instance in before_oig.class_instances:
        updated_attribute_ids = updated_attribute_ids_by_class_instance_id.get(
            class_instance.id
        )
        if updated_attribute_ids is None:
            replay_class_instances.append(class_instance)
            continue

        replay_edges = []
        for edge in class_instance.class_instance_attributes:
            attribute = edge.attribute
            if attribute.id not in updated_attribute_ids:
                replay_edges.append(edge)
                continue
            replay_value_root, copied_value_nodes = _copy_attribute_value_tree(
                attribute.value_root
            )
            replay_attribute = attribute.model_copy(
                deep=False,
                update={"value_root": replay_value_root},
            )
            replay_edges.append(
                edge.model_copy(
                    deep=False,
                    update={"attribute": replay_attribute},
                )
            )
            attribute_copy_count += 1
            value_node_copy_count += copied_value_nodes

        replay_class_instance = class_instance.model_copy(
            deep=False,
            update={"class_instance_attributes": replay_edges},
        )
        copied_class_instances_by_id[class_instance.id] = replay_class_instance
        replay_class_instances.append(replay_class_instance)

    replay_graph = before_oig.model_copy(deep=False)
    replay_graph.class_instances = replay_class_instances
    replay_graph.class_instance_relationships = list(
        before_oig.class_instance_relationships
    )
    root_class_instance_id = before_oig.root_class_instance_id
    if (
        root_class_instance_id is not None
        and root_class_instance_id in copied_class_instances_by_id
    ):
        replay_graph.root_class_instance = copied_class_instances_by_id[
            root_class_instance_id
        ]
    return ObjectInstanceGraphReplayCopy(
        graph=replay_graph,
        class_instance_copy_count=len(copied_class_instances_by_id),
        attribute_copy_count=attribute_copy_count,
        value_node_copy_count=value_node_copy_count,
    )


def _updated_attribute_ids_by_class_instance_id(
    *,
    changes: Iterable[ObjectInstanceGraphChange],
) -> dict[UUID, set[UUID]]:
    updated_attribute_ids_by_class_instance_id: dict[UUID, set[UUID]] = {}
    for root_change in changes:
        for class_instance_change in root_change.class_instance_changes:
            if class_instance_change.change.type is not ChangeType.update:
                continue
            updated_attribute_ids = (
                updated_attribute_ids_by_class_instance_id.setdefault(
                    class_instance_change.class_instance_id,
                    set(),
                )
            )
            updated_attribute_ids.update(
                attribute_change.attribute_id
                for attribute_change in class_instance_change.attribute_changes
                if attribute_change.change.type is ChangeType.update
            )
    return updated_attribute_ids_by_class_instance_id


def _copy_attribute_value_tree(
    value: AttributeValue,
) -> tuple[AttributeValue, int]:
    copied_node_count = 1
    copied_links = []
    for link in value.child_links:
        copied_child, child_node_count = _copy_attribute_value_tree(link.child)
        copied_node_count += child_node_count
        copied_links.append(
            link.model_copy(
                deep=False,
                update={"child": copied_child},
            )
        )
    return (
        value.model_copy(
            deep=False,
            update={"child_links": copied_links},
        ),
        copied_node_count,
    )


__all__ = [
    "copy_object_instance_graph_for_changes",
    "ObjectInstanceGraphReplayCopy",
]

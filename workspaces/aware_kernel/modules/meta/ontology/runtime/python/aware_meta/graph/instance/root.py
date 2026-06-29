from __future__ import annotations

from uuid import UUID

from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph


def resolve_root_class_instance(graph: ObjectInstanceGraph) -> ClassInstance:
    if graph.root_class_instance is not None:
        return graph.root_class_instance
    root_class_instance_id = graph.root_class_instance_id
    if root_class_instance_id is None:
        raise ValueError("ObjectInstanceGraph is missing root_class_instance_id")
    for class_instance in graph.class_instances:
        if class_instance.id == root_class_instance_id:
            return class_instance
    raise ValueError(
        "ObjectInstanceGraph root_class_instance_id does not resolve to a class instance: "
        + f"root_class_instance_id={root_class_instance_id}"
    )


def resolve_root_class_instance_id(graph: ObjectInstanceGraph) -> UUID:
    return resolve_root_class_instance(graph).id


def resolve_root_source_object_id(graph: ObjectInstanceGraph) -> UUID:
    root_class_instance = resolve_root_class_instance(graph)
    if root_class_instance.source_object_id is None:
        raise ValueError(
            "ObjectInstanceGraph root_class_instance is missing source_object_id: "
            + f"class_instance_id={root_class_instance.id}"
        )
    return root_class_instance.source_object_id


__all__ = [
    "resolve_root_class_instance",
    "resolve_root_class_instance_id",
    "resolve_root_source_object_id",
]

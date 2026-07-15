from __future__ import annotations

from collections.abc import Iterable
from typing import cast
from uuid import UUID

from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_orm.models.base_model import BaseORMModel


def resolve_root_class_instance_snapshot(
    *,
    class_instances: list[ClassInstance],
    expected_root_class_instance_id: UUID | None,
    fallback_root_class_instance: ClassInstance | None,
) -> ClassInstance:
    if expected_root_class_instance_id is None:
        if fallback_root_class_instance is None:
            raise RuntimeError(
                "ObjectInstanceGraph seed diff snapshot is missing fallback root ClassInstance"
            )
        return fallback_root_class_instance
    for class_instance in class_instances:
        if class_instance.id == expected_root_class_instance_id:
            return class_instance
    if (
        fallback_root_class_instance is not None
        and fallback_root_class_instance.id == expected_root_class_instance_id
    ):
        return fallback_root_class_instance
    raise RuntimeError(
        "Root ClassInstance missing from ObjectInstanceGraph seed diff snapshot: "
        + f"root_class_instance_id={expected_root_class_instance_id}"
    )


def collect_orm_models(root: object) -> dict[UUID, BaseORMModel]:
    """Traverse an object graph and collect unique ORM models by id."""
    objects: dict[UUID, BaseORMModel] = {}
    seen: set[UUID] = set()
    stack: list[object] = [root]

    while stack:
        current = stack.pop()
        if current is None:
            continue

        if isinstance(current, BaseORMModel):
            obj_id = current.id
            if obj_id in seen:
                continue
            seen.add(obj_id)
            objects[obj_id] = current

            for field_name, field_info in current.__class__.model_fields.items():
                if getattr(field_info, "exclude", False):
                    continue
                try:
                    value = cast(object, current.__dict__.get(field_name))
                except Exception:
                    continue
                stack.append(value)
            continue

        if isinstance(current, dict):
            current_dict = cast(dict[object, object], current)
            stack.extend(list(current_dict.values()))
            continue
        if isinstance(current, (list, tuple, set)):
            current_iterable = cast(Iterable[object], current)
            stack.extend(list(current_iterable))
            continue

    return objects


def _external_graph_reference(graph: ObjectConfigGraph) -> ObjectConfigGraph:
    return graph.model_copy(
        update={
            "object_config_graph_annotations": [],
            "object_config_graph_mirrors": [],
            "object_config_graph_nodes": [],
            "object_config_graph_overlays": [],
            "object_config_graph_bindings": [],
            "object_config_graph_relationships": [],
            "object_projection_graph_declarations": [],
            "object_projection_graphs": [],
        },
        deep=False,
    )


def collect_lane_instance_models(
    *,
    ocg: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph],
) -> dict[UUID, BaseORMModel]:
    """Collect ORM models needed to build OIG snapshots for the commit lane."""
    objects_by_id = collect_orm_models(ocg)
    external_graphs_list = list(external_graphs or ())

    referenced_graph_ids: set[UUID] = set()
    for rel in ocg.object_config_graph_relationships:
        referenced_graph_ids.add(rel.object_config_graph_id)
        referenced_graph_ids.add(rel.target_object_config_graph_id)

    allow_graph_ids: set[UUID] = set()
    if referenced_graph_ids:
        allow_graph_ids |= referenced_graph_ids
    if not allow_graph_ids:
        return objects_by_id

    for external_graph in sorted(external_graphs_list, key=lambda graph: str(graph.id)):
        external_graph_id = external_graph.id
        if external_graph_id not in allow_graph_ids:
            continue
        graph_ref = _external_graph_reference(external_graph)
        _ = objects_by_id.setdefault(graph_ref.id, graph_ref)
    return objects_by_id


__all__ = [
    "collect_lane_instance_models",
    "collect_orm_models",
    "resolve_root_class_instance_snapshot",
]

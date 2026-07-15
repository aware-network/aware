from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_binding import ObjectConfigGraphBinding
from aware_meta_ontology.graph.config.object_config_graph_binding_class import ObjectConfigGraphBindingClass

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_binding_id,
)

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_class(
    object_config_graph_binding: ObjectConfigGraphBinding,
    name: str,
    source_class_id: UUID,
    target_class_id: UUID,
    target_attribute_id: UUID,
    source_attr_id: UUID | None = None,
) -> ObjectConfigGraphBindingClass:
    """
    Create deterministic ObjectConfigGraphBindingClass under this binding.

    Contract:
    - Parent binding scope is propagated by constructor lowering.
    - `source_attr_id` is optional at the binding layer and does not widen source-scope identity.
    - `target_attribute_id` is required as the target anchor.
    """

    # --- AWARE: LOGIC START create_class
    if object_config_graph_binding.id is None:
        raise RuntimeError("ObjectConfigGraphBinding.create_class requires binding id")

    created = await ObjectConfigGraphBindingClass.build_via_object_config_graph_binding(
        object_config_graph_binding_id=object_config_graph_binding.id,
        name=name,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        target_attribute_id=target_attribute_id,
        source_attr_id=source_attr_id,
    )
    for existing in object_config_graph_binding.object_config_graph_binding_classes:
        if existing.id != created.id:
            continue
        if (
            existing.object_config_graph_binding_id != object_config_graph_binding.id
            or existing.name != name
            or existing.source_class_id != source_class_id
            or existing.target_class_id != target_class_id
            or existing.target_attribute_id != target_attribute_id
            or existing.source_attr_id != source_attr_id
        ):
            raise RuntimeError(
                "ObjectConfigGraphBinding.create_class payload mismatch for existing binding class: "
                f"object_config_graph_binding_class_id={created.id}"
            )
        return existing

    object_config_graph_binding.object_config_graph_binding_classes.append(created)
    return created
    # --- AWARE: LOGIC END create_class


async def build_via_object_config_graph(
    object_config_graph_id: UUID, target_object_config_graph_id: UUID
) -> ObjectConfigGraphBinding:
    """
    Build deterministic ObjectConfigGraphBinding within an ObjectConfigGraph scope.

    Contract:
    - Source OCG scope is propagated via `ObjectConfigGraph -> ObjectConfigGraphBinding`.
    - Binding identity resolves from `(object_config_graph_id via path, target_object_config_graph_id)`.
    """

    # --- AWARE: LOGIC START build_via_object_config_graph
    object_config_graph_binding_id = stable_object_config_graph_binding_id(
        object_config_graph_id=object_config_graph_id,
        target_object_config_graph_id=target_object_config_graph_id,
    )
    session = current_handler_session()
    target_object_config_graph = session.imap_get(ObjectConfigGraph, target_object_config_graph_id)
    if target_object_config_graph is None:
        raise RuntimeError(
            "ObjectConfigGraphBinding.build_via_object_config_graph requires existing target "
            f"ObjectConfigGraph: target_object_config_graph_id={target_object_config_graph_id}"
        )
    existing = session.imap_get(ObjectConfigGraphBinding, object_config_graph_binding_id)
    if existing is not None:
        if (
            existing.object_config_graph_id != object_config_graph_id
            or existing.target_object_config_graph_id != target_object_config_graph_id
        ):
            raise RuntimeError(
                "ObjectConfigGraphBinding.build_via_object_config_graph payload mismatch for existing "
                f"ObjectConfigGraphBinding: object_config_graph_binding_id={object_config_graph_binding_id}"
            )
        return existing

    return ObjectConfigGraphBinding(
        id=object_config_graph_binding_id,
        target_object_config_graph=target_object_config_graph,
        object_config_graph_id=object_config_graph_id,
        target_object_config_graph_id=target_object_config_graph_id,
    )
    # --- AWARE: LOGIC END build_via_object_config_graph

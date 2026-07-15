from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.stable_ids import stable_object_instance_graph_id

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_class_instance(
    object_instance_graph: ObjectInstanceGraph,
    class_config_id: UUID,
    source_object_id: UUID,
) -> ClassInstance:
    """
    Create deterministic ClassInstance under this ObjectInstanceGraph.

    Contract:
    - Parent ObjectInstanceGraph identity is propagated by constructor lowering.
    - The child ClassInstance stable id must resolve from
      `(object_instance_graph_id via path, class_config_id, source_object_id)`.
    """

    # --- AWARE: LOGIC START create_class_instance
    created = await ClassInstance.create_via_object_instance_graph(
        object_instance_graph_id=object_instance_graph.id,
        class_config_id=class_config_id,
        source_object_id=source_object_id,
    )
    if all(existing.id != created.id for existing in object_instance_graph.class_instances):
        object_instance_graph.class_instances.append(created)
    return created
    # --- AWARE: LOGIC END create_class_instance


async def build_via_object_projection_graph(
    object_projection_graph_id: UUID,
    key: str,
    root_class_config_id: UUID,
    root_source_object_id: UUID,
    name: str,
    description: str | None = None,
    hash: str = "",
) -> ObjectInstanceGraph:
    """
    Create deterministic ObjectInstanceGraph under one ObjectProjectionGraph.

    Contract:
    - Parent `object_projection_graph_id` is propagated by constructor lowering.
    - Identity resolves from `(object_projection_graph_id via path, key)`.
    - Root ClassInstance is created eagerly from `(root_class_config_id, root_source_object_id)`.
    - Empty OIGs are not allowed.
    - `name` is mutable payload metadata and must not participate in stable identity.
    - `hash` is snapshot metadata and must not participate in stable identity.
    """

    # --- AWARE: LOGIC START build_via_object_projection_graph
    object_instance_graph_id = stable_object_instance_graph_id(
        object_projection_graph_id=object_projection_graph_id,
        key=key,
    )
    session = current_handler_session()
    existing = session.imap_get(ObjectInstanceGraph, object_instance_graph_id)
    root_class_instance = await ClassInstance.create_via_object_instance_graph(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=root_class_config_id,
        source_object_id=root_source_object_id,
    )
    if existing is not None:
        if (
            existing.object_projection_graph_id != object_projection_graph_id
            or existing.key != key
            or existing.name != name
            or (existing.description or None) != (description or None)
            or existing.hash != hash
            or existing.root_class_instance_id != root_class_instance.id
        ):
            raise RuntimeError(
                "ObjectInstanceGraph.build_via_object_projection_graph payload mismatch for existing "
                f"ObjectInstanceGraph: object_instance_graph_id={object_instance_graph_id}"
            )
        return existing

    return ObjectInstanceGraph(
        id=object_instance_graph_id,
        object_projection_graph_id=object_projection_graph_id,
        key=key,
        name=name,
        description=description,
        hash=hash,
        root_class_instance_id=root_class_instance.id,
        root_class_instance=root_class_instance,
        class_instances=[root_class_instance],
        class_instance_relationships=[],
    )
    # --- AWARE: LOGIC END build_via_object_projection_graph

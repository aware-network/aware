from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.projection.object_projection_graph_enums import ObjectProjectionGraphNodeSelection
from aware_meta_ontology.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode
from aware_meta_ontology.graph.projection.object_projection_graph_node_key import ObjectProjectionGraphNodeKey

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.stable_ids import stable_object_projection_graph_node_id

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_key(
    object_projection_graph_node: ObjectProjectionGraphNode,
    object_config_graph_binding_class_id: UUID,
    key: str,
    position: int | None = None,
    required: bool = True,
) -> ObjectProjectionGraphNodeKey:
    """
    Create deterministic ObjectProjectionGraphNodeKey under this ObjectProjectionGraphNode.

    Contract:
    - Parent `object_projection_graph_node_id` is propagated by constructor lowering.
    - NodeKey consumes one `ObjectConfigGraphBindingClass` on top of binding + formula.
    - Identity resolves from `(object_projection_graph_node_id via path,
    object_config_graph_binding_class_id, key)`.
    """

    # --- AWARE: LOGIC START create_key
    created = await ObjectProjectionGraphNodeKey.build_via_object_projection_graph_node(
        object_projection_graph_node_id=object_projection_graph_node.id,
        object_config_graph_binding_class_id=object_config_graph_binding_class_id,
        key=key,
        position=position,
        required=required,
    )
    for existing in object_projection_graph_node.object_projection_graph_node_keys:
        if existing.id != created.id:
            continue
        if (
            existing.object_projection_graph_node_id != object_projection_graph_node.id
            or existing.object_config_graph_binding_class_id != object_config_graph_binding_class_id
            or existing.key != key
            or existing.position != position
            or existing.required != required
        ):
            raise RuntimeError(
                "ObjectProjectionGraphNode.create_key payload mismatch for existing "
                f"ObjectProjectionGraphNodeKey: object_projection_graph_node_key_id={created.id}"
            )
        return existing
    object_projection_graph_node.object_projection_graph_node_keys.append(created)
    return created
    # --- AWARE: LOGIC END create_key


async def build_via_object_projection_graph(
    object_projection_graph_id: UUID,
    class_config_id: UUID,
    is_root: bool = False,
    required_for_validity: bool = False,
    selection: ObjectProjectionGraphNodeSelection = ObjectProjectionGraphNodeSelection.all,
    top_n: int | None = None,
    selector_condition_id: UUID | None = None,
    policy_refs: list[str] = [],
) -> ObjectProjectionGraphNode:
    """
    Create deterministic ObjectProjectionGraphNode under one ObjectProjectionGraph.

    Contract:
    - Parent `object_projection_graph_id` is propagated by constructor lowering.
    - Identity is always OPG-scoped.
    """

    # --- AWARE: LOGIC START build_via_object_projection_graph
    object_projection_graph_node_id = stable_object_projection_graph_node_id(
        object_projection_graph_id=object_projection_graph_id,
        class_config_id=class_config_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ObjectProjectionGraphNode, object_projection_graph_node_id)
    if existing is not None:
        if (
            existing.object_projection_graph_id != object_projection_graph_id
            or existing.class_config_id != class_config_id
            or existing.is_root != is_root
            or existing.required_for_validity != required_for_validity
            or existing.selection != selection
            or existing.top_n != top_n
            or existing.selector_condition_id != selector_condition_id
            or existing.policy_refs != policy_refs
        ):
            raise RuntimeError(
                "ObjectProjectionGraphNode.build_via_object_projection_graph payload mismatch for existing "
                f"ObjectProjectionGraphNode: object_projection_graph_node_id={object_projection_graph_node_id}"
            )
        return existing

    return ObjectProjectionGraphNode(
        id=object_projection_graph_node_id,
        object_projection_graph_id=object_projection_graph_id,
        class_config_id=class_config_id,
        is_root=is_root,
        required_for_validity=required_for_validity,
        selection=selection,
        top_n=top_n,
        selector_condition_id=selector_condition_id,
        policy_refs=list(policy_refs),
    )
    # --- AWARE: LOGIC END build_via_object_projection_graph

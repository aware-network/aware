from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.projection.object_projection_graph_node_key import ObjectProjectionGraphNodeKey

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
from aware_meta_ontology.graph.config.object_config_graph_binding_class import (
    ObjectConfigGraphBindingClass,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode
from aware_meta_ontology.stable_ids import stable_object_projection_graph_node_key_id

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_object_projection_graph_node(
    object_projection_graph_node_id: UUID,
    object_config_graph_binding_class_id: UUID,
    key: str,
    position: int | None = None,
    required: bool = True,
) -> ObjectProjectionGraphNodeKey:
    """
    Create deterministic ObjectProjectionGraphNodeKey under one ObjectProjectionGraphNode.

    Contract:
    - Parent `object_projection_graph_node_id` is propagated by constructor lowering.
    - Identity resolves from `(object_projection_graph_node_id via path,
    object_config_graph_binding_class_id, key)`.
    - The binding-class target class must match the projected node class.
    - The binding-class target attribute must be an identity-resolution anchor.
    """

    # --- AWARE: LOGIC START build_via_object_projection_graph_node
    object_projection_graph_node_key_id = stable_object_projection_graph_node_key_id(
        object_projection_graph_node_id=object_projection_graph_node_id,
        object_config_graph_binding_class_id=object_config_graph_binding_class_id,
        key=key,
    )
    session = current_handler_session()
    existing = session.imap_get(ObjectProjectionGraphNodeKey, object_projection_graph_node_key_id)
    if existing is not None:
        if (
            existing.object_projection_graph_node_id != object_projection_graph_node_id
            or existing.object_config_graph_binding_class_id != object_config_graph_binding_class_id
            or existing.key != key
            or existing.position != position
            or existing.required != required
        ):
            raise RuntimeError(
                "ObjectProjectionGraphNodeKey.build_via_object_projection_graph_node payload mismatch for existing "
                f"ObjectProjectionGraphNodeKey: object_projection_graph_node_key_id={object_projection_graph_node_key_id}"
            )
        return existing

    object_projection_graph_node = session.imap_get(ObjectProjectionGraphNode, object_projection_graph_node_id)
    if object_projection_graph_node is None:
        raise RuntimeError(
            "ObjectProjectionGraphNodeKey.build_via_object_projection_graph_node requires "
            f"ObjectProjectionGraphNode in session: object_projection_graph_node_id={object_projection_graph_node_id}"
        )

    binding_class = session.imap_get(ObjectConfigGraphBindingClass, object_config_graph_binding_class_id)
    if binding_class is None:
        raise RuntimeError(
            "ObjectProjectionGraphNodeKey.build_via_object_projection_graph_node requires "
            "ObjectConfigGraphBindingClass in session: "
            f"object_config_graph_binding_class_id={object_config_graph_binding_class_id}"
        )

    if binding_class.target_class_id != object_projection_graph_node.class_config_id:
        raise RuntimeError(
            "ObjectProjectionGraphNodeKey target class mismatch: "
            f"node.class_config_id={object_projection_graph_node.class_config_id} "
            f"binding.target_class_id={binding_class.target_class_id}"
        )

    target_attribute = binding_class.target_attribute or session.imap_get(
        ClassConfigAttributeConfig,
        binding_class.target_attribute_id,
    )
    if target_attribute is None:
        raise RuntimeError(
            "ObjectProjectionGraphNodeKey.build_via_object_projection_graph_node requires "
            "binding target attribute in session: "
            f"class_config_attribute_config_id={binding_class.target_attribute_id}"
        )
    if not target_attribute.is_identity_key:
        raise RuntimeError(
            "ObjectProjectionGraphNodeKey requires identity-key target attribute: "
            f"class_config_attribute_config_id={binding_class.target_attribute_id}"
        )

    return ObjectProjectionGraphNodeKey(
        id=object_projection_graph_node_key_id,
        object_config_graph_binding_class=binding_class,
        object_projection_graph_node_id=object_projection_graph_node_id,
        object_config_graph_binding_class_id=object_config_graph_binding_class_id,
        key=key,
        position=position,
        required=required,
    )
    # --- AWARE: LOGIC END build_via_object_projection_graph_node

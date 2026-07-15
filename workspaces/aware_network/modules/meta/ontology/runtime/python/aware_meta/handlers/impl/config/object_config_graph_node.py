from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.graph.config.object_config_graph_node import ObjectConfigGraphNode

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# Meta
from aware_meta.graph.config.model_bootstrap import (
    build_object_config_graph_node,
    get_object_config_graph_node_class_config_id,
    get_object_config_graph_node_enum_config_id,
    get_object_config_graph_node_key,
)
from aware_meta.graph.config.stable_ids import (
    stable_class_config_id,
    stable_enum_config_id,
    stable_object_config_graph_node_id,
)

# --- AWARE: USER_IMPORTS END


async def create_class(
    object_config_graph_node: ObjectConfigGraphNode,
    class_fqn: str,
    name: str,
    is_base: bool = True,
    is_edge: bool = False,
    description: str | None = None,
    value_mode: ClassValueMode = ClassValueMode.graph_ref,
) -> ClassConfig:
    """
    Materialize ClassConfig under this node.
    """

    # --- AWARE: LOGIC START create_class
    if object_config_graph_node.type != ObjectConfigGraphNodeType.class_:
        raise RuntimeError(
            "ObjectConfigGraphNode.create_class requires node type=class: "
            f"node_id={object_config_graph_node.id} type={object_config_graph_node.type.value}"
        )
    normalized_class_fqn = (class_fqn or "").strip()
    if not normalized_class_fqn:
        raise RuntimeError("ObjectConfigGraphNode.create_class requires non-empty class_fqn")
    existing_node_key = get_object_config_graph_node_key(object_config_graph_node)
    if existing_node_key is not None and existing_node_key != normalized_class_fqn:
        raise RuntimeError(
            "ObjectConfigGraphNode.create_class requires node_key == class_fqn: "
            f"node_id={object_config_graph_node.id} "
            f"node_key={existing_node_key!r} class_fqn={normalized_class_fqn!r}"
        )
    existing_enum_config_id = get_object_config_graph_node_enum_config_id(object_config_graph_node)
    if existing_enum_config_id is not None:
        raise RuntimeError(
            "ObjectConfigGraphNode.create_class requires node without enum binding: "
            f"node_id={object_config_graph_node.id} enum_config_id={existing_enum_config_id}"
        )

    expected_class_config_id = stable_class_config_id(
        object_config_graph_node_id=object_config_graph_node.id,
        class_fqn=normalized_class_fqn,
    )
    if (
        get_object_config_graph_node_class_config_id(object_config_graph_node) is not None
        and get_object_config_graph_node_class_config_id(object_config_graph_node) != expected_class_config_id
    ):
        raise RuntimeError(
            "ObjectConfigGraphNode.create_class class_config mismatch on existing node: "
            f"node_id={object_config_graph_node.id} "
            f"existing_class_config_id={get_object_config_graph_node_class_config_id(object_config_graph_node)} "
            f"expected_class_config_id={expected_class_config_id}"
        )

    class_config = await ClassConfig.create_via_object_config_graph_node(
        object_config_graph_node_id=object_config_graph_node.id,
        class_fqn=normalized_class_fqn,
        name=name,
        is_base=is_base,
        is_edge=is_edge,
        description=description,
        value_mode=value_mode,
    )
    object_config_graph_node.class_config = class_config
    return class_config
    # --- AWARE: LOGIC END create_class


async def create_enum(
    object_config_graph_node: ObjectConfigGraphNode,
    enum_fqn: str,
    name: str,
    description: str | None = None,
    values: list[str] = [],
) -> EnumConfig:
    """
    Materialize EnumConfig under this node.
    """

    # --- AWARE: LOGIC START create_enum
    if object_config_graph_node.type != ObjectConfigGraphNodeType.enum:
        raise RuntimeError(
            "ObjectConfigGraphNode.create_enum requires node type=enum: "
            f"node_id={object_config_graph_node.id} type={object_config_graph_node.type.value}"
        )
    normalized_enum_fqn = (enum_fqn or "").strip()
    if not normalized_enum_fqn:
        raise RuntimeError("ObjectConfigGraphNode.create_enum requires non-empty enum_fqn")
    existing_node_key = get_object_config_graph_node_key(object_config_graph_node)
    if existing_node_key is not None and existing_node_key != normalized_enum_fqn:
        raise RuntimeError(
            "ObjectConfigGraphNode.create_enum requires node_key == enum_fqn: "
            f"node_id={object_config_graph_node.id} "
            f"node_key={existing_node_key!r} enum_fqn={normalized_enum_fqn!r}"
        )

    enum_config_id = stable_enum_config_id(
        object_config_graph_node_id=object_config_graph_node.id,
        enum_fqn=normalized_enum_fqn,
    )
    if (
        get_object_config_graph_node_enum_config_id(object_config_graph_node) is not None
        and get_object_config_graph_node_enum_config_id(object_config_graph_node) != enum_config_id
    ):
        raise RuntimeError(
            "ObjectConfigGraphNode.create_enum enum_config mismatch on existing node: "
            f"node_id={object_config_graph_node.id} "
            f"existing_enum_config_id={get_object_config_graph_node_enum_config_id(object_config_graph_node)} "
            f"requested_enum_config_id={enum_config_id}"
        )
    existing_class_config_id = get_object_config_graph_node_class_config_id(object_config_graph_node)
    if existing_class_config_id is not None:
        raise RuntimeError(
            "ObjectConfigGraphNode.create_enum requires node without class binding: "
            f"node_id={object_config_graph_node.id} class_config_id={existing_class_config_id}"
        )

    enum_config = await EnumConfig.create_via_object_config_graph_node(
        object_config_graph_node_id=object_config_graph_node.id,
        enum_fqn=normalized_enum_fqn,
        name=name,
        description=description,
        values=values,
    )
    object_config_graph_node.enum_config = enum_config
    return enum_config
    # --- AWARE: LOGIC END create_enum


async def create_via_object_config_graph(
    object_config_graph_id: UUID, type: ObjectConfigGraphNodeType, node_key: str
) -> ObjectConfigGraphNode:
    """
    Create deterministic node shell under an ObjectConfigGraph.

    Contract:
    - Parent `ObjectConfigGraph` scope is propagated by traversal lowering.
    - Canonical stable identity derives from parent scope + `(type, node_key)`.
    - Contained entities derive under this node instead of being the node identity source.
    """

    # --- AWARE: LOGIC START create_via_object_config_graph
    normalized_node_key = (node_key or "").strip()
    if not normalized_node_key:
        raise RuntimeError("ObjectConfigGraphNode.create_via_object_config_graph requires non-empty node_key")
    object_config_graph_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=object_config_graph_id,
        type=str(getattr(type, "value", type)),
        node_key=normalized_node_key,
    )
    session = current_handler_session()
    existing = session.imap_get(ObjectConfigGraphNode, object_config_graph_node_id)
    if existing is not None:
        existing_node_key = get_object_config_graph_node_key(existing)
        if (
            existing.object_config_graph_id != object_config_graph_id
            or existing.type != type
            or (existing_node_key is not None and existing_node_key != normalized_node_key)
        ):
            raise RuntimeError(
                "ObjectConfigGraphNode.create_via_object_config_graph payload mismatch for existing node: "
                f"object_config_graph_node_id={object_config_graph_node_id}"
            )
        return existing

    return build_object_config_graph_node(
        object_config_graph_node_id=object_config_graph_node_id,
        object_config_graph_id=object_config_graph_id,
        type=type,
        node_key=normalized_node_key,
    )
    # --- AWARE: LOGIC END create_via_object_config_graph

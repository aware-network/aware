from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_attribute import ClassInstanceAttribute

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.stable_ids import stable_class_instance_id
from aware_meta.handlers.impl.class_ import (
    class_instance_attribute as class_instance_attribute_handler,
)

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_attribute(
    class_instance: ClassInstance, attribute_config_id: UUID, value_root_id: UUID | None = None
) -> ClassInstanceAttribute:
    """
    Create deterministic Attribute membership under this ClassInstance.

    Contract:
    - ClassInstance owns membership and topology only.
    - Attribute identity resolves from `(source_object_id, attribute_config_id)` via shared owner key.
    """

    # --- AWARE: LOGIC START create_attribute
    class_instance_id = class_instance.id
    if class_instance_id is None:
        raise RuntimeError("ClassInstance.create_attribute requires class_instance.id")

    edge = await class_instance_attribute_handler.create_via_class_instance(
        class_instance_id=class_instance_id,
        owner_key=class_instance.source_object_id,
        attribute_config_id=attribute_config_id,
        value_root_id=value_root_id,
    )
    for existing in class_instance.class_instance_attributes:
        if existing.id == edge.id:
            if existing.attribute is None:
                existing.attribute = edge.attribute
                existing.attribute_id = edge.attribute_id
            return existing

    class_instance.class_instance_attributes.append(edge)
    return edge
    # --- AWARE: LOGIC END create_attribute


async def create_via_object_instance_graph(
    object_instance_graph_id: UUID, class_config_id: UUID, source_object_id: UUID
) -> ClassInstance:
    """
    Create deterministic ClassInstance under one ObjectInstanceGraph scope.

    Contract:
    - Parent `object_instance_graph_id` is propagated by constructor lowering.
    - Identity resolves from `(object_instance_graph_id via path, class_config_id, source_object_id)`.
    - `source_object_id` is the semantic source-object/worldline anchor, not a synthesized FK.
    """

    # --- AWARE: LOGIC START create_via_object_instance_graph
    class_instance_id = stable_class_instance_id(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config_id,
        source_object_id=source_object_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ClassInstance, class_instance_id)
    if existing is not None:
        if (
            existing.object_instance_graph_id != object_instance_graph_id
            or existing.class_config_id != class_config_id
            or existing.source_object_id != source_object_id
        ):
            raise RuntimeError(
                "ClassInstance.create_via_object_instance_graph payload mismatch for existing ClassInstance: "
                f"class_instance_id={class_instance_id}"
            )
        return existing

    return ClassInstance(
        id=class_instance_id,
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config_id,
        source_object_id=source_object_id,
        class_instance_attributes=[],
    )
    # --- AWARE: LOGIC END create_via_object_instance_graph

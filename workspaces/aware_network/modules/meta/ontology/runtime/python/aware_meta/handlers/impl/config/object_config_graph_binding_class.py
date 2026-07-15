from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_binding_class import ObjectConfigGraphBindingClass
from aware_meta_ontology.graph.config.object_config_graph_binding_formula import ObjectConfigGraphBindingFormula

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta
from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_binding_class_id,
)

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_formula(
    object_config_graph_binding_class: ObjectConfigGraphBindingClass,
    key: str = "default",
    content_part_text_id: UUID | None = None,
) -> ObjectConfigGraphBindingFormula:
    """
    Create deterministic formula ownership under this binding-class scope.

    Contract:
    - Parent binding-class scope is propagated by constructor lowering.
    - Formula identity resolves from `(object_config_graph_binding_class_id via path, key)`.
    - `content_part_text_id` may be attached later or during construction.
    """

    # --- AWARE: LOGIC START create_formula
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_formula


async def build_via_object_config_graph_binding(
    object_config_graph_binding_id: UUID,
    name: str,
    source_class_id: UUID,
    target_class_id: UUID,
    target_attribute_id: UUID,
    source_attr_id: UUID | None = None,
) -> ObjectConfigGraphBindingClass:
    """
    Build deterministic ObjectConfigGraphBindingClass within an ObjectConfigGraphBinding scope.

    Contract:
    - Parent binding scope is propagated via `ObjectConfigGraphBinding ->
    ObjectConfigGraphBindingClass`.
    - Stable identity resolves from `(object_config_graph_binding_id via path, source_class_id,
    target_class_id, target_attribute_id)`.
    - `source_attr_id` is optional and does not participate in v0 stable identity.
    """

    # --- AWARE: LOGIC START build_via_object_config_graph_binding
    object_config_graph_binding_class_id = stable_object_config_graph_binding_class_id(
        object_config_graph_binding_id=object_config_graph_binding_id,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        target_attribute_id=target_attribute_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ObjectConfigGraphBindingClass, object_config_graph_binding_class_id)
    if existing is not None:
        if (
            existing.object_config_graph_binding_id != object_config_graph_binding_id
            or existing.name != name
            or existing.source_class_id != source_class_id
            or existing.target_class_id != target_class_id
            or existing.target_attribute_id != target_attribute_id
            or existing.source_attr_id != source_attr_id
        ):
            raise RuntimeError(
                "ObjectConfigGraphBindingClass.build_via_object_config_graph_binding payload mismatch for existing "
                f"ObjectConfigGraphBindingClass: object_config_graph_binding_class_id={object_config_graph_binding_class_id}"
            )
        return existing

    return ObjectConfigGraphBindingClass(
        id=object_config_graph_binding_class_id,
        object_config_graph_binding_id=object_config_graph_binding_id,
        name=name,
        source_class_id=source_class_id,
        source_attr_id=source_attr_id,
        target_class_id=target_class_id,
        target_attribute_id=target_attribute_id,
    )
    # --- AWARE: LOGIC END build_via_object_config_graph_binding

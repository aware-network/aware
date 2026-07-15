from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.projection.object_projection_graph_binding import ObjectProjectionGraphBinding
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import ObjectProjectionGraphDeclaration

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.stable_ids import stable_object_projection_graph_binding_id

# --- AWARE: USER_IMPORTS END


async def create_binding(
    object_projection_graph_declaration: ObjectProjectionGraphDeclaration,
    fqn_prefix: str,
    namespace: str,
    class_name: str,
    attribute_name: str | None = None,
    target_projection_name: str | None = None,
    side: str | None = None,
    object_projection_graph_binding_id: UUID | None = None,
) -> ObjectProjectionGraphBinding:
    """
    Create deterministic ObjectProjectionGraphBinding under this declaration.
    """

    # --- AWARE: LOGIC START create_binding
    declaration_id = object_projection_graph_declaration.id
    if declaration_id is None:
        raise RuntimeError(
            "ObjectProjectionGraphDeclaration.create_binding requires declaration id"
        )
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    normalized_namespace = (namespace or "").strip()
    normalized_class_name = (class_name or "").strip()
    if not normalized_fqn_prefix:
        raise RuntimeError(
            "ObjectProjectionGraphDeclaration.create_binding requires non-empty fqn_prefix"
        )
    if not normalized_namespace:
        raise RuntimeError(
            "ObjectProjectionGraphDeclaration.create_binding requires non-empty namespace"
        )
    if not normalized_class_name:
        raise RuntimeError(
            "ObjectProjectionGraphDeclaration.create_binding requires non-empty class_name"
        )

    expected_binding_id = stable_object_projection_graph_binding_id(
        object_projection_graph_declaration_id=declaration_id,
        fqn_prefix=normalized_fqn_prefix,
        namespace=normalized_namespace,
        class_name=normalized_class_name,
    )
    if (
        object_projection_graph_binding_id is not None
        and object_projection_graph_binding_id != expected_binding_id
    ):
        raise RuntimeError(
            "ObjectProjectionGraphDeclaration.create_binding "
            "object_projection_graph_binding_id does not match deterministic "
            "stable-id for (declaration, fqn_prefix, namespace, class_name): "
            f"provided={object_projection_graph_binding_id} "
            f"expected={expected_binding_id}"
        )

    if object_projection_graph_declaration.object_projection_graph_bindings is None:
        object_projection_graph_declaration.object_projection_graph_bindings = []
    for (
        existing
    ) in object_projection_graph_declaration.object_projection_graph_bindings:
        if existing.id != expected_binding_id:
            continue
        if (
            existing.object_projection_graph_declaration_id != declaration_id
            or existing.fqn_prefix != normalized_fqn_prefix
            or existing.namespace != normalized_namespace
            or existing.class_name != normalized_class_name
            or (existing.attribute_name or None) != (attribute_name or None)
            or (existing.target_projection_name or None)
            != (target_projection_name or None)
            or (existing.side or None) != (side or None)
        ):
            raise RuntimeError(
                "ObjectProjectionGraphDeclaration.create_binding payload mismatch "
                "for existing ObjectProjectionGraphBinding: "
                f"object_projection_graph_binding_id={expected_binding_id}"
            )
        return existing

    created = ObjectProjectionGraphBinding(
        id=expected_binding_id,
        object_projection_graph_declaration_id=declaration_id,
        fqn_prefix=normalized_fqn_prefix,
        namespace=normalized_namespace,
        class_name=normalized_class_name,
        attribute_name=attribute_name,
        target_projection_name=target_projection_name,
        side=side,
    )
    object_projection_graph_declaration.object_projection_graph_bindings.append(created)
    return created
    # --- AWARE: LOGIC END create_binding

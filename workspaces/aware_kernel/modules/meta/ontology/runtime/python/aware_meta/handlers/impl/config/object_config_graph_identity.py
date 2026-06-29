from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_identity import ObjectConfigGraphIdentity
from aware_meta_ontology.graph.projection.object_projection_graph_identity import ObjectProjectionGraphIdentity

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Runtime
from aware_meta.graph.config.stable_ids import stable_object_config_graph_identity_id

# ORM
from aware_orm.session.execution_guard import allow_domain_create

# --- AWARE: USER_IMPORTS END


async def create(key: str, label: str | None = None) -> ObjectConfigGraphIdentity:
    """
    Create deterministic ObjectConfigGraphIdentity from semantic key only.
    """

    # --- AWARE: LOGIC START create
    object_config_graph_identity_id = stable_object_config_graph_identity_id(key=key)
    return ObjectConfigGraphIdentity(
        id=object_config_graph_identity_id,
        key=key,
        label=label,
    )
    # --- AWARE: LOGIC END create


async def create_object_projection_graph_identity(
    object_config_graph_identity: ObjectConfigGraphIdentity,
    object_projection_graph_id: UUID,
    projection_name: str,
    label: str | None = None,
) -> ObjectProjectionGraphIdentity:
    """
    Create deterministic ObjectProjectionGraphIdentity under this ObjectConfigGraphIdentity.
    """

    # --- AWARE: LOGIC START create_object_projection_graph_identity
    parent_id = object_config_graph_identity.id
    if parent_id is None:
        raise RuntimeError("ObjectConfigGraphIdentity.create_object_projection_graph_identity requires id")

    with allow_domain_create():
        created = await ObjectProjectionGraphIdentity.create_via_object_config_graph_identity(
            object_config_graph_identity_id=parent_id,
            object_projection_graph_id=object_projection_graph_id,
            projection_name=projection_name,
            label=label,
        )
    current = list(object_config_graph_identity.object_projection_graph_identities)
    for existing in current:
        if existing.id != created.id:
            continue
        if label is not None and existing.label != label:
            existing.label = label
        return existing
    current.append(created)
    object_config_graph_identity.object_projection_graph_identities = current
    return created
    # --- AWARE: LOGIC END create_object_projection_graph_identity

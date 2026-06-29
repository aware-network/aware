from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity
from aware_meta_ontology.graph.projection.object_projection_graph_identity import ObjectProjectionGraphIdentity
from aware_meta_ontology.graph.projection.object_projection_graph_observable import ObjectProjectionGraphObservable

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# ORM
from aware_orm.session.execution_guard import allow_domain_create

# Meta Ontology
from aware_meta_ontology.stable_ids import stable_object_projection_graph_identity_id

# Runtime
# --- AWARE: USER_IMPORTS END


async def create_object_instance_graph_identity(
    object_projection_graph_identity: ObjectProjectionGraphIdentity,
    object_instance_graph_id: UUID,
    label: str | None = None,
) -> ObjectInstanceGraphIdentity:
    """
    Create deterministic ObjectInstanceGraphIdentity under this ObjectProjectionGraphIdentity.
    """

    # --- AWARE: LOGIC START create_object_instance_graph_identity
    parent_id = object_projection_graph_identity.id
    if parent_id is None:
        raise RuntimeError(
            "ObjectProjectionGraphIdentity.create_object_instance_graph_identity requires "
            "ObjectProjectionGraphIdentity.id"
        )

    with allow_domain_create():
        created = await ObjectInstanceGraphIdentity.create_via_object_projection_graph_identity(
            object_projection_graph_identity_id=parent_id,
            object_instance_graph_id=object_instance_graph_id,
            label=label,
        )
    current = list(object_projection_graph_identity.object_instance_graph_identities)
    for existing in current:
        if existing.id != created.id:
            continue
        if label is not None and existing.label != label:
            existing.label = label
        return existing
    current.append(created)
    object_projection_graph_identity.object_instance_graph_identities = current
    return created
    # --- AWARE: LOGIC END create_object_instance_graph_identity


async def create_observable(
    object_projection_graph_identity: ObjectProjectionGraphIdentity,
    observable_key: str,
    key: str,
    kind: str | None = None,
    label: str | None = None,
    description: str | None = None,
    position: int | None = None,
    is_default: bool = False,
) -> ObjectProjectionGraphObservable:
    """
    Creates (or ensures) a new ObjectProjectionGraphObservable under this identity.

    Contract:
    - `ObjectProjectionGraphObservable.id` is deterministic for `(self.id, observable_key)`.
    - `ObjectProjectionGraphObservable.key` is the caller-materialized canonical key:
      "{projection_name}:{observable_key}".
    """

    # --- AWARE: LOGIC START create_observable
    with allow_domain_create():
        observable = await ObjectProjectionGraphObservable.create_via_object_projection_graph_identity(
            object_projection_graph_identity_id=object_projection_graph_identity.id,
            observable_key=observable_key,
            key=key,
            kind=kind,
            label=label,
            description=description,
            position=position or 0,
            is_default=is_default,
        )
    current = list(object_projection_graph_identity.object_projection_graph_observables)
    for existing in current:
        if existing.id == observable.id:
            return existing
    if observable.key not in [o.key for o in current]:
        current.append(observable)
        object_projection_graph_identity.object_projection_graph_observables = current
    return observable
    # --- AWARE: LOGIC END create_observable


async def create_via_object_config_graph_identity(
    object_config_graph_identity_id: UUID,
    object_projection_graph_id: UUID,
    projection_name: str,
    label: str | None = None,
) -> ObjectProjectionGraphIdentity:
    """
    Create deterministic ObjectProjectionGraphIdentity for one stable OPG payload.

    Contract:
    - Identity resolves from `(object_config_graph_identity_id via path, object_projection_graph_id)`.
    - `object_projection_graph` is the boundary pointer to the stable payload and must not be
      traversed inside the identity projection payload.
    """

    # --- AWARE: LOGIC START create_via_object_config_graph_identity
    object_projection_graph_identity_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=object_config_graph_identity_id,
        object_projection_graph_id=object_projection_graph_id,
    )
    return ObjectProjectionGraphIdentity(
        id=object_projection_graph_identity_id,
        object_config_graph_identity_id=object_config_graph_identity_id,
        object_projection_graph_id=object_projection_graph_id,
        projection_name=projection_name,
        label=label,
    )
    # --- AWARE: LOGIC END create_via_object_config_graph_identity

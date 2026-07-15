from __future__ import annotations

from uuid import UUID

# Identity Ontology
from aware_identity_ontology.actor.actor import Actor
from aware_identity_ontology.actor.actor_enums import ActorType

# Meta Runtime
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.handler_context import (
    current_handler_index,
)
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model


def _resolve_identity_opg(index: MetaGraphRuntimeIndex) -> ObjectProjectionGraph | None:
    projection_name = "identity"
    return next(
        (
            opg
            for opg in index.opg_by_hash.values()
            if (opg.name or "").strip().casefold() == projection_name
        ),
        None,
    )


def _coerce_actor_type(value: object) -> ActorType | None:
    if isinstance(value, ActorType):
        return value
    if isinstance(value, str):
        try:
            return ActorType(value.strip())
        except Exception:
            return None
    return None


async def resolve_actor_type_canonical(
    *, actor_id: UUID, identity_id: UUID
) -> ActorType | None:
    """
    Resolve Actor.type from one canonical identity lane.

    Contract:
    - Commit addressed only: `(branch_id=identity_id, projection_hash=identity)`.
    - No projection-wide lane scans.
    - No ontology read function invocation.
    """
    index = current_handler_index()
    identity_opg = _resolve_identity_opg(index=index)
    if identity_opg is None:
        return None

    head = await FSCommitStore().head(
        branch_id=identity_id,
        projection_hash=identity_opg.projection_hash,
    )
    if head is None or not head.get("commit_id"):
        return None

    commit_id = UUID(str(head["commit_id"]))
    oig_id = (
        UUID(str(head["object_instance_graph_id"]))
        if head.get("object_instance_graph_id")
        else None
    )
    oig, _ = await CachedLaneMaterializer().get(
        branch_id=identity_id,
        ocg=index.ocg,
        opg=identity_opg,
        commit_id=commit_id,
        oig_id=oig_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    actor = reify_oig_root_model(
        index=index,
        opg=identity_opg,
        oig=oig,
        model_type=Actor,
        root_id=actor_id,
        branch_id=identity_id,
    )
    if actor is None or actor.identity_id != identity_id:
        return None
    return _coerce_actor_type(actor.type)


__all__ = ["resolve_actor_type_canonical"]

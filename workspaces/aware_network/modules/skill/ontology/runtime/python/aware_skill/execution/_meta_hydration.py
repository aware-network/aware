from __future__ import annotations

from uuid import UUID

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_orm.session.session import Session


async def hydrate_committed_lane_session(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    error_context: str,
) -> Session:
    target_head = await FSCommitStore().head(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        raise RuntimeError(f"{error_context} requires a committed lane head.")

    return await hydrate_oig_commit_session(
        index=index,
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
        commit_id=UUID(str(target_head["commit_id"])),
        object_instance_graph_id=(
            UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        error_context=error_context,
    )


async def hydrate_oig_commit_session(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    object_instance_graph_id: UUID | None = None,
    error_context: str,
) -> Session:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} could not resolve projection hash {projection_hash!r}."
        )

    oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        oig_id=object_instance_graph_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )


__all__ = [
    "hydrate_committed_lane_session",
    "hydrate_oig_commit_session",
]

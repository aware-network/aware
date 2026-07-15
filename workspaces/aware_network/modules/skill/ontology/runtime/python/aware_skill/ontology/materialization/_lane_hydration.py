from __future__ import annotations

from typing import TypeVar
from uuid import UUID

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_orm.models.orm_model import ORMModel
from aware_orm.session.session import Session


_TOrm = TypeVar("_TOrm", bound=ORMModel)


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

    opg = index.opg_by_hash.get(lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} could not resolve projection hash {lane.projection_hash!r}."
        )

    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=lane.branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(target_head["commit_id"])),
        oig_id=(
            UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )

    return reify_oig_session(
        index=index,
        opg=opg,
        oig=target_oig,
        branch_id=lane.branch_id,
    )


async def hydrate_committed_lane_object(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    orm_class: type[_TOrm],
    object_id: UUID,
    error_context: str,
) -> _TOrm:
    session = await hydrate_committed_lane_session(
        index=index,
        lane=target_lane,
        error_context=error_context,
    )
    obj = session.imap_get(orm_class, object_id)
    if obj is None:
        raise RuntimeError(
            f"{error_context} could not hydrate committed {orm_class.__name__}: {object_id}"
        )
    return obj


__all__ = [
    "hydrate_committed_lane_object",
    "hydrate_committed_lane_session",
]

from __future__ import annotations

from dataclasses import replace
from typing import TypeVar, cast
from uuid import UUID

from aware_meta.graph.instance.commit.fs_store import FSCommitStore, FSSnapshotStore
from aware_meta.graph.instance.commit.materialization_cache import CachedLaneMaterializer
from aware_meta.runtime.graph_context import MetaGraphRuntimeIndexSnapshot
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_orm.models.orm_model import ORMModel


_TRoot = TypeVar("_TRoot", bound=ORMModel)


async def reify_meta_orm_root_from_oig_commit(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    branch_id: UUID,
    projection_hash: str,
    projection_name: str,
    commit_id: UUID,
    root_id: UUID,
    root_type: type[_TRoot],
    commit_store: FSCommitStore,
    snapshot_store: FSSnapshotStore,
) -> _TRoot | None:
    opg = _projection_graph_for_hash_or_name(
        index=index,
        projection_hash=projection_hash,
        projection_name=projection_name,
    )
    if opg is None:
        raise RuntimeError(
            "Meta OIG hydration missing projection hash: "
            f"projection_name={projection_name!r} projection_hash={projection_hash}"
        )
    resolved_opg = cast(ObjectProjectionGraph, opg)
    oig, _ = await CachedLaneMaterializer(
        commits=commit_store,
        snaps=snapshot_store,
    ).get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=resolved_opg,
        commit_id=commit_id,
        attribute_configs_by_id=dict(index.attribute_configs_by_id),
        class_configs_by_id=dict(index.class_configs_by_id),
    )
    return reify_oig_root_model(
        index=cast(MetaGraphRuntimeIndex, cast(object, index)),
        opg=resolved_opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=branch_id,
    )


def _projection_graph_for_hash_or_name(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    projection_hash: str,
    projection_name: str,
) -> ObjectProjectionGraph | None:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is not None:
        return opg
    matches = tuple(
        candidate
        for candidate in index.ocg.object_projection_graphs
        if (candidate.name or "").strip() == projection_name
    )
    if len(matches) != 1:
        return None
    candidate = matches[0]
    model_copy = getattr(candidate, "model_copy", None)
    if callable(model_copy):
        return cast(
            ObjectProjectionGraph,
            model_copy(update={"projection_hash": projection_hash}),
        )
    return replace(candidate, projection_hash=projection_hash)


__all__ = [
    "reify_meta_orm_root_from_oig_commit",
]

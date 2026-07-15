from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar
from uuid import UUID

from _meta_runtime_support import (
    build_interface_meta_runtime,
    isolated_meta_aware_root,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime import MetaGraphRuntime
from aware_meta.runtime import (
    find_meta_graph_projection_hash_by_name,
    reify_meta_orm_root_from_oig_commit,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_orm.models.orm_model import ORMModel

_TRoot = TypeVar("_TRoot", bound=ORMModel)


def build_interface_meta_proof_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    return build_interface_meta_runtime(
        repo_root,
        workspace_root=aware_root,
    )


def projection_by_name(
    runtime: MetaGraphRuntime,
    name: str,
) -> ObjectProjectionGraph | None:
    context = runtime.context
    assert context is not None
    return next(
        (opg for opg in context.index.opg_by_hash.values() if (opg.name or "") == name),
        None,
    )


def projection_hash_by_name(
    runtime: MetaGraphRuntime,
    name: str,
) -> str:
    context = runtime.context
    assert context is not None
    return find_meta_graph_projection_hash_by_name(
        index=context.index,
        projection_name=name,
    )


def class_config_by_fqn(
    runtime: MetaGraphRuntime,
    class_fqn: str,
) -> ClassConfig | None:
    context = runtime.context
    assert context is not None
    return next(
        (
            class_config
            for class_config in context.index.class_configs_by_id.values()
            if _class_fqn(class_config) == class_fqn
        ),
        None,
    )


def class_function_names(
    class_config: ClassConfig | None,
) -> tuple[str, ...]:
    if class_config is None:
        return ()
    names: list[str] = []
    for link in class_config.class_config_function_configs:
        function_config = getattr(link, "function_config", None)
        name = getattr(function_config, "name", None)
        if isinstance(name, str):
            names.append(name)
    return tuple(names)


async def rehydrate_lane_root_from_head(
    *,
    runtime: MetaGraphRuntime,
    aware_root: Path,
    branch_id: UUID,
    projection_name: str,
    root_id: UUID,
    root_type: type[_TRoot],
) -> _TRoot:
    context = runtime.context
    assert context is not None
    projection_hash = projection_hash_by_name(runtime, projection_name)
    commit_store = FSCommitStore(root_dir=aware_root)
    head = await commit_store.head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    commit_id = UUID(str(head["commit_id"]))
    root = await reify_meta_orm_root_from_oig_commit(
        index=context.index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        projection_name=projection_name,
        commit_id=commit_id,
        root_id=root_id,
        root_type=root_type,
        commit_store=commit_store,
        snapshot_store=FSSnapshotStore(root_dir=aware_root),
    )
    assert root is not None
    return root


def _class_fqn(class_config: Any) -> str | None:
    value = getattr(class_config, "class_fqn", None)
    return value if isinstance(value, str) else None


__all__ = [
    "build_interface_meta_proof_runtime",
    "class_config_by_fqn",
    "class_function_names",
    "isolated_meta_aware_root",
    "projection_hash_by_name",
    "projection_by_name",
    "rehydrate_lane_root_from_head",
]

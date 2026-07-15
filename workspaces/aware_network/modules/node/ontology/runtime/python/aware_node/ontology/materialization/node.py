from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime.graph_context import MetaGraphRuntimeIndexSnapshot
from aware_meta.runtime.oig_hydration import reify_meta_orm_root_from_oig_commit
from aware_meta.runtime.read_model_provider import (
    read_workspace_meta_runtime_read_model,
)
from aware_node_ontology.node.node_config import NodeConfig
from aware_node_ontology.node.node_package import NodePackage


class _NodeCommittedReadModel(Protocol):
    @property
    def index(self) -> MetaGraphRuntimeIndexSnapshot: ...

    def projection_hash_for_name(self, projection_name: str) -> str: ...


@dataclass(frozen=True, slots=True)
class CommittedNodePackageReadResult:
    branch_id: UUID
    node_package: NodePackage
    head_commit_id: str


async def read_committed_node_package(
    *,
    branch_id: UUID,
    node_package_id: UUID,
    root_dir: Path | None = None,
    repo_root: Path | None = None,
    node_config_id: UUID | None = None,
    node_config_object_instance_graph_commit_id: UUID | None = None,
) -> CommittedNodePackageReadResult:
    read_model = _resolve_node_read_model(root_dir=root_dir, repo_root=repo_root)
    projection_hash = read_model.projection_hash_for_name("NodePackage")
    commit_store = FSCommitStore(root_dir=root_dir)
    snapshot_store = FSSnapshotStore(root_dir=root_dir)
    head = await commit_store.head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        raise RuntimeError(
            "Node committed read-model is missing a committed lane head for "
            f"branch={branch_id} projection=node_package"
        )
    head_commit_id = str(head["commit_id"])
    node_package = await reify_meta_orm_root_from_oig_commit(
        index=read_model.index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        projection_name="NodePackage",
        commit_id=_uuid_from_raw(head["commit_id"]),
        root_id=node_package_id,
        root_type=NodePackage,
        commit_store=commit_store,
        snapshot_store=snapshot_store,
    )
    if node_package is None:
        raise RuntimeError(
            "Node committed read-model could not hydrate NodePackage from lane head: "
            + f"branch={branch_id} node_package_id={node_package_id}"
        )
    package_node_config_id = node_package.node_config_id
    if node_config_id is not None and package_node_config_id != node_config_id:
        raise RuntimeError(
            "Node committed read-model received a NodeConfig id that does not match "
            "the committed NodePackage FK: "
            f"node_package_id={node_package_id} package_node_config_id={package_node_config_id} "
            f"requested_node_config_id={node_config_id}"
        )
    if node_package.node_config is None:
        node_config = await _hydrate_committed_node_config(
            read_model=read_model,
            branch_id=branch_id,
            node_config_id=node_config_id or package_node_config_id,
            root_dir=root_dir,
            commit_store=commit_store,
            snapshot_store=snapshot_store,
            object_instance_graph_commit_id=node_config_object_instance_graph_commit_id,
        )
        if node_config is not None:
            node_package.node_config = node_config
    return CommittedNodePackageReadResult(
        branch_id=branch_id,
        node_package=node_package,
        head_commit_id=head_commit_id,
    )


def read_committed_node_package_sync(
    *,
    branch_id: UUID,
    node_package_id: UUID,
    root_dir: Path | None = None,
    repo_root: Path | None = None,
    node_config_id: UUID | None = None,
    node_config_object_instance_graph_commit_id: UUID | None = None,
) -> CommittedNodePackageReadResult:
    return _run_coroutine_sync(
        read_committed_node_package(
            branch_id=branch_id,
            node_package_id=node_package_id,
            root_dir=root_dir,
            repo_root=repo_root,
            node_config_id=node_config_id,
            node_config_object_instance_graph_commit_id=(
                node_config_object_instance_graph_commit_id
            ),
        )
    )


async def _hydrate_committed_node_config(
    *,
    read_model: _NodeCommittedReadModel,
    branch_id: UUID,
    node_config_id: UUID,
    root_dir: Path | None,
    commit_store: FSCommitStore,
    snapshot_store: FSSnapshotStore,
    object_instance_graph_commit_id: UUID | None,
) -> NodeConfig | None:
    projection_hash = read_model.projection_hash_for_name("NodeConfig")
    commit_id = None
    if object_instance_graph_commit_id is not None:
        commit_id = (
            await commit_store.domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=projection_hash,
                object_instance_graph_commit_id=object_instance_graph_commit_id,
            )
        )
        if commit_id is None:
            legacy_domain_commit = await commit_store.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=object_instance_graph_commit_id,
            )
            if legacy_domain_commit is None:
                raise RuntimeError(
                    "Node committed read-model could not resolve NodeConfig "
                    "ObjectInstanceGraphCommit in the committed workspace root: "
                    f"branch={branch_id} node_config_id={node_config_id} "
                    f"object_instance_graph_commit_id={object_instance_graph_commit_id} "
                    f"root_dir={root_dir}"
                )
            commit_id = object_instance_graph_commit_id
    if commit_id is None:
        head = await commit_store.head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        if head is None or head.get("commit_id") is None:
            return None
        commit_id = _uuid_from_raw(head["commit_id"])

    return await reify_meta_orm_root_from_oig_commit(
        index=read_model.index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        projection_name="NodeConfig",
        commit_id=commit_id,
        root_id=node_config_id,
        root_type=NodeConfig,
        commit_store=commit_store,
        snapshot_store=snapshot_store,
    )


def _uuid_from_raw(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _resolve_node_read_model(
    *,
    root_dir: Path | None,
    repo_root: Path | None = None,
) -> _NodeCommittedReadModel:
    resolved_repo_root = _node_read_model_repo_root(
        root_dir=root_dir,
        repo_root=repo_root,
    )
    return read_workspace_meta_runtime_read_model(
        repo_root=resolved_repo_root,
        aware_root=resolved_repo_root,
        required_projection_names=("NodePackage", "NodeConfig"),
        composite_name="Aware Node Committed Read Model Context",
    )


def _resolve_node_read_model_index(
    *,
    root_dir: Path | None,
    repo_root: Path | None = None,
) -> object:
    return _resolve_node_read_model(root_dir=root_dir, repo_root=repo_root).index


def _node_read_model_repo_root(
    *,
    root_dir: Path | None,
    repo_root: Path | None,
) -> Path:
    if repo_root is not None:
        resolved_repo_root = repo_root.expanduser().resolve()
        if (resolved_repo_root / "modules").is_dir():
            return resolved_repo_root
        raise RuntimeError(
            "Node committed read-model requires repo_root to contain a modules "
            f"directory: {resolved_repo_root}"
        )
    if root_dir is None:
        raise RuntimeError(
            "Node committed read-model requires an explicit repo_root when "
            "root_dir is not a source workspace root."
        )
    resolved = root_dir.expanduser().resolve()
    if (resolved / "modules").is_dir():
        return resolved
    raise RuntimeError(
        "Node committed read-model requires an explicit repo_root with a "
        "modules directory when root_dir is not a source workspace root."
    )


def _run_coroutine_sync(
    coro: Coroutine[object, object, CommittedNodePackageReadResult],
) -> CommittedNodePackageReadResult:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: CommittedNodePackageReadResult | None = None
    error: BaseException | None = None

    def _runner() -> None:
        nonlocal result, error
        try:
            result = asyncio.run(coro)
        except BaseException as exc:  # pragma: no cover - mirrored into caller
            error = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()
    if error is not None:
        raise RuntimeError(str(error)) from error
    if result is None:
        raise RuntimeError(
            "Node committed read-model returned no result on the sync bridge."
        )
    return result

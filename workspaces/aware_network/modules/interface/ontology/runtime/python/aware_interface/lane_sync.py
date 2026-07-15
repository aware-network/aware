from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from aware_interface.commit_materialization import (
    InterfaceCommitMaterializer,
    InterfaceMaterializedLane,
)
from aware_interface.lane_stores import (
    InterfaceLaneStores,
    LocalCommitRecord,
    LocalLaneCommitRecord,
    LocalLaneHeadRecord,
)
from aware_interface.projection_runtime import (
    InterfaceProjectionRuntime,
    InterfaceProjectionRuntimeResult,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


JsonObject = dict[str, object]


class InterfaceRemoteLaneMaterializationLike(Protocol):
    @property
    def branch_id(self) -> str: ...

    @property
    def projection_hash(self) -> str: ...

    @property
    def commit_id(self) -> str: ...

    @property
    def graph_hash_post(self) -> str | None: ...

    @property
    def object_instance_graph_id(self) -> str | None: ...

    @property
    def root_object_id(self) -> str | None: ...

    @property
    def head_version(self) -> int | None: ...

    @property
    def commit_payload(self) -> JsonObject | None: ...


@dataclass(frozen=True, slots=True)
class InterfaceRemoteLaneMaterialization:
    branch_id: str
    projection_hash: str
    commit_id: str
    graph_hash_post: str | None = None
    object_instance_graph_id: str | None = None
    root_object_id: str | None = None
    head_version: int | None = None
    commit_payload: JsonObject | None = None


class InterfaceLaneSyncSource(Protocol):
    async def load_latest(
        self,
        *,
        branch_id: str,
        projection_hash: str,
    ) -> InterfaceRemoteLaneMaterializationLike | None:
        ...

    async def load_commit(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        commit_id: str,
    ) -> InterfaceRemoteLaneMaterializationLike | None:
        ...

    def watch_lane(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        include_initial: bool = True,
    ) -> AsyncIterator[InterfaceRemoteLaneMaterializationLike]:
        ...


@dataclass(frozen=True, slots=True)
class InterfaceLaneSyncResult:
    branch_id: str
    projection_hash: str
    lane_id: str
    head_commit_id: str | None
    previous_head_commit_id: str | None
    fetched_commit_ids: tuple[str, ...] = ()
    advanced: bool = False
    materialized_lane: InterfaceMaterializedLane | None = None
    projection_result: InterfaceProjectionRuntimeResult | None = None

    @property
    def projected(self) -> bool:
        return self.projection_result is not None and self.projection_result.projected


class InterfaceLaneSyncService:
    """Interface-owned lane sync orchestration over committed local backend rails."""

    _source: InterfaceLaneSyncSource
    _stores: InterfaceLaneStores
    _materializer: InterfaceCommitMaterializer
    _projector: InterfaceProjectionRuntime

    def __init__(
        self,
        *,
        source: InterfaceLaneSyncSource,
        stores: InterfaceLaneStores,
        materializer: InterfaceCommitMaterializer,
        projector: InterfaceProjectionRuntime,
    ) -> None:
        self._source = source
        self._stores = stores
        self._materializer = materializer
        self._projector = projector

    async def sync_lane_head(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        lane_id: str,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
        force: bool = False,
    ) -> InterfaceLaneSyncResult:
        latest = await self._source.load_latest(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        if latest is None:
            return InterfaceLaneSyncResult(
                branch_id=branch_id,
                projection_hash=projection_hash,
                lane_id=lane_id,
                head_commit_id=None,
                previous_head_commit_id=None,
                advanced=False,
            )
        return await self.sync_remote_materialization(
            remote=latest,
            lane_id=lane_id,
            ocg=ocg,
            opg=opg,
            force=force,
        )

    async def sync_remote_materialization(
        self,
        *,
        remote: InterfaceRemoteLaneMaterializationLike,
        lane_id: str,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
        force: bool = False,
    ) -> InterfaceLaneSyncResult:
        remote = _coerce_remote_materialization(remote=remote)
        branch_id = remote.branch_id
        projection_hash = remote.projection_hash

        existing_head = await self._stores.load_lane_head(
            branch_id=branch_id,
            lane_id=lane_id,
            projection_hash=projection_hash,
        )
        previous_head_commit_id = existing_head.head_commit_id if existing_head is not None else None
        local_target_commit = await self._stores.load_commit(
            branch_id=branch_id,
            commit_id=remote.commit_id,
            projection_hash=projection_hash,
        )
        if (
            not force
            and existing_head is not None
            and existing_head.head_commit_id == remote.commit_id
            and local_target_commit is not None
        ):
            return InterfaceLaneSyncResult(
                branch_id=branch_id,
                projection_hash=projection_hash,
                lane_id=lane_id,
                head_commit_id=remote.commit_id,
                previous_head_commit_id=previous_head_commit_id,
                advanced=False,
            )

        fetched_commit_ids = await self._ensure_commit_lineage(remote=remote)
        persisted_target = await self._stores.load_commit(
            branch_id=branch_id,
            commit_id=remote.commit_id,
            projection_hash=projection_hash,
        )
        if persisted_target is None:
            raise ValueError(
                "Interface lane sync could not persist target commit: "
                + f"branch_id={branch_id} projection_hash={projection_hash} commit_id={remote.commit_id}"
            )

        await self._stores.save_lane_head(
            LocalLaneHeadRecord(
                id=lane_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                head_commit_id=remote.commit_id,
                graph_hash_post=remote.graph_hash_post or persisted_target.graph_hash_post,
                object_instance_graph_id=remote.object_instance_graph_id or persisted_target.object_instance_graph_id,
                root_object_instance_id=remote.root_object_id,
                v=_next_lane_head_version(existing=existing_head, head_commit_id=remote.commit_id),
            )
        )

        materialized_lane = await self._materializer.materialize_lane_head(
            branch_id=branch_id,
            projection_hash=projection_hash,
            lane_id=lane_id,
            ocg=ocg,
            opg=opg,
        )
        projection_result = await self._projector.project_materialized_lane(
            branch_id=branch_id,
            materialized_lane=materialized_lane,
        )
        return InterfaceLaneSyncResult(
            branch_id=branch_id,
            projection_hash=projection_hash,
            lane_id=lane_id,
            head_commit_id=remote.commit_id,
            previous_head_commit_id=previous_head_commit_id,
            fetched_commit_ids=fetched_commit_ids,
            advanced=(
                previous_head_commit_id != remote.commit_id
                or bool(fetched_commit_ids)
                or projection_result.projected
            ),
            materialized_lane=materialized_lane,
            projection_result=projection_result,
        )

    async def watch_lane(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        lane_id: str,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
        include_initial: bool = True,
        force: bool = False,
    ) -> AsyncIterator[InterfaceLaneSyncResult]:
        async for remote in self._source.watch_lane(
            branch_id=branch_id,
            projection_hash=projection_hash,
            include_initial=include_initial,
        ):
            yield await self.sync_remote_materialization(
                remote=remote,
                lane_id=lane_id,
                ocg=ocg,
                opg=opg,
                force=force,
            )

    async def _ensure_commit_lineage(
        self,
        *,
        remote: InterfaceRemoteLaneMaterialization,
    ) -> tuple[str, ...]:
        branch_id = remote.branch_id
        projection_hash = remote.projection_hash
        pending: list[ObjectInstanceGraphCommit] = []
        seen_commit_ids: set[str] = set()
        current = remote

        while True:
            current_commit_id = current.commit_id
            if current_commit_id in seen_commit_ids:
                raise ValueError(
                    "Interface lane sync detected a cyclic remote lineage: "
                    + f"branch_id={branch_id} projection_hash={projection_hash} commit_id={current_commit_id}"
                )
            seen_commit_ids.add(current_commit_id)

            existing = await self._stores.load_commit(
                branch_id=branch_id,
                commit_id=current_commit_id,
                projection_hash=projection_hash,
            )
            if existing is not None:
                break

            current = await self._ensure_remote_commit_payload(current=current)
            commit = _remote_commit_from_payload(current=current)
            pending.append(commit)

            parent_commit_id = _parent_commit_id(commit=commit)
            if parent_commit_id is None:
                break

            parent_record = await self._stores.load_commit(
                branch_id=branch_id,
                commit_id=parent_commit_id,
                projection_hash=projection_hash,
            )
            if parent_record is not None:
                break

            parent_remote = await self._source.load_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=parent_commit_id,
            )
            if parent_remote is None:
                raise ValueError(
                    "Interface lane sync missing parent commit during lineage backfill: "
                    + f"branch_id={branch_id} projection_hash={projection_hash} "
                    + f"commit_id={current_commit_id} parent_commit_id={parent_commit_id}"
                )
            current = _coerce_remote_materialization(remote=parent_remote)

        fetched_commit_ids: list[str] = []
        for commit in reversed(pending):
            commit_id = str(commit.commit.id)
            await self._stores.save_commit(
                _commit_record_from_commit(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit=commit,
                )
            )
            await self._stores.save_lane_commit(
                LocalLaneCommitRecord(
                    id=commit_id,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                )
            )
            fetched_commit_ids.append(commit_id)

        return tuple(fetched_commit_ids)

    async def _ensure_remote_commit_payload(
        self,
        *,
        current: InterfaceRemoteLaneMaterialization,
    ) -> InterfaceRemoteLaneMaterialization:
        if current.commit_payload is not None:
            return current
        fetched = await self._source.load_commit(
            branch_id=current.branch_id,
            projection_hash=current.projection_hash,
            commit_id=current.commit_id,
        )
        if fetched is None or fetched.commit_payload is None:
            raise ValueError(
                "Interface lane sync source could not resolve commit payload: "
                + f"branch_id={current.branch_id} projection_hash={current.projection_hash} "
                + f"commit_id={current.commit_id}"
            )
        return _coerce_remote_materialization(remote=fetched)


def _remote_commit_from_payload(*, current: InterfaceRemoteLaneMaterialization) -> ObjectInstanceGraphCommit:
    payload = current.commit_payload
    if payload is None:
        raise ValueError("Interface lane sync requires commit payload for remote materialization")
    commit = ObjectInstanceGraphCommit.model_validate(payload)
    commit_id = str(commit.commit.id)
    if commit_id != current.commit_id:
        raise ValueError(
            "Interface lane sync commit id mismatch between remote head and payload: "
            + f"remote={current.commit_id} payload={commit_id}"
        )
    payload_projection_hash = str(commit.projection_hash or "")
    if payload_projection_hash != current.projection_hash:
        raise ValueError(
            "Interface lane sync projection hash mismatch between remote head and payload: "
            + f"remote={current.projection_hash} payload={payload_projection_hash}"
        )
    return commit


def _parent_commit_id(*, commit: ObjectInstanceGraphCommit) -> str | None:
    parents = commit.commit.commit_parents
    if not parents:
        return None
    return str(parents[0].parent_commit_id)


def _commit_record_from_commit(
    *,
    branch_id: str,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
) -> LocalCommitRecord:
    payload_json = json.dumps(
        commit.model_dump(mode="json", exclude_none=True),
        sort_keys=True,
        separators=(",", ":"),
    )
    return LocalCommitRecord(
        branch_id=branch_id,
        id=str(commit.commit.id),
        commit_id=str(commit.commit.id),
        projection_hash=projection_hash,
        parent_commit_id=_parent_commit_id(commit=commit),
        graph_hash_pre=str(commit.graph_hash_pre or ""),
        graph_hash_post=str(commit.graph_hash_post or ""),
        object_instance_graph_id=str(commit.object_instance_graph_id),
        object_instance_graph_commit_id=str(commit.id),
        payload_json=payload_json,
    )


def _next_lane_head_version(
    *,
    existing: LocalLaneHeadRecord | None,
    head_commit_id: str,
) -> int:
    if existing is None:
        return 1
    if existing.head_commit_id == head_commit_id:
        return existing.v
    return existing.v + 1


def _coerce_remote_materialization(
    *,
    remote: InterfaceRemoteLaneMaterializationLike,
) -> InterfaceRemoteLaneMaterialization:
    return InterfaceRemoteLaneMaterialization(
        branch_id=str(remote.branch_id),
        projection_hash=str(remote.projection_hash),
        commit_id=str(remote.commit_id),
        graph_hash_post=remote.graph_hash_post,
        object_instance_graph_id=(
            str(remote.object_instance_graph_id)
            if remote.object_instance_graph_id is not None
            else None
        ),
        root_object_id=(
            str(remote.root_object_id) if remote.root_object_id is not None else None
        ),
        head_version=remote.head_version,
        commit_payload=dict(remote.commit_payload) if remote.commit_payload is not None else None,
    )


__all__ = [
    "InterfaceLaneSyncResult",
    "InterfaceLaneSyncService",
    "InterfaceLaneSyncSource",
    "InterfaceRemoteLaneMaterialization",
]

from __future__ import annotations

from collections.abc import Mapping
from typing import cast
from uuid import UUID

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
    MaterializedLaneSnapshot,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex


def _parse_uuid(
    *,
    value: object,
    field_name: str,
    projection_hash: str,
) -> UUID:
    try:
        return UUID(str(value))
    except Exception as exc:
        raise ValueError(
            "Program lane materialization received invalid UUID "
            + f"for {field_name} on projection_hash={projection_hash!r}: {value!r}"
        ) from exc


class ProgramLaneMaterializedReader:
    """
    Canonical program decode lane reader.

    Responsibilities:
    - Resolve lane HEAD metadata (commit_id/object_instance_graph_id) per projection.
    - Materialize lane snapshots via CachedLaneMaterializer (single runtime rail).
    - Deduplicate per-decode materialization requests by projection hash.
    """

    def __init__(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        branch_id: UUID,
        commit_store: FSCommitStore | None = None,
        materializer: CachedLaneMaterializer | None = None,
    ) -> None:
        self._index: MetaGraphRuntimeIndex = index
        self._branch_id: UUID = branch_id
        self._commit_store: FSCommitStore = commit_store or FSCommitStore()
        self._materializer: CachedLaneMaterializer = (
            materializer or CachedLaneMaterializer()
        )
        self._materialized_projection_hashes: set[str] = set()

    async def ensure_projection_lanes_materialized_by_ids(
        self,
        *,
        projection_ids: set[UUID],
    ) -> tuple[MaterializedLaneSnapshot, ...]:
        snapshots: list[MaterializedLaneSnapshot] = []
        for projection_id in sorted(projection_ids, key=str):
            snapshot = await self.ensure_projection_lane_materialized_by_id(
                projection_id=projection_id,
            )
            if snapshot is not None:
                snapshots.append(snapshot)
        return tuple(snapshots)

    async def ensure_projection_lane_materialized_by_id(
        self,
        *,
        projection_id: UUID,
    ) -> MaterializedLaneSnapshot | None:
        projection = self._index.opg_by_id.get(projection_id)
        if projection is None:
            raise ValueError(
                "Program lane materialization references unknown projection_id in runtime index: "
                + f"{projection_id}"
            )
        return await self.ensure_projection_lane_materialized(projection=projection)

    async def ensure_projection_lane_materialized(
        self,
        *,
        projection: ObjectProjectionGraph,
    ) -> MaterializedLaneSnapshot | None:
        projection_hash = (projection.projection_hash or "").strip()
        if not projection_hash:
            raise ValueError(
                "Program lane materialization requires projection_hash on ObjectProjectionGraph"
            )
        if projection_hash in self._materialized_projection_hashes:
            return None

        head_payload_raw = await self._commit_store.head(
            branch_id=self._branch_id,
            projection_hash=projection_hash,
        )
        if not isinstance(head_payload_raw, Mapping):
            self._materialized_projection_hashes.add(projection_hash)
            return None
        head_payload = cast(Mapping[str, object], head_payload_raw)
        commit_id_raw = head_payload.get("commit_id")
        if commit_id_raw is None:
            self._materialized_projection_hashes.add(projection_hash)
            return None
        commit_id = _parse_uuid(
            value=commit_id_raw,
            field_name="commit_id",
            projection_hash=projection_hash,
        )
        object_instance_graph_id_raw = head_payload.get("object_instance_graph_id")
        object_instance_graph_id: UUID | None
        if object_instance_graph_id_raw is None:
            object_instance_graph_id = None
        else:
            object_instance_graph_id = _parse_uuid(
                value=object_instance_graph_id_raw,
                field_name="object_instance_graph_id",
                projection_hash=projection_hash,
            )

        snapshot = await self._materializer.get(
            branch_id=self._branch_id,
            ocg=self._index.ocg,
            opg=projection,
            commit_id=commit_id,
            oig_id=object_instance_graph_id,
            attribute_configs_by_id=self._index.attribute_configs_by_id,
            class_configs_by_id=self._index.class_configs_by_id,
        )
        self._materialized_projection_hashes.add(projection_hash)
        return snapshot


__all__ = ["ProgramLaneMaterializedReader"]

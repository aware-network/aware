from __future__ import annotations

from collections.abc import Mapping
from collections import OrderedDict
from dataclasses import dataclass
import os
from pathlib import Path
from threading import Lock
from typing import Any, cast
from uuid import UUID
from weakref import WeakSet

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit.contract import (
    LaneHeadCommitReceipt,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


def _env_int(name: str, default: int, *, minimum: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except Exception:
        return default
    return value if value >= minimum else default


LaneKey = tuple[UUID, str]
MaterializedLaneSnapshot = tuple[ObjectInstanceGraph, dict[str, Any]]
COMMIT_STATE_HASH_INDEX_KEY = "commit_state_hash"
COMMIT_STATE_INDEX_KEY = "commit_state_index"


@dataclass(frozen=True, slots=True)
class MaterializationCacheKey:
    branch_id: UUID
    projection_hash: str
    store_authority: str
    commit_id: UUID | None
    object_instance_graph_id: UUID | None = None

    def __post_init__(self) -> None:
        normalized_projection_hash = str(self.projection_hash or "").strip()
        if not normalized_projection_hash:
            raise ValueError("MaterializationCacheKey requires projection_hash")
        object.__setattr__(self, "projection_hash", normalized_projection_hash)
        normalized_store_authority = str(self.store_authority or "").strip()
        if not normalized_store_authority:
            raise ValueError("MaterializationCacheKey requires store_authority")
        object.__setattr__(self, "store_authority", normalized_store_authority)

    @property
    def lane_key(self) -> LaneKey:
        return (self.branch_id, self.projection_hash)


@dataclass(frozen=True, slots=True)
class _MaterializationCacheEntry:
    revision: int
    snapshot: MaterializedLaneSnapshot


class SharedMaterializationCache:
    """Shared, bounded cache for commit/materialized lane snapshots.

    Truth remains commit/store materialization. This cache is derived and fail-closed:
    lane HEAD changes invalidate lane entries immediately via commit-store watchers.
    """

    _lane_revision_lock = Lock()
    _lane_revision_by_key: dict[LaneKey, int] = {}

    _watcher_registration_lock = Lock()
    _watcher_registered: bool = False

    _instances_lock = Lock()
    _instances: WeakSet["SharedMaterializationCache"] = WeakSet()

    def __init__(self, *, max_entries: int | None = None) -> None:
        self._ensure_lane_head_watcher_registered()
        self._cache: OrderedDict[
            MaterializationCacheKey,
            _MaterializationCacheEntry,
        ] = OrderedDict()
        self._cache_lock = Lock()
        self._cache_max_entries = (
            max_entries
            if max_entries is not None
            else _env_int(
                "AWARE_RUNTIME_MATERIALIZATION_CACHE_MAX_ENTRIES",
                2048,
                minimum=64,
            )
        )
        self._cache_hit_count = 0
        self._cache_miss_count = 0
        self._cache_store_count = 0
        self._cache_stale_evict_count = 0
        self._cache_lru_evict_count = 0
        self._cache_invalidation_evict_count = 0

        with self._instances_lock:
            self._instances.add(self)

    @classmethod
    def _current_lane_revision(cls, lane_key: LaneKey) -> int:
        with cls._lane_revision_lock:
            return int(cls._lane_revision_by_key.get(lane_key, 0))

    @classmethod
    def _bump_lane_revision(cls, lane_key: LaneKey) -> int:
        with cls._lane_revision_lock:
            next_revision = int(cls._lane_revision_by_key.get(lane_key, 0)) + 1
            cls._lane_revision_by_key[lane_key] = next_revision
            return next_revision

    @classmethod
    def _invalidate_lane_global(cls, *, lane_key: LaneKey) -> None:
        cls._bump_lane_revision(lane_key)
        with cls._instances_lock:
            instances = tuple(cls._instances)
        for instance in instances:
            instance._evict_lane_entries(lane_key=lane_key)

    @classmethod
    def _lane_head_commit_watcher(cls, receipt: LaneHeadCommitReceipt) -> None:
        projection_hash = str(getattr(receipt, "projection_hash", "") or "").strip()
        branch_id = getattr(receipt, "branch_id", None)
        if not projection_hash or not isinstance(branch_id, UUID):
            return
        cls._invalidate_lane_global(lane_key=(branch_id, projection_hash))

    @classmethod
    def _ensure_lane_head_watcher_registered(cls) -> None:
        with cls._watcher_registration_lock:
            if cls._watcher_registered:
                return
            FSCommitStore.register_lane_head_watcher(cls._lane_head_commit_watcher)
            cls._watcher_registered = True

    def current_lane_revision(self, *, branch_id: UUID, projection_hash: str) -> int:
        lane_key = (branch_id, str(projection_hash or "").strip())
        if not lane_key[1]:
            raise ValueError("current_lane_revision requires projection_hash")
        return self._current_lane_revision(lane_key)

    def invalidate_lane(self, *, branch_id: UUID, projection_hash: str) -> None:
        normalized_projection_hash = str(projection_hash or "").strip()
        if not normalized_projection_hash:
            raise ValueError("invalidate_lane requires projection_hash")
        self._invalidate_lane_global(
            lane_key=(branch_id, normalized_projection_hash),
        )

    def _evict_lane_entries(self, *, lane_key: LaneKey) -> None:
        with self._cache_lock:
            evicted = 0
            for key in tuple(self._cache.keys()):
                if key.lane_key != lane_key:
                    continue
                self._cache.pop(key, None)
                evicted += 1
            self._cache_invalidation_evict_count += evicted

    def get(
        self,
        *,
        cache_key: MaterializationCacheKey,
    ) -> MaterializedLaneSnapshot | object:
        with self._cache_lock:
            entry = self._cache.get(cache_key)
            if entry is None:
                self._cache_miss_count += 1
                return _CACHE_MISS

            current_revision = self._current_lane_revision(cache_key.lane_key)
            if int(entry.revision) != int(current_revision):
                self._cache.pop(cache_key, None)
                self._cache_stale_evict_count += 1
                self._cache_miss_count += 1
                return _CACHE_MISS

            self._cache.move_to_end(cache_key)
            self._cache_hit_count += 1
            return entry.snapshot

    def store(
        self,
        *,
        cache_key: MaterializationCacheKey,
        snapshot: MaterializedLaneSnapshot,
    ) -> None:
        lane_revision = self._current_lane_revision(cache_key.lane_key)
        with self._cache_lock:
            self._cache[cache_key] = _MaterializationCacheEntry(
                revision=int(lane_revision),
                snapshot=snapshot,
            )
            self._cache.move_to_end(cache_key)
            self._cache_store_count += 1
            while len(self._cache) > self._cache_max_entries:
                self._cache.popitem(last=False)
                self._cache_lru_evict_count += 1

    async def get_or_load(
        self,
        *,
        cache_key: MaterializationCacheKey,
        loader,
    ) -> tuple[MaterializedLaneSnapshot, bool]:
        cached_snapshot = self.get(cache_key=cache_key)
        if cached_snapshot is not _CACHE_MISS:
            return cast(MaterializedLaneSnapshot, cached_snapshot), True

        loaded_snapshot = await loader()
        self.store(cache_key=cache_key, snapshot=loaded_snapshot)
        return loaded_snapshot, False

    def snapshot_cache_metrics(self) -> dict[str, int]:
        with self._cache_lock:
            return {
                "cache_hit_count": max(int(self._cache_hit_count), 0),
                "cache_miss_count": max(int(self._cache_miss_count), 0),
                "cache_store_count": max(int(self._cache_store_count), 0),
                "cache_stale_evict_count": max(int(self._cache_stale_evict_count), 0),
                "cache_lru_evict_count": max(int(self._cache_lru_evict_count), 0),
                "cache_invalidation_evict_count": max(
                    int(self._cache_invalidation_evict_count),
                    0,
                ),
                "cache_entry_count": max(int(len(self._cache)), 0),
            }


class CachedLaneMaterializer:
    """Canonical runtime facade for commit/materialization lookups.

    - Delegates truth reads to `OIGMaterializer`.
    - Reuses the shared bounded `SharedMaterializationCache`.
    """

    def __init__(
        self,
        *,
        commits: FSCommitStore | None = None,
        snaps: FSSnapshotStore | None = None,
        materializer: OIGMaterializer | None = None,
        cache: SharedMaterializationCache | None = None,
    ) -> None:
        self._materializer = materializer or OIGMaterializer(
            commits=commits,
            snaps=snaps,
        )
        self._store_authority = _materializer_store_authority(self._materializer)
        self._cache = cache or get_shared_materialization_cache()

    async def get(
        self,
        *,
        branch_id: UUID,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
        commit_id: UUID | None,
        oig_id: UUID | None = None,
        attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
        class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
        timings: Any | None = None,
    ) -> MaterializedLaneSnapshot:
        cache_key = MaterializationCacheKey(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            store_authority=self._store_authority,
            commit_id=commit_id,
            object_instance_graph_id=oig_id,
        )

        async def _load() -> MaterializedLaneSnapshot:
            return await self._materializer.get(
                branch_id=branch_id,
                ocg=ocg,
                opg=opg,
                commit_id=commit_id,
                oig_id=oig_id,
                attribute_configs_by_id=attribute_configs_by_id,
                class_configs_by_id=class_configs_by_id,
                timings=timings,
            )

        trace_metadata = {
            "branch_id": str(branch_id),
            "projection_hash": opg.projection_hash,
            "store_authority": self._store_authority,
            "commit_id": str(commit_id) if commit_id is not None else None,
            "object_instance_graph_id": str(oig_id) if oig_id is not None else None,
        }
        with commit_perf_span(
            phase="oig_materialization_cache.get",
            category="meta.oig.materialization_cache",
            metadata=trace_metadata,
        ):
            snapshot, cache_hit = await self._cache.get_or_load(
                cache_key=cache_key,
                loader=_load,
            )
        with commit_perf_span(
            phase=(
                "oig_materialization_cache.hit"
                if cache_hit
                else "oig_materialization_cache.miss"
            ),
            category="meta.oig.materialization_cache",
            metadata=trace_metadata,
        ):
            pass
        return snapshot

    def prime(
        self,
        *,
        branch_id: UUID,
        opg: ObjectProjectionGraph,
        commit_id: UUID | None,
        oig_id: UUID | None = None,
        graph: ObjectInstanceGraph,
        indexes: dict[str, Any] | None = None,
        commit_state_hash: str | None = None,
        commit_state_index: Any | None = None,
    ) -> None:
        """Prime the shared materialization cache with a just-derived graph.

        This is derived cache state only; lane HEAD watchers still invalidate
        prior entries whenever truth advances through the commit store.
        """
        cache_key = MaterializationCacheKey(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            store_authority=self._store_authority,
            commit_id=commit_id,
            object_instance_graph_id=oig_id,
        )
        trace_metadata = {
            "branch_id": str(branch_id),
            "projection_hash": opg.projection_hash,
            "store_authority": self._store_authority,
            "commit_id": str(commit_id) if commit_id is not None else None,
            "object_instance_graph_id": str(oig_id) if oig_id is not None else None,
            "indexes_source": "provided" if indexes is not None else "built",
            "commit_state_hash_source": ("provided" if commit_state_hash else "absent"),
            "commit_state_index_source": (
                "provided" if commit_state_index is not None else "absent"
            ),
        }
        with commit_perf_span(
            phase="oig_materialization_cache.prime.build_indexes",
            category="meta.oig.materialization_cache",
            metadata=trace_metadata,
        ):
            snapshot_indexes = (
                indexes
                if indexes is not None
                else self._materializer.indexes_from_graph(graph)
            )
            if commit_state_hash:
                snapshot_indexes = {
                    **snapshot_indexes,
                    COMMIT_STATE_HASH_INDEX_KEY: str(commit_state_hash).strip(),
                }
            if commit_state_index is not None:
                snapshot_indexes = {
                    **snapshot_indexes,
                    COMMIT_STATE_INDEX_KEY: commit_state_index,
                }
        with commit_perf_span(
            phase="oig_materialization_cache.prime.store",
            category="meta.oig.materialization_cache",
            metadata=trace_metadata,
        ):
            self._cache.store(
                cache_key=cache_key,
                snapshot=(graph, snapshot_indexes),
            )

    def snapshot_cache_metrics(self) -> dict[str, int]:
        return self._cache.snapshot_cache_metrics()


def _materializer_store_authority(materializer: object) -> str:
    commits = getattr(materializer, "commits", None)
    aware_root = getattr(commits, "aware_root", None)
    if aware_root is not None:
        return Path(aware_root).expanduser().resolve().as_posix()
    materializer_type = type(materializer)
    return (
        f"materializer-instance:{materializer_type.__module__}."
        f"{materializer_type.__qualname__}:{id(materializer)}"
    )


_shared_materialization_cache: SharedMaterializationCache | None = None
_shared_materialization_cache_lock = Lock()


def get_shared_materialization_cache() -> SharedMaterializationCache:
    global _shared_materialization_cache
    if _shared_materialization_cache is not None:
        return _shared_materialization_cache

    with _shared_materialization_cache_lock:
        if _shared_materialization_cache is None:
            _shared_materialization_cache = SharedMaterializationCache()
        return _shared_materialization_cache


_CACHE_MISS = object()


__all__ = [
    "CachedLaneMaterializer",
    "MaterializationCacheKey",
    "SharedMaterializationCache",
    "get_shared_materialization_cache",
]

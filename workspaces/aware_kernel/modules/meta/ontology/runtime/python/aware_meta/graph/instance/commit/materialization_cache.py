from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import os
from threading import Lock
from typing import Any
from uuid import UUID
from weakref import WeakSet

from aware_meta.graph.instance.commit.fs_store import (
    FSCommitStore,
    FSSnapshotStore,
    LaneHeadCommitReceipt,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
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


@dataclass(frozen=True, slots=True)
class MaterializationCacheKey:
    branch_id: UUID
    projection_hash: str
    commit_id: UUID | None
    object_instance_graph_id: UUID | None = None

    def __post_init__(self) -> None:
        normalized_projection_hash = str(self.projection_hash or "").strip()
        if not normalized_projection_hash:
            raise ValueError("MaterializationCacheKey requires projection_hash")
        object.__setattr__(self, "projection_hash", normalized_projection_hash)

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
            return cached_snapshot, True

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
        self._cache = cache or get_shared_materialization_cache()

    async def get(
        self,
        *,
        branch_id: UUID,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
        commit_id: UUID | None,
        oig_id: UUID | None = None,
        attribute_configs_by_id: dict[UUID, AttributeConfig] | None = None,
        class_configs_by_id: dict[UUID, ClassConfig] | None = None,
        timings: Any | None = None,
    ) -> MaterializedLaneSnapshot:
        cache_key = MaterializationCacheKey(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
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

        snapshot, _cache_hit = await self._cache.get_or_load(
            cache_key=cache_key,
            loader=_load,
        )
        return snapshot

    def snapshot_cache_metrics(self) -> dict[str, int]:
        return self._cache.snapshot_cache_metrics()


_SHARED_MATERIALIZATION_CACHE: SharedMaterializationCache | None = None
_SHARED_MATERIALIZATION_CACHE_LOCK = Lock()


def get_shared_materialization_cache() -> SharedMaterializationCache:
    global _SHARED_MATERIALIZATION_CACHE
    if _SHARED_MATERIALIZATION_CACHE is not None:
        return _SHARED_MATERIALIZATION_CACHE

    with _SHARED_MATERIALIZATION_CACHE_LOCK:
        if _SHARED_MATERIALIZATION_CACHE is None:
            _SHARED_MATERIALIZATION_CACHE = SharedMaterializationCache()
        return _SHARED_MATERIALIZATION_CACHE


_CACHE_MISS = object()


__all__ = [
    "CachedLaneMaterializer",
    "MaterializationCacheKey",
    "SharedMaterializationCache",
    "get_shared_materialization_cache",
]

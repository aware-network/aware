from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from aware_meta.graph.instance.commit.contract import LaneHeadCommitReceipt
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit import materialization_cache as cache_module
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


@pytest.mark.asyncio
async def test_shared_materialization_cache_store_hit_and_watcher_invalidate() -> None:
    cache = cache_module.SharedMaterializationCache(max_entries=8)
    branch_id = uuid4()
    projection_hash = f"sha256:test:materialization-cache:{uuid4()}"
    cache_key = cache_module.MaterializationCacheKey(
        branch_id=branch_id,
        projection_hash=projection_hash,
        store_authority="test:first",
        commit_id=uuid4(),
    )
    second_authority_key = cache_module.MaterializationCacheKey(
        branch_id=branch_id,
        projection_hash=projection_hash,
        store_authority="test:second",
        commit_id=cache_key.commit_id,
    )
    first_graph = _make_graph()
    first_snapshot = (first_graph, {"state": "first"})
    cache.store(cache_key=cache_key, snapshot=first_snapshot)
    cache.store(
        cache_key=second_authority_key,
        snapshot=(_make_graph(), {"state": "second-authority"}),
    )

    cached_snapshot, cache_hit = await cache.get_or_load(
        cache_key=cache_key,
        loader=lambda: _load_snapshot((_make_graph(), {"state": "unexpected"})),
    )
    assert cache_hit is True
    assert cached_snapshot == first_snapshot

    cache_module.SharedMaterializationCache._lane_head_commit_watcher(
        LaneHeadCommitReceipt(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
            created_at_unix_ms=0,
            graph_hash_post="hash",
            object_instance_graph_id=uuid4(),
        )
    )

    second_snapshot = (_make_graph(), {"state": "second"})
    loaded_after_invalidate, cache_hit_after_invalidate = await cache.get_or_load(
        cache_key=cache_key,
        loader=lambda: _load_snapshot(second_snapshot),
    )
    assert cache_hit_after_invalidate is False
    assert loaded_after_invalidate == second_snapshot

    metrics = cache.snapshot_cache_metrics()
    assert metrics["cache_hit_count"] >= 1
    assert metrics["cache_store_count"] >= 3
    assert metrics["cache_invalidation_evict_count"] >= 2
    assert metrics["cache_entry_count"] == 1


@pytest.mark.asyncio
async def test_shared_materialization_cache_lru_eviction_is_bounded() -> None:
    cache = cache_module.SharedMaterializationCache(max_entries=2)
    projection_hash = f"sha256:test:lru:{uuid4()}"
    branch_a = uuid4()
    branch_b = uuid4()
    branch_c = uuid4()

    key_a = cache_module.MaterializationCacheKey(
        branch_id=branch_a,
        projection_hash=projection_hash,
        store_authority="test:lru",
        commit_id=uuid4(),
    )
    key_b = cache_module.MaterializationCacheKey(
        branch_id=branch_b,
        projection_hash=projection_hash,
        store_authority="test:lru",
        commit_id=uuid4(),
    )
    key_c = cache_module.MaterializationCacheKey(
        branch_id=branch_c,
        projection_hash=projection_hash,
        store_authority="test:lru",
        commit_id=uuid4(),
    )

    cache.store(cache_key=key_a, snapshot=(_make_graph(), {"k": "a"}))
    cache.store(cache_key=key_b, snapshot=(_make_graph(), {"k": "b"}))
    cache.store(cache_key=key_c, snapshot=(_make_graph(), {"k": "c"}))

    metrics = cache.snapshot_cache_metrics()
    assert metrics["cache_entry_count"] == 2
    assert metrics["cache_lru_evict_count"] >= 1

    _snapshot_a, cache_hit_a = await cache.get_or_load(
        cache_key=key_a,
        loader=lambda: _load_snapshot((_make_graph(), {"k": "a-reloaded"})),
    )
    assert cache_hit_a is False


@pytest.mark.asyncio
async def test_cached_lane_materializer_prime_stores_derived_snapshot(
    tmp_path: Path,
) -> None:
    cache = cache_module.SharedMaterializationCache(max_entries=8)
    branch_id = uuid4()
    commit_id = uuid4()
    oig_id = uuid4()
    projection_hash = f"sha256:test:prime:{uuid4()}"
    opg = ObjectProjectionGraph.model_construct(projection_hash=projection_hash)
    graph = _make_graph(oig_id=oig_id)
    materializer = cache_module.CachedLaneMaterializer(
        commits=FSCommitStore(root_dir=tmp_path),
        snaps=FSSnapshotStore(root_dir=tmp_path),
        cache=cache,
    )

    materializer.prime(
        branch_id=branch_id,
        opg=opg,
        commit_id=commit_id,
        oig_id=oig_id,
        graph=graph,
        indexes={"instance_map": {}, "classcfg_map": {}},
        commit_state_hash="sha256:test:state-hash",
    )

    cache_key = cache_module.MaterializationCacheKey(
        branch_id=branch_id,
        projection_hash=projection_hash,
        store_authority=FSCommitStore(root_dir=tmp_path)
        .aware_root.resolve()
        .as_posix(),
        commit_id=commit_id,
        object_instance_graph_id=oig_id,
    )
    snapshot, cache_hit = await cache.get_or_load(
        cache_key=cache_key,
        loader=lambda: _load_snapshot((_make_graph(), {"state": "unexpected"})),
    )

    assert cache_hit is True
    assert snapshot == (
        graph,
        {
            "instance_map": {},
            "classcfg_map": {},
            cache_module.COMMIT_STATE_HASH_INDEX_KEY: "sha256:test:state-hash",
        },
    )


@pytest.mark.asyncio
async def test_cached_lane_materializer_isolates_shared_cache_by_store_authority(
    tmp_path: Path,
) -> None:
    cache = cache_module.SharedMaterializationCache(max_entries=8)
    branch_id = uuid4()
    oig_id = uuid4()
    projection_hash = f"sha256:test:store-authority:{uuid4()}"
    opg = ObjectProjectionGraph.model_construct(projection_hash=projection_hash)
    ocg = object()
    first_graph = _make_graph(oig_id=oig_id)
    second_graph = _make_graph(oig_id=oig_id)
    first_loader = _RecordingMaterializer(
        commits=FSCommitStore(root_dir=tmp_path / "first"),
        snapshot=(first_graph, {"store": "first"}),
    )
    second_loader = _RecordingMaterializer(
        commits=FSCommitStore(root_dir=tmp_path / "second"),
        snapshot=(second_graph, {"store": "second"}),
    )
    first = cache_module.CachedLaneMaterializer(
        materializer=first_loader,
        cache=cache,
    )
    second = cache_module.CachedLaneMaterializer(
        materializer=second_loader,
        cache=cache,
    )

    first_snapshot = await first.get(
        branch_id=branch_id,
        ocg=ocg,
        opg=opg,
        commit_id=None,
        oig_id=oig_id,
    )
    second_snapshot = await second.get(
        branch_id=branch_id,
        ocg=ocg,
        opg=opg,
        commit_id=None,
        oig_id=oig_id,
    )

    assert first_snapshot == (first_graph, {"store": "first"})
    assert second_snapshot == (second_graph, {"store": "second"})
    assert first_loader.get_call_count == 1
    assert second_loader.get_call_count == 1
    assert cache.snapshot_cache_metrics()["cache_entry_count"] == 2


class _RecordingMaterializer:
    def __init__(self, *, commits: FSCommitStore, snapshot) -> None:
        self.commits = commits
        self._snapshot = snapshot
        self.get_call_count = 0

    async def get(self, **_kwargs):
        self.get_call_count += 1
        return self._snapshot


def _make_graph(*, oig_id=None) -> ObjectInstanceGraph:
    return ObjectInstanceGraph.model_construct(
        id=oig_id or uuid4(),
        class_instances=[],
        class_instance_relationships=[],
    )


async def _load_snapshot(snapshot):
    return snapshot

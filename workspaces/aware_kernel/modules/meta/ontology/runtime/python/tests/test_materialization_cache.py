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
        commit_id=uuid4(),
    )
    first_graph = _make_graph()
    first_snapshot = (first_graph, {"state": "first"})
    cache.store(cache_key=cache_key, snapshot=first_snapshot)

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
    assert metrics["cache_store_count"] >= 2
    assert metrics["cache_invalidation_evict_count"] >= 1


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
        commit_id=uuid4(),
    )
    key_b = cache_module.MaterializationCacheKey(
        branch_id=branch_b,
        projection_hash=projection_hash,
        commit_id=uuid4(),
    )
    key_c = cache_module.MaterializationCacheKey(
        branch_id=branch_c,
        projection_hash=projection_hash,
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
    )

    cache_key = cache_module.MaterializationCacheKey(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_id=oig_id,
    )
    snapshot, cache_hit = await cache.get_or_load(
        cache_key=cache_key,
        loader=lambda: _load_snapshot((_make_graph(), {"state": "unexpected"})),
    )

    assert cache_hit is True
    assert snapshot == (graph, {"instance_map": {}, "classcfg_map": {}})


def _make_graph(*, oig_id=None) -> ObjectInstanceGraph:
    return ObjectInstanceGraph.model_construct(
        id=oig_id or uuid4(),
        class_instances=[],
        class_instance_relationships=[],
    )


async def _load_snapshot(snapshot):
    return snapshot

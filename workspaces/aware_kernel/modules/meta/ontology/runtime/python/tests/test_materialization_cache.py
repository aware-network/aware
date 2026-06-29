from __future__ import annotations

from uuid import uuid4

import pytest

from aware_meta.graph.instance.commit.fs_store import LaneHeadCommitReceipt
from aware_meta.graph.instance.commit import materialization_cache as cache_module


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
    first_snapshot = (object(), {"state": "first"})
    cache.store(cache_key=cache_key, snapshot=first_snapshot)

    cached_snapshot, cache_hit = await cache.get_or_load(
        cache_key=cache_key,
        loader=lambda: _load_snapshot((object(), {"state": "unexpected"})),
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

    second_snapshot = (object(), {"state": "second"})
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

    cache.store(cache_key=key_a, snapshot=(object(), {"k": "a"}))
    cache.store(cache_key=key_b, snapshot=(object(), {"k": "b"}))
    cache.store(cache_key=key_c, snapshot=(object(), {"k": "c"}))

    metrics = cache.snapshot_cache_metrics()
    assert metrics["cache_entry_count"] == 2
    assert metrics["cache_lru_evict_count"] >= 1

    _snapshot_a, cache_hit_a = await cache.get_or_load(
        cache_key=key_a,
        loader=lambda: _load_snapshot((object(), {"k": "a-reloaded"})),
    )
    assert cache_hit_a is False


async def _load_snapshot(snapshot):
    return snapshot

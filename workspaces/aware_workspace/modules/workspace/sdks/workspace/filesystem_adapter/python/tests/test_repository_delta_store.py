from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import perf_counter

import aware_workspace_fs_adapter.repository_delta_store as repository_store
import pytest
from aware_workspace_fs_adapter.repository_delta_store import (
    WorkspaceRepositoryDeltaStore,
)
from aware_workspace_runtime.repository_delta_store_contract import (
    WorkspaceRepositoryDeltaStoreCapacityError,
    WorkspaceRepositoryDeltaStoreCorrupt,
)
from test_repository_delta import BINDING, capture, content_delta


def test_store_deduplicates_bodies_and_publishes_one_batch_index(
    tmp_path: Path,
) -> None:
    store = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path,
    )
    body = b"same body\n"
    refs = store.record_bodies((body, body, body))
    snapshot = store.snapshot()

    assert len(set(refs)) == 1
    assert snapshot.retained_body_count == 1
    assert snapshot.retained_body_bytes == len(body)
    assert snapshot.metrics.body_hash_count == 3
    assert snapshot.metrics.body_write_count == 1
    assert snapshot.metrics.index_write_count == 1
    assert snapshot.metrics.body_read_count == 0

    store.record_body(body)
    repeated = store.snapshot()
    assert repeated.metrics.body_write_count == 1
    assert repeated.metrics.index_write_count == 1


def test_concurrent_contexts_share_one_blob_and_one_transition(tmp_path: Path) -> None:
    before = b"before\n"
    after = b"after\n"
    store = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path,
    )
    store.record_body(before)
    capture_value = capture(body=before)
    store.record_capture(capture_value)

    with ThreadPoolExecutor(max_workers=10) as executor:
        refs = tuple(executor.map(store.record_body, (after,) * 10))
    delta_value = content_delta(capture_value, before=before, after=after)
    with ThreadPoolExecutor(max_workers=10) as executor:
        tuple(executor.map(store.record_delta, (delta_value,) * 10))

    snapshot = store.snapshot()
    assert len(set(refs)) == 1
    assert snapshot.retained_body_count == 2
    assert snapshot.retained_delta_count == 1
    assert snapshot.metrics.body_write_count == 2


def test_capture_and_transition_restart_without_loading_body_bytes(
    tmp_path: Path,
) -> None:
    before = b"before\n"
    after = b"after\n"
    store = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path,
    )
    body_refs = store.record_bodies((before, after))
    capture_value = capture(body=before)
    delta_value = content_delta(capture_value, before=before, after=after)
    store.record_capture(capture_value)
    store.record_delta(delta_value)

    restored = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path,
    )
    startup = restored.snapshot()
    assert startup.retained_body_count == 2
    assert startup.retained_capture_count == 1
    assert startup.retained_delta_count == 1
    assert startup.metrics.body_read_count == 0
    assert startup.metrics.body_hash_count == 0
    assert startup.metrics.index_write_count == 0
    assert restored.resolve_capture(capture_value.capture_ref) == capture_value
    assert restored.resolve_delta(delta_value.delta_ref) == delta_value
    assert restored.resolve_body(body_refs[0]) == before
    assert restored.snapshot().metrics.body_read_count == 1


def test_eviction_removes_blob_but_preserves_retained_transition_metadata(
    tmp_path: Path,
) -> None:
    before = b"before"
    after = b"after!"
    store = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path,
        body_capacity=2,
        maximum_bytes=12,
    )
    old_ref, new_ref = store.record_bodies((before, after))
    capture_value = capture(body=before)
    delta_value = content_delta(capture_value, before=before, after=after)
    store.record_capture(capture_value)
    store.record_delta(delta_value)

    replacement_ref = store.record_body(b"third!")
    assert replacement_ref not in {old_ref, new_ref}
    assert store.resolve_delta(delta_value.delta_ref) == delta_value
    assert sum(store.contains_body(ref) for ref in (old_ref, new_ref)) == 1
    assert store.snapshot().metrics.evicted_body_count == 1


def test_store_rejects_oversized_body_before_writing(tmp_path: Path) -> None:
    store = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path,
        maximum_bytes=4,
    )
    with pytest.raises(WorkspaceRepositoryDeltaStoreCapacityError):
        store.record_body(b"12345")
    snapshot = store.snapshot()
    assert snapshot.retained_body_count == 0
    assert snapshot.metrics.body_write_count == 0
    assert snapshot.metrics.index_write_count == 0


def test_store_rejects_tampered_index_without_reading_blobs(tmp_path: Path) -> None:
    store = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path,
    )
    store.record_body(b"body")
    index_path = store.store_root / "index.json"
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload["repository_binding_ref"] = "repository:other"
    index_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(WorkspaceRepositoryDeltaStoreCorrupt):
        WorkspaceRepositoryDeltaStore(
            repository_binding_ref=BINDING,
            state_root=tmp_path,
        )


def test_64_file_four_mebibyte_batch_meets_locked_io_shape_and_time(
    tmp_path: Path,
) -> None:
    bodies = tuple(
        index.to_bytes(2, "big") + bytes([index]) * (64 * 1024 - 2)
        for index in range(64)
    )
    store = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path,
        body_capacity=64,
        maximum_bytes=4 * 1024 * 1024,
    )
    started = perf_counter()
    store.record_bodies(bodies)
    elapsed_milliseconds = (perf_counter() - started) * 1000
    snapshot = store.snapshot()

    assert snapshot.retained_body_count == 64
    assert snapshot.retained_body_bytes == 4 * 1024 * 1024
    assert snapshot.metrics.body_hash_count == 64
    assert snapshot.metrics.body_write_count == 64
    assert snapshot.metrics.body_write_bytes == 4 * 1024 * 1024
    assert snapshot.metrics.index_write_count == 1
    assert snapshot.metrics.body_read_count == 0
    assert elapsed_milliseconds <= 250


def test_optional_repository_performance_probe_counts_body_resolution(tmp_path: Path):
    events = []

    class Probe:
        def record(self, **event):
            events.append(event)

    store = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path,
    )
    body_ref = store.record_body(b"body")
    token = repository_store.set_performance_probe(Probe())
    try:
        assert store.resolve_body(body_ref) == b"body"
    finally:
        repository_store.reset_performance_probe(token)

    assert events == [
        {
            "kind": "counter",
            "name": "workspace.retained_body_resolution",
            "amount": 1,
        }
    ]

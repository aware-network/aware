"""Original body/capture/delta values through fresh v1 and v2 representations."""

from __future__ import annotations

import pytest
from aware_workspace_fs_adapter.repository_delta_store import (
    WorkspaceRepositoryDeltaStore,
)
from test_repository_delta import BINDING, capture, content_delta


def test_v2_full_original_body_capture_delta_restart_matches_v1(tmp_path):
    before, after = b"original\n", b"successor\n"
    stores = [
        WorkspaceRepositoryDeltaStore(
            repository_binding_ref=BINDING,
            state_root=tmp_path / format,
            index_format=format,
        )
        for format in ("json_v1", "events_v2")
    ]
    value = capture(body=before)
    delta = content_delta(value, before=before, after=after)
    for store in stores:
        store.record_bodies((before, after))
        store.record_capture(value)
        store.record_delta(delta)
    assert stores[1]._index_journal.read() == stores[0]._index_path.read_bytes()
    reopened = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path / "events_v2",
        index_format="auto",
    )
    assert reopened.retained_captures() == (value,)
    assert reopened.retained_deltas() == (delta,)
    assert reopened.resolve_body(delta.old_body_ref) == before
    assert reopened.resolve_body(delta.new_body_ref) == after
    assert reopened.snapshot().metrics.body_read_count == 2
    assert not reopened._index_path.exists()
    default_reader = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=BINDING,
        state_root=tmp_path / "events_v2",
    )
    assert default_reader.retained_deltas() == (delta,)


def test_v2_old_body_metadata_freshly_serialized_and_evicted(tmp_path):
    stores = [
        WorkspaceRepositoryDeltaStore(
            repository_binding_ref=BINDING,
            state_root=tmp_path / format,
            body_capacity=2,
            index_format=format,
        )
        for format in ("json_v1", "events_v2")
    ]
    for store in stores:
        first = store.record_body(b"one")
        second = store.record_body(b"two")
        assert store.resolve_body(first) == b"one"
        store.record_body(b"three")
        assert store.contains_body(first) and not store.contains_body(second)
    assert stores[1]._index_journal.read() == stores[0]._index_path.read_bytes()


@pytest.mark.parametrize("variant", ["return", "raise", "restore"])
def test_original_delta_owner_retirement_spends_before_foreign_journal_refusal(
    tmp_path, variant
):
    from aware_workspace_fs_adapter import repository_delta_retention as physical

    factory = physical.FilesystemDeltaRetentionFactory.filesystem(
        state_root=tmp_path, index_format="auto"
    )
    owner = factory.allocate_owner()
    owner.initialize_original_store(repository_binding_ref=BINDING)
    record = physical._OWNERS[owner]
    store = record.store
    original = store._index_journal
    calls = []

    class Foreign:
        @property
        def failure_evidence(self):
            calls.append(True)
            if variant == "restore":
                store._index_journal = original
            if variant == "raise":
                raise OSError("foreign")

    store._index_journal = Foreign()
    with pytest.raises(physical.DeltaRetentionOwnerRefusal, match="origin_unknown"):
        owner.retire_owner()
    assert calls == [] and record.phase == "released" and record.store is None
    store._index_journal = original
    owner.retire_owner()
    assert calls == []

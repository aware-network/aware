"""Original mutation receipt semantics, independent of index representation."""

from __future__ import annotations

import json
import os
from dataclasses import replace

import pytest
from aware_workspace_fs_adapter.repository_mutation_store import (
    WorkspaceRepositoryMutationStore,
)
from test_repository_mutation import _coordinate, _digest

from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_mutation_terminal_evidence import (
    fixture,
)


@pytest.mark.asyncio
async def test_v2_original_receipts_fresh_old_fields_canonical_parity_and_restart(
    tmp_path,
):
    _, _, session, _, coordinator, request = await fixture(tmp_path)
    try:
        first = await coordinator.mutate(request)
        second = await coordinator.mutate(
            replace(
                request,
                operation_ref=request.operation_ref + ":next",
                idempotency_key=request.idempotency_key + ":next",
                expected_coordinate=_coordinate(session),
                expected_content_digest=_digest(b"after"),
                content=b"next",
            )
        )
        stores = [
            WorkspaceRepositoryMutationStore(
                repository_binding_ref=first.receipt.repository_binding_ref,
                state_root=tmp_path / format,
                capacity=2,
                index_format=format,
            )
            for format in ("json_v1", "events_v2")
        ]
        for store in stores:
            store.record(fingerprint="first", result=first)
        object.__setattr__(first.receipt, "context_refs", ("fresh-old-row",))
        for store in stores:
            store.record(fingerprint="second", result=second)
        assert stores[1]._index_journal.read() == stores[0]._index_path.read_bytes()
        assert json.loads(stores[1]._index_journal.read())["records"][0]["result"][
            "value"
        ]["receipt"]["value"]["context_refs"] == ["fresh-old-row"]
        reopened = WorkspaceRepositoryMutationStore(
            repository_binding_ref=first.receipt.repository_binding_ref,
            state_root=tmp_path / "events_v2",
            capacity=2,
            index_format="auto",
        )
        assert reopened.resolve(first.receipt.mutation_receipt_ref) == ("first", first)
        assert reopened.resolve(second.receipt.mutation_receipt_ref) == (
            "second",
            second,
        )
        assert not reopened._index_path.exists()
        default_reader = WorkspaceRepositoryMutationStore(
            repository_binding_ref=first.receipt.repository_binding_ref,
            state_root=tmp_path / "events_v2",
            capacity=2,
        )
        assert default_reader.resolve(first.receipt.mutation_receipt_ref) == (
            "first",
            first,
        )
    finally:
        await session.stop()


@pytest.mark.asyncio
async def test_mutation_encoding_remains_after_pending_acquisition(
    tmp_path, monkeypatch
):
    from aware_workspace_fs_adapter import repository_delta_store as physical
    from aware_workspace_fs_adapter import repository_mutation_store as module

    _, _, session, _, coordinator, request = await fixture(tmp_path)
    try:
        result = await coordinator.mutate(request)
        store = WorkspaceRepositoryMutationStore(
            repository_binding_ref=result.receipt.repository_binding_ref,
            state_root=tmp_path / "events",
            index_format="events_v2",
        )
        calls = []
        original_open, original_encode = (
            physical.os.fdopen,
            module.repository_authorized_mutation_payload,
        )

        def fdopen(*args, **kwargs):
            calls.append("acquire")
            return original_open(*args, **kwargs)

        def encode(value):
            calls.append("encode")
            return original_encode(value)

        with monkeypatch.context() as patch:
            patch.setattr(physical.os, "fdopen", fdopen)
            patch.setattr(module, "repository_authorized_mutation_payload", encode)
            store.record(fingerprint="original", result=result)
        assert calls == ["acquire", "encode"]
    finally:
        await session.stop()


def test_journal_code_constants_preserve_original_code_object_hashability():
    from aware_workspace_fs_adapter import repository_delta_store as delta
    from aware_workspace_fs_adapter import repository_mutation_store as mutation

    for function in (
        delta._atomic_write,
        delta.WorkspaceRepositoryDeltaStore._persist_index,
        mutation.WorkspaceRepositoryMutationStore._persist,
        mutation.WorkspaceRepositoryMutationStore._canonical_index,
    ):
        assert type(hash(function.__code__)) is int


def test_original_tree_cleanup_does_not_accept_a_clean_replacement_journal(tmp_path):
    import os
    import sys

    from aware_workspace_fs_adapter.repository_index_journal import IndexJournal
    from aware_workspace_fs_adapter.repository_source_projection import (
        FilesystemSourceProjectionPort,
        execution_identity,
    )

    root = tmp_path / "target"
    root.mkdir()
    physical = FilesystemSourceProjectionPort(
        repository_root=root,
        state_root=tmp_path / "state",
        execution_id=execution_identity(),
    )
    binding = physical.binding
    store = physical.create_tree_receipt_store(binding, capacity=2)
    original = store._index_journal
    close, code = os.close, IndexJournal.publication_guard.__wrapped__.__code__
    seen = []

    def lost(frame, event, callee):
        if (
            event == "c_return"
            and callee is close
            and frame.f_code is code
            and not seen
        ):
            seen.append(True)
            raise OSError("lost original metadata close")

    previous = sys.getprofile()
    try:
        sys.setprofile(lost)
        with pytest.raises(OSError, match="lost original"):
            store._persist()
    finally:
        sys.setprofile(previous)
    assert physical.read_tree_receipt_store_cleanup(binding, store)[0] is False
    replacement = IndexJournal(
        store._index_path,
        binding=store.repository_binding_ref,
        kind=1,
        index_format="auto",
    )
    store._index_journal = replacement
    assert physical.read_tree_receipt_store_cleanup(binding, store) == (
        False,
        ("receipt_index_origin_unknown",),
    )
    assert original.failure_evidence.cleanup == "unknown" and original._held


@pytest.mark.parametrize("variant", ["return", "raise", "restore"])
def test_original_tree_cleanup_rejects_foreign_journal_without_getter(
    tmp_path, variant
):
    from aware_workspace_fs_adapter.repository_source_projection import (
        FilesystemSourceProjectionPort,
        execution_identity,
    )

    root = tmp_path / "target"
    root.mkdir()
    physical = FilesystemSourceProjectionPort(
        repository_root=root,
        state_root=tmp_path / "state",
        execution_id=execution_identity(),
    )
    store = physical.create_tree_receipt_store(physical.binding, capacity=2)
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
    assert physical.read_tree_receipt_store_cleanup(physical.binding, store)[0] is False
    assert calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("mask", [0o022, 0o077])
async def test_original_private_root_mode_is_preserved(tmp_path, mask):
    _, _, session, _, coordinator, request = await fixture(tmp_path)
    try:
        result = await coordinator.mutate(request)
        previous = os.umask(mask)
        try:
            for format in ("json_v1", "events_v2"):
                store = WorkspaceRepositoryMutationStore(
                    repository_binding_ref=result.receipt.repository_binding_ref,
                    state_root=tmp_path / format,
                    index_format=format,
                )
                store.record(fingerprint="original", result=result)
                assert store._store_root.stat().st_mode & 0o777 == 0o700
        finally:
            os.umask(previous)
    finally:
        await session.stop()

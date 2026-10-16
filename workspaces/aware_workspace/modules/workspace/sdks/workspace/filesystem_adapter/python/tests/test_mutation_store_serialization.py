"""Original mutation receipts through unchanged durable store checkpoints."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from aware_workspace_fs_adapter import repository_mutation_store as module
from aware_workspace_fs_adapter.repository_mutation_store import (
    WorkspaceRepositoryMutationStore,
)
from aware_workspace_runtime.change_evidence_codec import (
    repository_authorized_mutation_payload,
)
from test_repository_mutation import _coordinate, _digest

from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_mutation_terminal_evidence import (
    fixture,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("legacy_pretty", [False, True])
async def test_compact_index_preserves_original_receipt_on_restart(
    tmp_path, legacy_pretty
):
    _, _, session, _, coordinator, request = await fixture(tmp_path)
    try:
        result = await coordinator.mutate(request)
        store = WorkspaceRepositoryMutationStore(
            repository_binding_ref=result.receipt.repository_binding_ref,
            state_root=tmp_path / "index",
            capacity=2,
        )
        store.record(fingerprint="original-input", result=result)
        index = tmp_path / "index/repository_mutations/index.json"
        first_bytes = index.read_bytes()
        payload = json.loads(first_bytes)
        assert (
            first_bytes
            == (
                json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode()
        )
        assert payload["records"][0][
            "result"
        ] == repository_authorized_mutation_payload(result)
        assert index.stat().st_mode & 0o777 == 0o600
        if legacy_pretty:
            index.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        reopened = WorkspaceRepositoryMutationStore(
            repository_binding_ref=result.receipt.repository_binding_ref,
            state_root=tmp_path / "index",
            capacity=2,
        )
        assert reopened.resolve(result.receipt.mutation_receipt_ref) == (
            "original-input",
            result,
        )
        before = index.read_bytes()
        reopened.record(fingerprint="original-input", result=result)
        assert index.read_bytes() == before
        with pytest.raises(ValueError, match="identity cannot change"):
            reopened.record(fingerprint="foreign-input", result=result)
        assert index.read_bytes() == before
    finally:
        await session.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["encode", "fsync", "replace"])
@pytest.mark.parametrize("interrupted", [False, True])
async def test_compact_index_failure_preserves_prior_disk_and_once_cleanup(
    tmp_path, monkeypatch, boundary, interrupted
):
    _, _, session, _, coordinator, request = await fixture(tmp_path)
    try:
        result = await coordinator.mutate(request)
        successor = await coordinator.mutate(
            replace(
                request,
                operation_ref=request.operation_ref + ":successor",
                idempotency_key=request.idempotency_key + ":successor",
                expected_coordinate=_coordinate(session),
                expected_content_digest=_digest(b"after"),
                content=b"later",
            )
        )
        root = tmp_path / "index"
        store = WorkspaceRepositoryMutationStore(
            repository_binding_ref=result.receipt.repository_binding_ref,
            state_root=root,
            capacity=2,
        )
        store.record(fingerprint="original-input", result=result)
        index = root / "repository_mutations/index.json"
        before = index.read_bytes()
        error = (
            KeyboardInterrupt("interrupted persistence")
            if interrupted
            else OSError("failed persistence")
        )
        calls = []

        def fail(*args, **kwargs):
            calls.append(True)
            raise error

        with monkeypatch.context() as patch:
            patch.setattr(
                module.json if boundary == "encode" else module.os,
                "dumps" if boundary == "encode" else boundary,
                fail,
            )
            with pytest.raises(type(error)) as caught:
                store.record(fingerprint="successor-input", result=successor)
        assert caught.value is error and calls == [True]
        assert (tmp_path / "issue.md").read_bytes() == b"later"
        assert index.read_bytes() == before
        assert tuple(index.parent.iterdir()) == (index,)
        reopened = WorkspaceRepositoryMutationStore(
            repository_binding_ref=result.receipt.repository_binding_ref,
            state_root=root,
            capacity=2,
        )
        assert reopened.resolve(result.receipt.mutation_receipt_ref) == (
            "original-input",
            result,
        )
        assert reopened.resolve(successor.receipt.mutation_receipt_ref) is None
    finally:
        await session.stop()


@pytest.mark.asyncio
async def test_receipt_encoding_keeps_every_durable_call_and_fresh_retained_field(
    tmp_path, monkeypatch
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
        root = tmp_path / "encoding-index"
        store = WorkspaceRepositoryMutationStore(
            repository_binding_ref=first.receipt.repository_binding_ref,
            state_root=root,
            capacity=2,
        )
        actual_fsync, actual_replace = module.os.fsync, module.os.replace
        calls = []

        def fsync(descriptor):
            calls.append("fsync")
            return actual_fsync(descriptor)

        def replace_index(source, target):
            calls.append("replace")
            return actual_replace(source, target)

        with monkeypatch.context() as patch:
            patch.setattr(module.os, "fsync", fsync)
            patch.setattr(module.os, "replace", replace_index)
            store.record(fingerprint="first", result=first)
            # The retained descriptive value remains freshly encoded; prior
            # identity or an earlier successful write cannot cache its fields.
            object.__setattr__(first.receipt, "context_refs", ("changed-after-write",))
            store.record(fingerprint="second", result=second)
        assert calls == ["fsync", "replace", "fsync", "replace"]
        index = root / "repository_mutations/index.json"
        payload = json.loads(index.read_bytes())
        assert payload["records"][0][
            "result"
        ] == repository_authorized_mutation_payload(first)
        assert payload["records"][0]["result"]["value"]["receipt"]["value"][
            "context_refs"
        ] == ["changed-after-write"]
        assert payload["records"][1][
            "result"
        ] == repository_authorized_mutation_payload(second)
        assert index.stat().st_mode & 0o777 == 0o600
        assert tuple(index.parent.iterdir()) == (index,)
    finally:
        await session.stop()

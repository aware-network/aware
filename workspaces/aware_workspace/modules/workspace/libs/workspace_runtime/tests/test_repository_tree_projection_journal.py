"""Original SDK/Runtime/Issue/FileSystem composition with selected index format."""

from __future__ import annotations

import json

import pytest
from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionFactory,
)


@pytest.mark.asyncio
async def test_original_retention_factory_selects_format_without_allocating_journal(
    tmp_path,
):
    factory = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
        state_root=tmp_path, index_format="auto"
    )
    client = factory.allocate_delta_retention()
    try:
        client.initialize_delta_retention(repository_binding_ref="repo:original")
        assert tuple(tmp_path.iterdir()) == ()
        refs = client.record_bodies((b"original",))
        assert client.resolve_bodies(refs) == (b"original",)
        assert len(tuple(tmp_path.rglob("index.events-v2"))) == 1
        assert not tuple(tmp_path.rglob("index.json"))
    finally:
        client.release_retention()


@pytest.mark.asyncio
async def test_genuine_sdk_owner_execution_and_cleanup_with_original_runner(tmp_path):
    from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_tree_projection import (
        run_complete_tree_resource_probe,
    )

    result = tmp_path / "original32-result.json"
    await run_complete_tree_resource_probe(32, 262144, str(result))
    value = json.loads(result.read_text())
    assert value["status"] == "complete"
    assert value["count"] == 32 and value["combined_body_bytes"] == 262144
    assert value["cleanup_errors"] == []


@pytest.mark.asyncio
async def test_original_receipt_lock_close_lost_return_preserves_known_write_and_unknown_cleanup(
    tmp_path, monkeypatch
):
    import os
    import sys

    from aware_workspace_fs_adapter.repository_index_journal import IndexJournal
    from aware_workspace_sdk.repository_tree_projection import (
        read_original_tree_projection_result,
    )
    from aware_workspace_sdk.repository_workflow import (
        release_original_repository_workflow_source,
    )

    from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_tree_projection import (
        genuine_issue_enrollment,
    )
    from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_workflow import (
        inputs,
    )

    args = inputs.__wrapped__(tmp_path, monkeypatch)
    (
        attempt,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        _path,
    ) = await genuine_issue_enrollment(args)
    calls = []
    error = OSError("lost original receipt lock close return")
    close, close_code = os.close, IndexJournal.publication_guard.__wrapped__.__code__
    pending = []

    def lost_return(frame, event, callee):
        if frame.f_code is not close_code or callee is not close:
            return
        if event == "c_call":
            descriptor = frame.f_locals.get("closing")
            if type(descriptor) is int:
                target = os.readlink(f"/proc/self/fd/{descriptor}")
                if target.endswith(".repository_mutations.index.lock"):
                    pending.append(True)
        elif event == "c_return" and pending and not calls:
            calls.append(True)
            raise error

    prior = sys.getprofile()
    try:
        sys.setprofile(lost_return)
        try:
            result = await workspace.project_tree(plan, admission=enrollment)
        finally:
            sys.setprofile(prior)
        observed = read_original_tree_projection_result(
            result, expected_binding=binding
        )
        assert calls == [True] and (args[1] / "out.py").is_file()
        assert observed.completed_prefix == 1 and len(observed.receipts) == 1
        assert observed.receipts[0].mutation_receipt_ref
        assert observed.index_state == "unavailable"
        assert (
            observed.cleanup.cleanup_state == "unknown"
            and not observed.cleanup.ledger_complete
        )
        assert not observed.ledger_complete
        row = next(
            row
            for row in observed.cleanup.resources
            if row.kind == "repository_index_metadata"
        )
        assert row.cleanup_state == "unknown" and row.diagnostics[1] == "committed"
        resolution = await workspace.resolve_tree_projection_receipts(enrollment)
        assert (
            resolution.observation.cleanup == observed.cleanup
            and not resolution.authorizes_retry
        )
        await workspace.release_tree_projection()
        assert calls == [True]
    finally:
        await workspace.release_tree_projection()
        await issuer.release_tree_projection_admission(issue)
        release_original_repository_workflow_source(source)
        args[-2].release_repository_workflow(attempt)

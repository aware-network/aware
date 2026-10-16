"""C authority refusals through original Issue and Workspace supplying owners."""

from __future__ import annotations

import os
import threading
from dataclasses import replace

import pytest
from aware_issue_sdk.source_projection import (
    IssueRepositoryTreeProjectionClient,
    IssueTreeProjectionRefusal,
    consume_tree_projection_admission,
    verify_tree_projection_consumption,
)
from aware_workspace_sdk.repository_tree_projection import (
    WorkspaceTreeProjectionRefusal,
)

from workspaces.aware_coordination.modules.workflow.sdks.issue.python.tests.test_repository_tree_projection_admission import (
    EXECUTION,
    digest,
    install_issue,
    prepared,
)
from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_workflow import (
    inputs as inputs,  # noqa: PLC0414
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change,code",
    (
        ("owner", "issue_owner_mismatch"),
        ("status", "issue_status_invalid"),
        ("scope", "issue_source_out_of_scope"),
        ("scratch", "issue_source_out_of_scope"),
        ("actor", "issue_owner_execution_mismatch"),
        ("digest", "issue_tree_source_sha256_mismatch"),
    ),
)
async def test_fresh_authority_and_all_enumerated_effects_are_required(
    inputs, change, code
):
    attempt, source, workspace, tree, binding, client, request, path = await prepared(
        inputs, defer=True
    )
    if change in ("owner", "status", "scope", "scratch"):
        path = install_issue(
            inputs[1],
            scope=("elsewhere",)
            if change == "scope"
            else ("out.py",)
            if change == "scratch"
            else binding.effect_paths,
            owner="codex-other" if change == "owner" else EXECUTION,
            status="Open" if change == "status" else "In Progress",
        )
        request = replace(
            request, expected_issue_source_sha256=digest(path.read_bytes())
        )
    else:
        request = (
            replace(request, actor_ref="codex-other")
            if change == "actor"
            else replace(request, expected_issue_source_sha256="sha256:" + "0" * 64)
        )
    with pytest.raises(IssueTreeProjectionRefusal, match=code) as failure:
        await client.prepare_tree_projection_admission(
            request,
            workspace_client=workspace,
            workspace_plan=tree,
            expected_binding=binding,
        )
    assert failure.value.observation.phase == "retired"
    assert failure.value.observation.consumption_state == "not_spent"
    assert failure.value.cleanup.cleanup_state == "completed"
    assert (
        workspace.verify_tree_projection_plan(tree, expected_binding=binding).phase
        == "prepared"
    )
    assert attempt is not None and source is not None
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_preserved_ancestor_is_not_added_to_mutating_scope(inputs):
    attempt, source, workspace, tree, binding, client, request, path = await prepared(
        inputs, kind="nested", defer=True
    )
    assert "public" in binding.read_guard_paths and "public" not in binding.effect_paths
    path = install_issue(inputs[1], scope=binding.effect_paths)
    request = replace(request, expected_issue_source_sha256=digest(path.read_bytes()))
    plan = await client.prepare_tree_projection_admission(
        request,
        workspace_client=workspace,
        workspace_plan=tree,
        expected_binding=binding,
    )
    admission = await client.admit_tree_projection(plan)
    assert consume_tree_projection_admission(admission, binding=binding) is not None
    await client.release_tree_projection_admission(admission)
    assert attempt is not None and source is not None
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_an_issue_from_a_distinct_root_cannot_authorize_target(inputs, tmp_path):
    attempt, source, workspace, tree, binding, _, request, _path = await prepared(
        inputs, defer=True
    )
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    path = install_issue(foreign, scope=binding.effect_paths)
    request = replace(request, expected_issue_source_sha256=digest(path.read_bytes()))
    client = IssueRepositoryTreeProjectionClient.filesystem(
        repository_root=foreign, execution_id=EXECUTION
    )
    with pytest.raises(IssueTreeProjectionRefusal, match="target_authority_mismatch"):
        await client.prepare_tree_projection_admission(
            request,
            workspace_client=workspace,
            workspace_plan=tree,
            expected_binding=binding,
        )
    assert (
        workspace.verify_tree_projection_plan(tree, expected_binding=binding).phase
        == "prepared"
    )
    assert attempt is not None and source is not None
    await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ("missing", "fifo", "permission"))
async def test_initial_source_refusals_are_typed_and_have_correlated_cleanup(
    inputs, monkeypatch, kind
):
    attempt, source, workspace, tree, binding, client, request, path = await prepared(
        inputs, defer=True
    )
    if kind == "missing":
        path.unlink()
    elif kind == "fifo":
        path.unlink()
        os.mkfifo(path)
    else:
        from aware_issue_fs_adapter import source_change

        original = source_change.os.open

        def denied(file, *args, **kwargs):
            if str(file) == path.name:
                raise PermissionError("disposable denied authority")
            return original(file, *args, **kwargs)

        monkeypatch.setattr(source_change.os, "open", denied)
    with pytest.raises(IssueTreeProjectionRefusal) as failure:
        await client.prepare_tree_projection_admission(
            request,
            workspace_client=workspace,
            workspace_plan=tree,
            expected_binding=binding,
        )
    assert failure.value.observation.phase == "retired"
    assert failure.value.__cause__ is not None
    assert failure.value.cleanup is not None
    assert attempt is not None and source is not None
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_real_issue_read_close_interruption_retains_unknown_cleanup(
    inputs, monkeypatch
):
    attempt, source, workspace, _tree, binding, client, plan, path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    from aware_issue_fs_adapter import source_change

    original = source_change.os.close
    count = 0

    def close_then_interrupt(fd):
        nonlocal count
        original(fd)
        count += 1
        if count == 1:
            raise KeyboardInterrupt("read close return unavailable")

    monkeypatch.setattr(source_change.os, "close", close_then_interrupt)
    with pytest.raises(
        IssueTreeProjectionRefusal, match="issue_read_descriptor_cleanup_failed"
    ) as failure:
        consume_tree_projection_admission(admission, binding=binding)
    assert failure.value.observation.consumption_state == "spent"
    assert not failure.value.observation.ledger_complete
    assert failure.value.cleanup.cleanup_state == "unknown"
    assert any(row.ownership == "unknown" for row in failure.value.cleanup.resources)
    assert path.exists() and not (inputs[1] / "out.py").exists()
    monkeypatch.setattr(source_change.os, "close", original)
    assert attempt is not None and source is not None
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_harness_revocation_stops_suffix_without_renewing_authority(
    inputs, monkeypatch
):
    attempt, source, workspace, _tree, binding, client, plan, _path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    consumption = consume_tree_projection_admission(admission, binding=binding)
    monkeypatch.setenv("CODEX_THREAD_ID", "foreign-execution")
    with pytest.raises(IssueTreeProjectionRefusal) as failure:
        verify_tree_projection_consumption(consumption, expected_binding=binding)
    assert failure.value.observation.consumption_state == "spent"
    monkeypatch.setenv("CODEX_THREAD_ID", "workflow-planning-test")
    with pytest.raises(IssueTreeProjectionRefusal):
        verify_tree_projection_consumption(consumption, expected_binding=binding)
    assert attempt is not None and source is not None
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_foreign_process_and_thread_refuse_before_owner_locks(
    inputs, monkeypatch
):
    attempt, source, workspace, _tree, binding, client, plan, _path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    errors = []

    def foreign_thread():
        try:
            consume_tree_projection_admission(admission, binding=binding)
        except IssueTreeProjectionRefusal as error:
            errors.append(error.code)

    worker = threading.Thread(target=foreign_thread)
    worker.start()
    worker.join(timeout=2)
    assert not worker.is_alive() and errors == ["issue_tree_origin_mismatch"]
    original = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(os, "getpid", lambda: original + 1)
        with pytest.raises(IssueTreeProjectionRefusal, match="origin_mismatch"):
            consume_tree_projection_admission(admission, binding=binding)
    assert consume_tree_projection_admission(admission, binding=binding) is not None
    assert attempt is not None and source is not None
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_workspace_enrollment_is_still_explicitly_unavailable(inputs):
    attempt, source, workspace, tree, _binding, client, plan, _path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="issue_unavailable"):
        await workspace.enroll_issue_tree_projection(tree, issue_admission=admission)
    assert (
        client.observe_tree_projection_admission(admission).consumption_state
        == "not_spent"
    )
    assert attempt is not None and source is not None
    await client.release_tree_projection_admission(admission)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ("authority_issue", "authority_manifest"))
async def test_original_plan_cannot_mutate_its_authority_sources(inputs, kind):
    attempt, source, workspace, tree, binding, client, request, path = await prepared(
        inputs, kind=kind, defer=True
    )
    with pytest.raises(
        IssueTreeProjectionRefusal, match="authority_effect_forbidden"
    ) as failure:
        await client.prepare_tree_projection_admission(
            request,
            workspace_client=workspace,
            workspace_plan=tree,
            expected_binding=binding,
        )
    assert failure.value.observation.consumption_state == "not_spent"
    assert path.exists() and (inputs[1] / "aware.protocol.toml").exists()
    assert attempt is not None and source is not None
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_interrupted_consumption_return_preserves_spending_and_refuses_replay(
    inputs, monkeypatch
):
    import aware_issue_operational_runtime.source_projection as runtime
    from aware_issue_sdk.source_projection import IssueTreeProjectionConsumption

    attempt, source, workspace, _tree, binding, client, plan, _path = await prepared(
        inputs
    )
    admission = await client.admit_tree_projection(plan)
    import aware_issue_sdk.source_projection as sdk

    original = sdk._tree_handle

    def interrupted(owner, kind):
        if kind is IssueTreeProjectionConsumption:
            raise KeyboardInterrupt("consumption return unavailable")
        return original(owner, kind)

    monkeypatch.setattr(sdk, "_tree_handle", interrupted)
    with pytest.raises(IssueTreeProjectionRefusal) as failure:
        consume_tree_projection_admission(admission, binding=binding)
    assert failure.value.observation.consumption_state == "spent"
    assert failure.value.observation.phase == "retired"
    assert isinstance(failure.value.__cause__, KeyboardInterrupt)
    monkeypatch.setattr(sdk, "_tree_handle", original)
    with pytest.raises(IssueTreeProjectionRefusal):
        consume_tree_projection_admission(admission, binding=binding)
    assert (
        runtime.IssueTreeProjectionRuntime is not None
        and attempt is not None
        and source is not None
    )
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_workspace_verification_runs_outside_issue_registry_lock(
    inputs, monkeypatch
):
    import aware_issue_operational_runtime.source_projection as runtime
    import aware_issue_sdk.source_projection as sdk

    attempt, source, workspace, _tree, _binding, client, plan, _path = await prepared(
        inputs
    )
    owner = sdk._TREE_CLIENTS[client][0]
    original = runtime._tree_workspace_binding
    calls = []

    def checked(*args):
        assert not owner.lock._is_owned()
        calls.append("outside_issue_lock")
        return original(*args)

    monkeypatch.setattr(runtime, "_tree_workspace_binding", checked)
    admission = await client.admit_tree_projection(plan)
    assert calls == ["outside_issue_lock"]
    assert attempt is not None and source is not None
    await client.release_tree_projection_admission(admission)
    await workspace.release_tree_projection()

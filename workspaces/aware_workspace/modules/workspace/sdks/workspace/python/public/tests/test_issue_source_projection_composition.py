"""Genuine owner composition over disposable filesystem inputs, not unit ports."""

from __future__ import annotations

import ast
import asyncio
import copy
import hashlib
import json
import os
import pickle
import shutil
import threading
from dataclasses import replace
from pathlib import Path

import aware_issue_operational_runtime.source_projection as issue_projection_runtime
import pytest
from aware_issue_sdk.operation import IssueMutationOutcome, IssueStartProgressRequest
from aware_issue_sdk.source_projection import (
    IssueSourceProjectionAdmission,
    IssueSourceProjectionRefusal,
    IssueStartProgressProjectionClient,
    consume_source_projection_admission,
)
from aware_workspace_runtime import repository_mutation as mutation
from aware_workspace_sdk.repository_source_projection import (
    WorkspaceRepositorySourceProjectionClient,
    WorkspaceSourceProjectionPlan,
    WorkspaceSourceProjectionRefusal,
)

REF = "fb/2026-10-10/example"
PATH = "docs/issues/2026/10/10/fb-2026-10-10-example.md"
EXECUTION = "codex-source-projection-test"


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "source-projection-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    root = tmp_path / "repository"
    root.mkdir()
    (root / "AGENTS.md").write_text("# Disposable consumer\n")
    (root / "aware.protocol.toml").write_text("""aware = 1
[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v1"
semantic_version = 1
[target]
kind = "repository"
authority_mode = "filesystem"
[bootstrap]
agent_contract = "AGENTS.md"
[records.issue]
profile = "aware.issue.markdown.v1"
root = "docs/issues"
role = "authority"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"
[records.goal]
profile = "aware.goal.markdown.v1"
role = "unavailable"
[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"
[records.specification]
profile = "specification_fs_v1"
role = "unavailable"
[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"
""")
    source = root / PATH
    source.parent.mkdir(parents=True)
    source.write_text(f"""# Issue: Example
- Slug: `example`
- Tag: `{REF}`
- Status: Open
- Owner: `{EXECUTION}`
- Priority: P1
- Captured: 2026-10-10
- Recorder: `{EXECUTION}`
- Source: Disposable composition proof

## Ownership Scope
- `src/example.py`

## Updates (append-only)
- Original activity.
""")
    workspace = WorkspaceRepositorySourceProjectionClient.filesystem(
        repository_root=root,
        state_root=tmp_path / "state",
        execution_id=EXECUTION,
    )
    issue = IssueStartProgressProjectionClient.filesystem(
        repository_root=root, execution_id=EXECUTION
    )
    request = IssueStartProgressRequest(
        issue_ref=REF,
        expected_source_sha256=digest(source.read_bytes()),
        client_intent_id="intent:example",
        actor_ref=EXECUTION,
        actor_evidence_ref="harness:source-projection-test",
    )
    return source, workspace, issue, request


async def admitted(inputs):
    source, workspace, issue, request = inputs
    plan = await issue.prepare_start_progress_projection(
        request, workspace_client=workspace
    )
    admission = await issue.admit_start_progress_projection(plan)
    return source, workspace, issue, request, plan, admission


def record(issue, plan):
    # Test-only introspection. Production never accesses a foreign registry.
    return issue._owner.plans[plan]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", ["projection_io", "projection_interrupt", "constructor", "malformed"]
)
async def test_final_issue_return_failure_preserves_original_observation(
    inputs, monkeypatch, failure
):
    source, workspace, issue, _, plan, admission = await admitted(inputs)
    before = source.read_bytes()
    original_writer = mutation.mutate_confined_file
    calls = []

    def writer(**kwargs):
        calls.append(kwargs)
        return original_writer(**kwargs)

    def failed(*_args, **_kwargs):
        if failure == "malformed":
            return
        if failure == "projection_interrupt":
            raise KeyboardInterrupt("final Issue projection interrupted")
        raise OSError("final Issue return unavailable")

    monkeypatch.setattr(mutation, "mutate_confined_file", writer)
    if failure == "constructor":
        monkeypatch.setattr(issue_projection_runtime, "IssueMutationResult", failed)
    else:
        monkeypatch.setattr(issue._owner.physical, "projected_read", failed)
    try:
        with pytest.raises(IssueSourceProjectionRefusal) as refusal:
            await issue.execute_start_progress_projection(plan, admission=admission)
        state = record(issue, plan)
        observation = refusal.value.observation
        assert refusal.value.code == "issue_projection_result_failed"
        assert refusal.value.__cause__ is not None
        assert observation is state.observation
        assert state.phase == "terminal"
        assert source.read_bytes() != before
        assert observation.source_effect_state == "applied"
        assert observation.retention.state == "retained"
        assert observation.physical_effect.after_content_digest == digest(
            source.read_bytes()
        )
        delta = workspace._owner.retention.resolve_delta(
            observation.retention.content_delta_ref
        )
        assert delta.capture_ref == observation.retention.capture_ref
        assert workspace._owner.retention.resolve_body(delta.old_body_ref) == before
        assert (
            workspace._owner.retention.resolve_body(delta.new_body_ref)
            == source.read_bytes()
        )
        with pytest.raises(IssueSourceProjectionRefusal) as replay:
            await issue.execute_start_progress_projection(plan, admission=admission)
        assert replay.value.observation is observation
        assert len(calls) == 1
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", ["manifest", "workspace_io", "workspace_interrupt", "issue_io"]
)
async def test_failed_admission_retires_only_original_preparation(
    inputs, monkeypatch, failure
):
    source, workspace, issue, request = inputs
    plan = await issue.prepare_start_progress_projection(
        request, workspace_client=workspace
    )
    other = await issue.prepare_start_progress_projection(
        request, workspace_client=workspace
    )
    before = source.read_bytes()
    # Use the original repository coordinate from the disposable fixture.
    manifest = source.parents[5] / "aware.protocol.toml"
    manifest_before = manifest.read_bytes()

    def failed(*_args, **_kwargs):
        if failure == "workspace_interrupt":
            raise KeyboardInterrupt("plan verification interrupted")
        raise OSError("freshness verification unavailable")

    try:
        with monkeypatch.context() as patch:
            if failure == "manifest":
                manifest.write_bytes(manifest_before + b"\n# authority drift\n")
            elif failure == "issue_io":
                patch.setattr(issue._owner.physical, "read", failed)
            else:
                patch.setattr(type(workspace), "verify_source_projection_plan", failed)
            with pytest.raises(
                (IssueSourceProjectionRefusal, OSError, KeyboardInterrupt)
            ):
                await issue.admit_start_progress_projection(plan)
        manifest.write_bytes(manifest_before)
        assert record(issue, plan).phase == "retired"
        assert record(issue, plan).admission is None
        assert record(issue, other).phase == "prepared"
        with pytest.raises(IssueSourceProjectionRefusal, match="admission_spent"):
            await issue.admit_start_progress_projection(plan)
        assert source.read_bytes() == before
        # Fresh preparation succeeds; restoring bytes never revives the refused original.
        fresh = await issue.prepare_start_progress_projection(
            request, workspace_client=workspace
        )
        admission = await issue.admit_start_progress_projection(fresh)
        result = await issue.execute_start_progress_projection(
            fresh, admission=admission
        )
        assert result.outcome is IssueMutationOutcome.APPLIED
    finally:
        manifest.write_bytes(manifest_before)
        await workspace.release_source_projection()


@pytest.mark.asyncio
async def test_real_issue_operation_retains_exact_original_delta(inputs):
    source, workspace, issue, _request, plan, admission = await admitted(inputs)
    before = source.read_bytes()
    try:
        result = await issue.execute_start_progress_projection(
            plan, admission=admission
        )
        state = record(issue, plan)
        assert result.outcome is IssueMutationOutcome.APPLIED, (
            await workspace.resolve_source_projection_receipt(state.workspace_admission)
        )
        assert result.projection.status == "in_progress"
        assert result.source_sha256_before == digest(before)
        assert result.source_sha256_after == digest(source.read_bytes())
        state = record(issue, plan)
        observed = workspace.observe_source_projection(state.workspace_admission)
        assert observed.source_effect_state == "applied"
        assert observed.convergence_state == "converged"
        assert observed.retention.state == "retained"
        assert observed.ledger_complete
        delta = workspace._owner.retention.resolve_delta(
            observed.retention.content_delta_ref
        )
        assert delta.capture_ref == observed.retention.capture_ref
        assert delta.before_coordinate.cursor + 1 == delta.after_coordinate.cursor
        assert delta.old_path == delta.new_path == PATH
        assert workspace._owner.retention.resolve_body(delta.old_body_ref) == before
        assert (
            workspace._owner.retention.resolve_body(delta.new_body_ref)
            == source.read_bytes()
        )
        receipt = await workspace.resolve_source_projection_receipt(
            state.workspace_admission
        )
        assert receipt.receipt.outcome is mutation.RepositoryMutationOutcome.APPLIED
        assert receipt.evidence.before_coordinate.observation == delta.before_coordinate
        assert receipt.evidence.after_coordinate.observation == delta.after_coordinate
    finally:
        cleanup = await workspace.release_source_projection()
    assert cleanup.state == "completed"
    assert (
        workspace.observe_source_projection(
            state.workspace_admission
        ).source_effect_state
        == "applied"
    )
    assert (
        await workspace.resolve_source_projection_receipt(state.workspace_admission)
        is receipt
    )


@pytest.mark.asyncio
async def test_no_reciprocal_workspace_verification_during_consumption(
    inputs, monkeypatch
):
    _, workspace, issue, _, plan, admission = await admitted(inputs)
    original = workspace._owner.verify_plan

    def prohibited(*args, **kwargs):
        raise AssertionError("reciprocal Workspace verification under writer lock")

    monkeypatch.setattr(workspace._owner, "verify_plan", prohibited)
    try:
        result = await issue.execute_start_progress_projection(
            plan, admission=admission
        )
        assert result.outcome is IssueMutationOutcome.APPLIED
    finally:
        monkeypatch.setattr(workspace._owner, "verify_plan", original)
        await workspace.release_source_projection()


@pytest.mark.asyncio
async def test_spent_admissions_refuse_replay_without_second_write(inputs, monkeypatch):
    source, workspace, issue, _, plan, admission = await admitted(inputs)
    original, writes = mutation.mutate_confined_file, []

    def writer(**kwargs):
        writes.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(mutation, "mutate_confined_file", writer)
    try:
        await issue.execute_start_progress_projection(plan, admission=admission)
        body = source.read_bytes()
        state = record(issue, plan)
        with pytest.raises(IssueSourceProjectionRefusal):
            await issue.execute_start_progress_projection(plan, admission=admission)
        with pytest.raises(WorkspaceSourceProjectionRefusal):
            await workspace.project_source(
                state.workspace_plan, admission=state.workspace_admission
            )
        with pytest.raises(IssueSourceProjectionRefusal):
            consume_source_projection_admission(admission, binding=state.binding)
        assert source.read_bytes() == body and len(writes) == 1
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["content", "identity", "manifest", "owner"])
async def test_changed_authority_refuses_before_physical_dispatch(
    inputs, monkeypatch, change
):
    source, workspace, issue, _, plan, admission = await admitted(inputs)
    body = source.read_bytes()
    if change == "identity":
        replacement = source.with_suffix(".replacement")
        replacement.write_bytes(body)
        replacement.replace(source)
    elif change == "manifest":
        with (source.parents[5] / "aware.protocol.toml").open("a") as stream:
            stream.write("\n# changed admitted source\n")
    elif change == "owner":
        source.write_bytes(body.replace(EXECUTION.encode(), b"codex-foreign"))
    else:
        source.write_bytes(body + b"\nchanged\n")
    expected = source.read_bytes()
    monkeypatch.setattr(
        mutation,
        "mutate_confined_file",
        lambda **_: pytest.fail("physical dispatch on stale authority"),
    )
    try:
        with pytest.raises(IssueSourceProjectionRefusal) as refusal:
            await issue.execute_start_progress_projection(plan, admission=admission)
        assert refusal.value.observation.source_effect_state == "none"
        assert (
            refusal.value.observation.execution_evidence.physical_return_state
            == "not_dispatched"
        )
        assert source.read_bytes() == expected
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("after_write", [False, True])
async def test_unavailable_physical_return_preserves_unknown_and_spent(
    inputs, monkeypatch, after_write
):
    source, workspace, issue, _, plan, admission = await admitted(inputs)
    before = source.read_bytes()
    original, writes = mutation.mutate_confined_file, []

    def writer(**kwargs):
        writes.append(kwargs)
        if after_write:
            original(**kwargs)
        raise KeyboardInterrupt("unavailable physical return")

    monkeypatch.setattr(mutation, "mutate_confined_file", writer)
    try:
        with pytest.raises(IssueSourceProjectionRefusal) as refusal:
            await issue.execute_start_progress_projection(plan, admission=admission)
        observation = refusal.value.observation
        assert observation.source_effect_state == "unknown"
        assert observation.physical_effect is None
        assert observation.execution_evidence.physical_return_state == "unavailable"
        assert not observation.ledger_complete
        assert (source.read_bytes() != before) == after_write
        with pytest.raises(IssueSourceProjectionRefusal):
            await issue.execute_start_progress_projection(plan, admission=admission)
        assert len(writes) == 1
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
async def test_known_write_survives_canonical_retention_failure(inputs, monkeypatch):
    source, workspace, issue, _, plan, admission = await admitted(inputs)

    def unavailable(*args):
        raise OSError("canonical retention unavailable")

    monkeypatch.setattr(workspace._owner.capture_owner, "observe", unavailable)
    try:
        with pytest.raises(IssueSourceProjectionRefusal) as refusal:
            await issue.execute_start_progress_projection(plan, admission=admission)
        observation = refusal.value.observation
        assert observation.source_effect_state == "applied"
        assert observation.physical_effect.after_content_digest == digest(
            source.read_bytes()
        )
        assert observation.retention.state == "unknown"
        assert not observation.ledger_complete
        with pytest.raises(IssueSourceProjectionRefusal):
            await issue.execute_start_progress_projection(plan, admission=admission)
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
async def test_forged_and_foreign_plans_cannot_use_observed_bindings(inputs, tmp_path):
    _, workspace, issue, request = inputs
    plan = await issue.prepare_start_progress_projection(
        request, workspace_client=workspace
    )
    state = record(issue, plan)
    try:
        forged = object.__new__(WorkspaceSourceProjectionPlan)
        with pytest.raises(WorkspaceSourceProjectionRefusal):
            workspace.verify_source_projection_plan(
                forged, expected_binding=state.binding
            )
        forged_issue = object.__new__(IssueSourceProjectionAdmission)
        with pytest.raises(WorkspaceSourceProjectionRefusal):
            await workspace.enroll_issue_projection(
                state.workspace_plan, issue_admission=forged_issue
            )
        with pytest.raises(TypeError):
            copy.copy(plan)
        with pytest.raises(TypeError):
            copy.deepcopy(forged_issue)
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["digest", "size", "bool_size", "mutable"])
async def test_byte_transfer_refuses_before_retention_io(inputs, monkeypatch, field):
    _, workspace, _, _ = inputs
    body, size, sha = b"new body", 8, digest(b"new body")
    if field == "digest":
        sha = digest(b"wrong")
    if field == "size":
        size = 7
    if field == "bool_size":
        size = True
    if field == "mutable":
        body = bytearray(body)
    monkeypatch.setattr(
        workspace._owner,
        "_start",
        lambda: pytest.fail("retention IO on invalid byte transfer"),
    )
    with pytest.raises(WorkspaceSourceProjectionRefusal):
        await workspace.retain_projection_body(
            body, expected_content_digest=sha, expected_size_bytes=size
        )


@pytest.mark.asyncio
async def test_cancellation_settles_original_worker_and_retains_known_write(
    inputs, monkeypatch
):
    source, workspace, issue, _, plan, admission = await admitted(inputs)
    original = mutation.mutate_confined_file
    entered, proceed = threading.Event(), threading.Event()

    def writer(**kwargs):
        entered.set()
        assert proceed.wait(5)
        return original(**kwargs)

    monkeypatch.setattr(mutation, "mutate_confined_file", writer)
    task = asyncio.create_task(
        issue.execute_start_progress_projection(plan, admission=admission)
    )
    cleanup_task = None
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        cleanup_task = asyncio.create_task(workspace.release_source_projection())
        await asyncio.sleep(0)
        assert not task.done() and not cleanup_task.done()
        proceed.set()
        with pytest.raises(IssueSourceProjectionRefusal) as refusal:
            await task
        assert refusal.value.observation.source_effect_state == "applied"
        assert not refusal.value.observation.ledger_complete
        assert (
            digest(source.read_bytes())
            == refusal.value.observation.physical_effect.after_content_digest
        )
        assert (await cleanup_task).state == "completed"
    finally:
        proceed.set()
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["fifo", "symlink", "hardlink"])
async def test_nonregular_source_refuses_without_blocking_or_write(inputs, kind):
    source, workspace, _, _ = inputs
    source.unlink()
    if kind == "fifo":
        os.mkfifo(source)
    if kind == "symlink":
        source.symlink_to(source.parents[5] / "AGENTS.md")
    if kind == "hardlink":
        os.link(source.parents[5] / "AGENTS.md", source)
    try:
        with pytest.raises(WorkspaceSourceProjectionRefusal):
            await asyncio.wait_for(workspace.observe_source(target_path=PATH), 5)
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
async def test_equal_bytes_in_different_repository_cannot_receive_issue_authority(
    inputs, tmp_path
):
    source, workspace, issue, request = inputs
    other_root = tmp_path / "foreign-repository"
    shutil.copytree(source.parents[5], other_root)
    other = WorkspaceRepositorySourceProjectionClient.filesystem(
        repository_root=other_root,
        state_root=tmp_path / "foreign-state",
        execution_id=EXECUTION,
    )
    before = source.read_bytes()
    try:
        with pytest.raises(
            IssueSourceProjectionRefusal, match="workspace_source_correlation_mismatch"
        ):
            await issue.prepare_start_progress_projection(
                request, workspace_client=other
            )
        assert source.read_bytes() == (other_root / PATH).read_bytes() == before
    finally:
        await workspace.release_source_projection()
        await other.release_source_projection()


@pytest.mark.asyncio
async def test_foreign_workspace_cannot_verify_original_plan(inputs, tmp_path):
    source, workspace, issue, request = inputs
    plan = await issue.prepare_start_progress_projection(
        request, workspace_client=workspace
    )
    state = record(issue, plan)
    other = WorkspaceRepositorySourceProjectionClient.filesystem(
        repository_root=source.parents[5],
        state_root=tmp_path / "other-state",
        execution_id=EXECUTION,
    )
    try:
        with pytest.raises(WorkspaceSourceProjectionRefusal, match="foreign_owner"):
            other.verify_source_projection_plan(
                state.workspace_plan, expected_binding=state.binding
            )
    finally:
        await workspace.release_source_projection()
        await other.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change",
    [
        "closed",
        "blocked",
        "in_progress",
        "wrong_owner",
        "unassigned",
        "wrong_digest",
        "wrong_actor",
    ],
)
async def test_domain_authority_refuses_preparation_without_write(inputs, change):
    source, workspace, issue, request = inputs
    body = source.read_bytes()
    if change in {"closed", "blocked", "in_progress"}:
        body = body.replace(
            b"Status: Open", b"Status: " + change.replace("_", " ").title().encode()
        )
    if change == "wrong_owner":
        body = body.replace(EXECUTION.encode(), b"codex-foreign")
    if change == "unassigned":
        body = body.replace(f"- Owner: `{EXECUTION}`".encode(), b"- Owner: (none)")
    source.write_bytes(body)
    request = replace(request, expected_source_sha256=digest(body))
    if change == "wrong_digest":
        request = replace(request, expected_source_sha256=digest(b"wrong"))
    if change == "wrong_actor":
        request = replace(request, actor_ref="codex-foreign")
    try:
        with pytest.raises(IssueSourceProjectionRefusal):
            await issue.prepare_start_progress_projection(
                request, workspace_client=workspace
            )
        assert source.read_bytes() == body
        assert workspace._owner.coordinator is None
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["ambiguous", "changed", "missing"])
async def test_harness_changes_refuse_before_motion(inputs, monkeypatch, change):
    source, workspace, issue, request = inputs
    before = source.read_bytes()
    if change == "ambiguous":
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "foreign")
    if change == "changed":
        monkeypatch.setenv("CODEX_THREAD_ID", "foreign")
    if change == "missing":
        monkeypatch.delenv("CODEX_THREAD_ID")
    with pytest.raises(
        (IssueSourceProjectionRefusal, WorkspaceSourceProjectionRefusal)
    ):
        await issue.prepare_start_progress_projection(
            request, workspace_client=workspace
        )
    assert source.read_bytes() == before
    monkeypatch.setenv("CODEX_THREAD_ID", "source-projection-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    await workspace.release_source_projection()


@pytest.mark.asyncio
async def test_cross_thread_refuses_original_plan(inputs):
    _, workspace, issue, request = inputs
    plan = await issue.prepare_start_progress_projection(
        request, workspace_client=workspace
    )
    state = record(issue, plan)
    try:

        def foreign_thread():
            with pytest.raises(
                WorkspaceSourceProjectionRefusal, match="origin_mismatch"
            ):
                workspace.verify_source_projection_plan(
                    state.workspace_plan, expected_binding=state.binding
                )

        await asyncio.to_thread(foreign_thread)
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
async def test_fork_refuses_original_handle_without_cleanup_or_effect(inputs):
    source, workspace, issue, request = inputs
    plan = await issue.prepare_start_progress_projection(
        request, workspace_client=workspace
    )
    state = record(issue, plan)
    before = source.read_bytes()
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        try:
            os.close(read_fd)
            try:
                workspace.verify_source_projection_plan(
                    state.workspace_plan, expected_binding=state.binding
                )
            except WorkspaceSourceProjectionRefusal as error:
                os.write(write_fd, error.code.encode())
            else:
                os.write(write_fd, b"unexpected_success")
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    try:
        assert os.read(read_fd, 128) == b"source_projection_origin_mismatch"
        assert (await asyncio.to_thread(os.waitpid, child, 0))[1] == 0
        assert source.read_bytes() == before
        workspace.verify_source_projection_plan(
            state.workspace_plan, expected_binding=state.binding
        )
    finally:
        os.close(read_fd)
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
async def test_live_handles_cannot_be_copied_or_serialized(inputs, operation):
    _, workspace, issue, _, plan, admission = await admitted(inputs)
    state = record(issue, plan)
    try:
        for handle in (
            workspace,
            issue,
            plan,
            admission,
            state.workspace_plan,
            state.workspace_admission,
        ):
            with pytest.raises(TypeError):
                operation(handle)
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
async def test_original_binding_can_roundtrip_but_cannot_reconstruct_plan(inputs):
    from aware_workspace_sdk.repository_source_projection_codec import (
        repository_source_projection_value_from_json,
        repository_source_projection_value_to_json,
    )

    _, workspace, issue, request = inputs
    plan = await issue.prepare_start_progress_projection(
        request, workspace_client=workspace
    )
    state = record(issue, plan)
    binding = repository_source_projection_value_from_json(
        type(state.binding), repository_source_projection_value_to_json(state.binding)
    )
    try:
        workspace.verify_source_projection_plan(
            state.workspace_plan, expected_binding=binding
        )
        with pytest.raises(WorkspaceSourceProjectionRefusal):
            workspace.verify_source_projection_plan(binding, expected_binding=binding)
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["unavailable", "mismatched"])
async def test_retention_reference_does_not_transfer_bytes(inputs, monkeypatch, state):
    _, workspace, _, _ = inputs
    original = await workspace.observe_source(target_path=PATH)
    retained = workspace._owner.retention
    monkeypatch.setattr(
        retained.__class__,
        "resolve_body",
        lambda *_: None if state == "unavailable" else b"wrong bytes",
    )
    try:
        with pytest.raises(WorkspaceSourceProjectionRefusal):
            await workspace.retain_projection_body(
                b"new", expected_content_digest=digest(b"new"), expected_size_bytes=3
            )
        assert original.body_ref
        assert not workspace._owner.plans
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("which", ["preimage", "postimage"])
async def test_missing_original_body_at_use_refuses_dispatch(
    inputs, monkeypatch, which
):
    source, workspace, issue, _, plan, admission = await admitted(inputs)
    state = record(issue, plan)
    cls = type(workspace._owner.retention)
    original = cls.resolve_body
    missing = (
        state.binding.preimage_body_ref
        if which == "preimage"
        else state.binding.projected_body_ref
    )
    monkeypatch.setattr(
        cls,
        "resolve_body",
        lambda self, ref: None if ref == missing else original(self, ref),
    )
    before = source.read_bytes()
    monkeypatch.setattr(
        mutation,
        "mutate_confined_file",
        lambda **_: pytest.fail("body custody missing before dispatch"),
    )
    try:
        with pytest.raises(IssueSourceProjectionRefusal) as refusal:
            await issue.execute_start_progress_projection(plan, admission=admission)
        assert refusal.value.observation.source_effect_state == "none"
        assert source.read_bytes() == before
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("which", ["observer", "operational_body", "receipt_index"])
async def test_postwrite_owner_failures_preserve_applied_evidence(
    inputs, monkeypatch, which
):
    source, workspace, issue, _, plan, admission = await admitted(inputs)

    def failed(*args, **kwargs):
        raise OSError("injected postwrite failure")

    if which == "observer":
        monkeypatch.setattr(workspace._owner.session.provider, "observe_paths", failed)
    if which == "operational_body":
        monkeypatch.setattr(workspace._owner.coordinator.body_store, "record", failed)
    if which == "receipt_index":
        monkeypatch.setattr(
            workspace._owner.coordinator._result_store, "record", failed
        )
    try:
        with pytest.raises(IssueSourceProjectionRefusal) as refusal:
            await issue.execute_start_progress_projection(plan, admission=admission)
        observation = refusal.value.observation
        assert observation.source_effect_state == "applied"
        assert observation.physical_effect.after_content_digest == digest(
            source.read_bytes()
        )
        assert not observation.ledger_complete
        with pytest.raises(IssueSourceProjectionRefusal):
            await issue.execute_start_progress_projection(plan, admission=admission)
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
async def test_racing_postimage_cannot_be_claimed_as_covered_delta(inputs, monkeypatch):
    source, workspace, issue, _, plan, admission = await admitted(inputs)
    original = workspace._owner.capture_owner.observe

    def raced(batch):
        source.write_bytes(b"another writer after confirmed projection")
        return original(batch)

    monkeypatch.setattr(workspace._owner.capture_owner, "observe", raced)
    try:
        with pytest.raises(IssueSourceProjectionRefusal) as refusal:
            await issue.execute_start_progress_projection(plan, admission=admission)
        assert refusal.value.observation.source_effect_state == "applied"
        assert refusal.value.observation.retention.state == "unknown"
        assert not refusal.value.observation.ledger_complete
    finally:
        await workspace.release_source_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("which", ["observer", "retention"])
async def test_failed_cleanup_never_regresses_known_publication(
    inputs, monkeypatch, which
):
    _, workspace, issue, _, plan, admission = await admitted(inputs)
    await issue.execute_start_progress_projection(plan, admission=admission)
    state = record(issue, plan)
    before = workspace.observe_source_projection(state.workspace_admission)

    def failed(*args):
        raise KeyboardInterrupt("cleanup unavailable")

    if which == "observer":
        monkeypatch.setattr(workspace._owner.session, "stop", failed)
    else:
        monkeypatch.setattr(
            type(workspace._owner.retention), "release_retention", failed
        )
    cleanup = await workspace.release_source_projection()
    assert cleanup.state == "unknown" and not cleanup.ledger_complete
    after = workspace.observe_source_projection(state.workspace_admission)
    assert after.source_effect_state == before.source_effect_state == "applied"
    assert after.retention == before.retention
    assert not after.ledger_complete
    assert await workspace.release_source_projection() is cleanup
    with pytest.raises(WorkspaceSourceProjectionRefusal):
        await workspace.project_source(
            state.workspace_plan, admission=state.workspace_admission
        )


@pytest.mark.asyncio
async def test_failed_initialization_disposes_only_original_acquired_resources(
    inputs, monkeypatch
):
    from aware_workspace_sdk.repository_delta_retention import (
        WorkspaceRepositoryDeltaRetentionClient,
    )

    _, workspace, _, _ = inputs

    def failed(*args, **kwargs):
        raise OSError("retention initialization refused")

    monkeypatch.setattr(
        WorkspaceRepositoryDeltaRetentionClient, "initialize_delta_retention", failed
    )
    with pytest.raises(WorkspaceSourceProjectionRefusal) as refusal:
        await workspace.observe_source(target_path=PATH)
    assert refusal.value.evidence.cleanup.observer_cleanup_state == "completed"
    assert workspace._owner.released
    assert not workspace._owner.plans


@pytest.mark.asyncio
async def test_unavailable_stronger_physical_profile_never_downgrades(inputs):
    from aware_workspace_sdk.repository_source_projection_values import (
        WorkspaceSourceProjectionRequest,
    )

    _, workspace, _, _ = inputs
    source = await workspace.observe_source(target_path=PATH)
    ref = await workspace.retain_projection_body(
        b"new", expected_content_digest=digest(b"new"), expected_size_bytes=3
    )
    try:
        with pytest.raises(
            WorkspaceSourceProjectionRefusal,
            match="continuous_root_backend_unavailable",
        ):
            await workspace.prepare_source_projection(
                WorkspaceSourceProjectionRequest(
                    source,
                    "issue_sdk.start_issue_progress",
                    REF,
                    "issue_start_progress_v0",
                    digest(b"new"),
                    3,
                    ref,
                    "continuous_root_v1",
                )
            )
        assert not workspace._owner.plans
    finally:
        await workspace.release_source_projection()


def test_domain_implementation_boundaries_and_one_writer():
    root = next(
        p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
    )
    issue_root = root / "workspaces/aware_coordination/modules/workflow"
    runtime = (
        issue_root
        / "libs/issue_operational_runtime/aware_issue_operational_runtime/source_projection.py"
    )
    physical = (
        issue_root
        / "sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/source_projection.py"
    )
    names = [
        node.module or ""
        for node in ast.walk(ast.parse(runtime.read_text()))
        if isinstance(node, ast.ImportFrom)
    ]
    assert not any(
        name.startswith(("aware_workspace_runtime", "aware_workspace_fs_adapter"))
        for name in names
    )
    physical_names = [
        node.module or ""
        for node in ast.walk(ast.parse(physical.read_text()))
        if isinstance(node, ast.ImportFrom)
    ]
    assert not any(name.startswith("aware_workspace") for name in physical_names)
    consume = next(
        node
        for node in ast.walk(ast.parse(runtime.read_text()))
        if isinstance(node, ast.FunctionDef) and node.name == "consume"
    )
    assert "workspace" not in ast.unparse(consume).replace("Workspace", "")
    mutation_source = Path(mutation.__file__).read_text()
    assert mutation_source.count("return mutate_confined_file(") == 1


@pytest.mark.asyncio
async def test_removing_real_consumption_guard_cannot_claim_domain_success(
    inputs, monkeypatch
):
    import aware_workspace_runtime.repository_source_projection as owner

    _, workspace, issue, _, plan, admission = await admitted(inputs)
    monkeypatch.setattr(
        owner, "consume_original_projection_plan", lambda *_args, **_kwargs: None
    )
    try:
        with pytest.raises(
            IssueSourceProjectionRefusal, match="consumption_unconfirmed"
        ) as refusal:
            await issue.execute_start_progress_projection(plan, admission=admission)
        assert refusal.value.observation.source_effect_state == "applied"
        assert record(issue, plan).consumption is None
    finally:
        await workspace.release_source_projection()


def test_fresh_baseline_is_exact_and_extension_is_bounded():
    import subprocess

    root = next(
        p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
    )
    ledger = json.loads(
        (
            root
            / "docs/reports/issue-workspace-source-projection-composition-inputs-20261010.json"
        ).read_text()
    )
    assert len(ledger["baseline_inputs"]) == 43
    for path, pin in ledger["baseline_inputs"].items():
        baseline = subprocess.check_output(
            ["git", "show", f"{ledger['revision']}:{path}"], cwd=root
        )
        assert hashlib.sha256(baseline).hexdigest() == pin["sha256"]
        assert (
            subprocess.check_output(
                ["git", "hash-object", "--stdin"], input=baseline, cwd=root, text=False
            )
            .strip()
            .decode()
            == pin["blob_oid"]
        )
        if pin["current_byte_disposition"] == "unchanged_baseline":
            assert (root / path).read_bytes() == baseline
        else:
            assert path.endswith("aware_workspace_runtime/repository_mutation.py")
            old_ast, new_ast = ast.parse(baseline), ast.parse((root / path).read_text())
            old_writer = next(
                n
                for n in ast.walk(old_ast)
                if isinstance(n, ast.FunctionDef) and n.name == "dispatch"
            )
            new_writer = next(
                n
                for n in ast.walk(new_ast)
                if isinstance(n, ast.FunctionDef) and n.name == "dispatch"
            )
            assert ast.dump(old_writer) == ast.dump(new_writer)
            old_method = next(
                n
                for n in ast.walk(old_ast)
                if isinstance(n, ast.AsyncFunctionDef) and n.name == "mutate"
            )
            new_method = next(
                n
                for n in ast.walk(new_ast)
                if isinstance(n, ast.AsyncFunctionDef) and n.name == "_mutate"
            )

            class StripProjectionSeams(ast.NodeTransformer):
                def visit_If(self, node):
                    if any(
                        isinstance(value, ast.Name) and value.id == "projection_plan"
                        for value in ast.walk(node.test)
                    ):
                        return None
                    return self.generic_visit(node)

            stripped = StripProjectionSeams().visit(new_method)
            stripped.name = "mutate"
            stripped.args.kwonlyargs = []
            stripped.args.kw_defaults = []
            assert ast.dump(old_method) == ast.dump(stripped)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "../outside.md",
        "/absolute.md",
        "a//b.md",
        "a/./b.md",
        "e\u0301/file.md",
        "a\u0080b.md",
        "a\\b.md",
    ],
)
async def test_noncanonical_source_paths_refuse_without_effect(inputs, path):
    source, workspace, _, _ = inputs
    before = source.read_bytes()
    try:
        with pytest.raises(WorkspaceSourceProjectionRefusal):
            await workspace.observe_source(target_path=path)
        assert source.read_bytes() == before
    finally:
        await workspace.release_source_projection()

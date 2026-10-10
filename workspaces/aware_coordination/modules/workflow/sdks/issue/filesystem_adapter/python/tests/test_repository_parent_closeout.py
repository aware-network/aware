"""Genuine parent/source-CAS/child writer loop; internal source bootstrap only."""

from __future__ import annotations

import copy
import hashlib
import os
import pickle
import stat
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from aware_issue_sdk import IssueCloseAdmission, IssueCloseRequest
from aware_issue_sdk.repository_publication import (
    IssueRepositoryPublicationBinding,
    IssueRepositoryPublicationClient,
    IssueRepositoryPublicationRefusal,
    IssueRepositoryPublicationRequest,
)
from aware_workspace_sdk.repository_publication.authority import (
    WorkspaceIssuePublicationEnrollmentClient,
    WorkspacePublicationHandleRefusal,
    WorkspaceRepositoryPublicationClient,
)
from aware_workspace_sdk.repository_publication.values import (
    WorkspaceRepositoryCommitRequest,
)
from test_repository_publication import _writer_work
from test_repository_publication import loop as original_loop

ISSUE_PATH = "docs/issues/2026/09/20/fb-2026-09-20-example.md"
ATTEMPT = "attempt:closeout"


def _digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(name="ready")
def ready_loop(tmp_path, monkeypatch):
    loop = original_loop.__wrapped__(tmp_path, monkeypatch)
    root, source, workspace, plan, runtime, issue, request = loop
    source.write_text(
        source.read_text().replace(
            "- `src/example.py`",
            f"- `src/example.py`\n- `{ISSUE_PATH}`",
        )
    )
    request = replace(request, expected_issue_source_sha256=_digest(source))
    admission, work = _writer_work((*loop[:-1], request))
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    assert result.admission_completion == "completed", result
    close = IssueCloseRequest(
        issue_ref=request.issue_ref,
        expected_source_sha256=_digest(source),
        client_intent_id="intent:closeout",
        actor_ref="codex-example",
        actor_evidence_ref="evidence:closeout",
        resolution="Completed exact source",
        verified_by=("genuine supplier tests",),
        publication_receipt_ref="git:" + result.commit_hash,
    )
    return root, source, workspace, runtime, issue, close, admission


def _prepare(ready):
    return ready[4].prepare_repository_closeout(ready[5], ATTEMPT)


def _child(ready, parent):
    root, _, workspace, _, issue, *_ = ready
    source_observation = issue.apply_repository_closeout_source(parent)
    assert source_observation.source_change_state == "applied"
    plan = workspace.plan_repository_commit(
        WorkspaceRepositoryCommitRequest(
            str(root), (ISSUE_PATH,), "Close genuine Issue", ATTEMPT
        )
    )
    b = plan.binding
    binding = IssueRepositoryPublicationBinding(
        b.binding_ref,
        b.attempt_ref,
        b.repository_ref,
        b.publication_reference,
        b.expected_head,
        b.target_paths,
        b.postimages_digest,
        b.message_digest,
        b.provider_generation,
        b.provider_ref,
        b.execution_id,
    )
    child = issue.bind_closeout_publication(parent, binding)
    work = WorkspaceIssuePublicationEnrollmentClient(
        workspace_client=workspace,
        issue_client=issue,
    ).enroll_issue_repository_publication(plan, child)
    return plan, child, work


def test_real_parent_closed_postimage_single_child_and_completion(ready):
    root, source, workspace, _, issue, close, *_ = ready
    before = source.read_bytes()
    parent = _prepare(ready)
    assert type(parent) is IssueCloseAdmission and parent.phase == "prepared"
    assert source.read_bytes() == before
    plan, child, work = _child(ready, parent)
    assert b"- Status: Closed" in source.read_bytes()
    assert close.resolution.encode() in source.read_bytes()
    assert close.publication_receipt_ref.encode() in source.read_bytes()
    assert (
        issue.observe_repository_publication_admission(child).purpose
        == "issue_closeout_publication"
    )
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    assert result.admission_completion == "completed", result
    effect = issue.observe_repository_publication_admission(child).publication
    completed = issue.finish_repository_closeout(parent, effect)
    assert completed.completion_state == "completed" and completed.ledger_complete
    assert completed.closeout_publication_receipt_ref == "git:" + result.commit_hash
    assert (
        completed.implementation_publication_receipt_ref
        == close.publication_receipt_ref
    )
    assert (
        subprocess.check_output(("git", "-C", str(root), "show", "HEAD:" + ISSUE_PATH))
        == source.read_bytes()
    )
    assert (
        issue.finish_repository_closeout(parent, effect).completion_state == "completed"
    )
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.publish_repository_commit(plan, work)
    with pytest.raises(IssueRepositoryPublicationRefusal):
        issue.bind_closeout_publication(
            parent, issue.observe_repository_publication_admission(child).binding
        )


@pytest.mark.parametrize(
    "change", ["digest", "actor", "owner", "status", "scope", "receipt"]
)
def test_prepare_refuses_invalid_authority_before_effects(ready, change):
    _, source, _, _, issue, close, *_ = ready
    if change == "digest":
        close = replace(close, expected_source_sha256="sha256:" + "0" * 64)
    elif change == "actor":
        close = replace(close, actor_ref="codex-foreign")
    elif change == "receipt":
        close = replace(close, publication_receipt_ref="git:" + "0" * 40)
    else:
        body = source.read_text()
        if change == "owner":
            body = body.replace("codex-example", "codex-foreign")
        elif change == "status":
            body = body.replace("In Progress", "Closed")
        else:
            body = body.replace(f"- `{ISSUE_PATH}`\n", "")
        source.write_text(body)
        close = replace(close, expected_source_sha256=_digest(source))
    before = source.read_bytes()
    with pytest.raises(IssueRepositoryPublicationRefusal):
        issue.prepare_repository_closeout(close, ATTEMPT)
    assert source.read_bytes() == before


def test_git_receipt_without_original_workspace_history_cannot_prepare(ready):
    from aware_issue_operational_runtime.repository_publication import (
        IssueRepositoryPublicationRuntime,
    )
    from aware_workspace_runtime.repository_publication import (
        WorkspaceRepositoryPublicationRuntime,
    )

    _, source, workspace, runtime, _, close, *_ = ready
    fresh_workspace = WorkspaceRepositoryPublicationClient(
        WorkspaceRepositoryPublicationRuntime(workspace._provider._physical)
    )
    fresh = IssueRepositoryPublicationClient(
        IssueRepositoryPublicationRuntime(
            source_port=runtime._source,
            workspace_client=fresh_workspace,
        )
    )
    before = source.read_bytes()
    with pytest.raises(
        IssueRepositoryPublicationRefusal, match="original_implementation_required"
    ):
        fresh.prepare_repository_closeout(close, ATTEMPT)
    assert source.read_bytes() == before


def test_original_workspace_receipt_without_original_issue_history_cannot_prepare(
    ready,
):
    from aware_issue_operational_runtime.repository_publication import (
        IssueRepositoryPublicationRuntime,
    )

    _, _, workspace, runtime, _, close, *_ = ready
    fresh = IssueRepositoryPublicationClient(
        IssueRepositoryPublicationRuntime(
            source_port=runtime._source,
            workspace_client=workspace,
        )
    )
    with pytest.raises(
        IssueRepositoryPublicationRefusal, match="original_issue_completion_required"
    ):
        fresh.prepare_repository_closeout(close, ATTEMPT)


def test_closed_source_never_grants_normal_publication_admission(ready):
    root, source, workspace, _, issue, close, *_ = ready
    parent = _prepare(ready)
    _child(ready, parent)
    other = workspace.plan_repository_commit(
        WorkspaceRepositoryCommitRequest(
            str(root),
            (ISSUE_PATH,),
            "Not a close parent",
            "attempt:other",
        )
    )
    b = other.binding
    binding = IssueRepositoryPublicationBinding(
        b.binding_ref,
        b.attempt_ref,
        b.repository_ref,
        b.publication_reference,
        b.expected_head,
        b.target_paths,
        b.postimages_digest,
        b.message_digest,
        b.provider_generation,
        b.provider_ref,
        b.execution_id,
    )
    with pytest.raises(IssueRepositoryPublicationRefusal):
        issue.admit_repository_publication(
            IssueRepositoryPublicationRequest(
                close.issue_ref,
                _digest(source),
                binding,
            )
        )


@pytest.mark.parametrize("phase", ["before_apply", "before_consume", "before_finish"])
def test_changed_exact_postimage_refuses_at_each_use(ready, phase):
    _, source, workspace, _, issue, *_ = ready
    parent = _prepare(ready)
    if phase == "before_apply":
        source.write_bytes(source.read_bytes() + b"\nconcurrent source\n")
        with pytest.raises(IssueRepositoryPublicationRefusal):
            issue.apply_repository_closeout_source(parent)
        assert b"In Progress" in source.read_bytes()
        return
    plan, child, work = _child(ready, parent)
    if phase == "before_finish":
        result = workspace.publish_repository_commit(plan, work)
        assert result.publication_state == "published", result
    source.write_bytes(source.read_bytes() + b"\nconcurrent postimage\n")
    if phase == "before_consume":
        result = workspace.publish_repository_commit(plan, work)
        assert result.publication_state != "published"
        assert (
            issue.observe_repository_publication_admission(child).consumption_state
            == "not_consumed"
        )
    else:
        with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
            issue.finish_repository_closeout(
                parent,
                issue.observe_repository_publication_admission(child).publication,
            )
        assert (
            raised.value.observation.publication_admission.publication.publication_state
            == "published"
        )
        assert raised.value.observation.completion_state == "pending"


def test_closeout_consumption_never_reciprocally_calls_workspace(ready, monkeypatch):
    _, _, workspace, runtime, _, *_ = ready
    parent = _prepare(ready)
    plan, _, work = _child(ready, parent)

    def forbidden(*args):
        pytest.fail("Consumption under repository transaction must not call Workspace")

    monkeypatch.setattr(runtime, "_verify_plan", forbidden)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    assert result.admission_completion == "completed", result


def test_unknown_unlock_retains_closed_source_without_parent_completion_or_rollback(
    ready, monkeypatch
):
    from aware_workspace_fs_adapter import git_writer

    _, source, workspace, _, issue, *_ = ready
    parent = _prepare(ready)
    plan, child, work = _child(ready, parent)
    original = git_writer.fcntl.flock

    def interrupted(fd, operation):
        if operation == git_writer.fcntl.LOCK_UN:
            raise KeyboardInterrupt("unlock unavailable")
        return original(fd, operation)

    monkeypatch.setattr(git_writer.fcntl, "flock", interrupted)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    assert result.admission_completion == "pending"
    assert (
        issue.observe_repository_publication_admission(child).consumption_state
        == "consumed"
    )
    with pytest.raises((TypeError, IssueRepositoryPublicationRefusal)):
        issue.finish_repository_closeout(parent, result)
    cleanup = issue.release_repository_closeout(parent)
    assert cleanup.publication.publication_state == "published"
    assert cleanup.publication.lock_release.repository_lock_release == "unknown"
    assert not cleanup.ledger_complete
    assert cleanup.source_observation.source_change_state == "applied"
    assert b"- Status: Closed" in source.read_bytes()
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.publish_repository_commit(plan, work)


def test_unknown_cas_and_missing_release_observations_preserve_child_uncertainty(
    ready, monkeypatch
):
    from aware_workspace_fs_adapter import git_writer

    root, source, workspace, _, issue, *_ = ready
    parent = _prepare(ready)
    plan, child, work = _child(ready, parent)
    original_git = git_writer._run_git

    def interrupted_cas(**arguments):
        value = original_git(**arguments)
        if arguments["args"][:2] == ("git", "update-ref"):
            raise KeyboardInterrupt("CAS return unavailable after actual update")
        return value

    def unavailable(transaction):
        raise RuntimeError("release observations unavailable")

    monkeypatch.setattr(git_writer, "_run_git", interrupted_cas)
    monkeypatch.setattr(
        workspace._provider._physical, "observe_transaction", unavailable
    )
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "unknown", result
    assert (
        subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"))
        .strip()
        .decode()
        == result.candidate_commit
    )
    cleanup = issue.release_repository_closeout(parent)
    assert cleanup.publication.publication_state == "unknown"
    assert cleanup.publication.reference_update == result.reference_update
    assert any(
        e.kind == "repository_reference_update" and e.state == "unknown"
        for e in cleanup.publication.effects
    )
    assert not cleanup.ledger_complete
    assert b"- Status: Closed" in source.read_bytes()
    again = issue.release_repository_closeout(parent)
    assert (
        replace(
            again.publication,
            workspace_observation_ref=cleanup.publication.workspace_observation_ref,
        )
        == cleanup.publication
    )
    assert again.diagnostics == cleanup.diagnostics
    assert (
        issue.observe_repository_publication_admission(child).consumption_state
        == "consumed"
    )
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.publish_repository_commit(plan, work)


def test_mode_durability_and_descriptor_cleanup(ready):
    _, source, _, _, issue, *_ = ready
    source.chmod(0o640)
    # Request was captured before mode change; capture its current exact bytes.
    before = len(os.listdir("/proc/self/fd"))
    parent = _prepare(ready)
    assert len(os.listdir("/proc/self/fd")) == before + 1
    observation = issue.apply_repository_closeout_source(parent)
    assert observation.source_mode_before == observation.source_mode_after == 0o640
    assert observation.durability_confirmed is True
    assert stat.S_IMODE(source.stat().st_mode) == 0o640
    assert len(os.listdir("/proc/self/fd")) == before
    cleanup = issue.release_repository_closeout(parent)
    assert cleanup.cleanup_state == "completed"
    assert issue.release_repository_closeout(parent).cleanup_state == "completed"
    assert b"- Status: Closed" in source.read_bytes()


def test_release_prepared_parent_retires_without_source_mutation(ready):
    _, source, _, _, issue, *_ = ready
    before_body = source.read_bytes()
    before_fd = len(os.listdir("/proc/self/fd"))
    parent = _prepare(ready)
    assert len(os.listdir("/proc/self/fd")) == before_fd + 1
    cleanup = issue.release_repository_closeout(parent)
    assert cleanup.cleanup_state == "completed" and cleanup.source_observation is None
    assert source.read_bytes() == before_body
    assert len(os.listdir("/proc/self/fd")) == before_fd
    with pytest.raises(IssueRepositoryPublicationRefusal):
        issue.apply_repository_closeout_source(parent)


def test_attempt_and_parent_cannot_be_reconstructed_or_reused(ready):
    parent = _prepare(ready)
    for operation in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            operation(parent)
    with pytest.raises(TypeError):
        IssueCloseAdmission()
    with pytest.raises(IssueRepositoryPublicationRefusal):
        _prepare(ready)
    with pytest.raises(IssueRepositoryPublicationRefusal):
        ready[4].apply_repository_closeout_source(object.__new__(IssueCloseAdmission))


def test_competing_parent_applications_only_one_source_effect(ready):
    parent = _prepare(ready)

    def apply():
        try:
            return ready[4].apply_repository_closeout_source(parent)
        except IssueRepositoryPublicationRefusal as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: apply(), range(2)))
    assert (
        sum(not isinstance(r, IssueRepositoryPublicationRefusal) for r in results) == 1
    )
    assert len(ready[3]._close_handles[parent].physical.effects) == 1


@pytest.mark.parametrize(
    "point", ["before", "after_replace", "after_finish", "ledger_read"]
)
def test_interrupted_source_paths_preserve_effects_and_terminal_authority(
    ready, monkeypatch, point
):
    from aware_file_system.retained_mutation import RetainedPhysicalMutation

    _, source, _, runtime, issue, *_ = ready
    parent = _prepare(ready)
    physical = runtime._close_handles[parent].physical
    original_replace = RetainedPhysicalMutation.replace_manifest
    original_finish = RetainedPhysicalMutation.finish
    original_effects = RetainedPhysicalMutation.effects

    def interrupt_replace(holder):
        if point == "before":
            raise KeyboardInterrupt("before replacement")
        original_replace(holder)
        raise KeyboardInterrupt("after replacement")

    def interrupt_finish(holder):
        original_finish(holder)
        raise KeyboardInterrupt("after finish")

    def unavailable_effects(holder):
        raise KeyboardInterrupt("effect read unavailable")

    if point in {"before", "after_replace"}:
        monkeypatch.setattr(
            RetainedPhysicalMutation, "replace_manifest", interrupt_replace
        )
    elif point == "after_finish":
        monkeypatch.setattr(RetainedPhysicalMutation, "finish", interrupt_finish)
    else:
        monkeypatch.setattr(
            RetainedPhysicalMutation, "effects", property(unavailable_effects)
        )
    if point == "ledger_read":
        # A source result that cannot be represented as a complete original
        # ledger must not return as successful authority.
        with pytest.raises(IssueRepositoryPublicationRefusal):
            issue.apply_repository_closeout_source(parent)
    else:
        with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
            issue.apply_repository_closeout_source(parent)
        observation = raised.value.observation.source_observation
        assert observation.source_change_state == (
            "not_attempted" if point == "before" else "applied"
        )
        assert observation.cleanup_state == "unknown"
        assert not observation.ledger_complete
    assert (b"- Status: Closed" in source.read_bytes()) is (point != "before")
    assert parent.phase == "refused"
    with pytest.raises(IssueRepositoryPublicationRefusal):
        issue.apply_repository_closeout_source(parent)
    monkeypatch.setattr(RetainedPhysicalMutation, "effects", original_effects)
    assert len(physical.effects) == (0 if point == "before" else 1)


def test_cleanup_interruption_is_once_only_unknown_and_preserves_input(
    ready, monkeypatch
):
    from aware_file_system.retained_mutation import RetainedPhysicalMutation

    _, source, _, runtime, issue, *_ = ready
    before = source.read_bytes()
    parent = _prepare(ready)
    physical = runtime._close_handles[parent].physical
    release = RetainedPhysicalMutation.release
    calls = []

    def interrupted(holder):
        calls.append(holder)
        release(holder)
        raise KeyboardInterrupt("cleanup return unavailable")

    monkeypatch.setattr(RetainedPhysicalMutation, "release", interrupted)
    first = issue.release_repository_closeout(parent)
    second = issue.release_repository_closeout(parent)
    assert first.cleanup_state == second.cleanup_state == "unknown"
    assert not first.ledger_complete and not second.ledger_complete
    assert len(calls) == 1 and calls[0] is physical
    assert source.read_bytes() == before


def test_owner_observation_failure_after_publication_preserves_known_result(
    ready, monkeypatch
):
    _, source, workspace, _, issue, *_ = ready
    parent = _prepare(ready)
    plan, child, work = _child(ready, parent)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    expected = issue.observe_repository_publication_admission(child).publication

    def unavailable(*args):
        raise KeyboardInterrupt("later original observation unavailable")

    monkeypatch.setattr(workspace._provider, "observe_repository_attempt", unavailable)
    # Completed original Issue evidence is retained, never replaced by an
    # unavailable read or reconstructed solely from Git facts.
    cleanup = issue.release_repository_closeout(parent)
    assert cleanup.publication == expected
    assert b"- Status: Closed" in source.read_bytes()


@pytest.mark.parametrize("kind", ["execution", "process", "foreign_handle"])
def test_original_parent_guards(ready, monkeypatch, kind):
    _, source, workspace, runtime, issue, *_ = ready
    parent = _prepare(ready)
    before = source.read_bytes()
    if kind == "execution":
        monkeypatch.setenv("CODEX_THREAD_ID", "changed")
    elif kind == "process":
        runtime._pid += 1
    else:
        from aware_issue_operational_runtime.repository_publication import (
            IssueRepositoryPublicationRuntime,
        )

        issue = IssueRepositoryPublicationClient(
            IssueRepositoryPublicationRuntime(
                source_port=runtime._source,
                workspace_client=workspace,
            )
        )
    with pytest.raises(IssueRepositoryPublicationRefusal):
        issue.apply_repository_closeout_source(parent)
    assert source.read_bytes() == before
    if kind == "process":
        runtime._pid -= 1
    ready[4].release_repository_closeout(parent)


def test_sdk_observations_do_not_hold_issue_registry_lock(ready, monkeypatch):
    _, _, workspace, runtime, issue, *_ = ready
    original = workspace._provider.observe_repository_publication

    def verify(request):
        assert not runtime._lock._is_owned()
        return original(request)

    monkeypatch.setattr(workspace._provider, "observe_repository_publication", verify)
    parent = _prepare(ready)
    plan, child, work = _child(ready, parent)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    issue.finish_repository_closeout(
        parent, issue.observe_repository_publication_admission(child).publication
    )


def test_failed_issuance_after_retention_disposes_original_descriptors(
    ready, monkeypatch
):
    _, source, _, runtime, issue, *_ = ready
    before_fd = len(os.listdir("/proc/self/fd"))
    before_source = source.read_bytes()

    def interrupted(*args):
        raise KeyboardInterrupt("failed entry after physical retention")

    monkeypatch.setattr(runtime._source, "validate_closeout", interrupted)
    with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
        _prepare(ready)
    assert raised.value.observation.source_observation is None
    assert not raised.value.observation.ledger_complete
    assert len(os.listdir("/proc/self/fd")) == before_fd
    assert source.read_bytes() == before_source
    with pytest.raises(IssueRepositoryPublicationRefusal):
        issue.prepare_repository_closeout(ready[5], ATTEMPT)


def test_real_fork_refuses_without_retiring_parent_original(ready):
    parent = _prepare(ready)
    before = ready[1].read_bytes()
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            ready[4].apply_repository_closeout_source(parent)
            message = b"unexpected-authority"
        except IssueRepositoryPublicationRefusal as error:
            message = error.code.encode()
        os.write(write_fd, message)
        os.close(write_fd)
        os._exit(0)
    os.close(write_fd)
    try:
        message = os.read(read_fd, 200)
    finally:
        os.close(read_fd)
        os.waitpid(child, 0)
    assert message == b"issue_publication_cross_process_refused"
    assert parent.phase == "prepared" and ready[1].read_bytes() == before
    assert (
        ready[4].apply_repository_closeout_source(parent).source_change_state
        == "applied"
    )

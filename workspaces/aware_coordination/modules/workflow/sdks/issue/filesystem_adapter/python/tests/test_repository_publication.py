"""Real Issue source + original Workspace plan SDK composition.

Consumption is genuine; no test here qualifies writer/finish/closeout or an
installed consumer. The selected host CLI remains untouched.
"""

from __future__ import annotations

import copy
import fcntl
import hashlib
import os
import pickle
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_fs_adapter.repository_publication import (
    FilesystemIssueRepositorySourcePort,
)
from aware_issue_operational_runtime.repository_publication import (
    IssueRepositoryPublicationRuntime,
)
from aware_issue_sdk.repository_publication import (
    IssueRepositoryPublicationAdmission,
    IssueRepositoryPublicationBinding,
    IssueRepositoryPublicationClient,
    IssueRepositoryPublicationConsumeRequest,
    IssueRepositoryPublicationEnrollmentRequest,
    IssueRepositoryPublicationLease,
    IssueRepositoryPublicationRefusal,
    IssueRepositoryPublicationRequest,
    repository_publication_value_from_payload,
    repository_publication_value_to_payload,
)
from aware_workspace_runtime.repository_publication import (
    WorkspaceRepositoryPublicationRuntime,
)
from aware_workspace_sdk.repository_publication.authority import (
    WorkspaceIssuePublicationEnrollmentClient,
    WorkspacePublicationHandleRefusal,
    WorkspacePublicationWorkAdmission,
    WorkspaceRepositoryPublicationClient,
)
from aware_workspace_sdk.repository_publication.values import (
    WorkspaceRepositoryAttemptObserveRequest,
    WorkspaceRepositoryCommitRequest,
    WorkspaceRepositoryPlanVerificationRequest,
)
from test_provider import ISSUE_REF, _repository


def _writer_work(loop):
    root, _, workspace, plan, _, client, request = loop
    for key, value in (
        ("user.name", "Aware Test"),
        ("user.email", "aware-test@example.invalid"),
    ):
        subprocess.run(("git", "-C", str(root), "config", key, value), check=True)
    admission = client.admit_repository_publication(request)
    work = WorkspaceIssuePublicationEnrollmentClient(
        workspace_client=workspace, issue_client=client
    ).enroll_issue_repository_publication(plan, admission)
    return admission, work


def test_original_writer_genuine_publication_and_release_gated_finish(loop):
    root, _, workspace, plan, _, issue, _ = loop
    admission, work = _writer_work(loop)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    assert result.reference_update == "cas_applied"
    assert result.index_projection == "applied"
    assert result.lock_release.repository_lock_release == "confirmed_released"
    assert result.admission_completion == "completed", result
    assert (
        issue.observe_repository_publication_admission(admission).completion_state
        == "completed"
    )
    body = subprocess.check_output(
        ("git", "-C", str(root), "show", "HEAD:src/example.py")
    )
    assert body == b"approved candidate\n"
    assert (
        subprocess.check_output(
            ("git", "-C", str(root), "diff", "--cached", "--name-only")
        )
        == b""
    )
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.publish_repository_commit(plan, work)
    assert workspace.finish_repository_publication(work) == result


def test_original_writer_refuses_stale_workspace_plan_before_issue_spend(loop):
    root, _, workspace, plan, _, issue, _ = loop
    admission, work = _writer_work(loop)
    (root / "src/example.py").write_bytes(b"changed after plan\n")
    result = workspace.publish_repository_commit(plan, work)
    assert result.reference_update == "unknown"
    assert "workspace_publication_postimages_stale" in result.diagnostics
    assert (
        issue.observe_repository_publication_admission(admission).consumption_state
        == "not_consumed"
    )
    assert (
        subprocess.run(
            ("git", "-C", str(root), "rev-parse", "--verify", "HEAD"),
            capture_output=True,
            check=False,
        ).returncode
        != 0
    )


def test_original_writer_stages_captured_binary_bytes_not_late_worktree(
    loop, monkeypatch
):
    from aware_workspace_fs_adapter import git_writer

    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    original = git_writer._initialize_isolated_index

    def changed_after_consumption(**arguments):
        original(**arguments)
        (root / "src/example.py").write_bytes(b"late unapproved bytes\x00\xff\n")

    monkeypatch.setattr(
        git_writer, "_initialize_isolated_index", changed_after_consumption
    )
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    assert (
        subprocess.check_output(("git", "-C", str(root), "show", "HEAD:src/example.py"))
        == b"approved candidate\n"
    )
    assert (root / "src/example.py").read_bytes() == b"late unapproved bytes\x00\xff\n"


def test_original_writer_preserves_foreign_staging(loop):
    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    (root / "foreign.txt").write_bytes(b"foreign staged bytes\n")
    subprocess.run(("git", "-C", str(root), "add", "foreign.txt"), check=True)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    assert (
        subprocess.check_output(("git", "-C", str(root), "show", ":foreign.txt"))
        == b"foreign staged bytes\n"
    )
    assert (
        subprocess.run(
            ("git", "-C", str(root), "cat-file", "-e", "HEAD:foreign.txt"),
            capture_output=True,
            check=False,
        ).returncode
        != 0
    )


def test_original_writer_unknown_unlock_keeps_publication_and_spent_authority(
    loop, monkeypatch
):
    from aware_workspace_fs_adapter import git_writer

    _, _, workspace, plan, _, issue, _ = loop
    admission, work = _writer_work(loop)
    original = git_writer.fcntl.flock

    def interrupted_unlock(descriptor, operation):
        if operation == fcntl.LOCK_UN:
            raise KeyboardInterrupt("unlock result unavailable")
        return original(descriptor, operation)

    monkeypatch.setattr(git_writer.fcntl, "flock", interrupted_unlock)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    assert result.lock_release.repository_lock_release == "unknown"
    assert result.admission_completion == "pending"
    observed = issue.observe_repository_publication_admission(admission)
    assert observed.consumption_state == "consumed"
    assert observed.completion_state != "completed"
    assert workspace.finish_repository_publication(work) == result
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.publish_repository_commit(plan, work)


@pytest.mark.parametrize("error_type", (RuntimeError, KeyboardInterrupt))
@pytest.mark.parametrize("release_before_cleanup", (False, True))
def test_original_writer_double_release_observation_failure_retains_publication(
    loop, monkeypatch, error_type, release_before_cleanup
):
    root, _, workspace, plan, _, issue, _ = loop
    admission, work = _writer_work(loop)
    physical = workspace._provider._physical
    original_release = physical.release
    original_observe = physical.observe_transaction
    calls = []

    def unavailable_observation(transaction):
        calls.append("observe")
        raise error_type("release observation unavailable")

    def unavailable_release(transaction):
        calls.append("release")
        if release_before_cleanup:
            raise error_type("release unavailable before cleanup")
        return original_release(transaction)

    def forbidden_finish(*arguments):
        pytest.fail("Issue finish requires confirmed release")

    monkeypatch.setattr(physical, "observe_transaction", unavailable_observation)
    monkeypatch.setattr(physical, "release", unavailable_release)
    monkeypatch.setattr(
        IssueRepositoryPublicationClient,
        "finish_repository_publication",
        forbidden_finish,
    )
    try:
        result = workspace.publish_repository_commit(plan, work)
        head = (
            subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"))
            .strip()
            .decode()
        )
        assert result.publication_state == "published", result
        assert result.commit_hash == result.candidate_commit == head
        assert result.reference_update == "cas_applied"
        assert result.original_writer_report.commit_hash == head
        assert result.original_writer_report.staged_paths == ["src/example.py"]
        assert result.effects and result.effects[0].state == "applied"
        assert result.cleanup_state == "unknown"
        assert result.lock_release.repository_lock_release == "unknown"
        assert not result.ledger_complete
        assert result.admission_completion == "pending"
        assert "physical_release_return:" + error_type.__name__ in result.diagnostics
        assert (
            "physical_release_observation:" + error_type.__name__ in result.diagnostics
        )
        assert work.phase == plan.phase == "spent"
        observed_issue = issue.observe_repository_publication_admission(admission)
        assert observed_issue.consumption_state == "consumed"
        assert observed_issue.completion_state == "not_attempted"
        binding = plan.binding
        observed = workspace.observe_repository_attempt(
            WorkspaceRepositoryAttemptObserveRequest(
                binding.repository_ref,
                binding.binding_ref,
                binding.attempt_ref,
                binding.provider_ref,
                binding.provider_generation,
                binding.execution_id,
            )
        )
        assert observed.attempt_recognized and observed.result == result
        assert observed.lock_release == result.lock_release
        assert not observed.ledger_complete
        assert workspace.finish_repository_publication(work) == result
        with pytest.raises(WorkspacePublicationHandleRefusal):
            workspace.publish_repository_commit(plan, work)
        assert calls == ["release"] + ["observe"] * (1 if release_before_cleanup else 2)
        assert (
            subprocess.check_output(
                ("git", "-C", str(root), "show", "HEAD:src/example.py")
            )
            == b"approved candidate\n"
        )
        assert (
            subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"))
            .strip()
            .decode()
            == head
        )
    finally:
        # Test-harness disposal of the deliberately unreleased real lock, not
        # an operational cleanup retry or renewed publication authority.
        monkeypatch.setattr(physical, "observe_transaction", original_observe)
        if release_before_cleanup:
            transaction = workspace._provider._work_admissions[work].transaction
            original_release(transaction)


@pytest.mark.parametrize("observation_error", (RuntimeError, KeyboardInterrupt))
@pytest.mark.parametrize("cas_outcome", ("unknown", "cas_failed"))
def test_original_writer_cas_outcome_survives_double_observation_failure(
    loop, monkeypatch, observation_error, cas_outcome
):
    from aware_workspace_fs_adapter import git_writer

    root, _, workspace, plan, _, issue, _ = loop
    admission, work = _writer_work(loop)
    physical = workspace._provider._physical
    original_git = git_writer._run_git
    original_publish = git_writer._publish_staged_transaction
    original_release = physical.release
    calls = []

    def interrupted_cas(**arguments):
        value = original_git(**arguments)
        if arguments["args"][:2] == ("git", "update-ref"):
            raise KeyboardInterrupt("CAS return unavailable after real update-ref")
        return value

    def competing_publication(**arguments):
        subprocess.run(
            ("git", "-C", str(root), "commit", "-qm", "competing publication"),
            check=True,
        )
        return original_publish(**arguments)

    def unavailable_observation(transaction):
        calls.append("observe")
        raise observation_error("release observation unavailable")

    def release(transaction):
        calls.append("release")
        return original_release(transaction)

    def forbidden_finish(*arguments):
        pytest.fail("Unavailable release cannot authorize Issue completion")

    if cas_outcome == "unknown":
        monkeypatch.setattr(git_writer, "_run_git", interrupted_cas)
    else:
        (root / "foreign.txt").write_bytes(b"competing candidate\n")
        subprocess.run(("git", "-C", str(root), "add", "foreign.txt"), check=True)
        monkeypatch.setattr(
            git_writer, "_publish_staged_transaction", competing_publication
        )
    monkeypatch.setattr(physical, "observe_transaction", unavailable_observation)
    monkeypatch.setattr(physical, "release", release)
    monkeypatch.setattr(
        IssueRepositoryPublicationClient,
        "finish_repository_publication",
        forbidden_finish,
    )
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == (
        "unknown" if cas_outcome == "unknown" else "not_published"
    ), result
    reference_effects = tuple(
        effect
        for effect in result.effects
        if effect.kind == "repository_reference_update"
    )
    assert len(reference_effects) == 1
    assert reference_effects[0].state == (
        "unknown" if cas_outcome == "unknown" else "failed"
    )
    assert reference_effects[0].after_ref is None
    assert result.candidate_commit == result.original_writer_report.candidate_commit
    assert result.candidate_commit
    assert result.reference_update == (
        "not_run" if cas_outcome == "unknown" else "cas_failed"
    )
    assert result.original_writer_report.error
    assert result.cleanup_state == "unknown"
    assert result.lock_release.repository_lock_release == "unknown"
    assert not result.ledger_complete
    assert result.admission_completion == "pending"
    assert work.phase == plan.phase == "spent"
    observed_issue = issue.observe_repository_publication_admission(admission)
    assert observed_issue.consumption_state == "consumed"
    assert observed_issue.completion_state == "not_attempted"
    binding = plan.binding
    observed = workspace.observe_repository_attempt(
        WorkspaceRepositoryAttemptObserveRequest(
            binding.repository_ref,
            binding.binding_ref,
            binding.attempt_ref,
            binding.provider_ref,
            binding.provider_generation,
            binding.execution_id,
        )
    )
    assert observed.result == result and not observed.ledger_complete
    assert workspace.finish_repository_publication(work) == result
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.publish_repository_commit(plan, work)
    assert calls == ["release", "observe", "observe"]
    # Diagnostic HEAD is not passed to any operational result or authority.
    head = (
        subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"))
        .strip()
        .decode()
    )
    if cas_outcome == "unknown":
        assert head == result.candidate_commit
        assert tuple(
            (root / ".git/aware/transactions").glob("repository-reference-*.json")
        )
    else:
        assert head != result.candidate_commit


def test_original_writer_fresh_issue_refusal_has_no_transaction_index_effects(loop):
    root, issue_source, workspace, plan, _, issue, _ = loop
    admission, work = _writer_work(loop)
    issue_source.write_bytes(issue_source.read_bytes() + b"\nchanged issue\n")
    result = workspace.publish_repository_commit(plan, work)
    assert result.original_writer_report is None
    assert result.lock_release.repository_lock_release == "confirmed_released"
    assert result.admission_completion == "not_attempted"
    assert not (root / ".git/aware-transactions").exists()
    assert (
        issue.observe_repository_publication_admission(admission).consumption_state
        == "not_consumed"
    )


def test_original_writer_finish_checks_actual_released_repository_lock(
    loop, monkeypatch
):
    from aware_workspace_fs_adapter import git_writer

    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    original = WorkspaceRepositoryPublicationClient.observe_repository_attempt
    calls = []

    def verified_release(client, request):
        lock_path = git_writer._repository_mutation_lock_path(repo_root=root)
        with lock_path.open("a+") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        calls.append(request.attempt_ref)
        return original(client, request)

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient,
        "observe_repository_attempt",
        verified_release,
    )
    result = workspace.publish_repository_commit(plan, work)
    assert result.admission_completion == "completed", result
    assert calls == [plan.binding.attempt_ref]


def test_original_writer_native_cas_race_refuses_without_foreign_index_loss(
    loop, monkeypatch
):
    from aware_workspace_fs_adapter import git_writer

    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    (root / "foreign.txt").write_bytes(b"foreign staged bytes\n")
    subprocess.run(("git", "-C", str(root), "add", "foreign.txt"), check=True)
    original = git_writer._publish_staged_transaction

    def race(**arguments):
        subprocess.run(
            ("git", "-C", str(root), "commit", "-qm", "competing native publication"),
            check=True,
        )
        return original(**arguments)

    monkeypatch.setattr(git_writer, "_publish_staged_transaction", race)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "not_published", result
    assert result.reference_update == "cas_failed"
    assert result.original_writer_report.error
    assert result.admission_completion == "completed", result
    assert (
        subprocess.check_output(("git", "-C", str(root), "show", "HEAD:foreign.txt"))
        == b"foreign staged bytes\n"
    )
    assert (
        subprocess.run(
            ("git", "-C", str(root), "cat-file", "-e", "HEAD:src/example.py"),
            capture_output=True,
            check=False,
        ).returncode
        != 0
    )


def test_original_writer_interrupted_cas_return_stays_unknown_without_replay(
    loop, monkeypatch
):
    from aware_workspace_fs_adapter import git_writer

    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    original = git_writer._run_git

    def interrupted_return(**arguments):
        value = original(**arguments)
        if arguments["args"][:2] == ("git", "update-ref"):
            raise KeyboardInterrupt("CAS return unavailable")
        return value

    monkeypatch.setattr(git_writer, "_run_git", interrupted_return)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "unknown", result
    assert result.admission_completion == "pending"
    assert result.candidate_commit
    assert not result.ledger_complete
    assert result.effects[0].state == "unknown"
    assert tuple((root / ".git/aware/transactions").glob("repository-reference-*.json"))
    assert (
        subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"))
        .strip()
        .decode()
        == result.candidate_commit
    )
    assert workspace.finish_repository_publication(work) == result
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.publish_repository_commit(plan, work)


def test_original_writer_interrupted_postpublication_return_preserves_known_cas(
    loop, monkeypatch
):
    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    physical = workspace._provider._physical
    original = physical.publish

    def failed_return(*arguments):
        original(*arguments)
        raise KeyboardInterrupt("published return lost")

    monkeypatch.setattr(physical, "publish", failed_return)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    assert (
        result.commit_hash
        == subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"))
        .strip()
        .decode()
    )
    assert result.admission_completion == "completed", result
    assert "KeyboardInterrupt" in result.diagnostics


def test_original_writer_refuses_foreign_work_handle(loop):
    _, _, workspace, plan, _, _, _ = loop
    _writer_work(loop)
    forged = object.__new__(WorkspacePublicationWorkAdmission)
    with pytest.raises(
        WorkspacePublicationHandleRefusal,
        match="workspace_original_work_admission_required",
    ):
        workspace.publish_repository_commit(plan, forged)


def test_original_writer_consumption_does_not_reciprocate_under_real_lock(
    loop, monkeypatch
):
    from aware_workspace_fs_adapter import git_writer

    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    original = WorkspaceRepositoryPublicationClient.verify_repository_plan

    def forbid_held_lock_callback(client, request):
        with git_writer._repository_mutation_lock_path(repo_root=root).open(
            "a+"
        ) as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return original(client, request)

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient,
        "verify_repository_plan",
        forbid_held_lock_callback,
    )
    result = workspace.publish_repository_commit(plan, work)
    assert result.admission_completion == "completed", result


def test_original_writer_results_do_not_share_mutable_ledger_fields(loop):
    _, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    result = workspace.publish_repository_commit(plan, work)
    original_paths = list(result.original_writer_report.requested_paths)
    result.original_writer_report.requested_paths.clear()
    result.original_writer_report.command_log.clear()
    fresh = workspace.finish_repository_publication(work)
    assert fresh.original_writer_report.requested_paths == original_paths
    assert fresh.original_writer_report.command_log


def test_original_writer_plan_release_refuses_during_consumed_publication(
    loop, monkeypatch
):
    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    physical = workspace._provider._physical
    original = physical.publish

    def in_use(*arguments):
        with pytest.raises(
            WorkspacePublicationHandleRefusal, match="workspace_plan_in_use"
        ):
            workspace.release_repository_plan(plan)
        with pytest.raises(
            WorkspacePublicationHandleRefusal, match="workspace_work_admission_in_use"
        ):
            workspace.release_publication_work_admission(work)
        return original(*arguments)

    monkeypatch.setattr(physical, "publish", in_use)
    result = workspace.publish_repository_commit(plan, work)
    assert result.admission_completion == "completed", result
    assert (
        subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"))
        .strip()
        .decode()
        == result.commit_hash
    )


def test_original_writer_late_execution_refusal_preserves_cas_without_finish_replay(
    loop, monkeypatch
):
    _, _, workspace, plan, _, issue, _ = loop
    admission, work = _writer_work(loop)
    physical = workspace._provider._physical
    original = physical.publish

    def changed_execution_after_publication(*arguments):
        value = original(*arguments)
        monkeypatch.setenv("CODEX_THREAD_ID", "different-execution")
        return value

    monkeypatch.setattr(physical, "publish", changed_execution_after_publication)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "published", result
    assert result.commit_hash
    assert result.admission_completion == "unknown"
    assert "workspace_execution_changed" in result.diagnostics
    monkeypatch.setenv("CODEX_THREAD_ID", "example")
    before = issue.observe_repository_publication_admission(admission)
    assert before.completion_state == "not_attempted"
    assert workspace.finish_repository_publication(work) == result
    assert (
        issue.observe_repository_publication_admission(admission).completion_state
        == "not_attempted"
    )


@pytest.fixture
def loop(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "example")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    root = _repository(tmp_path)
    subprocess.run(
        ("git", "init", "-q", "--initial-branch=main", str(root)), check=True
    )
    source = root / "src/example.py"
    source.parent.mkdir()
    source.write_bytes(b"approved candidate\n")
    issue = root / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    repository = Path(__file__).resolve().parents[9]
    monkeypatch.syspath_prepend(
        str(
            repository
            / "workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python"
        )
    )
    from aware_workspace_fs_adapter.repository_publication import (
        FilesystemRepositoryCandidatePort,
    )

    workspace = WorkspaceRepositoryPublicationClient(
        WorkspaceRepositoryPublicationRuntime(
            FilesystemRepositoryCandidatePort(repository_root=root)
        )
    )
    plan = workspace.plan_repository_commit(
        WorkspaceRepositoryCommitRequest(
            str(root), ("src/example.py",), "Approved exact source", "attempt:1"
        )
    )
    binding = plan.binding
    issue_binding = IssueRepositoryPublicationBinding(
        binding.binding_ref,
        binding.attempt_ref,
        binding.repository_ref,
        binding.publication_reference,
        binding.expected_head,
        binding.target_paths,
        binding.postimages_digest,
        binding.message_digest,
        binding.provider_generation,
        binding.provider_ref,
        binding.execution_id,
    )
    source_port = FilesystemIssueRepositorySourcePort(
        FilesystemIssueOperationProvider(repository_root=root)
    )
    runtime = IssueRepositoryPublicationRuntime(
        source_port=source_port, workspace_client=workspace
    )
    client = IssueRepositoryPublicationClient(runtime)
    request = IssueRepositoryPublicationRequest(
        ISSUE_REF,
        "sha256:" + hashlib.sha256(issue.read_bytes()).hexdigest(),
        issue_binding,
    )
    return root, issue, workspace, plan, runtime, client, request


def enrolled(loop):
    *_, client, request = loop
    admission = client.admit_repository_publication(request)
    enrollment = client.enroll_repository_publication(
        admission,
        IssueRepositoryPublicationEnrollmentRequest(
            request.binding,
            request.binding.workspace_provider_ref,
            "repository_publication",
        ),
    )
    b = request.binding
    consume = IssueRepositoryPublicationConsumeRequest(
        b.workspace_binding_ref,
        b.attempt_ref,
        b.workspace_provider_ref,
        b.workspace_provider_generation,
        b.execution_id,
        b.workspace_provider_ref,
        "repository_publication",
    )
    return admission, enrollment, consume


def test_genuine_source_scope_sdk_enrollment_and_single_consumption(loop):
    root, issue, _, plan, _, client, request = loop
    before = issue.read_bytes()
    admission, enrollment, consume = enrolled(loop)
    assert admission.phase == "enrolled"
    lease = client.consume_repository_publication(enrollment, consume)
    assert type(lease) is IssueRepositoryPublicationLease
    assert lease.phase == "consumed" and lease.receipt_ref.startswith(
        "issue-publication-work:"
    )
    observation = client.observe_repository_publication_admission(admission)
    assert observation.consumption_state == "consumed"
    assert observation.work_admission_receipt_ref == lease.receipt_ref
    assert observation.binding == request.binding
    assert (
        observation.publication is None
        and observation.completion_state == "not_attempted"
    )
    assert plan.phase == "planned"
    assert issue.read_bytes() == before
    assert not (root / ".git/index").exists()
    with pytest.raises(IssueRepositoryPublicationRefusal, match="terminal"):
        client.consume_repository_publication(enrollment, consume)
    with pytest.raises(IssueRepositoryPublicationRefusal, match="already_admitted"):
        client.admit_repository_publication(request)


def work_admitted(loop):
    _, _, workspace, plan, _, issue, request = loop
    original = issue.admit_repository_publication(request)
    bridge = WorkspaceIssuePublicationEnrollmentClient(
        workspace_client=workspace, issue_client=issue
    )
    work = bridge.enroll_issue_repository_publication(plan, original)
    return bridge, original, work


def test_workspace_work_admission_uses_original_issue_sdk_enrollment(loop):
    root, issue_path, workspace, plan, _, issue, _ = loop
    before = issue_path.read_bytes()
    bridge, original, work = work_admitted(loop)
    assert type(work) is WorkspacePublicationWorkAdmission
    assert work.phase == "enrolled"
    observed = issue.observe_repository_publication_admission(original)
    assert observed.phase == "enrolled"
    assert observed.consumer_ref == plan.binding.provider_ref
    assert observed.consumption_state == "not_consumed"
    assert observed.publication is None
    with pytest.raises(WorkspacePublicationHandleRefusal, match="already_enrolled"):
        bridge.enroll_issue_repository_publication(plan, original)
    assert (
        workspace.release_publication_work_admission(work).cleanup_state == "completed"
    )
    assert work.phase == "released"
    assert issue.observe_repository_publication_admission(original).phase == "released"
    assert issue_path.read_bytes() == before
    assert not (root / ".git/index").exists()


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_workspace_work_admission_cannot_be_copied(loop, operation):
    _, _, work = work_admitted(loop)
    with pytest.raises(TypeError):
        operation(work)


def test_workspace_work_admission_refuses_forged_foreign_and_decoded_inputs(loop):
    _, _, workspace, _, _, _, request = loop
    _, _, work = work_admitted(loop)
    with pytest.raises(TypeError):
        WorkspacePublicationWorkAdmission()
    with pytest.raises(WorkspacePublicationHandleRefusal, match="original_work"):
        workspace.release_publication_work_admission(
            object.__new__(WorkspacePublicationWorkAdmission)
        )
    foreign = WorkspaceRepositoryPublicationClient(
        WorkspaceRepositoryPublicationRuntime(workspace._provider._physical)
    )
    with pytest.raises(WorkspacePublicationHandleRefusal, match="original_work"):
        foreign.release_publication_work_admission(work)
    with pytest.raises(WorkspacePublicationHandleRefusal, match="original_work"):
        workspace.release_publication_work_admission(
            repository_publication_value_to_payload(request.binding)
        )


def test_workspace_bridge_refuses_a_forged_original_issue_admission(loop):
    _, _, workspace, plan, _, issue, _ = loop
    bridge = WorkspaceIssuePublicationEnrollmentClient(
        workspace_client=workspace, issue_client=issue
    )
    with pytest.raises(IssueRepositoryPublicationRefusal, match="original_handle"):
        bridge.enroll_issue_repository_publication(
            plan, object.__new__(IssueRepositoryPublicationAdmission)
        )
    with pytest.raises(WorkspacePublicationHandleRefusal, match="already_enrolled"):
        bridge.enroll_issue_repository_publication(plan, object())


def test_workspace_bridge_refuses_a_different_genuine_plan_binding(loop):
    _, _, workspace, plan, _, issue, request = loop
    original = issue.admit_repository_publication(request)
    other = workspace.plan_repository_commit(
        WorkspaceRepositoryCommitRequest(
            plan.binding.repository_ref,
            plan.binding.target_paths,
            "other candidate",
            "attempt:2",
        )
    )
    bridge = WorkspaceIssuePublicationEnrollmentClient(
        workspace_client=workspace, issue_client=issue
    )
    with pytest.raises(WorkspacePublicationHandleRefusal, match="correlation_mismatch"):
        bridge.enroll_issue_repository_publication(other, original)
    assert original.phase == "admitted"


def test_workspace_enrollment_callbacks_are_outside_workspace_registry_lock(
    loop, monkeypatch
):
    _, _, workspace, plan, _, issue, request = loop
    original = issue.admit_repository_publication(request)
    real = issue._provider.enroll_repository_publication
    entered = []

    def enroll(*args):
        with ThreadPoolExecutor(max_workers=1) as pool:
            acquired = pool.submit(workspace._provider._lock.acquire, True, 1).result()
            assert acquired
            pool.submit(workspace._provider._lock.release).result()
        entered.append(True)
        return real(*args)

    monkeypatch.setattr(issue._provider, "enroll_repository_publication", enroll)
    bridge = WorkspaceIssuePublicationEnrollmentClient(
        workspace_client=workspace, issue_client=issue
    )
    assert (
        bridge.enroll_issue_repository_publication(plan, original).phase == "enrolled"
    )
    assert entered == [True]


def test_released_workspace_plan_during_enrollment_retires_genuine_issue_enrollment(
    loop, monkeypatch
):
    _, _, workspace, plan, _, issue, request = loop
    original = issue.admit_repository_publication(request)
    real = issue._provider.enroll_repository_publication

    def enroll(*args):
        result = real(*args)
        workspace.release_repository_plan(plan)
        return result

    monkeypatch.setattr(issue._provider, "enroll_repository_publication", enroll)
    bridge = WorkspaceIssuePublicationEnrollmentClient(
        workspace_client=workspace, issue_client=issue
    )
    with pytest.raises(WorkspacePublicationHandleRefusal, match="plan_terminal"):
        bridge.enroll_issue_repository_publication(plan, original)
    assert original.phase == "released"


@pytest.mark.parametrize("interruption", [False, True])
def test_workspace_work_release_is_once_only_even_if_cleanup_is_unknown(
    loop, monkeypatch, interruption
):
    _, _, workspace, _, _, issue, _ = loop
    _, _, work = work_admitted(loop)
    real = issue._provider.release_repository_publication_enrollment
    calls = []

    def release(*args):
        calls.append(True)
        result = real(*args)
        if interruption:
            raise KeyboardInterrupt("after Issue release")
        return result

    monkeypatch.setattr(
        issue._provider, "release_repository_publication_enrollment", release
    )
    if interruption:
        with pytest.raises(KeyboardInterrupt):
            workspace.release_publication_work_admission(work)
    else:
        workspace.release_publication_work_admission(work)
    observed = workspace.release_publication_work_admission(work)
    assert observed.cleanup_state == ("unknown" if interruption else "completed")
    assert observed.ledger_complete is not interruption
    assert calls == [True]
    assert work.phase == "released"


@pytest.mark.parametrize("kind", ["changed_execution", "foreign_process"])
def test_workspace_work_admission_observation_checks_execution_and_process(
    loop, monkeypatch, kind
):
    _, _, workspace, _, _, _, _ = loop
    _, _, work = work_admitted(loop)
    if kind == "changed_execution":
        monkeypatch.setenv("CODEX_THREAD_ID", "changed")
    else:
        workspace._provider._pid += 1
    with pytest.raises(WorkspacePublicationHandleRefusal):
        _ = work.phase


def test_workspace_enrollment_interruption_preserves_unknown_without_blind_release(
    loop, monkeypatch
):
    _, _, workspace, plan, _, issue, request = loop
    original = issue.admit_repository_publication(request)
    real = issue._provider.enroll_repository_publication

    def enroll(*args):
        real(*args)
        raise KeyboardInterrupt("genuine enrollment returned no handle")

    def release(*args):
        raise AssertionError("No original enrollment returned: no blind release")

    monkeypatch.setattr(issue._provider, "enroll_repository_publication", enroll)
    monkeypatch.setattr(
        issue._provider, "release_repository_publication_enrollment", release
    )
    bridge = WorkspaceIssuePublicationEnrollmentClient(
        workspace_client=workspace, issue_client=issue
    )
    with pytest.raises(KeyboardInterrupt):
        bridge.enroll_issue_repository_publication(plan, original)
    retained = workspace._provider._work_by_plan[plan]
    assert retained.phase == "refused"
    assert retained.cleanup_state == "unknown"
    assert "issue_enrollment_return_unavailable" in retained.diagnostics
    b = plan.binding
    observation = workspace.observe_repository_attempt(
        WorkspaceRepositoryAttemptObserveRequest(
            b.repository_ref,
            b.binding_ref,
            b.attempt_ref,
            b.provider_ref,
            b.provider_generation,
            b.execution_id,
        )
    )
    assert not observation.ledger_complete
    assert "issue_enrollment_return_unavailable" in observation.diagnostics
    assert observation.result is None and observation.lock_release is None
    assert original.phase == "enrolled"
    # The caller still holds its original Issue admission; this observation
    # does not grant Workspace the missing enrollment or publication authority.
    assert (
        issue.release_repository_publication_admission(original).cleanup_state
        == "completed"
    )


def test_workspace_competing_enrollment_reserves_exact_plan_once(loop):
    _, _, workspace, plan, _, issue, request = loop
    original = issue.admit_repository_publication(request)
    bridge = WorkspaceIssuePublicationEnrollmentClient(
        workspace_client=workspace, issue_client=issue
    )

    def enroll():
        try:
            return bridge.enroll_issue_repository_publication(plan, original)
        except WorkspacePublicationHandleRefusal as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: enroll(), range(2)))
    assert (
        sum(type(result) is WorkspacePublicationWorkAdmission for result in results)
        == 1
    )
    assert (
        sum(
            getattr(result, "code", None) == "workspace_plan_already_enrolled"
            for result in results
        )
        == 1
    )
    assert original.phase == "enrolled"


@pytest.mark.parametrize(
    "failure",
    [
        "owner",
        "closed",
        "scope",
        "digest",
        "tag",
        "missing",
        "fifo",
        "symlink",
        "hardlink",
    ],
)
def test_source_refusals_before_issuance_are_typed_and_effect_free(loop, failure):
    root, issue, _, _, _, client, request = loop
    if failure == "owner":
        issue.write_text(issue.read_text().replace("codex-example", "codex-other"))
    elif failure == "closed":
        issue.write_text(issue.read_text().replace("In Progress", "Closed"))
    elif failure == "scope":
        issue.write_text(issue.read_text().replace("src/example.py", "other"))
    elif failure == "tag":
        issue.write_text(issue.read_text().replace(ISSUE_REF, "fb/2026-09-20/other"))
    elif failure != "digest":
        body = issue.read_bytes()
        issue.unlink()
        if failure == "fifo":
            os.mkfifo(issue)
        elif failure == "symlink":
            issue.symlink_to(root / "AGENTS.md")
        elif failure == "hardlink":
            other = root / "linked.md"
            other.write_bytes(body)
            os.link(other, issue)
    if failure in {"owner", "closed", "scope", "tag"}:
        request = replace(
            request,
            expected_issue_source_sha256="sha256:"
            + hashlib.sha256(issue.read_bytes()).hexdigest(),
        )
    elif failure == "digest":
        request = replace(request, expected_issue_source_sha256="sha256:" + "0" * 64)
    with pytest.raises(IssueRepositoryPublicationRefusal):
        client.admit_repository_publication(request)
    assert not (root / ".git/index").exists()


@pytest.mark.parametrize(
    "failure",
    [
        "content",
        "equal_byte_replacement",
        "closed",
        "scope",
        "missing",
        "fifo",
        "profile",
        "execution",
        "identity_unavailable",
    ],
)
def test_at_use_revalidation_retires_without_effects_or_replay(
    loop, monkeypatch, failure
):
    root, issue, _, _, _, client, _ = loop
    admission, enrollment, consume = enrolled(loop)
    body = issue.read_bytes()
    if failure == "content":
        issue.write_bytes(body + b"\n# drift\n")
    elif failure == "equal_byte_replacement":
        other = root / "replacement"
        other.write_bytes(body)
        other.replace(issue)
    elif failure == "closed":
        issue.write_text(issue.read_text().replace("In Progress", "Closed"))
    elif failure == "scope":
        issue.write_text(issue.read_text().replace("src/example.py", "other"))
    elif failure in {"missing", "fifo"}:
        issue.unlink()
        if failure == "fifo":
            os.mkfifo(issue)
    elif failure == "profile":
        manifest = root / "aware.protocol.toml"
        manifest.write_text(manifest.read_text().replace("docs/issues", "other/issues"))
    elif failure == "execution":
        monkeypatch.setenv("CODEX_THREAD_ID", "other")
    else:
        monkeypatch.delenv("CODEX_THREAD_ID")
    with pytest.raises(IssueRepositoryPublicationRefusal):
        client.consume_repository_publication(enrollment, consume)
    observed = client.observe_repository_publication_admission(admission)
    assert observed.phase == "refused"
    assert observed.consumption_state == "not_consumed"
    monkeypatch.setenv("CODEX_THREAD_ID", "example")
    with pytest.raises(IssueRepositoryPublicationRefusal, match="terminal"):
        client.consume_repository_publication(enrollment, consume)
    assert not (root / ".git/index").exists()


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_original_handles_no_copy_or_decode(loop, operation):
    *_, client, request = loop
    admission = client.admit_repository_publication(request)
    with pytest.raises(TypeError):
        operation(admission)
    with pytest.raises(ValueError):
        repository_publication_value_to_payload(admission)
    with pytest.raises(ValueError):
        repository_publication_value_from_payload(
            IssueRepositoryPublicationAdmission, {}
        )


@pytest.mark.parametrize(
    "field",
    [
        "workspace_binding_ref",
        "attempt_ref",
        "workspace_provider_ref",
        "workspace_provider_generation",
        "execution_id",
        "consumer_ref",
        "purpose",
    ],
)
def test_consume_correlations_do_not_authorize_changed_request(loop, field):
    *_, client, _request = loop
    _, enrollment, consume = enrolled(loop)
    altered = replace(
        consume, **{field: "index_reconciliation" if field == "purpose" else "other"}
    )
    with pytest.raises(IssueRepositoryPublicationRefusal, match="correlation"):
        client.consume_repository_publication(enrollment, altered)
    assert enrollment.phase == "enrolled"
    assert (
        client.consume_repository_publication(enrollment, consume).phase == "consumed"
    )


def test_foreign_forged_handles_and_structural_ports_refuse(loop):
    _, _, workspace, _, runtime, client, request = loop
    admission = client.admit_repository_publication(request)
    with pytest.raises(TypeError):
        IssueRepositoryPublicationAdmission()
    with pytest.raises(IssueRepositoryPublicationRefusal):
        client.observe_repository_publication_admission(
            object.__new__(IssueRepositoryPublicationAdmission)
        )
    other = IssueRepositoryPublicationClient(
        IssueRepositoryPublicationRuntime(
            source_port=runtime._source, workspace_client=workspace
        )
    )
    with pytest.raises(IssueRepositoryPublicationRefusal):
        other.observe_repository_publication_admission(admission)
    with pytest.raises(TypeError):
        IssueRepositoryPublicationRuntime(
            source_port=object(), workspace_client=workspace
        )


def test_competing_consumption_delivers_only_one_lease(loop, monkeypatch):
    *_, runtime, client, _request = loop
    admission, enrollment, consume = enrolled(loop)
    entered, proceed = Event(), Event()
    original = runtime._source.observe

    def held(issue_ref):
        entered.set()
        assert proceed.wait(5)
        return original(issue_ref)

    monkeypatch.setattr(runtime._source, "observe", held)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(client.consume_repository_publication, enrollment, consume)
        assert entered.wait(5)
        with pytest.raises(IssueRepositoryPublicationRefusal, match="terminal"):
            client.consume_repository_publication(enrollment, consume)
        proceed.set()
        assert first.result().phase == "consumed"
    assert (
        client.observe_repository_publication_admission(admission).consumption_state
        == "consumed"
    )


def test_interrupted_source_read_terminally_retires_enrollment(loop, monkeypatch):
    *_, runtime, client, _request = loop
    admission, enrollment, consume = enrolled(loop)

    def interrupted(*args):
        raise KeyboardInterrupt("injected source read interruption")

    monkeypatch.setattr(runtime._source, "observe", interrupted)
    with pytest.raises(IssueRepositoryPublicationRefusal) as captured:
        client.consume_repository_publication(enrollment, consume)
    assert isinstance(captured.value.__cause__, KeyboardInterrupt)
    assert admission.phase == "refused"
    assert (
        client.release_repository_publication_enrollment(enrollment).cleanup_state
        == "completed"
    )
    assert (
        client.release_repository_publication_admission(admission).cleanup_state
        == "completed"
    )


def test_consumed_authority_and_evidence_survive_cleanup(loop):
    *_, client, _request = loop
    admission, enrollment, consume = enrolled(loop)
    lease = client.consume_repository_publication(enrollment, consume)
    receipt = lease.receipt_ref
    client.release_repository_publication_admission(admission)
    observed = client.observe_repository_publication_admission(admission)
    assert observed.phase == "released" and observed.consumption_state == "consumed"
    assert observed.work_admission_receipt_ref == receipt
    assert observed.completion_state == "pending"
    assert lease.receipt_ref == receipt
    with pytest.raises(IssueRepositoryPublicationRefusal):
        client.consume_repository_publication(enrollment, consume)


def test_release_during_validation_cancels_without_resurrecting_custody(
    loop, monkeypatch
):
    *_, runtime, client, _request = loop
    admission, enrollment, consume = enrolled(loop)
    entered, proceed = Event(), Event()
    original = runtime._source.observe

    def held(issue_ref):
        entered.set()
        assert proceed.wait(5)
        return original(issue_ref)

    monkeypatch.setattr(runtime._source, "observe", held)
    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(client.consume_repository_publication, enrollment, consume)
        assert entered.wait(5)
        assert (
            client.release_repository_publication_admission(admission).cleanup_state
            == "completed"
        )
        proceed.set()
        with pytest.raises(IssueRepositoryPublicationRefusal, match="cancelled"):
            result.result()
    observation = client.observe_repository_publication_admission(admission)
    assert (
        observation.phase == "released"
        and observation.consumption_state == "not_consumed"
    )


def test_source_reads_restore_descriptors_on_success_and_refusal(loop):
    *_, runtime, client, request = loop
    before = len(os.listdir("/proc/self/fd"))
    admission, enrollment, consume = enrolled(loop)
    client.consume_repository_publication(enrollment, consume)
    for _ in range(30):
        runtime._source.observe(request.issue_ref)
        with pytest.raises(IssueRepositoryPublicationRefusal):
            client.admit_repository_publication(request)
    client.release_repository_publication_admission(admission)
    assert len(os.listdir("/proc/self/fd")) == before


def test_backend_replacement_and_unissued_clients_cannot_supply_verification(loop):
    *_, runtime, client, request = loop
    with pytest.raises(AttributeError):
        client._provider = object()
    with pytest.raises(AttributeError):
        runtime._workspace._provider = object()
    with pytest.raises(IssueRepositoryPublicationRefusal, match="not_issued"):
        object.__new__(IssueRepositoryPublicationClient).admit_repository_publication(
            request
        )


def test_forked_original_handles_refuse_without_parent_retirement(loop):
    *_, client, _request = loop
    admission, enrollment, consume = enrolled(loop)
    pid = os.fork()
    if pid == 0:
        try:
            client.consume_repository_publication(enrollment, consume)
        except IssueRepositoryPublicationRefusal:
            os._exit(0)
        except BaseException:  # noqa: BLE001 - child must report failures to the parent
            os._exit(2)
        os._exit(3)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert admission.phase == "enrolled"
    assert (
        client.consume_repository_publication(enrollment, consume).phase == "consumed"
    )


def test_reciprocal_sdk_calls_never_hold_issue_registry_lock(loop, monkeypatch):
    *_, runtime, client, _request = loop
    original = runtime._workspace.verify_repository_plan
    observed = []

    def verified(workspace_client, request):
        if workspace_client is runtime._workspace:
            assert not runtime._lock._is_owned()
            observed.append(request.binding.binding_ref)
        return original(request)

    monkeypatch.setattr(
        WorkspaceRepositoryPublicationClient, "verify_repository_plan", verified
    )
    _, enrollment, consume = enrolled(loop)
    client.consume_repository_publication(enrollment, consume)
    assert len(observed) == 2


@pytest.mark.parametrize("phase", ["admission", "enrollment"])
def test_released_workspace_plan_refuses_before_enrollment(loop, phase):
    _, _, workspace, plan, _, client, request = loop
    admission = (
        client.admit_repository_publication(request) if phase == "enrollment" else None
    )
    workspace.release_repository_plan(plan)
    assert not workspace.verify_repository_plan(
        WorkspaceRepositoryPlanVerificationRequest(plan.binding)
    ).original_plan_recognized
    with pytest.raises(
        IssueRepositoryPublicationRefusal, match="original_workspace_plan_required"
    ):
        if phase == "admission":
            client.admit_repository_publication(request)
        else:
            client.enroll_repository_publication(
                admission,
                IssueRepositoryPublicationEnrollmentRequest(
                    request.binding,
                    request.binding.workspace_provider_ref,
                    "repository_publication",
                ),
            )


def test_consumption_uses_retained_issue_enrollment_not_workspace_freshness(
    loop, monkeypatch
):
    root, _, workspace, plan, runtime, client, _ = loop
    admission, enrollment, consume = enrolled(loop)
    workspace.release_repository_plan(plan)

    class NoWorkspaceCallbacks:
        def __getattr__(self, name):
            raise AssertionError(
                f"Reciprocal Workspace access during consumption: {name}"
            )

    monkeypatch.setattr(runtime, "_workspace", NoWorkspaceCallbacks())
    lease = client.consume_repository_publication(enrollment, consume)
    assert lease.phase == "consumed"
    assert (
        client.observe_repository_publication_admission(admission).consumption_state
        == "consumed"
    )
    # The Workspace owner still rejects its released original plan. Issue's
    # independent scope spend is not permission to publish a stale plan. The
    # future writer transaction must enforce this same original-owner check.
    assert not workspace.verify_repository_plan(
        WorkspaceRepositoryPlanVerificationRequest(plan.binding)
    ).original_plan_recognized
    assert not (root / ".git/index").exists()


def test_consumption_under_original_repository_lock_makes_no_workspace_sdk_calls(
    loop, monkeypatch
):
    from aware_workspace_operator.commit import (
        _git_mutation_lock,
        _repository_mutation_lock_path,
    )

    root, _, _, _, _, client, _ = loop
    admission, enrollment, consume = enrolled(loop)
    callbacks = []

    def forbidden(*args, **kwargs):
        callbacks.append("unexpected_workspace_callback")
        raise AssertionError("Consumption must not call the reciprocal Workspace SDK")

    for method in (
        "plan_repository_commit",
        "verify_repository_plan",
        "observe_repository_attempt",
        "release_repository_plan",
    ):
        monkeypatch.setattr(WorkspaceRepositoryPublicationClient, method, forbidden)
    with _git_mutation_lock(
        repo_root=root,
        owner_id="codex-example",
        issue_tag=ISSUE_REF,
        command_summary="Issue consumption under original repository lock regression",
    ):
        # Confirm the real original flock is held, not just a fake lock flag.
        with (
            _repository_mutation_lock_path(repo_root=root).open("a+") as probe,
            pytest.raises(BlockingIOError),
        ):
            fcntl.flock(probe.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lease = client.consume_repository_publication(enrollment, consume)
        assert lease.phase == "consumed"
        with pytest.raises(IssueRepositoryPublicationRefusal, match="terminal"):
            client.consume_repository_publication(enrollment, consume)
    assert callbacks == []
    assert (
        client.observe_repository_publication_admission(admission).consumption_state
        == "consumed"
    )
    assert not (root / ".git/index").exists()

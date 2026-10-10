"""Genuine publication history observation, not closeout or installed proof."""

import subprocess
from dataclasses import replace

import pytest
from aware_workspace_sdk.repository_publication import (
    WorkspacePublicationHandleRefusal,
    WorkspacePublicationValueError,
    WorkspaceRepositoryPublicationClient,
    WorkspaceRepositoryPublicationObserveRequest,
)
from test_repository_publication import _writer_work
from test_repository_publication import loop as original_loop


@pytest.fixture(name="loop")
def observation_loop(tmp_path, monkeypatch):
    return original_loop.__wrapped__(tmp_path, monkeypatch)


def request_for(root, result, binding_ref=None):
    return WorkspaceRepositoryPublicationObserveRequest(
        str(root), "git:" + (result.commit_hash or result.candidate_commit), binding_ref
    )


def test_original_publication_observation_is_detached_and_non_authorizing(loop):
    root, _, workspace, plan, _, issue, _ = loop
    admission, work = _writer_work(loop)
    result = workspace.publish_repository_commit(plan, work)
    request = request_for(root, result, plan.binding.binding_ref)
    before = issue.observe_repository_publication_admission(admission)
    observed = workspace.observe_repository_publication(request)
    assert observed.request == request
    assert observed.receipt_state == "present"
    assert observed.reachability_state == "reachable"
    assert observed.commit_hash == result.commit_hash
    assert observed.binding == plan.binding
    assert observed.expected_binding_matches is True
    assert observed.result == result and observed.ledger_complete
    observed.result.original_writer_report.staged_paths.clear()
    assert workspace.observe_repository_publication(request).result == result
    assert (
        issue.observe_repository_publication_admission(admission).consumption_state
        == before.consumption_state
    )
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.publish_repository_commit(plan, work)


def test_publication_observation_requires_the_exact_retained_binding(loop):
    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    result = workspace.publish_repository_commit(plan, work)
    observed = workspace.observe_repository_publication(
        request_for(root, result, "other")
    )
    assert observed.receipt_state == "present"
    assert observed.expected_binding_matches is False
    assert observed.binding == plan.binding
    assert observed.result == result
    assert not observed.ledger_complete


def test_fresh_owner_does_not_reconstruct_authority_from_reachable_commit(loop):
    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    result = workspace.publish_repository_commit(plan, work)
    from aware_workspace_fs_adapter.repository_publication import (
        FilesystemRepositoryCandidatePort,
    )
    from aware_workspace_runtime.repository_publication import (
        WorkspaceRepositoryPublicationRuntime,
    )

    fresh = WorkspaceRepositoryPublicationClient(
        WorkspaceRepositoryPublicationRuntime(
            FilesystemRepositoryCandidatePort(repository_root=root)
        )
    )
    observed = fresh.observe_repository_publication(
        request_for(root, result, plan.binding.binding_ref)
    )
    assert observed.receipt_state == "present"
    assert observed.reachability_state == "reachable"
    assert observed.binding is None and observed.result is None
    assert observed.expected_binding_matches is None
    assert not observed.ledger_complete


def test_unknown_cas_is_not_resolved_by_receipt_reachability(loop, monkeypatch):
    from aware_workspace_fs_adapter import git_writer

    root, _, workspace, plan, _, issue, _ = loop
    admission, work = _writer_work(loop)
    original = git_writer._run_git

    def interrupted_return(**arguments):
        value = original(**arguments)
        if arguments["args"][:2] == ("git", "update-ref"):
            raise KeyboardInterrupt("CAS return unavailable")
        return value

    monkeypatch.setattr(git_writer, "_run_git", interrupted_return)
    result = workspace.publish_repository_commit(plan, work)
    assert result.publication_state == "unknown"
    observed = workspace.observe_repository_publication(
        request_for(root, result, plan.binding.binding_ref)
    )
    assert (
        observed.receipt_state == "present"
        and observed.reachability_state == "reachable"
    )
    assert observed.result == result
    assert observed.result.publication_state == "unknown"
    assert not observed.ledger_complete
    assert workspace.finish_repository_publication(work) == result
    assert (
        issue.observe_repository_publication_admission(admission).completion_state
        == "not_attempted"
    )


@pytest.mark.parametrize("error_type", (RuntimeError, KeyboardInterrupt))
def test_unavailable_physical_read_retains_known_result_without_inventing_reachability(
    loop, monkeypatch, error_type
):
    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    result = workspace.publish_repository_commit(plan, work)

    def unavailable(*arguments):
        raise error_type("physical observation unavailable")

    monkeypatch.setattr(
        workspace._provider._physical, "observe_publication_receipt", unavailable
    )
    observed = workspace.observe_repository_publication(request_for(root, result))
    assert observed.result == result
    assert observed.receipt_state == observed.reachability_state == "unknown"
    assert observed.commit_hash is None and not observed.ledger_complete
    assert result.publication_state == "published"


def test_absent_receipt_is_not_a_successful_negative_admission(loop):
    root, _, workspace, _, _, _, _ = loop
    observed = workspace.observe_repository_publication(
        WorkspaceRepositoryPublicationObserveRequest(str(root), "git:" + "1" * 40, None)
    )
    assert observed.receipt_state == "absent"
    assert observed.reachability_state == "unknown"
    assert observed.binding is None and observed.result is None
    assert observed.commit_hash is None and not observed.ledger_complete


@pytest.mark.parametrize("error_type", (OSError, KeyboardInterrupt))
def test_late_reachability_failure_preserves_observed_commit_presence(
    loop, monkeypatch, error_type
):
    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    result = workspace.publish_repository_commit(plan, work)
    original = subprocess.run

    def interrupted_read(arguments, **keywords):
        if "merge-base" in arguments:
            raise error_type("reachability read unavailable")
        return original(arguments, **keywords)

    monkeypatch.setattr(subprocess, "run", interrupted_read)
    observed = workspace.observe_repository_publication(request_for(root, result))
    assert observed.receipt_state == "present"
    assert observed.commit_hash == result.commit_hash
    assert observed.reachability_state == "unknown"
    assert observed.result == result and not observed.ledger_complete


@pytest.mark.parametrize("returncode", (2, 128))
def test_git_object_read_error_is_unknown_not_absent(loop, monkeypatch, returncode):
    root, _, workspace, _, _, _, _ = loop
    original = subprocess.run

    def failed_object_read(arguments, **keywords):
        if "cat-file" in arguments:
            return subprocess.CompletedProcess(arguments, returncode, b"", b"denied")
        return original(arguments, **keywords)

    monkeypatch.setattr(subprocess, "run", failed_object_read)
    observed = workspace.observe_repository_publication(
        WorkspaceRepositoryPublicationObserveRequest(str(root), "git:" + "1" * 40, None)
    )
    assert observed.receipt_state == observed.reachability_state == "unknown"
    assert observed.result is None and not observed.ledger_complete


def test_execution_change_refuses_before_physical_observation(loop, monkeypatch):
    root, _, workspace, _, _, _, _ = loop

    def forbidden(*arguments):
        pytest.fail("Changed execution must not invoke physical observation")

    monkeypatch.setattr(
        workspace._provider._physical, "observe_publication_receipt", forbidden
    )
    monkeypatch.setenv("CODEX_THREAD_ID", "different")
    with pytest.raises(
        WorkspacePublicationHandleRefusal, match="workspace_execution_changed"
    ):
        workspace.observe_repository_publication(
            WorkspaceRepositoryPublicationObserveRequest(
                str(root), "git:" + "1" * 40, None
            )
        )


def test_tree_object_is_not_a_publication_receipt(loop):
    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    workspace.publish_repository_commit(plan, work)
    tree = (
        subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD^{tree}"))
        .strip()
        .decode()
    )
    observed = workspace.observe_repository_publication(
        WorkspaceRepositoryPublicationObserveRequest(str(root), "git:" + tree, None)
    )
    assert observed.receipt_state == "absent"
    assert "workspace_receipt_not_commit" in observed.diagnostics


def test_dangling_real_candidate_remains_not_reachable(loop, monkeypatch):
    from aware_workspace_fs_adapter import git_writer

    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    original = git_writer._publish_staged_transaction
    (root / "foreign.txt").write_bytes(b"competitor\n")
    subprocess.run(("git", "-C", str(root), "add", "foreign.txt"), check=True)

    def race(**arguments):
        subprocess.run(
            ("git", "-C", str(root), "commit", "-qm", "competing commit"), check=True
        )
        return original(**arguments)

    monkeypatch.setattr(git_writer, "_publish_staged_transaction", race)
    result = workspace.publish_repository_commit(plan, work)
    observed = workspace.observe_repository_publication(request_for(root, result))
    assert observed.receipt_state == "present"
    assert observed.reachability_state == "not_reachable"
    assert observed.result == result
    assert observed.result.publication_state == "not_published"


@pytest.mark.parametrize(
    "receipt", ("HEAD", "git:HEAD", "git:" + "0" * 39, "git:" + "0" * 40 + "\n")
)
def test_malformed_receipt_refuses_before_provider_invocation(
    loop, monkeypatch, receipt
):
    root, _, workspace, _, _, _, _ = loop

    def forbidden(*arguments):
        pytest.fail("Malformed requests must not reach the provider")

    monkeypatch.setattr(
        workspace._provider, "observe_repository_publication", forbidden
    )
    with pytest.raises(WorkspacePublicationValueError):
        workspace.observe_repository_publication(
            WorkspaceRepositoryPublicationObserveRequest(str(root), receipt, None)
        )


def test_repository_mismatch_and_relocation_are_unknown_not_retargeted(loop, tmp_path):
    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    result = workspace.publish_repository_commit(plan, work)
    mismatched = replace(request_for(root, result), repository_ref=str(root.parent))
    observed = workspace.observe_repository_publication(mismatched)
    assert observed.result is None and observed.receipt_state == "unknown"
    relocated = root.parent / (root.name + "-relocated")
    root.rename(relocated)
    root.mkdir()
    observed = workspace.observe_repository_publication(request_for(root, result))
    assert observed.receipt_state == "unknown" and not observed.ledger_complete


def test_observation_does_not_take_mutation_lock_or_change_index(loop, monkeypatch):
    from aware_workspace_fs_adapter import git_writer

    root, _, workspace, plan, _, _, _ = loop
    _, work = _writer_work(loop)
    result = workspace.publish_repository_commit(plan, work)
    before = (root / ".git/index").read_bytes()

    def forbidden(*arguments, **keywords):
        pytest.fail("Read-only observation must not acquire mutation authority")

    monkeypatch.setattr(git_writer, "_git_mutation_lock", forbidden)
    monkeypatch.setattr(workspace._provider._physical, "begin", forbidden)
    monkeypatch.setattr(workspace._provider._physical, "publish", forbidden)
    monkeypatch.setattr(workspace._provider._physical, "release", forbidden)
    assert (
        workspace.observe_repository_publication(
            request_for(root, result)
        ).receipt_state
        == "present"
    )
    assert (root / ".git/index").read_bytes() == before

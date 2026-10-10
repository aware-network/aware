"""Same-original-provider orchestration, not legacy wire/CLI installation."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import fields, replace

import pytest
from aware_issue_sdk import IssueCloseRequest, IssueCommitWorkspaceRequest
from aware_issue_sdk.repository_publication import IssueRepositoryPublicationRefusal
from aware_workspace_sdk.repository_publication import (
    repository_publication_value_to_payload,
)
from test_repository_publication import loop as original_loop

ISSUE_PATH = "docs/issues/2026/09/20/fb-2026-09-20-example.md"


def _digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(name="composed")
def composed_loop(tmp_path, monkeypatch):
    root, source, workspace, _, runtime, issue, original = original_loop.__wrapped__(
        tmp_path, monkeypatch
    )
    source.write_text(
        source.read_text().replace(
            "- `src/example.py`", f"- `src/example.py`\n- `{ISSUE_PATH}`"
        )
    )
    for key, value in (
        ("user.name", "Aware Test"),
        ("user.email", "aware@example.invalid"),
    ):
        subprocess.run(("git", "-C", str(root), "config", key, value), check=True)
    request = IssueCommitWorkspaceRequest(
        original.issue_ref,
        _digest(source),
        ("src/example.py",),
        "Publish exact implementation",
        "codex-example",
        "evidence:composition",
        False,
    )
    return root, source, workspace, runtime, issue, request


def _close_request(composed, result):
    return IssueCloseRequest(
        issue_ref=composed[-1].issue_ref,
        expected_source_sha256=_digest(composed[1]),
        client_intent_id="close:composition",
        actor_ref="codex-example",
        actor_evidence_ref="evidence:composition-close",
        resolution="Completed",
        verified_by=("genuine source proofs",),
        publication_receipt_ref="git:" + result.commit_hash,
    )


def test_one_issue_sdk_normal_and_closeout_over_original_workspace_sdk(composed):
    root, source, _, _, issue, request = composed
    result, admission, cleanup = issue.commit_workspace(request)
    assert result.publication_state == "published", result
    assert result.admission_completion == admission.completion_state == "completed"
    assert cleanup and all(c.cleanup_state == "completed" for c in cleanup)
    assert len(fields(result.original_writer_report)) == 32
    full = repository_publication_value_to_payload(result)
    assert len(full["original_writer_report"]) == 32
    closed, parent, close_cleanup = issue.close_issue(_close_request(composed, result))
    assert closed.publication_state == "published", closed
    assert parent.completion_state == "completed" and parent.ledger_complete
    assert parent.closeout_publication_receipt_ref == "git:" + closed.commit_hash
    assert close_cleanup and all(c.cleanup_state == "completed" for c in close_cleanup)
    assert (
        subprocess.check_output(("git", "-C", str(root), "show", "HEAD:" + ISSUE_PATH))
        == source.read_bytes()
    )


def test_dry_run_has_no_writer_consumption_or_source_index_effect(
    composed, monkeypatch
):
    root, source, workspace, _, issue, request = composed
    before = source.read_bytes()

    def forbidden(*args):
        pytest.fail("Dry-run must not publish")

    monkeypatch.setattr(workspace._provider, "publish_repository_commit", forbidden)
    result, admission, cleanup = issue.commit_workspace(replace(request, dry_run=True))
    assert result is None
    assert admission.consumption_state == "not_consumed"
    assert admission.completion_state == "not_attempted"
    assert cleanup and all(c.cleanup_state == "completed" for c in cleanup)
    assert source.read_bytes() == before
    assert (
        subprocess.run(
            ("git", "-C", str(root), "rev-parse", "--verify", "HEAD"),
            capture_output=True,
            check=False,
        ).returncode
        != 0
    )


@pytest.mark.parametrize("kind", ["actor", "digest", "scope", "closed"])
def test_invalid_authority_refuses_before_workspace_plan(composed, monkeypatch, kind):
    _, source, workspace, _, issue, request = composed
    if kind == "actor":
        request = replace(request, actor_ref="codex-foreign")
    elif kind == "digest":
        request = replace(request, expected_issue_source_sha256="sha256:" + "0" * 64)
    elif kind == "scope":
        request = replace(request, target_paths=("outside.txt",))
    else:
        source.write_text(source.read_text().replace("In Progress", "Closed"))
        request = replace(request, expected_issue_source_sha256=_digest(source))

    def forbidden(*args):
        pytest.fail("Invalid authority must refuse before Workspace resources")

    monkeypatch.setattr(workspace._provider, "plan_repository_commit", forbidden)
    with pytest.raises(IssueRepositoryPublicationRefusal):
        issue.commit_workspace(request)


def test_same_input_shapes_do_not_authenticate_foreign_values(composed):
    issue = composed[4]
    with pytest.raises(TypeError):
        issue.commit_workspace(composed[-1].to_wire())
    with pytest.raises(TypeError):
        issue.close_issue({"issue_ref": composed[-1].issue_ref})


def test_known_publication_and_failed_observation_keep_full_result(
    composed, monkeypatch
):
    _, _, workspace, _, issue, request = composed

    def unavailable(*args):
        raise KeyboardInterrupt("observation unavailable after publication")

    # Finish also uses this port, so fail only the later orchestration read.
    original = workspace._provider.observe_repository_attempt
    calls = []

    def late(request):
        calls.append(request)
        if len(calls) > 1:
            unavailable()
        return original(request)

    monkeypatch.setattr(workspace._provider, "observe_repository_attempt", late)
    with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
        issue.commit_workspace(request)
    failure = raised.value
    assert failure.workspace_result.publication_state == "published"
    assert len(fields(failure.workspace_result.original_writer_report)) == 32
    assert failure.observation.consumption_state == "consumed"
    assert failure.cleanup_observations
    assert (
        len(calls) == 3
    )  # finish, failed read, one read-only fallback; no publication retry


@pytest.mark.parametrize("cas", ["known", "unknown"])
def test_closeout_unavailable_unlock_keeps_owner_results_no_rollback(
    composed, monkeypatch, cas
):
    from aware_workspace_fs_adapter import git_writer

    root, source, _, _, issue, request = composed
    implemented, _, _ = issue.commit_workspace(request)
    real_git = git_writer._run_git
    real_flock = git_writer.fcntl.flock

    def interrupted_git(**arguments):
        value = real_git(**arguments)
        if arguments["args"][:2] == ("git", "update-ref"):
            raise KeyboardInterrupt("CAS result unavailable")
        return value

    def interrupted_unlock(fd, operation):
        if operation == git_writer.fcntl.LOCK_UN:
            raise KeyboardInterrupt("unlock unavailable")
        return real_flock(fd, operation)

    if cas == "unknown":
        monkeypatch.setattr(git_writer, "_run_git", interrupted_git)
    monkeypatch.setattr(git_writer.fcntl, "flock", interrupted_unlock)
    result, parent, cleanup = issue.close_issue(_close_request(composed, implemented))
    assert result.publication_state == ("published" if cas == "known" else "unknown")
    assert result.lock_release.repository_lock_release == "unknown"
    assert parent.completion_state == "pending"
    assert not parent.ledger_complete
    assert (
        parent.publication_admission.publication.publication_state
        == result.publication_state
    )
    assert parent.source_observation.source_change_state == "applied"
    assert b"- Status: Closed" in source.read_bytes()
    assert (
        subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"))
        .strip()
        .decode()
        == result.candidate_commit
    )
    assert len(fields(result.original_writer_report)) == 32
    assert cleanup


def test_failed_closeout_plan_retains_applied_source_and_effect_evidence(
    composed, monkeypatch
):
    _, source, workspace, _, issue, request = composed
    result, _, _ = issue.commit_workspace(request)

    def refused(*args):
        raise RuntimeError("plan refused after authorized source CAS")

    monkeypatch.setattr(workspace._provider, "plan_repository_commit", refused)
    with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
        issue.close_issue(_close_request(composed, result))
    failure = raised.value
    assert failure.workspace_result is None
    assert failure.observation.source_observation.source_change_state == "applied"
    assert failure.observation.completion_state == "pending"
    assert b"- Status: Closed" in source.read_bytes()
    assert failure.cleanup_observations


@pytest.mark.parametrize("recapture", ["state", "observation"])
def test_applied_closeout_refusal_survives_unavailable_owner_recapture(
    composed, monkeypatch, recapture
):
    from aware_file_system.retained_mutation import RetainedPhysicalMutation

    root, source, workspace, runtime, issue, request = composed
    result, _, _ = issue.commit_workspace(request)
    real_finish = RetainedPhysicalMutation.finish
    real_replace = RetainedPhysicalMutation.replace_manifest
    real_observation = runtime._close_observation
    real_state = runtime._close_state
    replacements = []
    supplier_observations = []

    def replaced(holder):
        replacements.append(holder)
        return real_replace(holder)

    def interrupted_finish(holder):
        real_finish(holder)
        raise KeyboardInterrupt("Closed-source return interrupted after effects")

    def unavailable(*args):
        raise KeyboardInterrupt("owner recapture unavailable")

    def observe(state):
        observation = real_observation(state)
        if observation.source_observation is not None:
            supplier_observations.append(observation)
            # The genuine refusal has already captured applied effects. Only
            # subsequent orchestration recapture is unavailable.
            monkeypatch.setattr(
                runtime,
                "_close_state" if recapture == "state" else "_close_observation",
                unavailable,
            )
        return observation

    def no_publication_plan(*args):
        pytest.fail("Refused source transition must not plan publication")

    monkeypatch.setattr(RetainedPhysicalMutation, "replace_manifest", replaced)
    monkeypatch.setattr(RetainedPhysicalMutation, "finish", interrupted_finish)
    monkeypatch.setattr(runtime, "_close_observation", observe)
    monkeypatch.setattr(
        workspace._provider, "plan_repository_commit", no_publication_plan
    )
    with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
        issue.close_issue(_close_request(composed, result))

    failure = raised.value
    original = failure.__cause__
    assert isinstance(original, IssueRepositoryPublicationRefusal)
    assert original.observation == supplier_observations[0]
    assert original.observation.source_observation.source_change_state == "applied"
    assert (
        failure.observation.source_observation
        == original.observation.source_observation
    )
    assert failure.observation == replace(original.observation, ledger_complete=False)
    assert not failure.observation.ledger_complete
    assert "issue_observation_unavailable:KeyboardInterrupt" in failure.diagnostics
    assert failure.workspace_result is None
    assert len(replacements) == 1
    assert b"- Status: Closed" in source.read_bytes()
    assert (
        subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"))
        .strip()
        .decode()
        == result.commit_hash
    )
    monkeypatch.setattr(runtime, "_close_state", real_state)
    monkeypatch.setattr(runtime, "_close_observation", real_observation)
    parent = runtime._repository_operations[-1].parent
    with pytest.raises(IssueRepositoryPublicationRefusal):
        issue.apply_repository_closeout_source(parent)
    assert len(replacements) == 1


def test_fresh_runtime_cannot_close_based_on_reachable_receipt(composed):
    from aware_issue_operational_runtime.repository_publication import (
        IssueRepositoryPublicationRuntime,
    )
    from aware_issue_sdk.repository_publication import IssueRepositoryPublicationClient

    _, source, workspace, runtime, issue, request = composed
    result, _, _ = issue.commit_workspace(request)
    fresh = IssueRepositoryPublicationClient(
        IssueRepositoryPublicationRuntime(
            source_port=runtime._source,
            workspace_client=workspace,
        )
    )
    before = source.read_bytes()
    with pytest.raises(
        IssueRepositoryPublicationRefusal, match="original_issue_completion_required"
    ):
        fresh.close_issue(_close_request(composed, result))
    assert source.read_bytes() == before


def test_late_logical_cleanup_failure_carries_known_result(composed, monkeypatch):
    _, _, workspace, _, issue, request = composed
    real = workspace._provider.release_publication_work_admission
    calls = []

    def interrupted(work):
        calls.append(work)
        real(work)
        raise KeyboardInterrupt("logical cleanup return unavailable")

    monkeypatch.setattr(
        workspace._provider, "release_publication_work_admission", interrupted
    )
    with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
        issue.commit_workspace(request)
    assert raised.value.workspace_result.publication_state == "published"
    assert raised.value.observation.completion_state == "completed"
    assert (
        "orchestration_cleanup:KeyboardInterrupt"
        in raised.value.observation.diagnostics
    )
    assert len(calls) == 1


def test_real_writer_preserves_foreign_staging_through_runtime(composed):
    root, _, _, _, issue, request = composed
    (root / "foreign.txt").write_bytes(b"foreign\n")
    subprocess.run(("git", "-C", str(root), "add", "foreign.txt"), check=True)
    result, _, _ = issue.commit_workspace(request)
    assert result.publication_state == "published", result
    assert (
        subprocess.check_output(("git", "-C", str(root), "show", ":foreign.txt"))
        == b"foreign\n"
    )


@pytest.mark.parametrize("kind", ["returned_then_interrupted", "read_unavailable"])
def test_unreturned_publication_is_observed_without_effect_retry(
    composed, monkeypatch, kind
):
    _, _, workspace, _, issue, request = composed
    real = workspace._provider.publish_repository_commit
    calls = []

    def interrupted(plan, work):
        calls.append((plan, work))
        real(plan, work)
        raise KeyboardInterrupt("publication return unavailable")

    monkeypatch.setattr(workspace._provider, "publish_repository_commit", interrupted)
    if kind == "read_unavailable":
        original = workspace._provider.observe_repository_attempt
        observed = []

        def late(request):
            observed.append(request)
            if len(observed) > 1:
                raise RuntimeError("original retained result unavailable")
            return original(request)

        monkeypatch.setattr(workspace._provider, "observe_repository_attempt", late)
    with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
        issue.commit_workspace(request)
    assert len(calls) == 1
    failure = raised.value
    if kind == "returned_then_interrupted":
        assert failure.workspace_result.publication_state == "published"
        assert failure.workspace_observation.result == failure.workspace_result
    else:
        assert failure.workspace_result is None
        assert failure.workspace_observation is None
        assert "workspace_observation_unavailable:RuntimeError" in failure.diagnostics
        assert failure.observation.publication.publication_state == "published"


@pytest.mark.parametrize("point", ["enroll", "plan"])
def test_early_orchestration_refusal_is_typed_effect_free(composed, monkeypatch, point):
    root, source, workspace, _, issue, request = composed
    before = source.read_bytes()

    def unavailable(*args, **kwargs):
        raise KeyboardInterrupt("original provider unavailable")

    monkeypatch.setattr(
        workspace._provider,
        "enroll_issue_repository_publication"
        if point == "enroll"
        else "plan_repository_commit",
        unavailable,
    )
    with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
        issue.commit_workspace(request)
    assert raised.value.workspace_result is None
    assert source.read_bytes() == before
    assert (
        subprocess.run(
            ("git", "-C", str(root), "rev-parse", "--verify", "HEAD"),
            capture_output=True,
            check=False,
        ).returncode
        != 0
    )


def test_late_issue_projection_failure_cannot_erase_full_workspace_result(
    composed, monkeypatch
):
    _, _, _, runtime, issue, request = composed
    original = runtime.observe_repository_publication_admission
    calls = []

    def late(admission):
        calls.append(admission)
        # Admission/enrollment observations succeed; refuse only after the
        # completed operation's cleanup. Both result and failure observations.
        if runtime._repository_operations:
            raise KeyboardInterrupt("late Issue projection unavailable")
        return original(admission)

    monkeypatch.setattr(runtime, "observe_repository_publication_admission", late)
    with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
        issue.commit_workspace(request)
    assert raised.value.workspace_result.publication_state == "published"
    assert raised.value.workspace_result.admission_completion == "completed"
    assert len(fields(raised.value.workspace_result.original_writer_report)) == 32


def test_late_owner_identity_failure_preserves_known_workspace_effect(
    composed, monkeypatch
):
    _, _, workspace, runtime, issue, request = composed
    real = workspace._provider.publish_repository_commit

    def changed_owner(plan, work):
        result = real(plan, work)
        runtime._pid += 1
        return result

    monkeypatch.setattr(workspace._provider, "publish_repository_commit", changed_owner)
    try:
        with pytest.raises(IssueRepositoryPublicationRefusal) as raised:
            issue.commit_workspace(request)
        assert raised.value.workspace_result.publication_state == "published"
        assert not raised.value.observation.ledger_complete
        assert any(
            code.startswith("issue_observation_unavailable:")
            for code in raised.value.diagnostics
        )
    finally:
        runtime._pid -= 1

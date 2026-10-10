"""Fresh purpose-limited SDK recovery over real publication and original IO."""

import hashlib
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import astuple, replace

import pytest
from aware_issue_sdk.repository_publication import (
    IssueRepositoryPublicationBinding,
    IssueRepositoryPublicationRefusal,
    IssueRepositoryPublicationRequest,
)
from aware_workspace_sdk.repository_publication import (
    WorkspaceIssuePublicationEnrollmentClient,
    WorkspacePublicationHandleRefusal,
    WorkspacePublicationWorkAdmission,
    WorkspaceRepositoryIndexReconcileRequest,
    WorkspaceRepositoryPlanVerificationRequest,
    WorkspaceRepositoryPublicationClient,
    WorkspaceRepositoryPublicationObserveRequest,
)
from test_repository_runtime_orchestration import composed_loop

composed = composed_loop


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


@pytest.fixture
def debt(composed, monkeypatch):
    from aware_workspace_fs_adapter import git_writer as writer

    root, _, _, _, issue, request = composed
    first, _, _ = issue.commit_workspace(request)
    assert first.publication_state == "published"
    (root / "src/example.py").write_bytes(b"second governed postimage\n")
    with monkeypatch.context() as injection:
        injection.setattr(
            writer,
            "_project_shared_index_atomically",
            lambda **_: "review:forced_projection_failure",
        )
        published, _, _ = issue.commit_workspace(request)
    assert published.publication_state == "published"
    assert published.reference_update == "cas_applied"
    assert published.index_reconciliation_pending is True
    assert published.index_projection == "failed"
    reconciliation = WorkspaceRepositoryIndexReconcileRequest(
        str(root),
        "git:" + published.commit_hash,
        request.target_paths,
        "reconciliation:fresh",
        published.commit_hash,
    )
    return composed, published, reconciliation


def _admit(debt, request=None):
    composed, _, original_request = debt
    _, source, workspace, _, issue, original_operation = composed
    request = request or original_request
    plan = workspace.plan_repository_index_reconciliation(request)
    issue_request = IssueRepositoryPublicationRequest(
        original_operation.issue_ref,
        "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
        IssueRepositoryPublicationBinding(*astuple(plan.binding)),
    )
    admission = issue.admit_repository_index_reconciliation(issue_request)
    work = WorkspaceIssuePublicationEnrollmentClient(
        workspace_client=workspace,
        issue_client=issue,
    ).enroll_issue_repository_publication(plan, admission)
    return plan, issue_request, admission, work


def test_real_debt_is_reconciled_without_reference_update_or_history_rewrite(
    debt,
    monkeypatch,
):
    composed, previous, request = debt
    root, source, workspace, _, issue, _ = composed
    (root / "foreign.txt").write_bytes(b"foreign staging\n")
    subprocess.run(["git", "-C", str(root), "add", "foreign.txt"], check=True)
    foreign = _git(root, "ls-files", "--stage", "--", "foreign.txt")
    issue_body = source.read_bytes()
    before = _git(root, "rev-parse", "HEAD")
    plan, _, admission, work = _admit(debt)

    def forbidden(*args, **kwargs):
        pytest.fail(
            "Reconciliation must not invoke publication or reciprocal consumption"
        )

    monkeypatch.setattr(workspace._provider._physical, "publish", forbidden)
    monkeypatch.setattr(issue._provider, "_verify_plan", forbidden)
    result = workspace.reconcile_repository_index(request, work)
    assert result.reconciliation_state == "applied", result
    assert result.ledger_complete
    assert result.result.publication_state == "not_published"
    assert result.result.reference_update == "not_run"
    assert result.result.admission_completion == "completed"
    assert result.result.index_reconciliation_pending is False
    assert result.lock_release.repository_lock_release == "confirmed_released"
    assert all(
        effect.kind != "repository_reference_update" for effect in result.effects
    )
    assert _git(root, "rev-parse", "HEAD") == before
    assert _git(root, "rev-list", "--count", "HEAD").strip() == b"2"
    assert not _git(root, "diff", "--cached", "--name-only", "--", "src/example.py")
    assert _git(root, "ls-files", "--stage", "--", "foreign.txt") == foreign
    assert source.read_bytes() == issue_body
    assert (
        issue.observe_repository_publication_admission(admission).purpose
        == "index_reconciliation"
    )
    assert previous.index_reconciliation_pending is True
    original_history = workspace.observe_repository_publication(
        WorkspaceRepositoryPublicationObserveRequest(
            str(root),
            request.publication_receipt_ref,
            previous.binding_ref,
        )
    )
    assert original_history.result == previous
    assert original_history.expected_binding_matches is True
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.reconcile_repository_index(request, work)
    workspace.release_publication_work_admission(work)
    workspace.release_repository_plan(plan)


def test_index_plan_cannot_be_enrolled_or_invoked_as_publication(debt):
    composed, _, request = debt
    _, _, workspace, _, issue, _ = composed
    plan, issue_request, admission, work = _admit(debt)
    assert workspace.verify_repository_index_reconciliation_plan(
        WorkspaceRepositoryPlanVerificationRequest(plan.binding)
    ).original_plan_recognized
    assert not workspace.verify_repository_plan(
        WorkspaceRepositoryPlanVerificationRequest(plan.binding)
    ).original_plan_recognized
    with pytest.raises(IssueRepositoryPublicationRefusal):
        issue.admit_repository_publication(issue_request)
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.publish_repository_commit(plan, work)
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.reconcile_repository_index(
            replace(request, publication_receipt_ref="git:" + "0" * 40),
            work,
        )
    assert work.phase == "enrolled" and plan.phase == "planned"
    assert (
        issue.observe_repository_publication_admission(admission).consumption_state
        == "not_consumed"
    )


@pytest.mark.parametrize(
    "field", ["expected_head", "publication_receipt_ref", "target_paths"]
)
def test_wrong_source_coordinates_refuse_before_admission_or_index_io(debt, field):
    composed, _, request = debt
    root, _, workspace, _, _, _ = composed
    before = (root / ".git/index").read_bytes()
    captures = len(workspace._provider._physical._captures)
    bad = {
        "expected_head": "0" * 40,
        "publication_receipt_ref": "git:" + "0" * 40,
        "target_paths": ("foreign.txt",),
    }[field]
    with pytest.raises(ValueError):
        workspace.plan_repository_index_reconciliation(replace(request, **{field: bad}))
    assert (root / ".git/index").read_bytes() == before
    assert len(workspace._provider._physical._captures) == captures


@pytest.mark.parametrize("mode", ["source", "issue", "foreign_stage"])
def test_at_use_fences_preserve_foreign_work_and_refuse_retry(debt, mode):
    composed, _, request = debt
    root, source, workspace, _, issue, _ = composed
    plan, _, admission, work = _admit(debt)
    path = root / "src/example.py"
    if mode == "issue":
        source.write_bytes(source.read_bytes() + b"\nforeign Issue update\n")
    elif mode == "source":
        path.write_bytes(b"foreign source\n")
    else:
        body = path.read_bytes()
        path.write_bytes(b"foreign owned-path staging\n")
        subprocess.run(["git", "-C", str(root), "add", "src/example.py"], check=True)
        path.write_bytes(body)
    before = (root / ".git/index").read_bytes()
    head = _git(root, "rev-parse", "HEAD")
    result = workspace.reconcile_repository_index(request, work)
    assert result.reconciliation_state != "applied"
    assert (root / ".git/index").read_bytes() == before
    assert _git(root, "rev-parse", "HEAD") == head
    assert plan.phase == "spent"
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.reconcile_repository_index(request, work)
    observed = issue.observe_repository_publication_admission(admission)
    if mode in {"source", "issue"}:
        assert observed.consumption_state == "not_consumed"
    else:
        assert observed.consumption_state == "consumed"


@pytest.mark.parametrize("release_unavailable", [False, True])
def test_applied_index_with_interrupted_return_stays_unknown_and_spent(
    debt,
    monkeypatch,
    release_unavailable,
):
    from aware_workspace_fs_adapter import git_writer as writer

    composed, original, request = debt
    root, _, workspace, _, issue, _ = composed
    _, _, admission, work = _admit(debt)
    projection = writer._project_shared_index_atomically

    def interrupted(**kwargs):
        assert projection(**kwargs) is None
        raise KeyboardInterrupt("index return unavailable")

    monkeypatch.setattr(writer, "_project_shared_index_atomically", interrupted)
    if release_unavailable:
        physical = workspace._provider._physical
        release = physical.release

        def unavailable(*args):
            release(*args)
            raise KeyboardInterrupt("release return unavailable")

        def no_observation(*args):
            raise OSError("physical ledger unavailable")

        monkeypatch.setattr(physical, "release", unavailable)
        monkeypatch.setattr(physical, "observe_transaction", no_observation)
    result = workspace.reconcile_repository_index(request, work)
    assert result.reconciliation_state == "unknown"
    assert result.ledger_complete is False
    assert result.result.admission_completion != "completed"
    assert any(
        effect.kind == "shared_index_projection" and effect.state == "unknown"
        for effect in result.effects
    )
    assert (
        issue.observe_repository_publication_admission(admission).consumption_state
        == "consumed"
    )
    assert (
        original.reference_update == "cas_applied"
        and original.index_reconciliation_pending
    )
    assert not _git(root, "diff", "--cached", "--name-only", "--", "src/example.py")
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.reconcile_repository_index(request, work)


def test_forged_and_retired_admissions_refuse_without_index_effects(debt):
    composed, _, request = debt
    root, _, workspace, _, _, _ = composed
    plan, _, _, work = _admit(debt)
    before = (root / ".git/index").read_bytes()
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.reconcile_repository_index(
            request,
            object.__new__(WorkspacePublicationWorkAdmission),
        )
    workspace.release_publication_work_admission(work)
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.reconcile_repository_index(request, work)
    assert (root / ".git/index").read_bytes() == before
    workspace.release_repository_plan(plan)


def test_head_advance_after_admission_refuses_before_consumption(debt):
    composed, _, request = debt
    root, _, workspace, _, issue, original_operation = composed
    _, _, admission, work = _admit(debt)
    (root / "src/example.py").write_bytes(b"later separately governed version\n")
    later, _, _ = issue.commit_workspace(original_operation)
    assert later.publication_state == "published"
    before = (root / ".git/index").read_bytes()
    result = workspace.reconcile_repository_index(request, work)
    assert result.reconciliation_state != "applied"
    assert (root / ".git/index").read_bytes() == before
    assert _git(root, "rev-parse", "HEAD").strip().decode() == later.commit_hash
    assert (
        issue.observe_repository_publication_admission(admission).consumption_state
        == "not_consumed"
    )
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.reconcile_repository_index(request, work)


@pytest.mark.parametrize("mode", ["foreign_provider", "process", "retired_plan"])
def test_original_owner_guards_precede_reconciliation_io(debt, mode, monkeypatch):
    composed, _, request = debt
    root, _, workspace, _, _, _ = composed
    plan, _, _, work = _admit(debt)
    before = (root / ".git/index").read_bytes()
    if mode == "foreign_provider":
        selected = WorkspaceRepositoryPublicationClient.filesystem(repository_root=root)
    else:
        selected = workspace
        if mode == "process":
            monkeypatch.setattr(workspace._provider, "_pid", -1)
        else:
            workspace.release_repository_plan(plan)
    with pytest.raises(WorkspacePublicationHandleRefusal):
        selected.reconcile_repository_index(request, work)
    assert (root / ".git/index").read_bytes() == before


def test_concurrent_replay_spends_only_one_original_enrollment(debt, monkeypatch):
    from aware_workspace_fs_adapter import git_writer as writer

    composed, _, request = debt
    root, _, workspace, _, issue, _ = composed
    _, _, admission, work = _admit(debt)
    projection = writer._project_shared_index_atomically
    calls = []

    def counted(**kwargs):
        calls.append(kwargs["candidate_commit"])
        return projection(**kwargs)

    monkeypatch.setattr(writer, "_project_shared_index_atomically", counted)
    with ThreadPoolExecutor(max_workers=2) as workers:
        attempts = [
            workers.submit(workspace.reconcile_repository_index, request, work)
            for _ in range(2)
        ]
        completed, refused = [], []
        for attempt in attempts:
            try:
                completed.append(attempt.result(timeout=30))
            except WorkspacePublicationHandleRefusal as error:
                refused.append(error)
    assert len(completed) == len(refused) == len(calls) == 1
    assert completed[0].reconciliation_state == "applied"
    assert (
        issue.observe_repository_publication_admission(admission).consumption_state
        == "consumed"
    )
    assert _git(root, "rev-list", "--count", "HEAD").strip() == b"2"


@pytest.mark.parametrize("foreign_index", [False, True])
@pytest.mark.parametrize("discard_debt", [False, True])
def test_genesis_index_recovery_requires_original_debt(
    composed,
    monkeypatch,
    foreign_index,
    discard_debt,
):
    from aware_workspace_fs_adapter import git_writer as writer

    root, _, workspace, _, issue, operation = composed
    if foreign_index:
        (root / "foreign.txt").write_bytes(b"foreign genesis staging\n")
        subprocess.run(["git", "-C", str(root), "add", "foreign.txt"], check=True)
    foreign = _git(root, "ls-files", "--stage", "--", "foreign.txt")
    with monkeypatch.context() as injection:
        injection.setattr(
            writer, "_project_shared_index_atomically", lambda **_: "forced:missing"
        )
        published, _, _ = issue.commit_workspace(operation)
    assert (
        published.publication_state == "published"
        and published.index_reconciliation_pending
    )
    assert (root / ".git/index").exists() is foreign_index
    debts = tuple((root / ".git/aware-transactions").glob("index-projection-*.json"))
    assert debts
    if discard_debt:
        for debt_path in debts:
            debt_path.unlink()
    request = WorkspaceRepositoryIndexReconcileRequest(
        str(root),
        "git:" + published.commit_hash,
        operation.target_paths,
        "reconciliation:genesis",
        published.commit_hash,
    )
    _, _, admission, work = _admit((composed, published, request))
    result = workspace.reconcile_repository_index(request, work)
    assert (result.reconciliation_state == "applied") is not discard_debt
    assert result.result.index_reconciliation_pending is discard_debt
    assert (root / ".git/index").exists() is (foreign_index or not discard_debt)
    assert _git(root, "ls-files", "--stage", "--", "foreign.txt") == foreign
    assert result.result.reference_update == "not_run"
    assert result.result.publication_state == "not_published"
    if not discard_debt:
        for path in operation.target_paths:
            assert _git(root, "show", ":" + path) == (root / path).read_bytes()
        assert not tuple(
            (root / ".git/aware-transactions").glob("index-projection-*.json")
        )
    assert _git(root, "rev-list", "--count", "HEAD").strip() == b"1"
    assert (
        issue.observe_repository_publication_admission(admission).consumption_state
        == "consumed"
    )
    with pytest.raises(WorkspacePublicationHandleRefusal):
        workspace.reconcile_repository_index(request, work)


def test_recovery_does_not_upgrade_original_unknown_cas(composed, monkeypatch):
    from aware_workspace_fs_adapter import git_writer as writer

    root, _, workspace, _, issue, operation = composed
    initial, _, _ = issue.commit_workspace(operation)
    assert initial.publication_state == "published"
    (root / "src/example.py").write_bytes(b"uncertain CAS version\n")
    run_git = writer._run_git

    def interrupted_cas(**kwargs):
        value = run_git(**kwargs)
        if kwargs["args"][:2] == ("git", "update-ref"):
            raise KeyboardInterrupt(
                "CAS return unavailable after actual reference effect"
            )
        return value

    with monkeypatch.context() as injection:
        injection.setattr(writer, "_run_git", interrupted_cas)
        previous, _, _ = issue.commit_workspace(operation)
    assert previous.publication_state == "unknown" and not previous.ledger_complete
    existing = _git(root, "rev-parse", "HEAD").strip().decode()
    request = WorkspaceRepositoryIndexReconcileRequest(
        str(root),
        "git:" + existing,
        operation.target_paths,
        "reconciliation:uncertain-predecessor",
        existing,
    )
    journals = tuple(
        (root / ".git/aware/transactions").glob("repository-reference-*.json")
    )
    assert journals
    before = {path: path.read_bytes() for path in journals}
    _, _, _, work = _admit((composed, previous, request))
    recovered = workspace.reconcile_repository_index(request, work)
    assert recovered.reconciliation_state == "applied", recovered
    history = workspace.observe_repository_publication(
        WorkspaceRepositoryPublicationObserveRequest(
            str(root),
            "git:" + existing,
            previous.binding_ref,
        )
    )
    assert history.result == previous
    assert history.result.publication_state == "unknown"
    assert history.ledger_complete is False
    assert recovered.result.publication_state == "not_published"
    assert recovered.result.reference_update == "not_run"
    assert _git(root, "rev-parse", "HEAD").strip().decode() == existing
    assert {path: path.read_bytes() for path in journals} == before
